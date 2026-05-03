import asyncio
import json
from fastapi import APIRouter
from fastapi.responses import StreamingResponse
from services import adviser_service

router = APIRouter(prefix="/adviser", tags=["adviser"])


@router.get("/stream/{election_id}")
async def stream_results(election_id: str):
    """
    SSE endpoint — streams live vote counts to any connected client.
    Pushes a fresh snapshot every 2 seconds. No auth required;
    results are considered public once an election is active.
    """

    async def event_generator():
        try:
            while True:
                try:
                    data = await adviser_service.get_live_results(election_id)
                    yield f"data: {json.dumps(data)}\n\n"
                except Exception as e:
                    print(f"SSE Error for election {election_id}: {e}")
                    # Push an error event or just skip this tick
                    # yield f"data: {json.dumps({'error': 'Transient connection issue'})}\n\n"
                await asyncio.sleep(2)
        except asyncio.CancelledError:
            # Client disconnected — clean exit
            return

    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "X-Accel-Buffering": "no",  # Disable Nginx buffering
        },
    )
