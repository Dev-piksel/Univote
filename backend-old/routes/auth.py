from fastapi import APIRouter, HTTPException, status, Depends, Request
from database import get_async_supabase
from passlib.hash import argon2
from datetime import timedelta
from services import audit_service
from deps import create_access_token, get_current_user, AuthUser
from models import LoginRequest, RegisterRequest
from limiter import limiter

router = APIRouter()


ACCESS_TOKEN_EXPIRE_MINUTES = 60 * 24  # 1 day


@router.post("/login")
@limiter.limit("5/minute")
async def login(request: Request, body: LoginRequest):
    """Sign in via the custom admins/advisers tables using Argon2 and return PyJWT."""
    # Check admins first
    supabase = await get_async_supabase()
    admin_check = (
        await supabase.table("admins")
        .select("id, full_name, password_hash")
        .eq("id_number", body.username)
        .execute()
    )
    user = None
    role = None

    if admin_check.data:
        user = admin_check.data[0]
        role = "admin"
    else:
        # Check advisers next
        adviser_check = (
            await supabase.table("advisers")
            .select("id, full_name, password_hash, must_change_password")
            .eq("id_number", body.username)
            .execute()
        )
        if adviser_check.data:
            user = adviser_check.data[0]
            role = "adviser"

    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid credentials."
        )

    # Verify password with Argon2
    if not argon2.verify(body.password, user["password_hash"]):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid credentials."
        )

    # Generate token
    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": user["id"], "role": role}, expires_delta=access_token_expires
    )

    # Log login event
    await audit_service.log_session(
        user_id=user["id"], user_role=role, event_type="LOGIN", request=request
    )

    return {
        "access_token": access_token,
        "token_type": "bearer",
        "role": role,
        "full_name": user["full_name"],
        "user_id": user["id"],
        "must_change_password": bool(user.get("must_change_password")) if role == "adviser" else False,
    }


@router.post("/register")
@limiter.limit("3/hour")
async def register(request: Request, body: RegisterRequest):
    """Create a raw database account using Argon2 hashing."""
    if body.role not in ("admin", "adviser"):
        raise HTTPException(
            status_code=400, detail="Role must be 'admin' or 'adviser'."
        )

    # Hash password
    hashed_password = argon2.hash(body.password)

    # Check if email exists in either table to prevent duplicates
    try:
        supabase = await get_async_supabase()
        admin_exists = (
            await supabase.table("admins")
            .select("id")
            .eq("id_number", body.username)
            .execute()
        )
        adviser_exists = (
            await supabase.table("advisers")
            .select("id")
            .eq("id_number", body.username)
            .execute()
        )

        if admin_exists.data or adviser_exists.data:
            raise HTTPException(status_code=400, detail="ID Number already registered.")

        if body.role == "admin":
            payload = {
                "id_number": body.username,
                "full_name": body.full_name,
                "password_hash": hashed_password,
                "email": f"{body.username}@univote.temp",
            }
            res = await supabase.table("admins").insert(payload).execute()
        else:
            payload = {
                "id_number": body.username,
                "full_name": body.full_name,
                "password_hash": hashed_password,
                "email": f"{body.username}@univote.temp",
            }
            if body.department:
                payload["department"] = body.department
            res = await supabase.table("advisers").insert(payload).execute()

        if not res.data:
            raise Exception("Failed to insert user into database.")

        # Log registration event
        new_user = res.data[0]
        await audit_service.log_session(
            user_id=new_user["id"],
            user_role=body.role,
            event_type="REGISTER",
            request=request,
            details={"username": body.username, "full_name": body.full_name},
        )

    except HTTPException:
        raise
    except Exception as e:
        print(f"Registration error: {str(e)}")
        raise HTTPException(
            status_code=500, detail=f"Database error during registration: {str(e)}"
        )

    return {
        "message": f"{body.role.capitalize()} registered successfully. Please log in."
    }


@router.get("/me")
async def get_me(user: AuthUser = Depends(get_current_user)):
    """Retrieve user details for frontend validation using JWT."""
    supabase = await get_async_supabase()
    admin = (
        await supabase.table("admins")
        .select("id, full_name, email")
        .eq("id", user.id)
        .execute()
    )
    if admin.data:
        return {
            "role": "admin",
            "full_name": admin.data[0]["full_name"],
            "email": admin.data[0]["email"],
        }

    adviser = (
        await supabase.table("advisers")
        .select("id, full_name, email, department")
        .eq("id", user.id)
        .execute()
    )
    if adviser.data:
        return {"role": "adviser", **adviser.data[0]}

    raise HTTPException(status_code=404, detail="User profile not found.")
