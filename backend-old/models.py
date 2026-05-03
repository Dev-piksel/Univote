from pydantic import BaseModel
from typing import Optional, List
from uuid import UUID


class LoginRequest(BaseModel):
    username: str  # This is email for staff, or student_id for students (if unified)
    password: str


class StaffLoginRequest(BaseModel):
    username: str  # ID Number
    password: str


class StudentImport(BaseModel):
    student_id: str
    full_name: str


class StudentManualCreate(BaseModel):
    student_id: str
    full_name: str
    program: Optional[str] = None
    year_level: Optional[int] = None


class ElectionCreate(BaseModel):
    name: str
    description: Optional[str] = None
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


class CandidateCreate(BaseModel):
    student_id: str
    position: str
    partylist_id: Optional[UUID] = None


class VoteItem(BaseModel):
    candidate_id: UUID
    position: str


class VoteSubmit(BaseModel):
    student_id: str
    election_id: UUID
    passcode_id: UUID  # Original record ID used at entry
    adviser_id: UUID  # The adviser UID derived during entrance
    votes: List[VoteItem]
    session_passcode: str  # The 8-char alphanumeric passcode from advisor


class PasscodeVerify(BaseModel):
    election_id: UUID
    passcode: str


class StudentAuth(BaseModel):
    student_id: str


class StudentUpdate(BaseModel):
    full_name: Optional[str] = None
    program: Optional[str] = None
    year_level: Optional[int] = None


class AdviserCreate(BaseModel):
    id_number: str
    email: str
    password: str
    full_name: str
    department: Optional[str] = None


class RegisterRequest(BaseModel):
    username: str  # ID Number
    password: str
    full_name: str
    role: str  # 'admin' or 'adviser'
    department: Optional[str] = None


class AppSettingsUpdate(BaseModel):
    app_name: Optional[str] = None
    primary_color: Optional[str] = None
    accent_color: Optional[str] = None
    logo_url: Optional[str] = None


class AdviserImportRow(BaseModel):
    full_name: str
    email: str
    department: Optional[str] = None


class AdviserChangePassword(BaseModel):
    current_password: str
    new_password: str


class AdviserSetEntryPin(BaseModel):
    election_id: str
    pin: str  # exactly 6 digits

