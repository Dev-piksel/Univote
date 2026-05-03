import os
from dotenv import load_dotenv

load_dotenv()

SUPABASE_URL: str = os.environ.get("SUPABASE_URL", "")
SUPABASE_KEY: str = os.environ.get("SUPABASE_KEY", "")

# CORS origins separated by comma
ALLOWED_ORIGINS_RAW = os.environ.get(
    "ALLOWED_ORIGINS",
    "http://localhost:5173,http://localhost:4173,http://127.0.0.1:5173,http://127.0.0.1:4173"
)
ALLOWED_ORIGINS: list[str] = [
    o.strip() for o in ALLOWED_ORIGINS_RAW.split(",") if o.strip()
]

if not SUPABASE_URL or not SUPABASE_KEY:
    print("Warning: SUPABASE_URL or SUPABASE_KEY is missing. Please set them in .env")
