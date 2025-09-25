from __future__ import annotations

from datetime import datetime
from typing import List, Optional, TYPE_CHECKING
from sqlmodel import Field, Relationship
from sqlalchemy import Column, String, CheckConstraint
from sqlalchemy.orm import relationship
from pydantic import EmailStr
from pydantic import field_validator

from src.models.base import BaseModel

if TYPE_CHECKING:
    from .profile import Profile
    from .membership import OrganizationMembership
    from .organization import Organization
    from .availability import Availability
    from .assignment import Assignment
    from .availability import TimeOffRequest


class User(BaseModel, table=True):
    __tablename__ = "users"

    username: str = Field(
        sa_column=Column(String(50), unique=True, index=True, nullable=False),
        min_length=3,
        max_length=50,
        regex=r"^[a-zA-Z0-9_-]+$",
    )
    email: EmailStr = Field(
        sa_column=Column(String(320), unique=True, index=True, nullable=False)
    )
    password_hash: str = Field(
        sa_column=Column(String(255), nullable=False),
        min_length=60,  # bcrypt hash length
    )
    is_super_admin: bool = Field(default=False, nullable=False)
    is_active: bool = Field(default=True, nullable=False, index=True)
    last_login_at: Optional[datetime] = Field(default=None, nullable=True)
    deactivated_at: Optional[datetime] = Field(default=None, nullable=True)

    __table_args__ = (
        CheckConstraint("length(username) >= 3", name="ck_username_min_length"),
        CheckConstraint("username ~ '^[a-zA-Z0-9_-]+$'", name="ck_username_format"),
        CheckConstraint(
            r"email ~* '^[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}$'",
            name="ck_email_format",
        ),
        CheckConstraint("length(password_hash) >= 60", name="ck_password_hash_length"),
    )

    @field_validator("username")
    def validate_username(cls, v: str) -> str:
        if not v or len(v.strip()) < 3:
            raise ValueError("Username must be at least 3 characters long")
        if not v.replace("_", "").replace("-", "").isalnum():
            raise ValueError(
                "Username can only contain letters, numbers, underscores, and hyphens"
            )
        return v.strip().lower()

    @field_validator("email")
    def validate_email(cls, v: EmailStr) -> EmailStr:
        if not v or "@" not in v:
            raise ValueError("Invalid email format")
        return v.strip().lower()

    # Relationships
    profile: Optional["Profile"] = Relationship(
        sa_relationship=relationship(
            "Profile",
            back_populates="user",
            uselist=False,
            cascade="all, delete-orphan",
            foreign_keys="Profile.user_id",
        )
    )

    organization_memberships: List["OrganizationMembership"] = Relationship(
        sa_relationship=relationship(
            "OrganizationMembership",
            back_populates="user",
            cascade="all, delete-orphan",
            foreign_keys="OrganizationMembership.user_id",
        )
    )
    owned_organizations: List["Organization"] = Relationship(
        sa_relationship=relationship(
            "Organization",
            back_populates="owner",
            foreign_keys="Organization.owner_user_id",
        )
    )

    # Availability relationships
    availability: List["Availability"] = Relationship(
        sa_relationship=relationship(
            "Availability",
            back_populates="user",
            cascade="all, delete-orphan",
            foreign_keys="Availability.user_id",
        )
    )
    # Time off requests submitted by this user
    time_off_requests: List["TimeOffRequest"] = Relationship(
        sa_relationship=relationship(
            "TimeOffRequest",
            back_populates="user",
            cascade="all, delete-orphan",
            foreign_keys="TimeOffRequest.user_id",
        )
    )
    # Time off requests this user has approved
    approved_time_off_requests: List["TimeOffRequest"] = Relationship(
        sa_relationship=relationship(
            "TimeOffRequest",
            back_populates="approver",
            foreign_keys="TimeOffRequest.approver_id",
        )
    )

    # Assignment relationships
    assignments: List["Assignment"] = Relationship(
        sa_relationship=relationship(
            "Assignment", back_populates="user", foreign_keys="Assignment.user_id"
        )
    )
    assigned_assignments: List["Assignment"] = Relationship(
        sa_relationship=relationship(
            "Assignment",
            back_populates="assigned_by_user",
            foreign_keys="Assignment.assigned_by",
        )
    )
    approved_assignments: List["Assignment"] = Relationship(
        sa_relationship=relationship(
            "Assignment",
            back_populates="approved_by_user",
            foreign_keys="Assignment.approved_by",
        )
    )
