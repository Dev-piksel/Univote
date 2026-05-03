from fastapi import APIRouter, HTTPException, Request, Depends
from services import student_service, adviser_service, audit_service, election_service
from dependencies.auth import require_student
from models import StudentAuth, VoteSubmit, PasscodeVerify, StudentUser
from limiter import limiter
from database import get_async_supabase

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
        details={
                "first_name": result["student"].get("first_name"),
                "last_name": result["student"].get("last_name"),
            },
    )

    return {
        "message": "Access granted",
        "student": result["student"],
        "access_token": result["access_token"],
        "active_elections": result["active_elections"],
    }


@router.get("/me")
async def get_student_me(student: StudentUser = Depends(require_student)):
    """Retrieve the student's full profile details using their JWT."""
    supabase = await get_async_supabase()
    res = (
        await supabase.table("students")
        .select("id, student_id, first_name, last_name, middle_initial, program, year_level, photo_url, email, department_id")
        .eq("student_id", student.student_id)
        .single()
        .execute()
    )
    if not res.data:
        raise HTTPException(status_code=404, detail="Student not found.")
    return res.data


@router.post("/vote")
@limiter.limit("10/minute")
async def cast_vote(
    request: Request,
    vote_submit: VoteSubmit,
    student: StudentUser = Depends(require_student),
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
        department_id=student.department_id,
        request=request,
        actor_name=student.full_name,
        actor_username=student.username,
    )


    return {
        "message": "Vote submitted successfully",
        "receipt_id": result["receipt_id"],
        "vote_count": result["vote_count"],
    }


@router.get("/candidates")
async def get_candidates(election_id: str, student: StudentUser = Depends(require_student)):
    # HIGH: Secure scoping to prevent cross-department leakage
    await election_service.get_election_secure(election_id, student)
    return {"data": await adviser_service.get_candidates(election_id)}


@router.put("/profile-photo")
async def upload_student_photo(
    request: Request,
    body: dict,
    student: StudentUser = Depends(require_student),
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
        department_id=student.department_id,
        request=request,
        actor_name=student.full_name,
        actor_username=student.username,
    )

    
    return {"message": "Photo updated.", "photo_url": photo_url}


@router.get("/profile-photo")
async def get_student_photo(student: StudentUser = Depends(require_student)):
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
    student_id: str, election_id: str, student: StudentUser = Depends(require_student)
):
    # Security check
    if student_id != student.student_id:
        raise HTTPException(
            status_code=403, detail="Unauthorized: Cannot view other students' summary."
        )
    return await student_service.get_vote_summary(student_id, election_id)


@router.get("/results")
async def get_results(election_id: str, student: StudentUser = Depends(require_student)):
    # Enforce department scoping — student can only view results for their own election
    await election_service.get_election_secure(election_id, student)
    return {"data": await adviser_service.get_live_results(election_id)}


@router.post("/verify-passcode")
@limiter.limit("3/minute")
async def verify_passcode(
    request: Request,
    payload: PasscodeVerify, 
    student: StudentUser = Depends(require_student)
):
    # Security Layer: Ensure the election actually exists and matches the student's jurisdiction
    await election_service.get_election_secure(payload.election_id, student)
    
    supabase = await get_async_supabase()

    # First check if it exists and is active for this election
    res = await (
        supabase.table("election_passcodes")
        .select("id, adviser_id")
        .eq("election_id", str(payload.election_id))
        .eq("entry_pin", payload.passcode.strip())
        .eq("is_active", True)
        .execute()
    )

    if not res.data:
        # Intentional 403 with generic message to prevent PIN enumeration
        raise HTTPException(status_code=403, detail="Invalid Entry credentials.")

    record = res.data[0]
    return {
        "message": "Passcode verified.", 
        "passcode_id": record["id"], 
        "adviser_id": record["adviser_id"]
    }


@router.get("/voting-pin")
async def get_voting_pin(student_id: str, student: StudentUser = Depends(require_student)):
    if student_id != student.student_id:
        raise HTTPException(status_code=403, detail="Unauthorized")

    # We need the UUID for the service call
    supabase = await get_async_supabase()

    st_res = (
        await supabase.table("students")
        .select("id")
        .eq("student_id", student_id)
        .execute()
    )
    if not st_res.data:
        raise HTTPException(status_code=404, detail="Student not found")

    pin = await student_service.get_or_create_voting_pin(st_res.data[0]["id"])
    
    # Log sensitive PIN retrieval
    await audit_service.log_action(
        actor_id=student.student_id,
        actor_role="student",
        action="GET_VOTING_PIN",
        target_type="student",
        target_id=student.student_id,
        department_id=student.department_id,
        actor_name=student.full_name,
        actor_username=student.username,
    )

    return {"voting_pin": pin}

