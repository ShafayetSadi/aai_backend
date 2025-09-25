"""
Pydantic schemas for TimeOffRequest model.
"""

from __future__ import annotations

from datetime import datetime
from typing import Optional
from uuid import UUID
from pydantic import BaseModel
from src.models.base import RequestStatus


class TimeOffRequestBase(BaseModel):
    """Base time off request schema with common fields."""

    start_dt: datetime
    end_dt: datetime
    reason: Optional[str] = None


class TimeOffRequestCreate(TimeOffRequestBase):
    """Schema for creating a new time off request."""

    organization_id: UUID
    profile_id: UUID


class TimeOffRequestUpdate(BaseModel):
    """Schema for updating a time off request."""

    start_dt: Optional[datetime] = None
    end_dt: Optional[datetime] = None
    reason: Optional[str] = None
    status: Optional[RequestStatus] = None


class TimeOffRequestResponse(TimeOffRequestBase):
    """Schema for time off request response."""

    id: UUID
    organization_id: UUID
    profile_id: UUID
    status: RequestStatus
    approved_by: Optional[UUID] = None
    approved_at: Optional[datetime] = None
    is_active: bool
    created_at: datetime
    updated_at: datetime
    deactivated_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class TimeOffRequestListResponse(BaseModel):
    """Schema for time off request list response with pagination."""

    time_off_requests: list[TimeOffRequestResponse]
    total: int
    page: int
    size: int
    pages: int
