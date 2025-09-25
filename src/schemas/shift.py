"""
Pydantic schemas for Shift model.
"""

from __future__ import annotations

from datetime import datetime, time
from typing import Optional
from uuid import UUID
from pydantic import BaseModel


class ShiftBase(BaseModel):
    """Base shift schema with common fields."""

    name: str
    start_time: time
    end_time: time


class ShiftCreate(ShiftBase):
    """Schema for creating a new shift."""
    pass


class ShiftUpdate(BaseModel):
    """Schema for updating a shift."""

    name: Optional[str] = None
    start_time: Optional[time] = None
    end_time: Optional[time] = None


class ShiftResponse(ShiftBase):
    """Schema for shift response."""

    id: UUID
    organization_id: UUID
    created_at: datetime
    updated_at: datetime
    created_by: Optional[UUID] = None
    updated_by: Optional[UUID] = None

    class Config:
        from_attributes = True


class ShiftListResponse(BaseModel):
    """Schema for shift list response with pagination."""

    shifts: list[ShiftResponse]
    total: int
    page: int
    size: int
    pages: int
