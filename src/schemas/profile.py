"""
Pydantic schemas for Profile model.
"""

from __future__ import annotations

from datetime import datetime, date
from typing import Optional, List
from uuid import UUID
from pydantic import BaseModel
from src.models.profile import Gender


class ProfileBase(BaseModel):
    """Base profile schema with common fields."""

    first_name: Optional[str] = None
    last_name: Optional[str] = None
    date_of_birth: Optional[date] = None
    gender: Optional[Gender] = None
    location_id: Optional[UUID] = None
    bio: Optional[str] = None
    profile_picture_url: Optional[str] = None
    is_public: bool = True
    allow_contact: bool = True


class ProfileCreate(ProfileBase):
    """Schema for creating a new profile."""

    user_id: UUID


class ProfileUpdate(ProfileBase):
    """Schema for updating a profile."""

    first_name: Optional[str] = None
    last_name: Optional[str] = None
    date_of_birth: Optional[date] = None
    gender: Optional[Gender] = None
    location_id: Optional[UUID] = None
    bio: Optional[str] = None
    profile_picture_url: Optional[str] = None
    is_public: Optional[bool] = None
    allow_contact: Optional[bool] = None


class LocationSummary(BaseModel):
    """Summary of location information."""

    id: UUID
    country: str
    state_province: Optional[str] = None
    city: Optional[str] = None
    postal_code: Optional[str] = None

    class Config:
        from_attributes = True


class ContactSummary(BaseModel):
    """Summary of contact information."""

    id: UUID
    type: str
    value: str
    is_primary: bool

    class Config:
        from_attributes = True


class JobSummary(BaseModel):
    """Summary of job information."""

    id: UUID
    title: str
    company: str
    industry: Optional[str] = None
    start_date: Optional[date] = None
    end_date: Optional[date] = None

    class Config:
        from_attributes = True


class ProfileResponse(ProfileBase):
    """Schema for profile response."""

    id: UUID
    user_id: UUID
    is_active: bool
    created_at: datetime
    updated_at: datetime
    deactivated_at: Optional[datetime] = None

    # Related data
    location: Optional[LocationSummary] = None
    contacts: List[ContactSummary] = []
    jobs: List[JobSummary] = []

    class Config:
        from_attributes = True


class ProfileListResponse(BaseModel):
    """Schema for profile list response with pagination."""

    profiles: list[ProfileResponse]
    total: int
    page: int
    size: int
    pages: int
