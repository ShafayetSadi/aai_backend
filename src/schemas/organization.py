"""
Pydantic schemas for Organization model.
"""

from __future__ import annotations

from datetime import datetime
from typing import Optional
from uuid import UUID
from pydantic import BaseModel, Field, validator
from src.models.base import MembershipRole


class OrganizationBase(BaseModel):
    """Base organization schema with common fields."""

    name: str = Field(
        ..., min_length=1, max_length=255, description="Organization name"
    )
    category: Optional[str] = Field(
        None, max_length=255, description="Organization category"
    )
    subcategory: Optional[str] = Field(
        None, max_length=255, description="Organization subcategory"
    )


class OrganizationCreate(OrganizationBase):
    """Schema for creating a new organization."""

    slug: Optional[str] = Field(
        None,
        max_length=100,
        description="Organization slug (auto-generated if not provided)",
    )

    @validator("slug", pre=True, always=True)
    def generate_slug(cls, v, values):
        """Generate slug from name if not provided."""
        if v is None and "name" in values:
            from src.models.organization import Organization

            return Organization.generate_slug(values["name"])
        return v


class OrganizationUpdate(BaseModel):
    """Schema for updating an organization."""

    name: Optional[str] = Field(None, min_length=1, max_length=255)
    category: Optional[str] = Field(None, max_length=255)
    subcategory: Optional[str] = Field(None, max_length=255)
    slug: Optional[str] = Field(None, max_length=100)

    @validator("slug", pre=True, always=True)
    def generate_slug_from_name(cls, v, values):
        """Generate slug from name if name is provided but slug is not."""
        if v is None and "name" in values and values["name"] is not None:
            from src.models.organization import Organization

            return Organization.generate_slug(values["name"])
        return v


class OrganizationResponse(OrganizationBase):
    """Schema for organization response."""

    id: UUID
    slug: str
    owner_user_id: UUID
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class OrganizationWithRole(OrganizationResponse):
    """Organization with user's role in it."""

    role: str  # MembershipRole
    is_owner: bool


class OrganizationListResponse(BaseModel):
    """Response for listing organizations with pagination."""

    organizations: list[OrganizationWithRole]
    total: int
    page: int
    size: int
    pages: int


class InviteRequest(BaseModel):
    user_id: UUID
    role: MembershipRole
    primary_role_id: UUID
    other_role_ids: list[UUID] | None = None
