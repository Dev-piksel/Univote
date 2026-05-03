from fastapi import APIRouter, HTTPException, Response
from database import get_async_supabase
import base64

router = APIRouter()

@router.get("/candidates/{candidate_id}/photo")
async def get_candidate_photo(candidate_id: str):
    """
    Serves a candidate's profile photo as a raw image response.
    This helps reduce JSON payload size and enables browser caching.
    """
    supabase = await get_async_supabase()
    res = (
        await supabase.table("candidates")
        .select("photo_url")
        .eq("id", candidate_id)
        .execute()
    )
    
    if not res.data or not res.data[0].get("photo_url"):
        raise HTTPException(status_code=404, detail="Photo not found")
        
    photo_data_url = res.data[0]["photo_url"]
    
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
                    "Cache-Control": "public, max-age=3600" # Cache for 1 hour
                }
            )
        else:
            # Fallback for old/unexpected data
            raise HTTPException(status_code=400, detail="Invalid photo data format")
    except Exception as e:
        print(f"Error decoding photo for {candidate_id}: {e}")
        raise HTTPException(status_code=500, detail="Error processing image")
