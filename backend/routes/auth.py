from fastapi import APIRouter, HTTPException, status, Depends, Request
from database import get_async_supabase
from passlib.hash import argon2
from datetime import timedelta
from services import audit_service
from dependencies.auth import get_current_user
from models import LoginRequest, RegisterRequest, SuperAdminSetup, AuthUser
from utils.common import build_full_name
from limiter import limiter
from utils.jwt import create_access_token

router = APIRouter()


ACCESS_TOKEN_EXPIRE_MINUTES = 60 * 24  # 1 day


@router.post("/login")
@limiter.limit("5/minute")
async def login(request: Request, body: LoginRequest):
    """Sign in via the custom admins/advisers tables using Argon2 and return PyJWT."""
    supabase = await get_async_supabase()
    admin_check = (
        await supabase.table("admins")
        .select("id, id_number, first_name, last_name, middle_initial, email, photo_url, password_hash, role, department_id, departments(name)")
        .eq("id_number", body.username)
        .execute()
    )
    user = None
    role = None
    department_id = None

    if admin_check.data:
        user = admin_check.data[0]
        role = user.get("role", "dept_admin")
        department_id = user.get("department_id")
    else:
        adviser_check = (
            await supabase.table("advisers")
            .select("id, id_number, first_name, last_name, middle_initial, email, photo_url, password_hash, must_change_password, department_id, departments(name)")
            .eq("id_number", body.username)
            .execute()
        )
        if adviser_check.data:
            user = adviser_check.data[0]
            role = "adviser"
            department_id = user.get("department_id")

    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid credentials."
        )

    if not argon2.verify(body.password, user["password_hash"]):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid credentials."
        )

    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    
    display_name = build_full_name(
        user["first_name"], user["last_name"], user.get("middle_initial")
    )

    token_data = {
        "sub": user["id"],
        "role": role,
        "username": body.username,
        "full_name": display_name
    }

    if department_id:
        token_data["department_id"] = str(department_id)


    access_token = create_access_token(
        data=token_data, expires_delta=access_token_expires
    )

    await audit_service.log_session(
        user_id=user["id"], user_role=role, event_type="LOGIN", request=request
    )

    display_name = build_full_name(
        user["first_name"], user["last_name"], user.get("middle_initial")
    )

    return {
        "access_token": access_token,
        "token_type": "bearer",
        "role": role,
        "full_name": display_name,
        "first_name": user["first_name"],
        "last_name": user["last_name"],
        "middle_initial": user.get("middle_initial"),
        "user_id": user["id"],
        "id_number": user["id_number"],
        "email": user.get("email"),
        "photo_url": user.get("photo_url"),
        "department_id": department_id,
        "department_name": user.get("departments", {}).get("name") if user.get("departments") else None,
        "must_change_password": bool(user.get("must_change_password")) if role == "adviser" else False,
    }


@router.post("/register")
@limiter.limit("3/hour")
async def register(request: Request, body: RegisterRequest):
    """Create a raw database account using Argon2 hashing."""
    if body.role not in ("dept_admin", "adviser"):
        raise HTTPException(
            status_code=400, detail="Role must be 'dept_admin' or 'adviser'."
        )

    hashed_password = argon2.hash(body.password)

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

        name_payload = {
            "first_name": body.first_name,
            "last_name": body.last_name,
        }
        if body.middle_initial:
            name_payload["middle_initial"] = body.middle_initial[0].upper()

        if body.role == "dept_admin":
            payload = {
                "id_number": body.username,
                **name_payload,
                "password_hash": hashed_password,
                "email": f"{body.username}@univote.temp",
                "role": "dept_admin",
            }
            if body.department_id:
                payload["department_id"] = str(body.department_id)
            res = await supabase.table("admins").insert(payload).execute()
        else:
            payload = {
                "id_number": body.username,
                **name_payload,
                "password_hash": hashed_password,
                "email": f"{body.username}@univote.temp",
            }
            if body.department_id:
                payload["department_id"] = str(body.department_id)
            res = await supabase.table("advisers").insert(payload).execute()

        if not res.data:
            raise Exception("Failed to insert user into database.")

        new_user = res.data[0]
        display_name = build_full_name(body.first_name, body.last_name, body.middle_initial)
        await audit_service.log_session(
            user_id=new_user["id"],
            user_role=body.role,
            event_type="REGISTER",
            request=request,
            details={"username": body.username, "full_name": display_name},
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
        .select("id, id_number, first_name, last_name, middle_initial, email, role, photo_url, department_id, departments(name)")
        .eq("id", user.id)
        .execute()
    )
    if admin.data:
        row = admin.data[0]
        return {
            "role": row["role"],
            "full_name": build_full_name(row["first_name"], row["last_name"], row.get("middle_initial")),
            "first_name": row["first_name"],
            "last_name": row["last_name"],
            "middle_initial": row.get("middle_initial"),
            "email": row["email"],
            "id_number": row["id_number"],
            "photo_url": row.get("photo_url"),
            "department_id": row.get("department_id"),
            "department_name": row.get("departments", {}).get("name") if row.get("departments") else None,
        }

    adviser = (
        await supabase.table("advisers")
        .select("id, id_number, first_name, last_name, middle_initial, email, department_id, photo_url, departments(name)")
        .eq("id", user.id)
        .execute()
    )
    if adviser.data:
        row = adviser.data[0]
        return {
            "role": "adviser",
            "full_name": build_full_name(row["first_name"], row["last_name"], row.get("middle_initial")),
            "department_name": row.get("departments", {}).get("name") if row.get("departments") else None,
            **row,
        }

    raise HTTPException(status_code=404, detail="User profile not found.")


@router.patch("/update-profile")
async def update_profile(request: Request, body: dict, user: AuthUser = Depends(get_current_user)):
    """Allow staff to update their own profile (avatar, email, etc)."""
    supabase = await get_async_supabase()
    allowed_fields = {"email", "photo_url", "first_name", "last_name", "middle_initial"}
    payload = {k: v for k, v in body.items() if k in allowed_fields}
    
    if not payload:
        raise HTTPException(status_code=400, detail="No valid fields provided.")

    table = "admins" if user.role in ("super_admin", "dept_admin") else "advisers"
    res = await supabase.table(table).update(payload).eq("id", user.id).execute()
    
    if not res.data:
        raise HTTPException(status_code=404, detail="User not found.")
        
    await audit_service.log_action(
        actor_id=user.id,
        actor_role=user.role,
        action="UPDATE_OWN_PROFILE",
        target_type="user",
        target_id=user.id,
        details=payload,
        department_id=user.department_id,
        request=request
    )
    return {"message": "Profile updated successfully.", "data": res.data[0]}


@router.post("/change-password")
async def change_password(request: Request, body: dict, user: AuthUser = Depends(get_current_user)):
    """Allow staff to change their own password."""
    current_pw = body.get("current_password")
    new_pw = body.get("new_password")
    
    if not current_pw or not new_pw:
        raise HTTPException(status_code=400, detail="Current and new password required.")

    supabase = await get_async_supabase()
    table = "admins" if user.role in ("super_admin", "dept_admin") else "advisers"
    
    # 1. Verify current password
    user_res = await supabase.table(table).select("password_hash").eq("id", user.id).execute()
    if not user_res.data:
        raise HTTPException(status_code=404, detail="User not found.")
        
    if not argon2.verify(current_pw, user_res.data[0]["password_hash"]):
        raise HTTPException(status_code=400, detail="Incorrect current password.")
        
    # 2. Hash and update
    hashed = argon2.hash(new_pw)
    await supabase.table(table).update({"password_hash": hashed}).eq("id", user.id).execute()
    
    await audit_service.log_action(
        actor_id=user.id,
        actor_role=user.role,
        action="CHANGE_OWN_PASSWORD",
        target_type="user",
        target_id=user.id,
        department_id=user.department_id,
        request=request
    )
    return {"message": "Password changed successfully."}


@router.post("/super-admin/setup", status_code=201)
async def super_admin_setup(request: Request, body: SuperAdminSetup):
    """One-time setup: create the first super_admin account.
    Returns 409 if a super_admin already exists.
    """
    supabase = await get_async_supabase()

    existing = (
        await supabase.table("admins")
        .select("id")
        .eq("role", "super_admin")
        .limit(1)
        .execute()
    )
    if existing.data:
        raise HTTPException(
            status_code=409,
            detail="Super Admin is already configured. Please log in instead.",
        )

    if len(body.password) < 8:
        raise HTTPException(
            status_code=400,
            detail="Super Admin password must be at least 8 characters long."
        )

    hashed = argon2.hash(body.password)
    insert_payload = {
        "id_number": body.id_number,
        "first_name": body.first_name,
        "last_name": body.last_name,
        "password_hash": hashed,
        "email": f"{body.id_number}@univote.superadmin",
        "role": "super_admin",
    }
    if body.middle_initial:
        insert_payload["middle_initial"] = body.middle_initial[0].upper()

    res = await supabase.table("admins").insert(insert_payload).execute()
    if not res.data:
        raise HTTPException(status_code=500, detail="Failed to create Super Admin.")

    display_name = build_full_name(body.first_name, body.last_name, body.middle_initial)
    await audit_service.log_session(
        user_id=res.data[0]["id"],
        user_role="super_admin",
        event_type="REGISTER",
        request=request,
        details={"id_number": body.id_number, "full_name": display_name, "setup": True},
    )
    return {"message": "Super Admin created successfully. You may now log in."}


@router.get("/super-admin/setup-status")
async def super_admin_setup_status():
    """Public endpoint — lets the setup page know if setup is already complete."""
    supabase = await get_async_supabase()
    existing = (
        await supabase.table("admins")
        .select("id")
        .eq("role", "super_admin")
        .limit(1)
        .execute()
    )
    return {"configured": bool(existing.data)}
