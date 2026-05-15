import os
import jwt
from datetime import datetime, timedelta, timezone
from typing import Optional

SECRET_KEY = os.environ.get("UNIVOTE_JWT_SECRET")
# Security check: Never allow default secrets in production-like environments
if not SECRET_KEY:
    if os.environ.get("ENVIRONMENT") == "production":
         raise RuntimeError("UNIVOTE_JWT_SECRET must be set in production!")
    SECRET_KEY = "UNIVOTE_SUPER_SECRET_KEY_DEV_ONLY"
    print("Warning: Using insecure default JWT secret. Set UNIVOTE_JWT_SECRET in .env")

ALGORITHM = "HS256"

def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    """Generate a PyJWT for authentication."""
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.now(timezone.utc) + expires_delta
    else:
        expire = datetime.now(timezone.utc) + timedelta(minutes=15)
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)

def decode_access_token(token: str) -> Optional[dict]:
    """Decode and validate a PyJWT. Returns the payload or None if invalid."""
    try:
        return jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
    except (jwt.ExpiredSignatureError, jwt.InvalidTokenError):
        return None
