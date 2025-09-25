from __future__ import annotations

import re
from typing import Optional, List, TYPE_CHECKING
from uuid import UUID

from pydantic import field_validator
from sqlmodel import Field, Relationship
from sqlalchemy.orm import relationship
from sqlalchemy import Column, String
from src.models.base import BaseModel

if TYPE_CHECKING:
    from .user import User
    from .membership import OrganizationMembership
    from .business_days import BusinessOpenDays
    from .role import Role
    from .shift import Shift
    from .availability import Availability, TimeOffRequest
    from .schedule import Schedule
    from .assignment import Assignment
    from .requirements import (
        RequirementDay,
        RequirementDayItem,
    )


class Organization(BaseModel, table=True):
    __tablename__ = "organizations"

    name: str = Field(sa_column=Column(String(255)))
    slug: str = Field(sa_column=Column(String(255), unique=True, index=True))
    category: Optional[str] = Field(default=None, sa_column=Column(String(255)))
    subcategory: Optional[str] = Field(default=None, sa_column=Column(String(255)))
    owner_user_id: UUID = Field(foreign_key="users.id", index=True)

    owner: "User" = Relationship(
        sa_relationship=relationship(
            "User",
            back_populates="owned_organizations",
            foreign_keys="Organization.owner_user_id",
        )
    )
    memberships: List["OrganizationMembership"] = Relationship(
        sa_relationship=relationship(
            "OrganizationMembership",
            back_populates="organization",
            foreign_keys="OrganizationMembership.organization_id",
        )
    )

    business_open_days: Optional["BusinessOpenDays"] = Relationship(
        sa_relationship=relationship(
            "BusinessOpenDays",
            back_populates="organization",
            foreign_keys="BusinessOpenDays.organization_id",
        )
    )

    # Core business relationships
    roles: List["Role"] = Relationship(
        sa_relationship=relationship(
            "Role", back_populates="organization", foreign_keys="Role.organization_id"
        )
    )
    shifts: List["Shift"] = Relationship(
        sa_relationship=relationship(
            "Shift", back_populates="organization", foreign_keys="Shift.organization_id"
        )
    )
    availability: List["Availability"] = Relationship(
        sa_relationship=relationship(
            "Availability",
            back_populates="organization",
            foreign_keys="Availability.organization_id",
        )
    )

    schedules: List["Schedule"] = Relationship(
        sa_relationship=relationship(
            "Schedule",
            back_populates="organization",
            foreign_keys="Schedule.organization_id",
        )
    )

    requirement_days: List["RequirementDay"] = Relationship(
        sa_relationship=relationship(
            "RequirementDay",
            back_populates="organization",
            foreign_keys="RequirementDay.organization_id",
        )
    )
    requirement_day_items: List["RequirementDayItem"] = Relationship(
        sa_relationship=relationship(
            "RequirementDayItem",
            back_populates="organization",
            foreign_keys="RequirementDayItem.organization_id",
        )
    )

    # Assignment relationships
    assignments: List["Assignment"] = Relationship(
        sa_relationship=relationship(
            "Assignment",
            back_populates="organization",
            foreign_keys="Assignment.organization_id",
        )
    )

    # Time off requests
    time_off_requests: List["TimeOffRequest"] = Relationship(
        sa_relationship=relationship(
            "TimeOffRequest",
            back_populates="organization",
            foreign_keys="TimeOffRequest.organization_id",
        )
    )

    @field_validator("slug")
    @classmethod
    def validate_slug(cls, v: str) -> str:
        if not v or len(v.strip()) < 1:
            raise ValueError("Slug cannot be empty")
        if len(v.strip()) > 255:
            raise ValueError("Slug cannot exceed 255 characters")
        if not v.replace("-", "").replace("_", "").isalnum():
            raise ValueError(
                "Slug can only contain letters, numbers, hyphens, and underscores"
            )
        if v.strip() != cls.generate_slug(v):
            raise ValueError("Slug is not valid")
        return cls.generate_slug(v)

    @field_validator("name")
    @classmethod
    def validate_name(cls, v: str) -> str:
        if not v or len(v.strip()) < 1:
            raise ValueError("Name cannot be empty")
        if len(v.strip()) > 255:
            raise ValueError("Name cannot exceed 255 characters")
        return v.strip()

    @staticmethod
    def generate_slug(name: str) -> str:
        """Generate a URL-friendly slug from organization name."""
        # Convert to lowercase and replace spaces with hyphens
        slug = re.sub(r"[^\w\s-]", "", name.lower())
        slug = re.sub(r"[-\s]+", "-", slug)
        # Remove leading/trailing hyphens
        return slug.strip("-")
