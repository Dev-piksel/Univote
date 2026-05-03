from fastapi import APIRouter, HTTPException, Response
from database import get_async_supabase
import base64

router = APIRouter()

@router.get("/candidates/{candidate_id}/photo")
async def get_candidate_photo(candidate_id: str):
    """
    Serves a candidate's profile photo as a raw image response.
    Falls back to the linked student's profile photo if no dedicated
    candidate photo has been uploaded.
    """
    supabase = await get_async_supabase()

    # Fetch candidate's own photo AND the linked student's photo in one query
    res = (
        await supabase.table("candidates")
        .select("photo_url, students!left(photo_url)")
        .eq("id", candidate_id)
        .execute()
    )

    if not res.data:
        raise HTTPException(status_code=404, detail="Candidate not found")

    record = res.data[0]

    # Prefer candidate-specific photo; fall back to student profile photo
    photo_data_url = record.get("photo_url") or (
        record.get("students") or {}
    ).get("photo_url")

    if not photo_data_url:
        raise HTTPException(status_code=404, detail="Photo not found")

    try:
        # Expected format: data:image/png;base64,iVBORw0KGgo...
        if "," in photo_data_url:
            header, encoded = photo_data_url.split(",", 1)
            content_type = header.split(";")[0].split(":")[1]
            image_bytes = base64.b64decode(encoded)

            return Response(
                content=image_bytes,
                media_type=content_type,
                headers={
                    "Cache-Control": "public, max-age=3600"  # Cache for 1 hour
                }
            )
        else:
            raise HTTPException(status_code=400, detail="Invalid photo data format")
    except HTTPException:
        raise
    except Exception as e:
        print(f"Error decoding photo for {candidate_id}: {e}")
        raise HTTPException(status_code=500, detail="Error processing image")
