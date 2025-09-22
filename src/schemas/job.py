"""
Pydantic schemas for Job model.
"""

from __future__ import annotations

from datetime import datetime, date
from typing import Optional
from uuid import UUID
from pydantic import BaseModel


class JobBase(BaseModel):
    """Base job schema with common fields."""

    title: str
    company: str
    industry: Optional[str] = None
    start_date: Optional[date] = None
    end_date: Optional[date] = None


class JobCreate(JobBase):
    """Schema for creating a new job."""

    profile_id: UUID


class JobUpdate(JobBase):
    """Schema for updating a job."""

    title: Optional[str] = None
    company: Optional[str] = None
    industry: Optional[str] = None
    start_date: Optional[date] = None
    end_date: Optional[date] = None


class JobResponse(JobBase):
    """Schema for job response."""

    id: UUID
    profile_id: UUID
    is_active: bool
    created_at: datetime
    updated_at: datetime
    deactivated_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class JobListResponse(BaseModel):
    """Schema for job list response with pagination."""

    jobs: list[JobResponse]
    total: int
    page: int
    size: int
    pages: int
