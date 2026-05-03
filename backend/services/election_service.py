from fastapi import HTTPException
from database import get_async_supabase
from datetime import datetime, timezone
from typing import Optional


from models import AuthUser

async def get_election_secure(election_id: str, user: AuthUser) -> dict:
    """
    Fetches an election but strictly scopes it to the user's department jurisdiction.
    Ensures that a Dept Admin or Adviser cannot guess IDs and access elections from other departments.
    """
    supabase = await get_async_supabase()
    query = supabase.table("elections").select("*").eq("id", election_id)
    
    # If it's a Dept Admin or Adviser, force the query to only look within their department
    if user.role in ("dept_admin", "adviser") and user.department_id:
        query = query.eq("department_id", user.department_id)
    
    # Students are also restricted to their own department
    elif user.role == "student" and user.department_id:
        query = query.eq("department_id", user.department_id)
        
    res = await query.execute()
    
    # If not found (or in wrong dept), return 404 to avoid leaking existence
    if not res.data:
        raise HTTPException(
            status_code=404,
            detail="Election not found or access denied."
        )
        
    return res.data[0]


async def get_elections() -> list:
    supabase = await get_async_supabase()
    result = await (
        supabase.table("elections")
        .select(
            "id, name, start_date, end_date, description, status, created_at, adviser_passcode, department_id"
        )
        .order("created_at", desc=True)
        .execute()
    )
    return result.data


async def create_election(
    name: str, start_date: str, end_date: str, description: Optional[str] = None, department_id: Optional[str] = None
) -> list:
    try:
        # Handle ISO strings from frontend (e.g. 2024-03-19T10:00:00.000Z)
        s_date = start_date.replace("Z", "+00:00")
        e_date = end_date.replace("Z", "+00:00")
        start = datetime.fromisoformat(s_date)
        end = datetime.fromisoformat(e_date)
        if end <= start:
            raise HTTPException(
                status_code=400, detail="End date must be after start date."
            )
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid date format provided.")

    payload = {
        "name": name,
        "start_date": start_date,
        "end_date": end_date,
        "description": description,
        "status": "upcoming",
        "department_id": department_id,
    }
    supabase = await get_async_supabase()
    result = await supabase.table("elections").insert(payload).execute()
    if not result.data:
        raise HTTPException(
            status_code=500,
            detail="Failed to store election. This may be due to database permissions (RLS). Please ensure you are using a service_role key.",
        )
    return result.data


async def update_election_status(election_id: str, status: str) -> list:
    payload = {"status": status}
    if status == "completed":
        payload["ended_at"] = datetime.now(timezone.utc).isoformat()

    supabase = await get_async_supabase()
    result = (
        await supabase.table("elections")
        .update(payload)
        .eq("id", election_id)
        .execute()
    )
    if not result.data:
        raise HTTPException(status_code=404, detail="Election not found.")
    return result.data


async def update_election(election_id: str, payload: dict) -> list:
    """Update election configuration (only allowed if status is 'upcoming')."""
    supabase = await get_async_supabase()

    # 1. Fetch current status
    curr = (
        await supabase.table("elections").select("status").eq("id", election_id).execute()
    )
    if not curr.data:
        raise HTTPException(status_code=404, detail="Election not found.")

    if curr.data[0]["status"] != "upcoming":
        raise HTTPException(
            status_code=400,
            detail="Only scheduled (upcoming) elections can be modified.",
        )

    # 2. Validate dates if provided
    update_data = {k: v for k, v in payload.items() if v is not None}
    if "start_date" in update_data or "end_date" in update_data:
        try:
            # We need both to validate
            full_curr = (
                await supabase.table("elections")
                .select("start_date, end_date")
                .eq("id", election_id)
                .execute()
            )
            s_str = update_data.get("start_date") or full_curr.data[0]["start_date"]
            e_str = update_data.get("end_date") or full_curr.data[0]["end_date"]

            s_date = s_str.replace("Z", "+00:00")
            e_date = e_str.replace("Z", "+00:00")
            start = datetime.fromisoformat(s_date)
            end = datetime.fromisoformat(e_date)
            if end <= start:
                raise HTTPException(
                    status_code=400, detail="End date must be after start date."
                )
        except ValueError:
            raise HTTPException(status_code=400, detail="Invalid date format.")

    # 3. Perform update
    result = (
        await supabase.table("elections")
        .update(update_data)
        .eq("id", election_id)
        .execute()
    )
    return result.data


async def get_active_election() -> dict | None:
    """Retrieve the currently active election, if any."""
    supabase = await get_async_supabase()
    result = (
        await supabase.table("elections").select("*").eq("status", "active").execute()
    )
    return result.data[0] if result.data else None


async def get_active_elections() -> list:
    """Retrieve all currently active elections."""
    supabase = await get_async_supabase()
    result = (
        await supabase.table("elections")
        .select("id, name, start_date, end_date, description, status")
        .eq("status", "active")
        .execute()
    )
    return result.data or []


async def get_available_elections() -> list:
    """Retrieve all active and completed elections for student access."""
    supabase = await get_async_supabase()
    result = (
        await supabase.table("elections")
        .select("id, name, start_date, end_date, description, status, department_id")
        .in_("status", ["active", "completed", "upcoming"])
        .execute()
    )
    return result.data or []


async def import_students_from_rows(rows: list[dict]) -> list:
    """
    Expects rows to be dicts with at least 'student_id' and 'name' keys.
    Returns the inserted data.
    """
    to_insert = []
    for row in rows:
        sid = row.get("id_number") or row.get("student_id") or row.get("id")
        first_name = (row.get("first_name") or "").strip()
        last_name = (row.get("last_name") or "").strip()
        middle_initial = (row.get("middle_initial") or "").strip() or None

        # Legacy fallback: split full_name if new fields aren't present
        if not first_name and not last_name:
            fname = row.get("full_name") or row.get("name") or ""
            parts = fname.strip().split()
            first_name = parts[0] if parts else ""
            last_name = parts[-1] if len(parts) > 1 else ""
            middle_initial = parts[1][0] if len(parts) >= 3 else None

        if sid and first_name and last_name:
            student_data = {
                "student_id": sid,
                "first_name": first_name,
                "last_name": last_name,
            }
            if middle_initial:
                student_data["middle_initial"] = middle_initial[0].upper()
            if "email" in row and row["email"]:
                student_data["email"] = row["email"]
            if "department_id" in row and row["department_id"]:
                student_data["department_id"] = row["department_id"]
            if "program" in row and row["program"]:
                student_data["program"] = row["program"]
            if "year_level" in row and row["year_level"]:
                try:
                    student_data["year_level"] = int(row["year_level"])
                except (ValueError, TypeError):
                    pass
            if "photo_url" in row and row["photo_url"]:
                student_data["photo_url"] = row["photo_url"]
            to_insert.append(student_data)

    if not to_insert:
        raise HTTPException(
            status_code=400,
            detail="Invalid CSV format. Need student_id, first_name, last_name columns.",
        )

    supabase = await get_async_supabase()
    result = await supabase.table("students").upsert(to_insert).execute()
    if not result.data:
        raise HTTPException(
            status_code=500,
            detail="Failed to store students. This may be due to database permissions (RLS).",
        )
    return result.data


async def delete_election(election_id: str) -> dict:
    # 1. Delete all votes related to this election
    # We need to get all candidates first or just delete by election_id if votes table has it
    # Looking at the architecture, votes usually link to candidates.
    # If the database has FK with ON DELETE CASCADE, this is easier.
    # But we'll do it manually to be safe.

    # Actually, let's check if 'votes' has 'election_id'
    # For now, we'll try to delete from votes where candidate_id is in this election's candidates
    supabase = await get_async_supabase()
    candidates_res = (
        await supabase.table("candidates")
        .select("id")
        .eq("election_id", election_id)
        .execute()
    )
    candidate_ids = [c["id"] for c in candidates_res.data]

    if candidate_ids:
        await (
            supabase.table("votes")
            .delete()
            .in_("candidate_id", candidate_ids)
            .execute()
        )
        await supabase.table("candidates").delete().in_("id", candidate_ids).execute()

    # 2. Delete partylists
    await supabase.table("partylists").delete().eq("election_id", election_id).execute()

    # 3. Finally delete the election
    result = await supabase.table("elections").delete().eq("id", election_id).execute()
    if not result.data:
        raise HTTPException(status_code=404, detail="Election not found.")

    return {"message": "Election and all related data deleted successfully."}


async def update_student(student_id: str, payload: dict) -> list:
    """Update student information with mass assignment protection."""
    # Whitelist allowed fields
    allowed_fields = {"first_name", "last_name", "middle_initial", "program", "year_level", "email", "department_id", "photo_url"}
    update_data = {k: v for k, v in payload.items() if k in allowed_fields}

    if "year_level" in update_data:
        try:
            update_data["year_level"] = int(update_data["year_level"])
        except (ValueError, TypeError):
            raise HTTPException(
                status_code=400, detail="year_level must be an integer."
            )

    if not update_data:
        raise HTTPException(status_code=400, detail="No valid update fields provided.")

    supabase = await get_async_supabase()
    result = (
        await supabase.table("students")
        .update(update_data)
        .eq("student_id", student_id)
        .execute()
    )
    return result.data


async def delete_student(student_id: str) -> dict:
    """Delete a student and their votes."""
    # First get the internal UUID
    supabase = await get_async_supabase()
    student_res = (
        await supabase.table("students")
        .select("id")
        .eq("student_id", student_id)
        .execute()
    )
    if not student_res.data:
        raise HTTPException(status_code=404, detail="Student not found.")
    uuid = student_res.data[0]["id"]
    
    # 2. Delete votes
    await supabase.table("votes").delete().eq("student_id", uuid).execute()
    
    # 3. Delete student
    await supabase.table("students").delete().eq("id", uuid).execute()
    
    return {"message": "Student and related votes deleted successfully."}


async def auto_transition_status() -> dict:
    """
    Check all upcoming and active elections and transition them 
    automatically based on their scheduled dates using batch updates.
    """
    now_iso = datetime.now(timezone.utc).isoformat()
    supabase = await get_async_supabase()
    summary = {"started": 0, "ended": 0}

    # 1. Batch Upcoming -> Active
    started_res = await supabase.table("elections") \
        .update({"status": "active"}) \
        .eq("status", "upcoming") \
        .lte("start_date", now_iso) \
        .execute()
    summary["started"] = len(started_res.data) if started_res.data else 0

    # 2. Batch Active -> Completed
    ended_res = await supabase.table("elections") \
        .update({"status": "completed", "ended_at": now_iso}) \
        .eq("status", "active") \
        .lte("end_date", now_iso) \
        .execute()
    summary["ended"] = len(ended_res.data) if ended_res.data else 0

    if summary["started"] > 0 or summary["ended"] > 0:
        print(f"[Scheduler] Batch transition: {summary['started']} started, {summary['ended']} ended.")

    return summary