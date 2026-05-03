from fastapi import HTTPException
from database import get_async_supabase
from uuid import UUID
from typing import Optional
import secrets
import string
from datetime import datetime, timedelta, timezone


async def _ensure_election_modifiable(election_id: str):
    """Raise error if election is active or completed."""
    supabase = await get_async_supabase()
    res = (
        await supabase.table("elections")
        .select("status")
        .eq("id", election_id)
        .execute()
    )
    if res.data:
        status = res.data[0]["status"]
        if status in ("active", "completed"):
            raise HTTPException(
                status_code=400,
                detail=f"Cannot modify data because the election is already {status}.",
            )


async def get_partylists(election_id: Optional[str] = None) -> list:
    supabase = await get_async_supabase()
    query = supabase.table("partylists").select("id, name, election_id, created_at")
    if election_id:
        query = query.eq("election_id", election_id)
    result = await query.execute()
    return result.data


async def create_partylist(election_id: str, name: str) -> dict:
    await _ensure_election_modifiable(election_id)
    supabase = await get_async_supabase()
    result = (
        await supabase.table("partylists")
        .insert({"election_id": election_id, "name": name})
        .execute()
    )
    return result.data


async def update_partylist(partylist_id: str, name: str) -> dict:
    supabase = await get_async_supabase()
    result = (
        await supabase.table("partylists")
        .update({"name": name})
        .eq("id", partylist_id)
        .execute()
    )
    return result.data


async def delete_partylist(partylist_id: str) -> dict:
    # Get election_id first to check status
    supabase = await get_async_supabase()
    pl = (
        await supabase.table("partylists")
        .select("election_id")
        .eq("id", partylist_id)
        .execute()
    )
    if pl.data:
        await _ensure_election_modifiable(pl.data[0]["election_id"])

    # Explicitly delete candidates associated with this partylist first (Cascading Delete)
    await (
        supabase.table("candidates").delete().eq("partylist_id", partylist_id).execute()
    )
    # Then delete the partylist
    result = (
        await supabase.table("partylists").delete().eq("id", partylist_id).execute()
    )
    return result.data


async def get_candidates(election_id: Optional[str] = None) -> list:
    # Fixed: use full_name (matches new schema), join partylists for name
    supabase = await get_async_supabase()
    query = supabase.table("candidates").select(
        "id, position, election_id, student_id, partylist_id, students!inner(student_id, first_name, last_name, middle_initial), partylists(name)"
    )
    if election_id:
        query = query.eq("election_id", election_id)
    result = await query.execute()
    return result.data


async def create_candidate(
    student_id: str,
    position: str,
    election_id: str,
    partylist_id: Optional[UUID] = None,
) -> dict:
    await _ensure_election_modifiable(election_id)
    # Verify the student exists
    supabase = await get_async_supabase()
    student = (
        await supabase.table("students")
        .select("id")
        .eq("student_id", student_id)
        .execute()
    )
    if not student.data:
        raise HTTPException(
            status_code=404, detail="Student not found. Cannot be made a candidate."
        )

    student_uuid = student.data[0]["id"]

    # Check for duplicate
    existing = (
        await supabase.table("candidates")
        .select("id")
        .eq("election_id", election_id)
        .eq("student_id", student_uuid)
        .execute()
    )
    if existing.data:
        raise HTTPException(
            status_code=400,
            detail="This student is already a candidate in this election.",
        )

    payload = {
        "election_id": election_id,
        "student_id": student_uuid,
        "position": position,
    }
    if partylist_id:
        payload["partylist_id"] = str(partylist_id)

    result = await supabase.table("candidates").insert(payload).execute()
    return result.data


async def delete_candidate(candidate_id: str) -> dict:
    # Get election_id to check status
    supabase = await get_async_supabase()
    cand = (
        await supabase.table("candidates")
        .select("election_id")
        .eq("id", candidate_id)
        .execute()
    )
    if cand.data:
        await _ensure_election_modifiable(cand.data[0]["election_id"])

    result = (
        await supabase.table("candidates").delete().eq("id", candidate_id).execute()
    )
    return result.data


async def get_live_results(election_id: str) -> dict:
    """Retrieve tallies using the optimized vote_count column."""
    supabase = await get_async_supabase()
    elec_res = (
        await supabase.table("elections")
        .select("status")
        .eq("id", election_id)
        .execute()
    )
    status = elec_res.data[0]["status"] if elec_res.data else "unknown"

    # Fetch all candidates first to establish the baseline (including 0 votes)
    candidates_res = (
        await supabase.table("candidates")
        .select("id, position")
        .eq("election_id", election_id)
        .execute()
    )

    # Fetch all actual votes to calculate live tallies accurately
    votes_res = (
        await supabase.table("votes")
        .select("position, candidate_id, created_at, student_id")
        .eq("election_id", election_id)
        .execute()
    )

    # Calculate turnout metrics from the actual votes table
    voted_count = 0
    last_vote_at = None
    
    if votes_res.data:
        # Unique students who cast at least one vote in this election
        voted_count = len(set(v["student_id"] for v in votes_res.data))
        # Most recent vote timestamp
        last_vote_at = max(v["created_at"] for v in votes_res.data)
    
    # Calculate total eligible voters based on department scoping
    election_res = await supabase.table("elections").select("department_id").eq("id", election_id).single().execute()
    dept_id = election_res.data.get("department_id") if election_res.data else None
    
    total_voters = 0
    if dept_id:
        voters_res = await supabase.table("students").select("id", count="exact").eq("department_id", dept_id).execute()
        total_voters = voters_res.count if voters_res.count is not None else 0
    else:
        voters_res = await supabase.table("students").select("id", count="exact").execute()
        total_voters = voters_res.count if voters_res.count is not None else 0

    turnout_percentage = round((voted_count / total_voters * 100), 2) if total_voters > 0 else 0

    tallies: dict = {}

    # Initialize all candidates with 0 votes to ensure they appear on the dashboard
    for cand in candidates_res.data:
        pos = cand["position"]
        cid = cand["id"]
        tallies.setdefault(pos, {})
        tallies[pos][cid] = 0

    # Tally up the actual cast votes
    for vote in votes_res.data or []:
        pos = vote["position"]
        cid = vote["candidate_id"]
        if pos in tallies and cid in tallies[pos]:
            tallies[pos][cid] += 1

    return {
        "status": status, 
        "tallies": tallies,
        "voted_count": voted_count,
        "total_voters": total_voters,
        "turnout_percentage": turnout_percentage,
        "last_vote_at": last_vote_at
    }


async def refresh_adviser_passcode(election_id: str, adviser_id: str) -> dict:
    """Generate a new 16-digit alphanumeric passcode for an election and adviser."""
    # Format: XXXX-XXXX-XXXX-XXXX
    alphabet = string.ascii_uppercase + string.digits
    blocks = []
    for _ in range(4):
        blocks.append("".join(secrets.choice(alphabet) for _ in range(4)))

    new_passcode = "-".join(blocks)
    expires_at = (datetime.now(timezone.utc) + timedelta(minutes=30)).isoformat()

    supabase = await get_async_supabase()
    # Call the atomic RPC function
    res = await supabase.rpc(
        "generate_election_passcode",
        {
            "p_election_id": election_id,
            "p_adviser_id": adviser_id,
            "p_passcode": new_passcode,
            "p_expires_at": expires_at,
        },
    ).execute()

    if not res.data:
        raise HTTPException(
            status_code=500, detail="Failed to generate passcode via RPC."
        )

    return res.data


async def get_active_passcode(election_id: str, adviser_id: str) -> Optional[dict]:
    """Retrieve the current active and non-expired passcode for an adviser."""
    supabase = await get_async_supabase()
    now = datetime.now(timezone.utc).isoformat()

    res = await (
        supabase.table("election_passcodes")
        .select("passcode, expires_at")
        .eq("election_id", election_id)
        .eq("adviser_id", adviser_id)
        .eq("is_active", True)
        .gt("expires_at", now)
        .order("created_at", desc=True)
        .limit(1)
        .execute()
    )

    return res.data[0] if res.data else None
