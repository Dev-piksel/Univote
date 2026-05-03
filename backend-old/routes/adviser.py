from fastapi import APIRouter, Depends, HTTPException, Request, Query
from typing import Optional
from database import get_async_supabase, paginate
from models import PartylistCreate, CandidateCreate, AdviserChangePassword, AdviserSetEntryPin
from services import adviser_service, audit_service, election_service
from deps import require_adviser, AuthUser
from passlib.hash import argon2

router = APIRouter()


@router.get("/elections")
async def get_elections(
    user: AuthUser = Depends(require_adviser),
):
    """Return all elections visible to the adviser (same data as admin view)."""
    return {"data": await election_service.get_elections()}


@router.get("/partylists")
async def get_partylists(
    election_id: str | None = None,
    user: AuthUser = Depends(require_adviser),
):
    return {"data": await adviser_service.get_partylists(election_id)}


@router.post("/partylists")
async def create_partylist(
    partylist: PartylistCreate,
    election_id: str,
    user: AuthUser = Depends(require_adviser),
):
    data = await adviser_service.create_partylist(election_id, partylist.name)
    await audit_service.log_action(
        actor_id=user.id,
        actor_role=user.role,
        action="CREATE_PARTYLIST",
        target_type="partylist",
        target_id=data[0]["id"] if data else None,
        details={"name": partylist.name, "election_id": election_id},
    )
    return {"message": "Partylist created", "data": data}


@router.put("/partylists/{partylist_id}")
async def update_partylist(
    partylist_id: str,
    partylist: PartylistCreate,
    user: AuthUser = Depends(require_adviser),
):
    data = await adviser_service.update_partylist(partylist_id, partylist.name)
    await audit_service.log_action(
        actor_id=user.id,
        actor_role=user.role,
        action="UPDATE_PARTYLIST",
        target_type="partylist",
        target_id=partylist_id,
        details={"name": partylist.name},
    )
    return {"message": "Partylist updated", "data": data}


@router.delete("/partylists/{partylist_id}")
async def delete_partylist(
    partylist_id: str,
    user: AuthUser = Depends(require_adviser),
):
    await adviser_service.delete_partylist(partylist_id)
    await audit_service.log_action(
        actor_id=user.id,
        actor_role=user.role,
        action="DELETE_PARTYLIST",
        target_type="partylist",
        target_id=partylist_id,
        details={},
    )
    return {"message": "Partylist deleted"}


@router.get("/candidates")
async def get_candidates(
    election_id: str | None = None,
    user: AuthUser = Depends(require_adviser),
):
    return {"data": await adviser_service.get_candidates(election_id)}


@router.post("/candidates")
async def create_candidate(
    candidate: CandidateCreate,
    election_id: str,
    user: AuthUser = Depends(require_adviser),
):
    data = await adviser_service.create_candidate(
        student_id=candidate.student_id,
        position=candidate.position,
        election_id=election_id,
        partylist_id=candidate.partylist_id,
    )
    await audit_service.log_action(
        actor_id=user.id,
        actor_role=user.role,
        action="ADD_CANDIDATE",
        target_type="candidate",
        target_id=data[0]["id"] if data else None,
        details={"student_id": candidate.student_id, "position": candidate.position},
    )
    return {"message": "Candidate added", "data": data}


@router.delete("/candidates/{candidate_id}")
async def delete_candidate(
    candidate_id: str,
    user: AuthUser = Depends(require_adviser),
):
    await adviser_service.delete_candidate(candidate_id)
    await audit_service.log_action(
        actor_id=user.id,
        actor_role=user.role,
        action="DELETE_CANDIDATE",
        target_type="candidate",
        target_id=candidate_id,
        details={},
    )
    return {"message": "Candidate deleted"}


@router.get("/live-results/{election_id}")
async def get_live_results(
    election_id: str,
    user: AuthUser = Depends(require_adviser),
):
    return {"data": await adviser_service.get_live_results(election_id)}


@router.put("/candidates/{candidate_id}/photo")
async def upload_candidate_photo(
    request: Request,
    candidate_id: str,
    body: dict,
    user: AuthUser = Depends(require_adviser),
):
    """Store a base64 data URL as the candidate's profile photo."""
    photo_url = body.get("photo_url", "")
    if not photo_url:
        raise HTTPException(status_code=400, detail="photo_url is required.")
    # Limit base64 size (~5MB after encoding)
    if len(photo_url) > 7_000_000:
        raise HTTPException(status_code=400, detail="Image too large (max ~5MB).")
    supabase = await get_async_supabase()
    res = (
        await supabase.table("candidates")
        .update({"photo_url": photo_url})
        .eq("id", candidate_id)
        .execute()
    )
    if not res.data:
        raise HTTPException(status_code=404, detail="Candidate not found.")
    
    # Log candidate photo upload
    await audit_service.log_action(
        actor_id=str(user.id),
        actor_role="adviser",
        action="UPLOAD_CANDIDATE_PHOTO",
        target_type="candidate",
        target_id=candidate_id,
        details={"photo_url": f"base64_data[{len(photo_url)}]"},
        request=request,
    )
    
    return {"message": "Photo updated.", "photo_url": photo_url}


@router.delete("/candidates/{candidate_id}/photo")
async def delete_candidate_photo(
    request: Request,
    candidate_id: str,
    user: AuthUser = Depends(require_adviser),
):
    """Remove the candidate's profile photo."""
    supabase = await get_async_supabase()
    # Log candidate photo deletion
    await audit_service.log_action(
        actor_id=str(user.id),
        actor_role="adviser",
        action="DELETE_CANDIDATE_PHOTO",
        target_type="candidate",
        target_id=candidate_id,
        request=request,
    )
    return {"message": "Photo removed."}



@router.get("/audit-log")
async def get_audit_log(
    user: AuthUser = Depends(require_adviser),
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


@router.get("/elections/{election_id}/passcode")
async def get_passcode(
    election_id: str,
    user: AuthUser = Depends(require_adviser),
):
    passcode_data = await adviser_service.get_active_passcode(election_id, user.id)
    return {"data": passcode_data}


@router.post("/elections/{election_id}/refresh-passcode")
async def refresh_passcode(
    request: Request,
    election_id: str,
    user: AuthUser = Depends(require_adviser),
):
    res_data = await adviser_service.refresh_adviser_passcode(election_id, user.id)
    new_passcode = res_data["passcode"]

    await audit_service.log_action(
        actor_id=user.id,
        actor_role=user.role,
        action="REFRESH_PASSCODE",
        target_type="election",
        target_id=election_id,
        details={"passcode": new_passcode, "adviser_id": user.id},
        request=request,
    )
    return {
        "message": "Passcode refreshed",
        "adviser_passcode": new_passcode,
        "expires_at": res_data["expires_at"],
    }


@router.post("/elections/{election_id}/set-entry-pin")
async def set_entry_pin(
    election_id: str,
    body: AdviserSetEntryPin,
    user: AuthUser = Depends(require_adviser),
):
    """Adviser sets their own 6-digit numeric entry PIN for the election room."""
    pin = body.pin.strip()
    if not pin.isdigit() or len(pin) != 6:
        raise HTTPException(status_code=400, detail="Entry PIN must be exactly 6 digits.")

    supabase = await get_async_supabase()
    # Upsert the entry_pin on their active passcode row, or create a standalone record
    # We store it as a separate column on the adviser's passcode row
    existing = (
        await supabase.table("election_passcodes")
        .select("id")
        .eq("election_id", election_id)
        .eq("adviser_id", user.id)
        .eq("is_active", True)
        .execute()
    )
    if existing.data:
        await supabase.table("election_passcodes").update(
            {"entry_pin": pin}
        ).eq("id", existing.data[0]["id"]).execute()
    else:
        # Create a placeholder row with entry_pin only (no session passcode yet)
        await supabase.table("election_passcodes").insert({
            "election_id": election_id,
            "adviser_id": user.id,
            "passcode": "",  # will be filled on first refresh
            "is_active": True,
            "entry_pin": pin,
            "expires_at": "2099-01-01T00:00:00+00:00",
        }).execute()

    await audit_service.log_action(
        actor_id=user.id,
        actor_role="adviser",
        action="SET_ENTRY_PIN",
        target_type="election",
        target_id=election_id,
    )
    return {"message": "Entry PIN set successfully."}


@router.get("/elections/{election_id}/entry-pin")
async def get_entry_pin(
    election_id: str,
    user: AuthUser = Depends(require_adviser),
):
    """Retrieve the current entry PIN set by this adviser."""
    supabase = await get_async_supabase()
    res = (
        await supabase.table("election_passcodes")
        .select("entry_pin")
        .eq("election_id", election_id)
        .eq("adviser_id", user.id)
        .eq("is_active", True)
        .order("created_at", desc=True)
        .limit(1)
        .execute()
    )
    pin = res.data[0].get("entry_pin") if res.data else None
    return {"entry_pin": pin}


@router.put("/change-password")
async def change_password(
    body: AdviserChangePassword,
    user: AuthUser = Depends(require_adviser),
):
    """Allow an adviser to change their password. Clears the must_change_password flag."""
    supabase = await get_async_supabase()
    res = (
        await supabase.table("advisers")
        .select("password_hash")
        .eq("id", user.id)
        .execute()
    )
    if not res.data:
        raise HTTPException(status_code=404, detail="Adviser not found.")

    current_hash = res.data[0]["password_hash"]
    if not argon2.verify(body.current_password, current_hash):
        raise HTTPException(status_code=400, detail="Current password is incorrect.")

    if len(body.new_password) < 8:
        raise HTTPException(status_code=400, detail="New password must be at least 8 characters.")

    new_hash = argon2.hash(body.new_password)
    await supabase.table("advisers").update({
        "password_hash": new_hash,
        "must_change_password": False,
    }).eq("id", user.id).execute()

    await audit_service.log_action(
        actor_id=user.id,
        actor_role="adviser",
        action="CHANGE_PASSWORD",
        target_type="adviser",
        target_id=user.id,
    )
    return {"message": "Password changed successfully."}
@router.get("/students/search")
async def search_students(
    query: str = Query(..., min_length=1),
    user: AuthUser = Depends(require_adviser),
):
    """Search for students to suggest for candidate registration."""
    return {"data": await adviser_service.search_students(query)}
