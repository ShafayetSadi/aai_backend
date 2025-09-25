"""
Pydantic schemas for Role model.
"""

from __future__ import annotations

from datetime import datetime
from typing import Optional
from uuid import UUID
from pydantic import BaseModel


class RoleBase(BaseModel):
    """Base role schema with common fields."""

    name: str
    description: Optional[str] = None


class RoleCreate(RoleBase):
    """Schema for creating a new role."""


class RoleUpdate(BaseModel):
    """Schema for updating a role."""

    name: Optional[str] = None
    description: Optional[str] = None


class RoleResponse(RoleBase):
    """Schema for role response."""

    slug: Optional[str] = None
    id: UUID
    organization_id: UUID
    is_active: bool
    created_at: datetime
    updated_at: datetime
    deactivated_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class RoleListResponse(BaseModel):
    """Schema for role list response with pagination."""

    roles: list[RoleResponse]
    total: int
    page: int
    size: int
    pages: int
