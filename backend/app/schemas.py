"""Pydantic request/response schemas."""
from datetime import datetime, date
from typing import Optional, List

from pydantic import BaseModel, EmailStr, Field, ConfigDict


# --------------------------------------------------------------------------- #
#  Projects
# --------------------------------------------------------------------------- #
class ProjectBase(BaseModel):
    name: str
    description: Optional[str] = ""
    manager_name: Optional[str] = ""
    status: Optional[str] = "Active"


class ProjectCreate(ProjectBase):
    pass


class ProjectOut(ProjectBase):
    model_config = ConfigDict(from_attributes=True)
    id: int
    created_at: Optional[datetime] = None


# --------------------------------------------------------------------------- #
#  Employees
# --------------------------------------------------------------------------- #
class EmployeeBase(BaseModel):
    name: str
    email: EmailStr
    department: Optional[str] = ""
    role: Optional[str] = ""
    joining_date: Optional[date] = None
    status: Optional[str] = "Active"
    project_id: Optional[int] = None


class EmployeeCreate(EmployeeBase):
    employee_code: Optional[str] = None  # auto-generated when omitted


class EmployeeUpdate(BaseModel):
    name: Optional[str] = None
    email: Optional[EmailStr] = None
    department: Optional[str] = None
    role: Optional[str] = None
    joining_date: Optional[date] = None
    status: Optional[str] = None
    project_id: Optional[int] = None


class SeatMini(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    floor: int
    zone: str
    bay: int
    seat_number: str
    status: str


class EmployeeOut(EmployeeBase):
    model_config = ConfigDict(from_attributes=True)
    id: int
    employee_code: str
    created_at: Optional[datetime] = None
    project_name: Optional[str] = None
    allocation_status: str = "Pending"       # Allocated / Pending
    seat: Optional[SeatMini] = None


class EmployeeList(BaseModel):
    total: int
    items: List[EmployeeOut]


# --------------------------------------------------------------------------- #
#  Seats
# --------------------------------------------------------------------------- #
class SeatBase(BaseModel):
    floor: int
    zone: str
    bay: int
    seat_number: str
    status: Optional[str] = "Available"


class SeatCreate(SeatBase):
    pass


class SeatOut(SeatBase):
    model_config = ConfigDict(from_attributes=True)
    id: int
    created_at: Optional[datetime] = None
    employee_name: Optional[str] = None
    employee_id: Optional[int] = None
    project_name: Optional[str] = None


class SeatList(BaseModel):
    total: int
    items: List[SeatOut]


class AllocateRequest(BaseModel):
    employee_id: int
    seat_id: Optional[int] = None          # if omitted, system auto-suggests
    preferred_floor: Optional[int] = None
    preferred_zone: Optional[str] = None


class ReleaseRequest(BaseModel):
    seat_id: Optional[int] = None
    employee_id: Optional[int] = None


# --------------------------------------------------------------------------- #
#  AI Assistant
# --------------------------------------------------------------------------- #
class AIQuery(BaseModel):
    query: str = Field(..., examples=["Where is my seat? My email is amit@ethara.ai"])


class AIResponse(BaseModel):
    answer: str
    intent: Optional[str] = None
    data: Optional[dict] = None
