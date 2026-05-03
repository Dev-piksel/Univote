from fastapi import APIRouter, HTTPException, Request
from models import StudentAuth, VoteSubmit, PasscodeVerify
from services import student_service, adviser_service, audit_service
from deps import CurrentStudent, StudentUser
from limiter import limiter
from database import get_async_supabase
from datetime import datetime, timezone

router = APIRouter()


@router.post("/validate")
@limiter.limit("5/minute")
async def validate_student(request: Request, auth: StudentAuth):
    result = await student_service.validate_student(auth.student_id)
    # Log student validation event
    await audit_service.log_session(
        user_id=result["student"]["student_id"],
        user_role="student",
        event_type="VALIDATE",
        request=request,
        details={"full_name": result["student"]["full_name"]},
    )

    return {
        "message": "Access granted",
        "student": result["student"],
        "access_token": result["access_token"],
        "active_elections": result["active_elections"],
    }


@router.post("/vote")
@limiter.limit("10/minute")
async def cast_vote(
    request: Request,
    vote_submit: VoteSubmit,
    student: StudentUser = CurrentStudent,
):
    # Security check: ensure student_id in payload matches token
    if vote_submit.student_id != student.student_id:
        raise HTTPException(
            status_code=403, detail="Unauthorized: Student ID mismatch."
        )

    votes_payload = [
        {"candidate_id": str(v.candidate_id), "position": v.position}
        for v in vote_submit.votes
    ]
    result = await student_service.cast_votes(
        student_id=vote_submit.student_id,
        election_id=vote_submit.election_id,
        passcode_id=vote_submit.passcode_id,
        adviser_id=vote_submit.adviser_id,
        votes=votes_payload,
        session_passcode=vote_submit.session_passcode,
    )
    # Log voting event
    await audit_service.log_action(
        actor_id=student.student_id,
        actor_role="student",
        action="VOTE",
        target_type="election",
        target_id=str(vote_submit.election_id),
        details={"receipt_id": result["receipt_id"]},
        request=request,
    )

    return {
        "message": "Vote submitted successfully",
        "receipt_id": result["receipt_id"],
        "vote_count": result["vote_count"],
    }


@router.get("/candidates")
async def get_candidates(election_id: str, student: StudentUser = CurrentStudent):
    return {"data": await adviser_service.get_candidates(election_id)}


@router.put("/profile-photo")
async def upload_student_photo(
    request: Request,
    body: dict,
    student: StudentUser = CurrentStudent,
):
    """Student uploads their own profile photo (base64 data URL)."""
    photo_url = body.get("photo_url", "")
    if not photo_url:
        raise HTTPException(status_code=400, detail="photo_url is required.")
    if len(photo_url) > 7_000_000:
        raise HTTPException(status_code=400, detail="Image too large (max ~5MB).")
    supabase = await get_async_supabase()
    res = (
        await supabase.table("students")
        .update({"photo_url": photo_url})
        .eq("student_id", student.student_id)
        .execute()
    )
    if not res.data:
        raise HTTPException(status_code=404, detail="Student not found.")
    
    # Log student photo upload
    await audit_service.log_action(
        actor_id=student.student_id,
        actor_role="student",
        action="UPLOAD_PROFILE_PHOTO",
        target_type="student",
        target_id=student.student_id,
        details={"photo_url": f"base64_data[{len(photo_url)}]"},
        request=request,
    )
    
    return {"message": "Photo updated.", "photo_url": photo_url}


@router.get("/profile-photo")
async def get_student_photo(student: StudentUser = CurrentStudent):
    """Retrieve the student's current profile photo."""
    supabase = await get_async_supabase()
    res = (
        await supabase.table("students")
        .select("photo_url")
        .eq("student_id", student.student_id)
        .single()
        .execute()
    )
    photo_url = res.data.get("photo_url") if res.data else None
    return {"photo_url": photo_url}



@router.get("/vote-summary")
async def get_vote_summary(
    student_id: str, election_id: str, student: StudentUser = CurrentStudent
):
    # Security check
    if student_id != student.student_id:
        raise HTTPException(
            status_code=403, detail="Unauthorized: Cannot view other students' summary."
        )
    return await student_service.get_vote_summary(student_id, election_id)


@router.get("/results")
async def get_results(election_id: str):
    # Results are usually public for students once the election is active/completed
    return {"data": await adviser_service.get_live_results(election_id)}


@router.post("/verify-passcode")
async def verify_passcode(
    payload: PasscodeVerify, student: StudentUser = CurrentStudent
):
    supabase = await get_async_supabase()

    # First check if it exists and is active for this election
    # The Entry PIN itself does not expire (only the 8-char session passcode does)
    res = await (
        supabase.table("election_passcodes")
        .select("id, adviser_id")
        .eq("election_id", str(payload.election_id))
        .eq("entry_pin", payload.passcode.strip())
        .eq("is_active", True)
        .execute()
    )

    if not res.data:
        raise HTTPException(status_code=403, detail="Invalid Entry PIN. Please check with your adviser.")

    record = res.data[0]
    return {
        "message": "Passcode verified.", 
        "passcode_id": record["id"], 
        "adviser_id": record["adviser_id"]
    }


@router.get("/voting-pin")
async def get_voting_pin(student_id: str, student: StudentUser = CurrentStudent):
    if student_id != student.student_id:
        raise HTTPException(status_code=403, detail="Unauthorized")

    # We need the UUID for the service call
    supabase = await student_service.get_async_supabase()
    st_res = (
        await supabase.table("students")
        .select("id")
        .eq("student_id", student_id)
        .execute()
    )
    if not st_res.data:
        raise HTTPException(status_code=404, detail="Student not found")

    pin = await student_service.get_or_create_voting_pin(st_res.data[0]["id"])
    return {"voting_pin": pin}
