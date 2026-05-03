import os
from typing import Optional
import base64
import json as _json
from dotenv import load_dotenv
from supabase import create_client, Client, create_async_client, AsyncClient
from supabase.client import ClientOptions

load_dotenv()

SUPABASE_URL = os.environ.get("SUPABASE_URL")
SUPABASE_KEY = os.environ.get("SUPABASE_KEY")

if not SUPABASE_URL or not SUPABASE_KEY:
    print("Warning: SUPABASE_URL or SUPABASE_KEY is missing. Please set them in .env")

# Force HTTP/1.1 to avoid "RemoteProtocolError: Server disconnected" errors with HTTP/2
# Also increase timeouts for complex queries
options = ClientOptions(
    postgrest_client_timeout=30,
    storage_client_timeout=30,
)

# Defer client creation — raises a clear error at runtime instead of crashing at import
if not SUPABASE_URL or not SUPABASE_KEY:
    raise RuntimeError(
        "SUPABASE_URL and SUPABASE_KEY environment variables must be set. "
        "Add them to Railway Variables (or your .env file for local dev)."
    )

supabase: Client = create_client(
    SUPABASE_URL, SUPABASE_KEY, options=options
)

_async_supabase: Optional[AsyncClient] = None


async def get_async_supabase() -> AsyncClient:
    global _async_supabase
    if _async_supabase is None:
        _async_supabase = await create_async_client(
            SUPABASE_URL, SUPABASE_KEY, options=options
        )
    return _async_supabase


def _encode_token(last_id: str) -> str:
    """Encode the last record's id into an opaque Base64 page token."""
    return base64.urlsafe_b64encode(_json.dumps({"id": last_id}).encode()).decode()


def _decode_token(token: str) -> Optional[str]:
    """Decode a page token back to the cursor id. Returns None on error."""
    try:
        return _json.loads(base64.urlsafe_b64decode(token.encode()))["id"]
    except Exception:
        return None


async def paginate(
    table: str,
    select: str = "*",
    order_column: str = "id",
    page_size: int = 50,
    page_token: Optional[str] = None,
    filters: Optional[dict] = None,
) -> dict:
    """
    Google AIP-158 cursor-based pagination over any Supabase table.

    Returns:
        {
          "data": [...],
          "next_page_token": "<str or None>",
        }
    """
    supabase = await get_async_supabase()
    query = supabase.table(table).select(select).order(order_column).limit(page_size)

    # Apply caller-supplied equality filters (e.g. {"election_id": "abc"})
    if filters:
        for col, val in filters.items():
            query = query.eq(col, val)

    # If a cursor token was supplied, start after that id
    if page_token:
        cursor_id = _decode_token(page_token)
        if cursor_id:
            query = query.gt(order_column, cursor_id)

    res = await query.execute()
    data = res.data or []

    next_token = None
    if len(data) == page_size:
        # There may be more — encode the last id as the next cursor
        next_token = _encode_token(str(data[-1][order_column]))

    return {"data": data, "next_page_token": next_token}
