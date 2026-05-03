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
    request: Optional[Request] = None,
) -> None:
    """
    Insert a row into the audit_log table.
    Call this at the end of every mutating service operation.
    Failures are silently swallowed so audit errors never break the main flow.
    """
    try:
        supabase = await get_async_supabase()

        # Enrich details with IP and User-Agent if request is provided
        if request:
            if details is None:
                details = {}
            details["ip_address"] = request.client.host if request.client else None
            details["user_agent"] = request.headers.get("user-agent")

        await (
            supabase.table("audit_log")
            .insert(
                {
                    "actor_id": actor_id,
                    "actor_role": actor_role,
                    "action": action,
                    "target_type": target_type,
                    "target_id": target_id,
                    "details": details,
                }
            )
            .execute()
        )
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


async def get_audit_log(limit: int = 100) -> list:
    """Retrieve the most recent audit log entries, newest first."""
    supabase = await get_async_supabase()
    result = await (
        supabase.table("audit_log")
        .select("*")
        .order("created_at", desc=True)
        .limit(limit)
        .execute()
    )
    return result.data
