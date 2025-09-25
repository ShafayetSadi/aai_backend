"""
Pydantic schemas for BusinessOpenDays model.
"""

from __future__ import annotations

from datetime import datetime
from typing import Optional
from uuid import UUID
from pydantic import BaseModel

from src.models.base import Weekday


class BusinessOpenDaysBase(BaseModel):
    """Base business open days schema with common fields."""

    monday: bool = True
    tuesday: bool = True
    wednesday: bool = True
    thursday: bool = True
    friday: bool = True
    saturday: bool = False
    sunday: bool = False
    notes: Optional[str] = None
    is_active: bool = True


class BusinessOpenDaysCreate(BusinessOpenDaysBase):
    """Schema for creating business open days."""

    organization_id: UUID


class BusinessOpenDaysUpdate(BaseModel):
    """Schema for updating business open days."""

    monday: Optional[bool] = None
    tuesday: Optional[bool] = None
    wednesday: Optional[bool] = None
    thursday: Optional[bool] = None
    friday: Optional[bool] = None
    saturday: Optional[bool] = None
    sunday: Optional[bool] = None
    notes: Optional[str] = None
    is_active: Optional[bool] = None


class BusinessOpenDaysResponse(BusinessOpenDaysBase):
    """Schema for business open days response."""

    id: UUID
    organization_id: UUID
    created_at: datetime
    updated_at: datetime
    created_by: Optional[UUID] = None
    updated_by: Optional[UUID] = None

    class Config:
        from_attributes = True

    def is_open_on_day(self, weekday: Weekday) -> bool:
        """Check if the organization is open on a specific weekday."""
        day_mapping = {
            Weekday.MONDAY: self.monday,
            Weekday.TUESDAY: self.tuesday,
            Weekday.WEDNESDAY: self.wednesday,
            Weekday.THURSDAY: self.thursday,
            Weekday.FRIDAY: self.friday,
            Weekday.SATURDAY: self.saturday,
            Weekday.SUNDAY: self.sunday,
        }
        return day_mapping.get(weekday, False)

    def get_open_days(self) -> list[Weekday]:
        """Get a list of all open weekdays."""
        open_days = []
        if self.monday:
            open_days.append(Weekday.MONDAY)
        if self.tuesday:
            open_days.append(Weekday.TUESDAY)
        if self.wednesday:
            open_days.append(Weekday.WEDNESDAY)
        if self.thursday:
            open_days.append(Weekday.THURSDAY)
        if self.friday:
            open_days.append(Weekday.FRIDAY)
        if self.saturday:
            open_days.append(Weekday.SATURDAY)
        if self.sunday:
            open_days.append(Weekday.SUNDAY)
        return open_days

    def get_closed_days(self) -> list[Weekday]:
        """Get a list of all closed weekdays."""
        closed_days = []
        if not self.monday:
            closed_days.append(Weekday.MONDAY)
        if not self.tuesday:
            closed_days.append(Weekday.TUESDAY)
        if not self.wednesday:
            closed_days.append(Weekday.WEDNESDAY)
        if not self.thursday:
            closed_days.append(Weekday.THURSDAY)
        if not self.friday:
            closed_days.append(Weekday.FRIDAY)
        if not self.saturday:
            closed_days.append(Weekday.SATURDAY)
        if not self.sunday:
            closed_days.append(Weekday.SUNDAY)
        return closed_days
