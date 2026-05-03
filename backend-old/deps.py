"""
FastAPI dependency for extracting and verifying the Custom PyJWT
from the Authorization: Bearer <token> header.
"""

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from dataclasses import dataclass
import jwt
import os
from datetime import datetime, timedelta, timezone

bearer_scheme = HTTPBearer()

SECRET_KEY = os.environ.get("UNIVOTE_JWT_SECRET", "UNIVOTE_SUPER_SECRET_KEY_DEV_ONLY")
ALGORITHM = "HS256"


def create_access_token(data: dict, expires_delta: timedelta | None = None):
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.now(timezone.utc) + expires_delta
    else:
        expire = datetime.now(timezone.utc) + timedelta(minutes=15)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt


@dataclass
class AuthUser:
    id: str
    role: str  # 'admin' or 'adviser' or 'student'


@dataclass
class StudentUser:
    id: str  # The UUID from database
    student_id: str  # The human-readable ID (e.g. 2024-0001)


async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(bearer_scheme),
) -> AuthUser:
    """
    Validate the PyJWT and resolve the user's role from the token payload.
    Used for staff (admin/adviser) and general auth.
    """
    token = credentials.credentials

    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        user_id: str = payload.get("sub")
        role: str = payload.get("role")

        if user_id is None or role is None:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid token payload.",
            )

        return AuthUser(id=user_id, role=role)

    except jwt.ExpiredSignatureError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="Token has expired."
        )
    except jwt.InvalidTokenError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token."
        )


async def get_current_student(
    credentials: HTTPAuthorizationCredentials = Depends(bearer_scheme),
) -> StudentUser:
    """
    Validate the Student PyJWT.
    """
    token = credentials.credentials
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        if payload.get("role") != "student":
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Student token required.",
            )

        return StudentUser(id=payload.get("sub"), student_id=payload.get("student_id"))
    except jwt.ExpiredSignatureError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Student token has expired.",
        )
    except jwt.InvalidTokenError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid student token."
        )
    except Exception as e:
        print(f"Student auth error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="Student session error."
        )


async def require_admin(user: AuthUser = Depends(get_current_user)) -> AuthUser:
    if user.role != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, detail="Admin access required."
        )
    return user


async def require_adviser(user: AuthUser = Depends(get_current_user)) -> AuthUser:
    if user.role not in ("admin", "adviser"):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, detail="Adviser access required."
        )
    return user


async def require_student(
    student: StudentUser = Depends(get_current_student),
) -> StudentUser:
    return student


# Type aliases for use in route signatures
CurrentUser = Depends(get_current_user)
AdminUser = Depends(require_admin)
AdviserUser = Depends(require_adviser)
CurrentStudent = Depends(require_student)
