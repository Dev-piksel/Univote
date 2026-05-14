from pydantic import BaseModel
from typing import Optional, List


class AuthUser(BaseModel):
    id: str
    role: str  # 'super_admin', 'dept_admin', 'adviser', or 'student'
    username: Optional[str] = None
    full_name: Optional[str] = None
    department_id: Optional[str] = None




class StudentUser(BaseModel):
    id: str  # The UUID from database
    student_id: str  # The human-readable ID (e.g. 2024-0001)
    role: str = "student"  # Always 'student'; used for compatibility with get_election_secure
    username: Optional[str] = None
    full_name: Optional[str] = None
    department_id: Optional[str] = None




class LoginRequest(BaseModel):
    username: str  # ID Number for staff, student_id for students
    password: str


class StaffLoginRequest(BaseModel):
    username: str  # ID Number
    password: str


class StudentImport(BaseModel):
    student_id: str
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    middle_initial: Optional[str] = None
    full_name: Optional[str] = None


class StudentManualCreate(BaseModel):
    student_id: str
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    middle_initial: Optional[str] = None
    full_name: Optional[str] = None
    email: Optional[str] = None
    department_id: Optional[str] = None
    program: Optional[str] = None
    year_level: Optional[int] = None


class ElectionCreate(BaseModel):
    name: str
    description: Optional[str] = None
    department_id: Optional[str] = None
    start_date: str  # ISO format
    end_date: str  # ISO format


class ElectionStatusUpdate(BaseModel):
    status: str  # 'upcoming', 'active', or 'completed'


class ElectionUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    start_date: Optional[str] = None
    end_date: Optional[str] = None


class PartylistCreate(BaseModel):
    name: str
    logo_url: Optional[str] = None
    election_id: Optional[str] = None


class CandidateCreate(BaseModel):
    student_id: str
    position: str
    partylist_id: Optional[str] = None
    photo_url: Optional[str] = None


class VoteItem(BaseModel):
    candidate_id: str
    position: str


class VoteSubmit(BaseModel):
    student_id: str
    election_id: str
    passcode_id: str       # Original record ID used at entry
    adviser_id: str        # The adviser UID derived during entrance
    votes: List[VoteItem]
    session_passcode: str   # The 8-char alphanumeric passcode from advisor


class PasscodeVerify(BaseModel):
    election_id: str
    passcode: str


class StudentAuth(BaseModel):
    student_id: str


class StudentUpdate(BaseModel):
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    middle_initial: Optional[str] = None
    full_name: Optional[str] = None
    email: Optional[str] = None
    department_id: Optional[str] = None
    program: Optional[str] = None
    year_level: Optional[int] = None
    photo_url: Optional[str] = None


class AdviserCreate(BaseModel):
    id_number: str
    email: str
    password: str
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    middle_initial: Optional[str] = None
    full_name: Optional[str] = None
    department_id: Optional[str] = None
    photo_url: Optional[str] = None


class AdviserUpdate(BaseModel):
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    middle_initial: Optional[str] = None
    full_name: Optional[str] = None
    email: Optional[str] = None
    department_id: Optional[str] = None
    photo_url: Optional[str] = None


class RegisterRequest(BaseModel):
    username: str               # ID Number
    password: str
    first_name: str
    last_name: str
    middle_initial: Optional[str] = None
    role: str                   # 'dept_admin' or 'adviser'
    department_id: Optional[str] = None


class AppSettingsUpdate(BaseModel):
    app_name: Optional[str] = None
    primary_color: Optional[str] = None
    accent_color: Optional[str] = None
    logo_url: Optional[str] = None
    show_bg_anims: Optional[bool] = None
    theme: Optional[str] = 'light'


class AdviserImportRow(BaseModel):
    first_name: str
    last_name: str
    middle_initial: Optional[str] = None
    email: str
    department: Optional[str] = None


class AdviserChangePassword(BaseModel):
    current_password: str
    new_password: str


class AdviserSetEntryPin(BaseModel):
    election_id: str
    pin: str  # exactly 6 digits


class DepartmentCreate(BaseModel):
    name: str
    code: Optional[str] = None  # Short code — requires `code` column in departments table
    description: Optional[str] = None


class DeptAdminCreate(BaseModel):
    id_number: str          # Login ID / Employee ID
    first_name: str
    last_name: str
    middle_initial: Optional[str] = None
    email: str
    password: str
    department_id: Optional[str] = None
    photo_url: Optional[str] = None


class DeptAdminUpdate(BaseModel):
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    middle_initial: Optional[str] = None
    email: Optional[str] = None
    department_id: Optional[str] = None
    photo_url: Optional[str] = None


class SuperAdminSetup(BaseModel):
    id_number: str
    first_name: str
    last_name: str
    middle_initial: Optional[str] = None
    password: str
