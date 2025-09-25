"""
Pydantic schemas for Schedule models.
"""

from __future__ import annotations

from datetime import datetime, time, date
from typing import Optional, List
from uuid import UUID
from pydantic import BaseModel
from src.models.base import ScheduleStatus
from src.models.schedule import RoleSlot
from src.models.shift import Shift


class ScheduleBase(BaseModel):
    """Base schedule schema with common fields."""

    name: Optional[str] = None
    week_start: date
    notes: Optional[str] = None


class ScheduleCreate(ScheduleBase):
    """Schema for creating a new schedule."""

    pass


class ScheduleUpdate(BaseModel):
    """Schema for updating a schedule."""

    name: Optional[str] = None
    notes: Optional[str] = None


class ScheduleResponse(ScheduleBase):
    """Schema for schedule response."""

    id: UUID
    organization_id: UUID
    status: ScheduleStatus
    created_at: datetime
    updated_at: datetime
    created_by: Optional[UUID] = None
    updated_by: Optional[UUID] = None

    class Config:
        from_attributes = True


class ScheduleDayBase(BaseModel):
    """Base schedule day schema."""

    schedule_date: date


class ScheduleDayCreate(ScheduleDayBase):
    """Schema for creating a new schedule day."""

    organization_id: UUID
    schedule_id: UUID


class ScheduleDayResponse(ScheduleDayBase):
    """Schema for schedule day response."""

    id: UUID
    organization_id: UUID
    schedule_id: UUID
    created_at: datetime
    updated_at: datetime
    created_by: Optional[UUID] = None
    updated_by: Optional[UUID] = None

    class Config:
        from_attributes = True


class RoleSlotBase(BaseModel):
    """Base role slot schema."""

    role_id: UUID
    shift_id: UUID
    required_count: int = 0
    notes: Optional[str] = None


class RoleSlotCreate(RoleSlotBase):
    """Schema for creating a role slot."""

    organization_id: UUID
    schedule_day_id: UUID


class RoleSlotResponse(RoleSlotBase):
    """Schema for role slot response."""

    id: UUID
    organization_id: UUID
    schedule_day_id: UUID
    created_at: datetime
    updated_at: datetime
    created_by: Optional[UUID] = None
    updated_by: Optional[UUID] = None

    class Config:
        from_attributes = True


class RoleSlotWithShift(RoleSlotResponse):
    """Role slot response with shift information."""

    shift_name: str
    start_time: time
    end_time: time


class ScheduleWithDays(ScheduleResponse):
    """Schema for schedule with days."""

    days: List[ScheduleDayResponse] = []


class ScheduleDayWithShifts(ScheduleDayResponse):
    """Schema for schedule day with shift instances."""

    shifts: List[Shift] = []


class ShiftWithRoleSlots(BaseModel):
    """Schema for shift with role slots."""

    id: UUID
    organization_id: UUID
    shift_id: UUID
    start_time: Optional[time] = None
    end_time: Optional[time] = None
    notes: Optional[str] = None
    is_cancelled: bool = False
    cancellation_reason: Optional[str] = None
    role_slots: List[RoleSlot] = []


class ScheduleByRoleView(BaseModel):
    """Schema for schedule by role view."""

    role_name: str
    day: str
    date: date
    shift: str
    assigned: int
    shortfall: int


class ScheduleByStaffView(BaseModel):
    """Schema for schedule by staff view."""

    staff_name: str
    role_name: str
    day: str
    date: date
    shift: str


class AutoAssignResult(BaseModel):
    """Schema for auto-assignment result."""

    schedule_id: UUID
    total_slots: int
    filled_slots: int
    fill_rate: float
    assignments_made: int
    shortfalls: List[dict]
    fairness_index: float


class ScheduleListResponse(BaseModel):
    """Schema for schedule list response with pagination."""

    schedules: list[ScheduleResponse]
    total: int
    page: int
    size: int
    pages: int
