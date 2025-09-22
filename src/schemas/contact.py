"""
Pydantic schemas for Contact model.
"""

from __future__ import annotations

from datetime import datetime
from typing import Optional
from uuid import UUID
from pydantic import BaseModel


class ContactBase(BaseModel):
    """Base contact schema with common fields."""

    type: str  # e.g., "phone", "email"
    value: str
    is_primary: bool = False


class ContactCreate(ContactBase):
    """Schema for creating a new contact."""

    profile_id: UUID


class ContactUpdate(ContactBase):
    """Schema for updating a contact."""

    type: Optional[str] = None
    value: Optional[str] = None
    is_primary: Optional[bool] = None


class ContactResponse(ContactBase):
    """Schema for contact response."""

    id: UUID
    profile_id: UUID
    is_active: bool
    created_at: datetime
    updated_at: datetime
    deactivated_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class ContactListResponse(BaseModel):
    """Schema for contact list response with pagination."""

    contacts: list[ContactResponse]
    total: int
    page: int
    size: int
    pages: int
