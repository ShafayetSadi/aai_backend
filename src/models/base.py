from __future__ import annotations

from datetime import datetime
from typing import Optional
from uuid import UUID, uuid4
from enum import Enum

from sqlmodel import SQLModel, Field
from sqlalchemy import text, func


class MembershipRole(str, Enum):
    owner = "owner"
    manager = "manager"
    staff = "staff"


class Weekday(str, Enum):
    """Weekday for availability."""

    MONDAY = "monday"
    TUESDAY = "tuesday"
    WEDNESDAY = "wednesday"
    THURSDAY = "thursday"
    FRIDAY = "friday"
    SATURDAY = "saturday"
    SUNDAY = "sunday"


class AvailabilityStatus(str, Enum):
    """Availability status for user profile."""

    Available = "Available"
    Off = "Off"
    Unavailable = "Unavailable"


class RequestStatus(str, Enum):
    """Request status for time-off requests."""

    Pending = "Pending"
    Approved = "Approved"
    Rejected = "Rejected"


class Gender(str, Enum):
    """Gender for user profile."""

    Male = "Male"
    Female = "Female"
    Other = "Other"
    PreferNotToSay = "PreferNotToSay"


class AvailabilityType(str, Enum):
    """Availability type for recurring/exception patterns."""

    Recurring = "Recurring"
    Exception = "Exception"


class RoleStatus(str, Enum):
    """Role status for active/inactive management."""

    Active = "Active"
    Inactive = "Inactive"
    Archived = "Archived"


class RolePriority(str, Enum):
    """Role priority for scheduling conflicts."""

    Low = "Low"
    Medium = "Medium"
    High = "High"
    Critical = "Critical"


class ScheduleStatus(str, Enum):
    """Schedule status for draft/published/archived."""

    Draft = "Draft"
    Published = "Published"
    Archived = "Archived"


class AssignmentStatus(str, Enum):
    """Assignment status for lifecycle management."""

    Pending = "Pending"
    Confirmed = "Confirmed"
    InProgress = "InProgress"
    Completed = "Completed"
    Cancelled = "Cancelled"
    NoShow = "NoShow"


class AssignmentPriority(str, Enum):
    """Assignment priority for scheduling conflicts."""

    Low = "Low"
    Medium = "Medium"
    High = "High"
    Critical = "Critical"


class MembershipRequestType(str, Enum):
    """Type of membership request (invite vs user-initiated request)."""

    Invite = "Invite"
    Request = "Request"


class MembershipRequestStatus(str, Enum):
    """Status of membership request lifecycle."""

    Pending = "Pending"
    Accepted = "Accepted"
    Rejected = "Rejected"
    Cancelled = "Cancelled"


class RequirementTemplateType(str, Enum):
    """Requirement template type for scheduling purposes."""

    BusyDay = "BusyDay"
    NormalDay = "NormalDay"
    LazyDay = "LazyDay"
    Custom = "Custom"


class RequirementTemplateCategory(str, Enum):
    """Requirement template category for organization."""

    Normal = "Normal"
    Holiday = "Holiday"
    Special = "Special"
    Event = "Event"


class BaseModel(SQLModel):
    """
    Abstract base class with common fields for all models.
    """

    id: UUID = Field(
        default_factory=uuid4, primary_key=True, index=True, nullable=False
    )
    created_at: datetime = Field(
        default_factory=datetime.utcnow,
        nullable=False,
        sa_column_kwargs={
            "server_default": text("now()"),
        },
    )
    updated_at: datetime = Field(
        default_factory=datetime.utcnow,
        nullable=False,
        sa_column_kwargs={
            "server_default": text("now()"),
            "onupdate": func.now(),
        },
    )
    created_by: Optional[UUID] = Field(
        default=None, foreign_key="users.id", nullable=True, index=True
    )
    updated_by: Optional[UUID] = Field(
        default=None, foreign_key="users.id", nullable=True, index=True
    )

    class Config:
        arbitrary_types_allowed = True
        validate_assignment = True
