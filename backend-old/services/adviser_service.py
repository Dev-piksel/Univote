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
        "id, position, election_id, student_id, partylist_id, vote_count, students!inner(student_id, full_name), partylists(name)"
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

    # Fetch total registered students efficiently (count only, no data)
    students_count_res = (
        await supabase.table("students").select("*", count="exact", head=True).execute()
    )
    total_registered = students_count_res.count or 0

    # Mask results if the election is not yet active (or completed)
    if status == "upcoming":
        return {
            "status": "upcoming",
            "tallies": {},
            "total_voters": total_registered,
            "voted_count": 0,
            "not_voted_count": total_registered,
            "message": "Live results will be available once the election begins."
        }

    # Fetch all candidates first to establish the baseline (including 0 votes)
    candidates_res = (
        await supabase.table("candidates")
        .select("id, position")
        .eq("election_id", election_id)
        .execute()
    )

    # Fetch cast votes with timestamps to calculate participation and last activity
    votes_res = (
        await supabase.table("votes")
        .select("position, candidate_id, student_id, created_at")
        .eq("election_id", election_id)
        .execute()
    )

    tallies: dict = {}
    unique_voters = set()
    last_vote_at = None

    # Initialize all candidates with 0 votes to ensure they appear on the dashboard
    for cand in candidates_res.data:
        pos = cand["position"]
        cid = cand["id"]
        tallies.setdefault(pos, {})
        tallies[pos][cid] = 0

    # Tally up the actual cast votes and find the latest activity
    for vote in votes_res.data or []:
        pos = vote["position"]
        cid = vote["candidate_id"]
        voter_id = vote.get("student_id")
        vote_time = vote.get("created_at")

        if voter_id:
            unique_voters.add(voter_id)
        
        if vote_time:
            if not last_vote_at or vote_time > last_vote_at:
                last_vote_at = vote_time

        if pos in tallies and cid in tallies[pos]:
            tallies[pos][cid] += 1

    voted_count = len(unique_voters)
    turnout_pct = (voted_count / total_registered * 100) if total_registered > 0 else 0

    return {
        "status": status,
        "tallies": tallies,
        "total_voters": total_registered,
        "voted_count": voted_count,
        "not_voted_count": max(0, total_registered - voted_count),
        "turnout_percentage": round(turnout_pct, 1),
        "last_vote_at": last_vote_at
    }


async def refresh_adviser_passcode(election_id: str, adviser_id: str) -> dict:
    """Generate a new 8-character alphanumeric session passcode for an adviser.
    Each adviser gets their own independent passcode for the same election.
    Ensures that any existing 'entry_pin' is preserved.
    """
    alphabet = string.ascii_uppercase + string.digits
    new_passcode = "".join(secrets.choice(alphabet) for _ in range(8))
    expires_at = (datetime.now(timezone.utc) + timedelta(minutes=30)).isoformat()

    supabase = await get_async_supabase()

    # 1. Fetch existing entry_pin if any
    existing = (
        await supabase.table("election_passcodes")
        .select("entry_pin")
        .eq("election_id", election_id)
        .eq("adviser_id", adviser_id)
        .eq("is_active", True)
        .execute()
    )
    preserved_pin = existing.data[0].get("entry_pin") if existing.data else None

    # 2. Call the atomic RPC function (which handles deactivation of old rows)
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

    new_id = res.data.get("id")

    # 3. If we had a pin, ensure it's on the new record (Safeguard in case RPC isn't updated)
    if preserved_pin and new_id:
        await (
            supabase.table("election_passcodes")
            .update({"entry_pin": preserved_pin})
            .eq("id", new_id)
            .execute()
        )

    return res.data


async def get_active_passcode(election_id: str, adviser_id: str) -> Optional[dict]:
    """Retrieve the current active and non-expired passcode for an adviser.
    Auto-regenerates if no active/non-expired passcode is found.
    """
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

    if res.data:
        return res.data[0]
    
    # Auto-regenerate if missing or expired
    print(f"[Passcode] Auto-refreshing passcode for adviser {adviser_id} (expired or missing)")
    return await refresh_adviser_passcode(election_id, adviser_id)
async def search_students(query: str, limit: int = 5) -> list:
    """Search for students by student_id or full_name with prefix matching."""
    supabase = await get_async_supabase()
    # Search by student_id prefix or full_name (case-insensitive)
    res = (
        await supabase.table("students")
        .select("id, student_id, full_name, program, year_level")
        .or_(f"student_id.ilike.{query}%,full_name.ilike.%{query}%")
        .limit(limit)
        .execute()
    )
    return res.data or []
