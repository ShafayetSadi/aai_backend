"""
Pydantic schemas for Location model.
"""

from __future__ import annotations

from datetime import datetime
from typing import Optional
from uuid import UUID
from pydantic import BaseModel


class LocationBase(BaseModel):
    """Base location schema with common fields."""

    country: str
    state_province: Optional[str] = None
    city: Optional[str] = None
    postal_code: Optional[str] = None


class LocationCreate(LocationBase):
    """Schema for creating a new location."""

    pass


class LocationUpdate(LocationBase):
    """Schema for updating a location."""

    country: Optional[str] = None
    state_province: Optional[str] = None
    city: Optional[str] = None
    postal_code: Optional[str] = None


class LocationResponse(LocationBase):
    """Schema for location response."""

    id: UUID
    is_active: bool
    created_at: datetime
    updated_at: datetime
    deactivated_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class LocationListResponse(BaseModel):
    """Schema for location list response with pagination."""

    locations: list[LocationResponse]
    total: int
    page: int
    size: int
    pages: int
