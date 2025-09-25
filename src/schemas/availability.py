"""
Pydantic schemas for Availability models.
"""

from __future__ import annotations

from datetime import datetime, date
from typing import Optional
from uuid import UUID
from pydantic import BaseModel, model_validator
from src.models.base import AvailabilityStatus, AvailabilityType, Weekday


class AvailabilityBase(BaseModel):
    """Base availability schema with explicit availability_type required.

    Client must provide availability_type and the correct supporting field:
    - Recurring: availability_day required, availability_date must be null
    - Exception: availability_date required, availability_day must be null
    """

    # For legacy rows shift_id may still be null; create schema will enforce requirement.
    shift_id: Optional[UUID] = None
    availability_day: Optional[Weekday] = None
    availability_date: Optional[date] = None
    availability_type: AvailabilityType
    status: AvailabilityStatus = AvailabilityStatus.Unavailable
    notes: Optional[str] = None

    @model_validator(mode="after")
    def validate_explicit(cls, values: "AvailabilityBase") -> "AvailabilityBase":  # type: ignore[override]
        a_type = values.availability_type
        day = values.availability_day
        date_val = values.availability_date
        if a_type == AvailabilityType.Recurring:
            if day is None:
                raise ValueError("availability_day is required for Recurring availability_type")
            if date_val is not None:
                raise ValueError("availability_date must be omitted for Recurring availability_type")
        elif a_type == AvailabilityType.Exception:
            if date_val is None:
                raise ValueError("availability_date is required for Exception availability_type")
            if day is not None:
                raise ValueError("availability_day must be omitted for Exception availability_type")
        else:
            raise ValueError(f"Unsupported availability_type '{a_type}'")
        return values


class AvailabilityCreate(AvailabilityBase):
    """Schema for creating a new availability (explicit mode). shift_id required."""

    shift_id: UUID  # override as required

    @classmethod
    def create_recurring(
        cls,
        shift_id: UUID,
        availability_day: Weekday,
        status: AvailabilityStatus,
        notes: Optional[str] = None,
    ) -> "AvailabilityCreate":
        return cls(
            shift_id=shift_id,
            availability_day=availability_day,
            availability_type=AvailabilityType.Recurring,
            status=status,
            notes=notes,
        )

    @classmethod
    def create_exception(
        cls,
        shift_id: UUID,
        availability_date: date,
        status: AvailabilityStatus,
        notes: Optional[str] = None,
    ) -> "AvailabilityCreate":
        return cls(
            shift_id=shift_id,
            availability_date=availability_date,
            availability_type=AvailabilityType.Exception,
            status=status,
            notes=notes,
        )


class AvailabilityUpdate(BaseModel):
    """Schema for updating an availability."""

    shift_id: Optional[UUID] = None
    availability_day: Optional[Weekday] = None
    availability_date: Optional[date] = None
    availability_type: Optional[AvailabilityType] = None
    status: Optional[AvailabilityStatus] = None
    notes: Optional[str] = None


class AvailabilityResponse(AvailabilityBase):
    """Schema for availability response (tolerates legacy null shift_id)."""

    id: UUID
    organization_id: UUID
    user_id: UUID
    created_at: datetime
    updated_at: datetime
    created_by: Optional[UUID] = None
    updated_by: Optional[UUID] = None

    class Config:
        from_attributes = True


class AvailabilityListResponse(BaseModel):
    """Schema for availability list response with pagination."""

    availabilities: list[AvailabilityResponse]
    total: int
    page: int
    size: int
    pages: int


# Legacy schemas for backward compatibility
class AvailabilityRecurringBase(BaseModel):
    """Legacy recurring availability schema."""

    weekday: Weekday
    shift_id: Optional[UUID] = None
    status: AvailabilityStatus


class AvailabilityRecurringCreate(AvailabilityRecurringBase):
    """Legacy schema for creating recurring availability."""


class AvailabilityRecurringUpdate(BaseModel):
    """Legacy schema for updating recurring availability."""

    weekday: Optional[Weekday] = None
    shift_id: Optional[UUID] = None
    status: Optional[AvailabilityStatus] = None


class AvailabilityRecurringResponse(AvailabilityRecurringBase):
    """Legacy schema for recurring availability response."""

    id: UUID
    organization_id: UUID
    user_id: UUID
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class AvailabilityExceptionBase(BaseModel):
    """Legacy exception availability schema."""

    availability_date: date
    shift_id: Optional[UUID] = None
    status: AvailabilityStatus
    notes: Optional[str] = None


class AvailabilityExceptionCreate(AvailabilityExceptionBase):
    """Legacy schema for creating exception availability."""


class AvailabilityExceptionUpdate(BaseModel):
    """Legacy schema for updating exception availability."""

    availability_date: Optional[date] = None
    shift_id: Optional[UUID] = None
    status: Optional[AvailabilityStatus] = None
    notes: Optional[str] = None


class AvailabilityExceptionResponse(AvailabilityExceptionBase):
    """Legacy schema for exception availability response."""

    id: UUID
    organization_id: UUID
    user_id: UUID
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True
