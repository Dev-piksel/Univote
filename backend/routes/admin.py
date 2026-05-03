from fastapi import APIRouter, UploadFile, File, Depends, HTTPException, Query
from fastapi.responses import StreamingResponse
from models import (
    ElectionCreate,
    ElectionUpdate,
    ElectionStatusUpdate,
    StudentManualCreate,
    StudentUpdate,
    AdviserCreate,
    AdviserUpdate,
    AppSettingsUpdate,
    DepartmentCreate,
    DeptAdminCreate,
    DeptAdminUpdate,
)
from services import election_service, audit_service
from dependencies.auth import require_admin, require_adviser, require_super_admin, require_dept_access
from models import AuthUser
from utils.common import build_full_name
from database import get_async_supabase, paginate
from passlib.hash import argon2
import csv
from io import StringIO
from typing import Optional
import uuid as _uuid

router = APIRouter()


@router.get("/elections")
async def get_elections(user: AuthUser = Depends(require_adviser)):
    supabase = await get_async_supabase()
    query = supabase.table("elections").select("id, name, start_date, end_date, description, status, created_at, adviser_passcode, department_id").order("created_at", desc=True)
    
    if user.role != "super_admin" and user.department_id:
        query = query.eq("department_id", user.department_id)
        
    result = await query.execute()
    return {"data": result.data}


@router.post("/elections")
async def create_election(
    election: ElectionCreate,
    user: AuthUser = Depends(require_admin),
):
    # If not super_admin, force the user's department_id
    dept_id = election.department_id
    if user.role != "super_admin":
        dept_id = user.department_id

    data = await election_service.create_election(
        name=election.name,
        start_date=election.start_date,
        end_date=election.end_date,
        description=election.description,
        department_id=dept_id,
    )
    election_id = data[0]["id"] if data else None
    await audit_service.log_action(
        actor_id=user.id,
        actor_role=user.role,
        action="CREATE_ELECTION",
        target_type="election",
        target_id=election_id,
        details={"name": election.name},
        department_id=user.department_id,
        actor_name=user.full_name,
        actor_username=user.username,
    )

    return {"message": "Election created", "data": data}


@router.put("/elections/{election_id}/status")
async def update_election_status(
    election_id: str,
    body: ElectionStatusUpdate,
    user: AuthUser = Depends(require_dept_access),
):
    # Security Layer: Ensure the user has access to this specific election
    election = await election_service.get_election_secure(election_id, user)
    
    # Business Logic Layer
    data = await election_service.update_election_status(election["id"], body.status)
    
    await audit_service.log_action(
        actor_id=user.id,
        actor_role=user.role,
        action="UPDATE_ELECTION_STATUS",
        target_type="election",
        target_id=election_id,
        details={"status": body.status},
        department_id=user.department_id,
        actor_name=user.full_name,
        actor_username=user.username,
    )

    return {"message": "Status updated", "data": data}


@router.put("/elections/{election_id}")
async def update_election(
    election_id: str,
    payload: ElectionUpdate,
    user: AuthUser = Depends(require_admin),
):
    data = await election_service.update_election(
        election_id, payload.dict(exclude_unset=True)
    )
    await audit_service.log_action(
        actor_id=user.id,
        actor_role=user.role,
        action="UPDATE_ELECTION",
        target_type="election",
        target_id=election_id,
        details=payload.dict(exclude_unset=True),
        department_id=user.department_id,
        actor_name=user.full_name,
        actor_username=user.username,
    )

    return {"message": "Election updated", "data": data}


@router.delete("/elections/{election_id}")
async def delete_election(
    election_id: str,
    user: AuthUser = Depends(require_admin),
):
    result = await election_service.delete_election(election_id)
    await audit_service.log_action(
        actor_id=user.id,
        actor_role=user.role,
        action="DELETE_ELECTION",
        target_type="election",
        target_id=election_id,
        details={"status": "deleted"},
        department_id=user.department_id,
        actor_name=user.full_name,
        actor_username=user.username,
    )

    return result


@router.get("/students")
async def get_students(
    user: AuthUser = Depends(require_admin),
    page_size: int = Query(50, ge=1, le=200),
    page_token: Optional[str] = Query(None),
):
    """Retrieve voters using AIP-158 cursor-based pagination. Scoped by department."""
    filters = {}
    if user.role != "super_admin" and user.department_id:
        filters["department_id"] = user.department_id

    result = await paginate(
        table="students",
        select="id, student_id, first_name, last_name, middle_initial, email, department_id, program, year_level, has_voted, photo_url, departments(name)",
        order_column="id",
        page_size=page_size,
        page_token=page_token,
        filters=filters,
    )
    return result


@router.get("/students/import-template")
async def download_student_template():
    """Return a comprehensive CSV template for bulk voter import."""
    # Headers matching the expected columns in the import logic
    headers = "student_id,first_name,last_name,middle_initial,email,department,program,year_level\n"
    example1 = "2024-0001,Juan,Dela Cruz,D,juan@school.edu,CITE,BSIT,1\n"
    example2 = "2024-0002,Maria,Santos,,maria@school.edu,CITE,BSCS,2\n"
    csv_content = headers + example1 + example2
    
    return StreamingResponse(
        iter([csv_content]),
        media_type="text/csv",
        headers={"Content-Disposition": "attachment; filename=univote_voters_template.csv"},
    )


@router.put("/students/{student_id}")
async def update_student(
    student_id: str,
    payload: StudentUpdate,
    user: AuthUser = Depends(require_admin),
):
    # Only allow specific fields via StudentUpdate model
    update_data = {k: v for k, v in payload.model_dump(exclude_unset=True).items() if v is not None and v != ''}
    
    # Security: If not super_admin, force scoping and prevent department changes
    if user.role != "super_admin":
        update_data.pop("department_id", None)  # Prevent changing department
        
        # Verify student belongs to this admin's department
        supabase = await get_async_supabase()
        check = await supabase.table("students").select("department_id").eq("student_id", student_id).execute()
        if not check.data or str(check.data[0].get("department_id")) != str(user.department_id):
            raise HTTPException(status_code=403, detail="You do not have permission to update this student.")

    if not update_data:
        raise HTTPException(status_code=400, detail="No valid update fields provided.")

    data = await election_service.update_student(student_id, update_data)
    await audit_service.log_action(
        actor_id=user.id,
        actor_role=user.role,
        action="UPDATE_STUDENT",
        target_type="student",
        target_id=student_id,
        details=payload.model_dump(),
        actor_name=user.full_name,
        actor_username=user.username,
    )

    return {"message": "Student updated", "data": data}


@router.delete("/students/{student_id}")
async def delete_student(
    student_id: str,
    user: AuthUser = Depends(require_admin),
):
    result = await election_service.delete_student(student_id)
    await audit_service.log_action(
        actor_id=user.id,
        actor_role=user.role,
        action="DELETE_STUDENT",
        target_type="student",
        target_id=student_id,
        actor_name=user.full_name,
        actor_username=user.username,
    )

    return result


# Adviser Management
@router.get("/advisers")
async def get_advisers(
    user: AuthUser = Depends(require_admin),
    page_size: int = Query(50, ge=1, le=200),
    page_token: Optional[str] = Query(None),
):
    filters = {}
    if user.role != "super_admin" and user.department_id:
        filters["department_id"] = user.department_id

    result = await paginate(
        table="advisers",
        select="id, first_name, last_name, middle_initial, email, id_number, department_id, created_at, photo_url, departments(name)",
        order_column="id",
        page_size=page_size,
        page_token=page_token,
        filters=filters,
    )
    return result


@router.post("/advisers")
async def create_adviser(
    adviser: AdviserCreate,
    user: AuthUser = Depends(require_admin),
):
    # Check if exists
    supabase = await get_async_supabase()
    exists = (
        await supabase.table("advisers")
        .select("id")
        .eq("email", adviser.email)
        .execute()
    )
    if exists.data:
        raise HTTPException(
            status_code=400, detail="Adviser with this email already exists."
        )

    hashed = argon2.hash(adviser.password)
    
    # Handle department scoping
    dept_id = adviser.department_id if adviser.department_id and adviser.department_id != "" else None
    if user.role != "super_admin":
        dept_id = user.department_id

    # Handle full_name parsing if first/last are missing
    fn, ln, mi = adviser.first_name, adviser.last_name, adviser.middle_initial
    if not fn and adviser.full_name:
        parts = adviser.full_name.strip().split()
        fn = parts[0] if parts else ""
        ln = parts[-1] if len(parts) > 1 else ""
        mi = parts[1][0] if len(parts) >= 3 else mi

    res = (
        await supabase.table("advisers")
        .insert(
            {
                "email": adviser.email,
                "id_number": adviser.id_number,
                "first_name": fn,
                "last_name": ln,
                "middle_initial": mi[0].upper() if mi else None,
                "password_hash": hashed,
                "department_id": dept_id,
                "photo_url": adviser.photo_url or None,
            }
        )
        .execute()
    )

    await audit_service.log_action(
        actor_id=user.id,
        actor_role=user.role,
        action="CREATE_ADVISER",
        target_type="adviser",
        details={"email": adviser.email},
        actor_name=user.full_name,
        actor_username=user.username,
    )

    return {"message": "Adviser created", "data": res.data}


@router.put("/advisers/{adviser_id}")
async def update_adviser(
    adviser_id: str,
    payload: AdviserUpdate,
    user: AuthUser = Depends(require_admin),
):
    """Update an adviser account details."""
    supabase = await get_async_supabase()
    update_data = payload.dict(exclude_unset=True)
    
    if "middle_initial" in update_data and update_data["middle_initial"]:
        update_data["middle_initial"] = update_data["middle_initial"][0].upper()

    res = await supabase.table("advisers").update(update_data).eq("id", adviser_id).execute()
    if not res.data:
        raise HTTPException(status_code=404, detail="Adviser not found.")
    
    await audit_service.log_action(
        actor_id=user.id,
        actor_role=user.role,
        action="UPDATE_ADVISER",
        target_type="adviser",
        target_id=adviser_id,
        details=update_data,
        actor_name=user.full_name,
        actor_username=user.username,
    )

    return {"message": "Adviser updated", "data": res.data[0]}


@router.delete("/advisers/{adviser_id}")
async def delete_adviser(
    adviser_id: str,
    user: AuthUser = Depends(require_admin),
):
    supabase = await get_async_supabase()
    res = await supabase.table("advisers").delete().eq("id", adviser_id).execute()
    if not res.data:
        raise HTTPException(status_code=404, detail="Adviser not found.")

    await audit_service.log_action(
        actor_id=user.id,
        actor_role=user.role,
        action="DELETE_ADVISER",
        target_type="adviser",
        target_id=adviser_id,
        actor_name=user.full_name,
        actor_username=user.username,
    )

    return {"message": "Adviser account deleted."}


@router.post("/staff/{user_id}/reset-password")
async def reset_staff_password(
    user_id: str,
    user: AuthUser = Depends(require_super_admin),
):
    """Super Admin only: Reset a staff member's password to UV@<id_number>."""
    supabase = await get_async_supabase()
    
    # Try finding in advisers first
    target = await supabase.table("advisers").select("id, id_number").eq("id", user_id).execute()
    table = "advisers"
    
    if not target.data:
        # Try admins
        target = await supabase.table("admins").select("id, id_number").eq("id", user_id).execute()
        table = "admins"
        
    if not target.data:
        raise HTTPException(status_code=404, detail="Staff member not found.")
        
    record = target.data[0]
    id_num = record["id_number"]
    default_pw = f"UV@{id_num}"
    hashed = argon2.hash(default_pw)
    
    update_payload = {"password_hash": hashed}
    if table == "advisers":
        update_payload["must_change_password"] = True
        
    await supabase.table(table).update(update_payload).eq("id", user_id).execute()
    
    await audit_service.log_action(
        actor_id=user.id,
        actor_role=user.role,
        action="RESET_STAFF_PASSWORD",
        target_type=table.rstrip('s'),
        target_id=user_id,
        details={"id_number": id_num},
        actor_name=user.full_name,
        actor_username=user.username,
    )

    
    return {"message": f"Password reset successful. New password is: {default_pw}"}


@router.get("/advisers/import-template")
async def download_adviser_template():
    """Return a role-specific CSV template for bulk adviser import."""
    csv_content = (
        "employee_id,first_name,last_name,middle_initial,email,department\n"
        "EMP-001,Jane,Doe,M,jane.doe@school.edu,CITE\n"
        "EMP-002,John,Smith,,john.smith@school.edu,COE\n"
    )
    return StreamingResponse(
        iter([csv_content]),
        media_type="text/csv",
        headers={"Content-Disposition": "attachment; filename=univote_advisers_template.csv"},
    )


@router.post("/advisers/import")
async def import_advisers(
    file: UploadFile = File(...),
    user: AuthUser = Depends(require_admin),
):
    """Bulk import advisers from CSV. Default password is Changeme@<employee_id>.
    Advisers will be forced to change their password on first login.
    CSV columns: full_name, email, employee_id (required, becomes login ID), department (optional)
    """
    contents = await file.read()
    try:
        reader = csv.DictReader(StringIO(contents.decode("utf-8")))
        rows = list(reader)
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid CSV file.")

    if not rows:
        raise HTTPException(status_code=400, detail="CSV file is empty.")

    supabase = await get_async_supabase()
    created = []
    skipped = []

    for row in rows:
        first_name = (row.get("first_name") or "").strip()
        last_name = (row.get("last_name") or "").strip()
        middle_initial = (row.get("middle_initial") or "").strip() or None
        email = (row.get("email") or "").strip().lower()
        department = (row.get("department") or row.get("department_name") or "").strip() or None
        employee_id = (row.get("id_number") or row.get("employee_id") or "").strip()
        if not employee_id:
            employee_id = email.split("@")[0].replace(".", "")[:20] if email else ""

        if not first_name or not last_name or not email or not employee_id:
            skipped.append({"reason": "Missing first_name, last_name, email, or employee_id", "row": row})
            continue

        email_exists = await supabase.table("advisers").select("id").eq("email", email).execute()
        if email_exists.data:
            skipped.append({"reason": "Email already exists", "email": email})
            continue

        id_exists = await supabase.table("advisers").select("id").eq("id_number", employee_id).execute()
        if id_exists.data:
            employee_id = employee_id + _uuid.uuid4().hex[:4]

        default_password = f"UV@{employee_id}"
        hashed = argon2.hash(default_password)

        dept_id = None
        if user.role != "super_admin":
            dept_id = user.department_id
        elif department:
            dept_res = await supabase.table("departments").select("id").eq("name", department).execute()
            if dept_res.data:
                dept_id = dept_res.data[0]["id"]

        payload = {
            "first_name": first_name,
            "last_name": last_name,
            "email": email,
            "id_number": employee_id,
            "password_hash": hashed,
            "must_change_password": True,
            "department_id": dept_id,
        }
        if middle_initial:
            payload["middle_initial"] = middle_initial[0].upper()

        res = await supabase.table("advisers").insert(payload).execute()
        display_name = build_full_name(first_name, last_name, middle_initial)
        if res.data:
            created.append({
                "full_name": display_name,
                "email": email,
                "employee_id": employee_id,
                "default_password": default_password,
            })
        else:
            skipped.append({"reason": "DB insert failed", "email": email})

    await audit_service.log_action(
        actor_id=user.id,
        actor_role=user.role,
        action="IMPORT_ADVISERS",
        target_type="adviser",
        details={"created": len(created), "skipped": len(skipped)},
        actor_name=user.full_name,
        actor_username=user.username,
    )

    return {
        "message": f"Imported {len(created)} adviser(s), skipped {len(skipped)}.",
        "created": created,
        "skipped": skipped,
    }



@router.post("/students/upload")
async def upload_students(
    file: UploadFile = File(...),
    user: AuthUser = Depends(require_admin),
):
    contents = await file.read()
    reader = csv.DictReader(StringIO(contents.decode("utf-8")))
    rows = list(reader)
    
    supabase = await get_async_supabase()
    
    # Cache departments to avoid repeat lookups
    dept_map = {} 
    
    for row in rows:
        # 1. Force dept_admin's own department
        if user.role == "dept_admin" and user.department_id:
            row["department_id"] = str(user.department_id)
        
        # 2. Otherwise, resolve from 'department' column (Super Admin or fallback)
        elif "department" in row and row["department"]:
            dept_name = row["department"].strip()
            if dept_name not in dept_map:
                # Try by code first (case insensitive), then by name
                res = await supabase.table("departments").select("id").or_(f"code.ilike.{dept_name},name.ilike.{dept_name}").execute()
                if res.data:
                    dept_map[dept_name] = res.data[0]["id"]
            
            if dept_name in dept_map:
                row["department_id"] = dept_map[dept_name]

    data = await election_service.import_students_from_rows(rows)
    await audit_service.log_action(
        actor_id=user.id,
        actor_role=user.role,
        action="IMPORT_STUDENTS",
        target_type="student",
        details={"count": len(data)},
        actor_name=user.full_name,
        actor_username=user.username,
    )

    return {"message": f"Successfully imported {len(data)} students.", "data": data}


@router.post("/students")
async def add_student(
    student: StudentManualCreate,
    user: AuthUser = Depends(require_admin),
):
    # Build a clean dict — serialize UUID → str, drop empty strings
    row = {
        "student_id": student.student_id.strip(),
    }
    
    if student.full_name:
        row["full_name"] = student.full_name.strip()
    if student.first_name:
        row["first_name"] = student.first_name.strip()
    if student.last_name:
        row["last_name"] = student.last_name.strip()
    if student.middle_initial:
        row["middle_initial"] = student.middle_initial.strip()
    if student.email:
        row["email"] = student.email.strip()
    if student.program:
        row["program"] = student.program.strip()
    if student.year_level is not None:
        row["year_level"] = int(student.year_level)

    # Resolve department_id: force dept_admin's own dept if not super_admin
    if user.role != "super_admin":
        dept_id = user.department_id
    else:
        dept_id = student.department_id
    
    if dept_id:
        row["department_id"] = str(dept_id)

    data = await election_service.import_students_from_rows([row])
    await audit_service.log_action(
        actor_id=user.id,
        actor_role=user.role,
        action="ADD_STUDENT_MANUAL",
        target_type="student",
        target_id=student.student_id,
        details={"student_id": student.student_id},
        department_id=user.department_id,
        actor_name=user.full_name,
        actor_username=user.username,
    )

    return {"message": "Student added successfully.", "data": data}


@router.get("/audit-log")
async def get_audit_log(
    user: AuthUser = Depends(require_admin),
    page_size: int = Query(15, ge=1, le=500),
    page_token: Optional[str] = Query(None),
):
    filters = {}
    if user.role != "super_admin" and user.department_id:
        filters["department_id"] = user.department_id

    result = await paginate(
        table="audit_log",
        select="*",
        order_column="id",
        page_size=page_size,
        page_token=page_token,
        filters=filters,
    )
    return result


# ---------------------------------------------------------------------------
# App Settings (Branding & Customisation)
# ---------------------------------------------------------------------------

@router.get("/settings")
async def get_settings():
    """Public endpoint — returns branding settings. Returns defaults if table not yet created."""
    defaults = {
        "app_name": "UniVote",
        "primary_color": "#0b75fe",
        "accent_color": "#5c60f5",
        "logo_url": None,
        "show_bg_anims": True,
    }
    try:
        supabase = await get_async_supabase()
        res = await supabase.table("app_settings").select("*").eq("id", 1).execute()
        if res.data:
            return {"data": res.data[0]}
    except Exception:
        pass
    return {"data": defaults}


@router.put("/settings")
async def update_settings(
    payload: AppSettingsUpdate,
    user: AuthUser = Depends(require_admin),
):
    update_data = payload.dict(exclude_unset=True)
    if not update_data:
        raise HTTPException(status_code=400, detail="No fields to update.")

    try:
        supabase = await get_async_supabase()
        update_data["id"] = 1
        res = await supabase.table("app_settings").upsert(update_data).execute()
    except Exception as e:
        err_msg = str(e).lower()
        # If any column error occurs, try stripping new fields one by one
        if "column" in err_msg:
            # Blindly strip newer fields that might be missing in the DB
            for key in ["show_bg_anims", "theme"]:
                update_data.pop(key, None)
            try:
                res = await supabase.table("app_settings").upsert(update_data).execute()
            except Exception as inner_e:
                raise HTTPException(status_code=503, detail=f"Database error: {inner_e}")
        else:
            raise HTTPException(status_code=503, detail=f"Database error: {e}")

    await audit_service.log_action(
        actor_id=user.id,
        actor_role=user.role,
        action="UPDATE_APP_SETTINGS",
        target_type="app_settings",
        details=payload.dict(exclude_unset=True),
        actor_name=user.full_name,
        actor_username=user.username,
    )

    return {"message": "Settings updated.", "data": res.data[0] if res.data else update_data}


@router.post("/settings/logo")
async def upload_logo(
    file: UploadFile = File(...),
    user: AuthUser = Depends(require_admin),
):
    """Upload a logo image to Supabase Storage and save the public URL."""
    if not file.content_type or not file.content_type.startswith("image/"):
        raise HTTPException(status_code=400, detail="Only image files are allowed.")

    contents = await file.read()
    ext = (file.filename or "logo").rsplit(".", 1)[-1].lower()
    allowed_exts = {"png", "jpg", "jpeg", "gif", "svg", "webp"}
    if ext not in allowed_exts:
        raise HTTPException(status_code=400, detail=f"Extension .{ext} not allowed.")

    file_path = f"logo_{_uuid.uuid4().hex}.{ext}"

    try:
        supabase = await get_async_supabase()
        storage = supabase.storage.from_("logos")
        await storage.upload(
            path=file_path,
            file=contents,
            file_options={"content-type": file.content_type, "upsert": "true"},
        )
        public_url_res = storage.get_public_url(file_path)
        logo_url = public_url_res if isinstance(public_url_res, str) else str(public_url_res)

        await supabase.table("app_settings").upsert({"id": 1, "logo_url": logo_url}).execute()
    except Exception as e:
        raise HTTPException(
            status_code=503,
            detail=f"Storage upload failed: {e}. Ensure the 'logos' bucket exists in Supabase Storage.",
        )

    await audit_service.log_action(
        actor_id=user.id,
        actor_role=user.role,
        action="UPLOAD_LOGO",
        target_type="app_settings",
        details={"logo_url": logo_url},
        actor_name=user.full_name,
        actor_username=user.username,
    )

    return {"message": "Logo uploaded.", "logo_url": logo_url}


# ---------------------------------------------------------------------------
# Department Management (Super Admin Only)
# ---------------------------------------------------------------------------

@router.get("/departments")
async def get_departments(user: AuthUser = Depends(require_adviser)):
    """Advisers/Admins can list departments for selection."""
    supabase = await get_async_supabase()
    res = await supabase.table("departments").select("*").order("name").execute()
    return {"data": res.data}


@router.post("/departments")
async def create_department(
    body: DepartmentCreate,
    user: AuthUser = Depends(require_super_admin),
):
    supabase = await get_async_supabase()
    payload = {"name": body.name.strip()}
    if body.description:
        payload["description"] = body.description.strip()
    # Only include code if the column exists in your DB schema
    # Run: ALTER TABLE public.departments ADD COLUMN code text UNIQUE;
    if body.code:
        payload["code"] = body.code.upper().strip()
    try:
        res = await supabase.table("departments").insert(payload).execute()
    except Exception as e:
        err_msg = str(e)
        if "code" in err_msg and "column" in err_msg.lower():
            # code column doesn't exist yet — retry without it
            payload.pop("code", None)
            res = await supabase.table("departments").insert(payload).execute()
        else:
            raise HTTPException(status_code=500, detail=f"Database error: {err_msg}")
    if not res.data:
        raise HTTPException(status_code=500, detail="Failed to create department.")
    
    await audit_service.log_action(
        actor_id=user.id,
        actor_role=user.role,
        action="CREATE_DEPARTMENT",
        target_type="department",
        target_id=res.data[0]["id"],
        details={"name": body.name},
        actor_name=user.full_name,
        actor_username=user.username,
    )
    return {"message": "Department created", "data": res.data[0]}



@router.put("/departments/{dept_id}")
async def update_department(
    dept_id: str,
    body: DepartmentCreate,
    user: AuthUser = Depends(require_super_admin),
):
    supabase = await get_async_supabase()
    payload = {"name": body.name.strip()}
    if body.description:
        payload["description"] = body.description.strip()
    if body.code:
        payload["code"] = body.code.upper().strip()
    try:
        res = await supabase.table("departments").update(payload).eq("id", dept_id).execute()
    except Exception as e:
        err_msg = str(e)
        if "code" in err_msg and "column" in err_msg.lower():
            payload.pop("code", None)
            res = await supabase.table("departments").update(payload).eq("id", dept_id).execute()
        else:
            raise HTTPException(status_code=500, detail=f"Database error: {err_msg}")
    if not res.data:
        raise HTTPException(status_code=404, detail="Department not found.")
        
    await audit_service.log_action(
        actor_id=user.id,
        actor_role=user.role,
        action="UPDATE_DEPARTMENT",
        target_type="department",
        target_id=dept_id,
        details={"name": body.name},
        actor_name=user.full_name,
        actor_username=user.username,
    )
    return {"message": "Department updated", "data": res.data[0]}



@router.delete("/departments/{dept_id}")
async def delete_department(
    dept_id: str,
    user: AuthUser = Depends(require_super_admin),
):
    supabase = await get_async_supabase()
    # Check if in use
    use_check = await supabase.table("students").select("id").eq("department_id", dept_id).limit(1).execute()
    if use_check.data:
        raise HTTPException(status_code=400, detail="Cannot delete department. It is still assigned to students.")
    
    await supabase.table("departments").delete().eq("id", dept_id).execute()
    
    await audit_service.log_action(
        actor_id=user.id,
        actor_role=user.role,
        action="DELETE_DEPARTMENT",
        target_type="department",
        target_id=dept_id,
        actor_name=user.full_name,
        actor_username=user.username,
    )
    return {"message": "Department deleted"}



# ---------------------------------------------------------------------------
# Dept Admin Management (Super Admin Only)
# ---------------------------------------------------------------------------

@router.get("/dept-admins")
async def get_dept_admins(
    user: AuthUser = Depends(require_super_admin),
    page_size: int = Query(50, ge=1, le=200),
    page_token: Optional[str] = Query(None),
):
    """List all dept_admin accounts (super_admin only)."""
    result = await paginate(
        table="admins",
        select="id, first_name, last_name, middle_initial, email, id_number, department_id, created_at, photo_url",
        order_column="id",
        page_size=page_size,
        page_token=page_token,
        filters={"role": "dept_admin"},
    )
    # Compute full_name for the frontend
    for row in result.get("data", []):
        row["full_name"] = build_full_name(
            row.get("first_name", ""),
            row.get("last_name", ""),
            row.get("middle_initial"),
        )
    return result


@router.post("/dept-admins")
async def create_dept_admin(
    body: DeptAdminCreate,
    user: AuthUser = Depends(require_super_admin),
):
    """Manually create a single dept_admin account."""
    supabase = await get_async_supabase()

    exists = await supabase.table("admins").select("id").eq("id_number", body.id_number).execute()
    if exists.data:
        raise HTTPException(status_code=400, detail="An account with this Employee ID already exists.")

    hashed = argon2.hash(body.password)
    payload = {
        "id_number": body.id_number,
        "first_name": body.first_name,
        "last_name": body.last_name,
        "password_hash": hashed,
        "email": body.email,
        "role": "dept_admin",
        "photo_url": body.photo_url or None,
    }
    if body.middle_initial:
        payload["middle_initial"] = body.middle_initial[0].upper()
    if body.department_id:
        payload["department_id"] = str(body.department_id)

    res = await supabase.table("admins").insert(payload).execute()
    if not res.data:
        raise HTTPException(status_code=500, detail="Failed to create dept admin.")

    await audit_service.log_action(
        actor_id=user.id,
        actor_role=user.role,
        action="CREATE_DEPT_ADMIN",
        target_type="admin",
        target_id=res.data[0]["id"],
        details={"id_number": body.id_number, "full_name": build_full_name(body.first_name, body.last_name, body.middle_initial)},
        actor_name=user.full_name,
        actor_username=user.username,
    )

    return {"message": "Dept Admin created.", "data": res.data[0]}


@router.put("/dept-admins/{admin_id}")
async def update_dept_admin(
    admin_id: str,
    payload: DeptAdminUpdate,
    user: AuthUser = Depends(require_super_admin),
):
    """Update a dept_admin account details."""
    supabase = await get_async_supabase()
    update_data = payload.dict(exclude_unset=True)
    
    if "middle_initial" in update_data and update_data["middle_initial"]:
        update_data["middle_initial"] = update_data["middle_initial"][0].upper()

    res = await supabase.table("admins").update(update_data).eq("id", admin_id).eq("role", "dept_admin").execute()
    if not res.data:
        raise HTTPException(status_code=404, detail="Dept Admin not found.")
    
    # Enrich log details with full name for better context
    log_details = {**update_data}
    if "first_name" in update_data or "last_name" in update_data:
        # Fetch current record to get missing name parts if needed, or just log what we have
        log_details["full_name"] = build_full_name(
            update_data.get("first_name", ""), 
            update_data.get("last_name", ""), 
            update_data.get("middle_initial")
        )

    await audit_service.log_action(
        actor_id=user.id,
        actor_role=user.role,
        action="UPDATE_DEPT_ADMIN",
        target_type="admin",
        target_id=admin_id,
        details=log_details,
        actor_name=user.full_name,
        actor_username=user.username,
    )


    return {"message": "Dept Admin updated", "data": res.data[0]}


@router.delete("/dept-admins/{admin_id}")
async def delete_dept_admin(
    admin_id: str,
    user: AuthUser = Depends(require_super_admin),
):
    """Delete a dept_admin account."""
    supabase = await get_async_supabase()
    res = await supabase.table("admins").delete().eq("id", admin_id).eq("role", "dept_admin").execute()
    if not res.data:
        raise HTTPException(status_code=404, detail="Dept Admin not found.")
    await audit_service.log_action(
        actor_id=user.id,
        actor_role=user.role,
        action="DELETE_DEPT_ADMIN",
        target_type="admin",
        target_id=admin_id,
        actor_name=user.full_name,
        actor_username=user.username,
    )

    return {"message": "Dept Admin deleted."}


@router.get("/dept-admins/import-template")
async def download_dept_admin_template():
    """Return a standardized CSV template for bulk dept_admin import."""
    csv_content = (
        "id_number,first_name,last_name,middle_initial,email,department_name\n"
        "ADM-2024-001,Juan,Dela Cruz,D,juan@school.edu,College of Information Technology\n"
        "ADM-2024-002,Maria,Santos,,maria@school.edu,College of Education\n"
    )
    return StreamingResponse(
        iter([csv_content]),
        media_type="text/csv",
        headers={"Content-Disposition": "attachment; filename=univote_dept_admins_template.csv"},
    )


@router.post("/dept-admins/import")
async def import_dept_admins(
    file: UploadFile = File(...),
    user: AuthUser = Depends(require_super_admin),
):
    """Bulk import dept_admin accounts from CSV.
    Columns: full_name, employee_id, department_name (optional, resolved by name)
    Default password: UV@<employee_id>
    """
    contents = await file.read()
    try:
        reader = csv.DictReader(StringIO(contents.decode("utf-8")))
        rows = list(reader)
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid CSV file.")

    if not rows:
        raise HTTPException(status_code=400, detail="CSV file is empty.")

    supabase = await get_async_supabase()
    created = []
    skipped = []

    for row in rows:
        first_name = (row.get("first_name") or "").strip()
        last_name = (row.get("last_name") or "").strip()
        middle_initial = (row.get("middle_initial") or "").strip() or None
        employee_id = (row.get("id_number") or row.get("employee_id") or "").strip()
        email = (row.get("email") or "").strip().lower()
        department_name = (row.get("department_name") or row.get("department") or "").strip() or None

        if not first_name or not last_name or not employee_id:
            skipped.append({"reason": "Missing first_name, last_name or employee_id", "row": row})
            continue

        dup = await supabase.table("admins").select("id").eq("id_number", employee_id).execute()
        if dup.data:
            skipped.append({"reason": "Employee ID already exists", "employee_id": employee_id})
            continue

        dept_id = None
        if department_name:
            dept_res = await supabase.table("departments").select("id").eq("name", department_name).execute()
            if dept_res.data:
                dept_id = dept_res.data[0]["id"]

        default_password = f"UV@{employee_id}"
        hashed = argon2.hash(default_password)

        payload = {
            "id_number": employee_id,
            "first_name": first_name,
            "last_name": last_name,
            "password_hash": hashed,
            "email": email or f"{employee_id}@univote.temp",
            "role": "dept_admin",
        }
        if middle_initial:
            payload["middle_initial"] = middle_initial[0].upper()
        if dept_id:
            payload["department_id"] = str(dept_id)

        res = await supabase.table("admins").insert(payload).execute()
        display_name = build_full_name(first_name, last_name, middle_initial)
        if res.data:
            created.append({
                "full_name": display_name,
                "employee_id": employee_id,
                "default_password": default_password,
                "department": department_name or "—",
            })
        else:
            skipped.append({"reason": "DB insert failed", "employee_id": employee_id})

    await audit_service.log_action(
        actor_id=user.id,
        actor_role=user.role,
        action="IMPORT_DEPT_ADMINS",
        target_type="admin",
        details={"created": len(created), "skipped": len(skipped)},
        actor_name=user.full_name,
        actor_username=user.username,
    )

    return {
        "message": f"Imported {len(created)} dept admin(s), skipped {len(skipped)}.",
        "created": created,
        "skipped": skipped,
    }

