from fastapi import APIRouter, UploadFile, File, Depends, HTTPException, Query
from fastapi.responses import StreamingResponse
from models import (
    ElectionCreate,
    ElectionUpdate,
    ElectionStatusUpdate,
    StudentManualCreate,
    StudentUpdate,
    AdviserCreate,
    AppSettingsUpdate,
    AdviserImportRow,
)
from services import election_service, audit_service
from deps import require_admin, require_adviser, AuthUser
from database import get_async_supabase, paginate
from passlib.hash import argon2
import csv
from io import StringIO
from typing import Optional
import uuid as _uuid

router = APIRouter()


@router.get("/elections")
async def get_elections(user: AuthUser = Depends(require_adviser)):
    return {"data": await election_service.get_elections()}


@router.post("/elections")
async def create_election(
    election: ElectionCreate,
    user: AuthUser = Depends(require_admin),
):
    data = await election_service.create_election(
        name=election.name,
        start_date=election.start_date,
        end_date=election.end_date,
        description=election.description,
    )
    election_id = data[0]["id"] if data else None
    await audit_service.log_action(
        actor_id=user.id,
        actor_role="admin",
        action="CREATE_ELECTION",
        target_type="election",
        target_id=election_id,
        details={"name": election.name},
    )
    return {"message": "Election created", "data": data}


@router.put("/elections/{election_id}/status")
async def update_election_status(
    election_id: str,
    body: ElectionStatusUpdate,
    user: AuthUser = Depends(require_admin),
):
    data = await election_service.update_election_status(election_id, body.status)
    await audit_service.log_action(
        actor_id=user.id,
        actor_role="admin",
        action="UPDATE_ELECTION_STATUS",
        target_type="election",
        target_id=election_id,
        details={"status": body.status},
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
        actor_role="admin",
        action="UPDATE_ELECTION",
        target_type="election",
        target_id=election_id,
        details=payload.dict(exclude_unset=True),
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
        actor_role="admin",
        action="DELETE_ELECTION",
        target_type="election",
        target_id=election_id,
        details={"status": "deleted"},
    )
    return result


@router.get("/students")
async def get_students(
    user: AuthUser = Depends(require_admin),
    page_size: int = Query(50, ge=1, le=200),
    page_token: Optional[str] = Query(None),
):
    """Retrieve voters using AIP-158 cursor-based pagination."""
    result = await paginate(
        table="students",
        select="id, student_id, full_name, program, year_level, has_voted",
        order_column="id",
        page_size=page_size,
        page_token=page_token,
    )
    return result


@router.put("/students/{student_id}")
async def update_student(
    student_id: str,
    payload: StudentUpdate,
    user: AuthUser = Depends(require_admin),
):
    # Only allow specific fields via StudentUpdate model
    update_data = payload.dict(exclude_unset=True)
    if not update_data:
        raise HTTPException(status_code=400, detail="No valid update fields provided.")

    data = await election_service.update_student(student_id, update_data)
    await audit_service.log_action(
        actor_id=user.id,
        actor_role="admin",
        action="UPDATE_STUDENT",
        target_type="student",
        target_id=student_id,
        details=payload,
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
        actor_role="admin",
        action="DELETE_STUDENT",
        target_type="student",
        target_id=student_id,
    )
    return result


# Adviser Management
@router.get("/advisers")
async def get_advisers(
    user: AuthUser = Depends(require_admin),
    page_size: int = Query(50, ge=1, le=200),
    page_token: Optional[str] = Query(None),
):
    result = await paginate(
        table="advisers",
        select="id, full_name, email, id_number, department, created_at",
        order_column="id",
        page_size=page_size,
        page_token=page_token,
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
    res = (
        await supabase.table("advisers")
        .insert(
            {
                "email": adviser.email,
                "id_number": adviser.id_number,
                "full_name": adviser.full_name,
                "password_hash": hashed,
                "department": adviser.department,
            }
        )
        .execute()
    )

    await audit_service.log_action(
        actor_id=user.id,
        actor_role="admin",
        action="CREATE_ADVISER",
        target_type="adviser",
        details={"email": adviser.email},
    )
    return {"message": "Adviser created", "data": res.data}


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
        actor_role="admin",
        action="DELETE_ADVISER",
        target_type="adviser",
        target_id=adviser_id,
    )
    return {"message": "Adviser account deleted."}


@router.get("/advisers/import-template")
async def download_adviser_template():
    """Return a CSV template for bulk adviser import."""
    csv_content = "full_name,email,employee_id,department\nProf. Jane Doe,jane.doe@school.edu,EMP-001,CITE\n"
    return StreamingResponse(
        iter([csv_content]),
        media_type="text/csv",
        headers={"Content-Disposition": "attachment; filename=advisers_template.csv"},
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
        full_name = (row.get("full_name") or "").strip()
        email = (row.get("email") or "").strip().lower()
        department = (row.get("department") or "").strip() or None
        # employee_id is required; fall back to deriving from email if omitted
        employee_id = (row.get("employee_id") or "").strip()
        if not employee_id:
            employee_id = email.split("@")[0].replace(".", "")[:20] if email else ""

        if not full_name or not email or not employee_id:
            skipped.append({"reason": "Missing full_name, email, or employee_id", "row": row})
            continue

        # Check duplicate by email
        email_exists = await supabase.table("advisers").select("id").eq("email", email).execute()
        if email_exists.data:
            skipped.append({"reason": "Email already exists", "email": email})
            continue

        # Check duplicate by employee_id (id_number)
        id_exists = await supabase.table("advisers").select("id").eq("id_number", employee_id).execute()
        if id_exists.data:
            # Append suffix to make unique
            employee_id = employee_id + _uuid.uuid4().hex[:4]

        default_password = f"UV@{employee_id}"
        hashed = argon2.hash(default_password)

        payload = {
            "full_name": full_name,
            "email": email,
            "id_number": employee_id,
            "password_hash": hashed,
            "must_change_password": True,
        }
        if department:
            payload["department"] = department

        res = await supabase.table("advisers").insert(payload).execute()
        if res.data:
            created.append({
                "full_name": full_name,
                "email": email,
                "employee_id": employee_id,
                "default_password": default_password,
            })
        else:
            skipped.append({"reason": "DB insert failed", "email": email})

    await audit_service.log_action(
        actor_id=user.id,
        actor_role="admin",
        action="IMPORT_ADVISERS",
        target_type="adviser",
        details={"created": len(created), "skipped": len(skipped)},
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
    data = await election_service.import_students_from_rows(rows)
    await audit_service.log_action(
        actor_id=user.id,
        actor_role="admin",
        action="IMPORT_STUDENTS",
        target_type="student",
        details={"count": len(data)},
    )
    return {"message": f"Successfully imported {len(data)} students.", "data": data}


@router.post("/students")
async def add_student(
    student: StudentManualCreate,
    user: AuthUser = Depends(require_admin),
):
    data = await election_service.import_students_from_rows([student.dict()])
    await audit_service.log_action(
        actor_id=user.id,
        actor_role="admin",
        action="ADD_STUDENT_MANUAL",
        target_type="student",
        details={"student_id": student.student_id},
    )
    return {"message": "Student added successfully.", "data": data}


@router.get("/audit-log")
async def get_audit_log(
    user: AuthUser = Depends(require_admin),
    page_size: int = Query(15, ge=1, le=500),
    page_token: Optional[str] = Query(None),
):
    result = await paginate(
        table="audit_log",
        select="*",
        order_column="id",
        page_size=page_size,
        page_token=page_token,
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
        raise HTTPException(
            status_code=503,
            detail=(
                "Database error: the app_settings table may not exist yet. "
                "Please run the setup SQL in your Supabase SQL editor. "
                f"Details: {e}"
            ),
        )

    await audit_service.log_action(
        actor_id=user.id,
        actor_role="admin",
        action="UPDATE_APP_SETTINGS",
        target_type="app_settings",
        details=payload.dict(exclude_unset=True),
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
        actor_role="admin",
        action="UPLOAD_LOGO",
        target_type="app_settings",
        details={"logo_url": logo_url},
    )
    return {"message": "Logo uploaded.", "logo_url": logo_url}
