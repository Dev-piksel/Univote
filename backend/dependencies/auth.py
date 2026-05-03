from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from utils.jwt import decode_access_token
from models import AuthUser, StudentUser

bearer_scheme = HTTPBearer()

async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(bearer_scheme),
) -> AuthUser:
    """
    Decodes the JWT and returns the user object for staff.
    """
    token = credentials.credentials
    payload = decode_access_token(token)
    
    if not payload:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired authentication credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    user_id = payload.get("sub")
    role = payload.get("role")
    username = payload.get("username")
    full_name = payload.get("full_name")
    department_id = payload.get("department_id")
    
    if not user_id or not role:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token payload.",
        )
        
    return AuthUser(id=user_id, role=role, username=username, full_name=full_name, department_id=department_id)



async def require_super_admin(user: AuthUser = Depends(get_current_user)) -> AuthUser:
    if user.role != "super_admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, detail="Super Admin access required."
        )
    return user

async def require_admin(user: AuthUser = Depends(get_current_user)) -> AuthUser:
    if user.role not in ("super_admin", "dept_admin"):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, detail="Admin access required."
        )
    return user

async def require_adviser(user: AuthUser = Depends(get_current_user)) -> AuthUser:
    if user.role not in ("super_admin", "dept_admin", "adviser"):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, detail="Adviser access required."
        )
    return user

async def require_dept_access(current_user: AuthUser = Depends(get_current_user)) -> AuthUser:
    """
    Enforces that the user is either a Super Admin or a Dept Admin.
    Passes the validated user object down to the route handler.
    """
    if current_user.role not in ["super_admin", "dept_admin"]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You do not have department-level administrative privileges."
        )
    return current_user

async def get_current_student(
    credentials: HTTPAuthorizationCredentials = Depends(bearer_scheme),
) -> StudentUser:
    """
    Decodes the JWT and returns the user object for students.
    """
    token = credentials.credentials
    payload = decode_access_token(token)
    
    if not payload or payload.get("role") != "student":
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid student session.",
        )
        
    return StudentUser(
        id=payload.get("sub"),
        student_id=payload.get("student_id"),
        username=payload.get("username"),
        full_name=payload.get("full_name"),
        department_id=payload.get("department_id")
    )



async def require_student(
    student: StudentUser = Depends(get_current_student),
) -> StudentUser:
    return student
