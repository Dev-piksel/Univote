from typing import Optional
from fastapi import Request
from database import get_async_supabase


async def log_action(
    actor_id: str,
    actor_role: str,
    action: str,
    target_type: Optional[str] = None,
    target_id: Optional[str] = None,
    details: Optional[dict] = None,
    department_id: Optional[str] = None,
    request: Optional[Request] = None,
    actor_name: Optional[str] = None,
    actor_username: Optional[str] = None,
) -> None:
    """
    Insert a row into the audit_log table.
    """
    try:
        supabase = await get_async_supabase()
        
        # Auto-fetch name/username if missing and we have actor info
        if actor_id and (not actor_name or not actor_username):
            try:
                table_map = {
                    "super_admin": "admins",
                    "dept_admin": "admins",
                    "adviser": "advisers",
                    "student": "students",
                }
                db_table = table_map.get(actor_role)
                if db_table:
                    id_col = "id_number" if db_table in ["admins", "advisers"] else "student_id"
                    res = await supabase.table(db_table).select(f"first_name, last_name, middle_initial, {id_col}").eq("id", actor_id).execute()
                    if res.data:
                        user_data = res.data[0]
                        if not actor_name:
                            from utils.common import build_full_name
                            actor_name = build_full_name(user_data["first_name"], user_data["last_name"], user_data.get("middle_initial"))
                        if not actor_username:
                            actor_username = user_data.get(id_col)
            except Exception as e:
                print(f"[audit_service] Failed to auto-fetch actor info: {e}")

        # Enrich details with IP and User-Agent if request is provided
        if request:
            if details is None:
                details = {}
            details["ip_address"] = request.client.host if request.client else None
            details["user_agent"] = request.headers.get("user-agent")

        payload = {
            "actor_id": actor_id,
            "actor_role": actor_role,
            "action": action,
            "target_type": target_type,
            "target_id": target_id,
            "details": details,
            "department_id": department_id,
            "actor_name": actor_name,
            "actor_username": actor_username,
        }

        await supabase.table("audit_log").insert(payload).execute()


    except Exception as exc:
        # Never let audit failures surface to the caller
        print(f"[audit_service] Failed to log action '{action}': {exc}")


async def log_session(
    user_id: str,
    user_role: str,
    event_type: str,
    request: Optional[Request] = None,
    details: Optional[dict] = None,
) -> None:
    """
    Log session events like LOGIN, REGISTER, VALIDATE, etc.
    Extracts IP and User-Agent from the FastAPI Request if provided.
    """
    try:
        supabase = await get_async_supabase()
        ip_address = request.client.host if request and request.client else None
        user_agent = request.headers.get("user-agent") if request else None

        await (
            supabase.table("session_logs")
            .insert(
                {
                    "user_id": user_id,
                    "user_role": user_role,
                    "event_type": event_type,
                    "ip_address": ip_address,
                    "user_agent": user_agent,
                    "details": details,
                }
            )
            .execute()
        )
    except Exception as exc:
        print(f"[audit_service] Failed to log session '{event_type}': {exc}")


async def get_audit_log(limit: int = 100, department_id: Optional[str] = None) -> list:
    """Retrieve the most recent audit log entries, newest first."""
    supabase = await get_async_supabase()
    query = supabase.table("audit_log").select("*").order("created_at", desc=True).limit(limit)
    if department_id:
        query = query.eq("department_id", department_id)
    result = await query.execute()
    return result.data
