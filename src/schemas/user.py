"""
Pydantic schemas for User model.
"""

from __future__ import annotations

from datetime import datetime
from typing import Optional
from uuid import UUID
from pydantic import BaseModel, EmailStr


class UserBase(BaseModel):
    """Base user schema with common fields."""

    username: str
    email: EmailStr
    is_super_admin: bool = False


class UserCreate(UserBase):
    """Schema for creating a new user."""

    password: str


class UserUpdate(BaseModel):
    """Schema for updating a user."""

    username: Optional[str] = None
    email: Optional[EmailStr] = None
    password: Optional[str] = None
    is_super_admin: Optional[bool] = None


class UserResponse(UserBase):
    """Schema for user response."""

    id: UUID
    created_at: datetime
    updated_at: datetime
    last_login_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class UserListResponse(BaseModel):
    """Schema for user list response with pagination."""

    users: list[UserResponse]
    total: int
    page: int
    size: int
    pages: int
