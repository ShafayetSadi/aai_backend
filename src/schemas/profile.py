"""
Pydantic schemas for Profile model.
"""

from __future__ import annotations

from datetime import datetime
from typing import Optional
from uuid import UUID
from pydantic import BaseModel


class ProfileBase(BaseModel):
    """Base profile schema with common fields."""

    first_name: Optional[str] = None
    last_name: Optional[str] = None


class ProfileCreate(ProfileBase):
    """Schema for creating a new profile."""

    user_id: UUID


class ProfileUpdate(ProfileBase):
    """Schema for updating a profile."""

    first_name: Optional[str] = None
    last_name: Optional[str] = None


class ProfileResponse(ProfileBase):
    """Schema for profile response."""

    id: UUID
    user_id: UUID
    created_at: datetime
    updated_at: datetime
    created_by: Optional[UUID] = None
    updated_by: Optional[UUID] = None

    @property
    def full_name(self) -> str:
        """Get the user's full name."""
        if self.first_name and self.last_name:
            return f"{self.first_name} {self.last_name}"
        elif self.first_name:
            return self.first_name
        elif self.last_name:
            return self.last_name
        return "Unknown User"

    class Config:
        from_attributes = True


class ProfileListResponse(BaseModel):
    """Schema for profile list response with pagination."""

    profiles: list[ProfileResponse]
    total: int
    page: int
    size: int
    pages: int
