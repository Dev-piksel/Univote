import os
import sys
import logging

# Configure basic logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    handlers=[logging.StreamHandler(sys.stdout)],
)
logger = logging.getLogger(__name__)

sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# ruff: noqa: E402
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
from starlette.exceptions import HTTPException as StarletteHTTPException
from slowapi.errors import RateLimitExceeded
from limiter import limiter
from routes import (
    admin,
    adviser,
    student,
    auth as auth_router,
    results as results_router,
    common as common_router,
)

from config import ALLOWED_ORIGINS


import asyncio
from services.election_service import auto_transition_status

app = FastAPI(title="UniVote API")
app.state.limiter = limiter

async def run_election_scheduler():
    """Background task to automatically start/end elections based on schedule."""
    print("[Scheduler] Starting election status scheduler...")
    while True:
        try:
            summary = await auto_transition_status()
            if summary["started"] > 0 or summary["ended"] > 0:
                print(f"[Scheduler] Processed: {summary['started']} started, {summary['ended']} ended.")
        except Exception as e:
            print(f"[Scheduler] Error in auto-transition: {e}")
        
        # Run every 60 seconds
        await asyncio.sleep(60)

@app.on_event("startup")
async def startup_event():
    # Start the background scheduler
    asyncio.create_task(run_election_scheduler())


def rate_limit_handler(request: Request, exc: RateLimitExceeded):
    """Custom handler to provide the retry_after value to the frontend."""
    # SlowAPI's RateLimitExceeded exception contains the limit that was hit.
    # We can calculate/extract the wait time if the library provides it,
    # but the simplest reliable way is to let the handler return the standard message
    # and maybe add a default or extracted 'Retry-After' header.

    # Actually, we can just return a custom JSON response.
    response = JSONResponse(
        status_code=429,
        content={
            "message": "Too many requests. Please wait before trying again.",
            "detail": str(exc.detail),
            "retry_after": 60,  # Default to 60s if not specified, or we could extract it
        },
    )
    return response


app.add_exception_handler(RateLimitExceeded, rate_limit_handler)


@app.exception_handler(StarletteHTTPException)
async def http_exception_handler(request: Request, exc: StarletteHTTPException):
    return JSONResponse(
        status_code=exc.status_code,
        content={"message": str(exc.detail), "detail": exc.detail},
    )


@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    return JSONResponse(
        status_code=422,
        content={"message": "Validation Error", "detail": exc.errors()},
    )


@app.exception_handler(Exception)
async def universal_exception_handler(request: Request, exc: Exception):
    return JSONResponse(
        status_code=500,
        content={"message": "An internal server error occurred.", "detail": str(exc)},
    )


app.add_middleware(
    CORSMiddleware,
    allow_origins=ALLOWED_ORIGINS,  # Loaded from environment
    allow_credentials=False,  # App uses Bearer tokens (headers), not cookies
    allow_methods=["*"],
    allow_headers=["*"],
    expose_headers=["Content-Type"],
)


# Public: no auth required
app.include_router(results_router.router, prefix="/api/results", tags=["results"])

app.include_router(auth_router.router, prefix="/api/auth", tags=["auth"])

# Student voting: validated by student_id only (no account required)
app.include_router(student.router, prefix="/api/student", tags=["student"])

# Protected: admin and adviser routes require a valid Supabase JWT
app.include_router(admin.router, prefix="/api/admin", tags=["admin"])
app.include_router(adviser.router, prefix="/api/adviser", tags=["adviser"])
app.include_router(common_router.router, prefix="/api/common", tags=["common"])


@app.get("/")
async def read_root():
    return {"message": "Welcome to UniVote API"}


@app.get("/health")
async def health_check():
    """Health check endpoint for monitoring."""
    return {"status": "ok", "version": "1.0.0"}
