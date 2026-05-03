from fastapi import HTTPException
from database import get_async_supabase
from services import election_service
from deps import create_access_token
from datetime import timedelta
import hashlib
import secrets
import string


async def validate_student(student_id: str) -> dict:
    """Check that a student exists and return all active/completed elections with a secure access token."""
    available_elections = await election_service.get_available_elections()
    # Logic note: we allow students to login even if no elections are active/completed, 
    # so they can see upcoming ones or their results history.

    # Role guard: check if this ID belongs to an adviser or admin to prevent unauthorized access
    supabase = await get_async_supabase()
    adviser_check = (
        await supabase.table("advisers")
        .select("id")
        .eq("id_number", student_id)
        .execute()
    )
    admin_check = (
        await supabase.table("admins")
        .select("id")
        .eq("id_number", student_id)
        .execute()
    )
    if adviser_check.data or admin_check.data:
        raise HTTPException(
            status_code=403,
            detail="Only registered students can access the voting portal.",
        )

    result = (
        await supabase.table("students")
        .select("id, student_id, full_name, program, year_level, photo_url")
        .eq("student_id", student_id)
        .execute()
    )

    if not result.data:
        raise HTTPException(
            status_code=404,
            detail="Student ID not found in the registered voters list.",
        )

    student = result.data[0]

    # Generate a short-lived student token (30 minutes)
    access_token = create_access_token(
        data={
            "sub": student["id"],
            "student_id": student["student_id"],
            "role": "student",
        },
        expires_delta=timedelta(minutes=30),
    )

    # Check which elections the student has already voted in
    voted_result = await (
        supabase.table("votes")
        .select("election_id")
        .eq("student_id", student["id"])
        .execute()
    )
    voted_election_ids = set(v["election_id"] for v in (voted_result.data or []))

    # Annotate each election with has_voted
    elections_with_status = []
    for election in available_elections:
        elections_with_status.append(
            {**election, "has_voted": election["id"] in voted_election_ids}
        )

    return {
        "access_token": access_token,
        "student": student,
        "active_elections": elections_with_status,
    }


async def get_or_create_voting_pin(student_uuid: str) -> str:
    """Generate a 6-character alphanumeric PIN if missing, excluding ambiguous chars."""
    supabase = await get_async_supabase()
    res = (
        await supabase.table("students")
        .select("voting_pin")
        .eq("id", student_uuid)
        .execute()
    )

    # If PIN already exists, return it (one PIN per voting session/life until used)
    if res.data and res.data[0].get("voting_pin"):
        return res.data[0]["voting_pin"]

    # Generate a fresh 6-character Alphanumeric PIN (excluding O, 0, I, 1)
    chars = string.ascii_uppercase + string.digits
    excluded = {"O", "0", "I", "1"}
    alphabet = "".join(c for c in chars if c not in excluded)
    new_pin = "".join(secrets.choice(alphabet) for _ in range(6))

    await (
        supabase.table("students")
        .update({"voting_pin": new_pin})
        .eq("id", student_uuid)
        .execute()
    )
    return new_pin


def _generate_receipt_id(student_uuid: str, election_id: str) -> str:
    """Generate a unique, deterministic receipt ID for vote verification."""
    raw = f"{student_uuid}:{election_id}"
    return hashlib.sha256(raw.encode()).hexdigest()[:12].upper()


async def cast_votes(
    student_id: str,
    election_id: str,
    passcode_id: str,
    adviser_id: str,
    votes: list,
    session_passcode: str,
) -> dict:
    """Insert vote records via RPC and mark the student as voted. Returns receipt info."""
    supabase = await get_async_supabase()

    # 0. VERIFY ELECTION STATUS (Security Layer 0)
    # Ensure the election is actually "active" before allowing any votes.
    elec_res = (
        await supabase.table("elections")
        .select("status")
        .eq("id", election_id)
        .execute()
    )
    if not elec_res.data:
        raise HTTPException(status_code=404, detail="Election session not found.")
    
    status = elec_res.data[0]["status"]
    if status != "active":
        raise HTTPException(
            status_code=403, 
            detail=f"Voting is not permitted for this election. Current status: {status.upper()}"
        )

    # 1. VERIFY SESSION PASSCODE (Layer 2 - Adviser Passcode)
    # Use the adviser_id to find the LATEST active record for this election.
    # This allows the student to vote even if the record they used at entry (passcode_id)
    # has been replaced by a fresher one (due to adviser rotation).
    from datetime import datetime, timezone

    now = datetime.now(timezone.utc).isoformat()
    passcode_check = await (
        supabase.table("election_passcodes")
        .select("id, passcode, expires_at")
        .eq("election_id", str(election_id))
        .eq("adviser_id", str(adviser_id))
        .eq("is_active", True)
        .execute()
    )

    if not passcode_check.data:
        raise HTTPException(
            status_code=403,
            detail="Active session not found. Please re-enter with the current 6-digit Entry PIN.",
        )

    # Use the most recent active record
    passcode_record = passcode_check.data[0]
    
    # Check if the provided session_passcode matches the latest record
    if passcode_record["passcode"].upper() != session_passcode.strip().upper():
        raise HTTPException(
            status_code=403,
            detail="Invalid Adviser Session Passcode. Please ensure you are using the current 8-character code shown on your adviser's screen.",
        )

    # Check expiration (This applies to the 8-char passcode)
    if passcode_record["expires_at"] < now:
        raise HTTPException(
            status_code=403,
            detail="This Session Passcode has expired. Please ask your adviser to generate a new one.",
        )

    # 2. VERIFY STUDENT (Layer 3 - Identity)
    student_result = (
        await supabase.table("students")
        .select("id")
        .eq("student_id", student_id)
        .execute()
    )

    if not student_result.data:
        raise HTTPException(status_code=404, detail="Student ID not found.")

    student_uuid = student_result.data[0]["id"]

    # Use the High-Concurrency RPC for atomic updates
    try:
        rpc_result = await supabase.rpc(
            "cast_ballot_v2",
            {
                "election_id_param": str(election_id),
                "student_uuid_param": str(student_uuid),
                "votes_json": votes,
            },
        ).execute()

        data = rpc_result.data
        result_dict: dict = {}
        if isinstance(data, list) and len(data) > 0:
            result_dict = data[0]
        elif isinstance(data, dict):
            result_dict = data

        # Ensure we always have a receipt_id and vote_count for the frontend
        if not result_dict.get("receipt_id"):
            result_dict["receipt_id"] = _generate_receipt_id(str(student_uuid), str(election_id))
        if "vote_count" not in result_dict:
            result_dict["vote_count"] = len(votes)

        # IMPORTANT: Return the result
        return result_dict
    except Exception as e:
        error_msg = str(e)
        if "already_voted" in error_msg.lower() or "duplicate key" in error_msg.lower():
            raise HTTPException(
                status_code=403,
                detail="You have already cast your ballot for this election.",
            )
        raise HTTPException(
            status_code=400, detail=f"Database error during voting: {error_msg}"
        )


async def get_vote_summary(student_id: str, election_id: str) -> dict:
    """Get the vote summary for a student in a specific election."""
    supabase = await get_async_supabase()
    student_result = (
        await supabase.table("students")
        .select("id, student_id, full_name")
        .eq("student_id", student_id)
        .execute()
    )
    if not student_result.data:
        raise HTTPException(status_code=404, detail="Student not found.")

    student_uuid = student_result.data[0]["id"]

    # Get votes with candidate and partylist info
    votes_result = await (
        supabase.table("votes")
        .select(
            "position, candidate_id, created_at, candidates!inner(id, students!inner(full_name), partylists(name))"
        )
        .eq("student_id", student_uuid)
        .eq("election_id", election_id)
        .execute()
    )

    if not votes_result.data:
        return {"has_voted": False, "votes": [], "receipt_id": None}

    # Generate deterministic receipt from student+election
    receipt_id = (
        hashlib.sha256(f"{student_uuid}:{election_id}".encode())
        .hexdigest()[:12]
        .upper()
    )

    return {
        "has_voted": True,
        "receipt_id": receipt_id,
        "voted_at": votes_result.data[0].get("created_at")
        if votes_result.data
        else None,
        "votes": votes_result.data,
    }
