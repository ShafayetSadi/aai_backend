"""
Availability models for workforce scheduling.
"""

from __future__ import annotations

from datetime import date, datetime
from typing import Optional, TYPE_CHECKING
from uuid import UUID

from sqlmodel import Field, UniqueConstraint, Relationship
from sqlalchemy.orm import relationship

from src.models.base import (
    BaseModel,
    AvailabilityStatus,
    AvailabilityType,
    RequestStatus,
    Weekday,
)

if TYPE_CHECKING:
    from .user import User
    from .shift import Shift
    from .organization import Organization


class Availability(BaseModel, table=True):
    """
    Unified availability model supporting both recurring and exception patterns.
    """

    __tablename__ = "availability"

    organization_id: UUID = Field(foreign_key="organizations.id", index=True)
    user_id: UUID = Field(foreign_key="users.id", index=True)
    # Shift now required (non-null). Existing null data must be cleaned before applying a NOT NULL DB migration.
    shift_id: UUID = Field(foreign_key="shifts.id", index=True)

    # For recurring availability (availability_type = Recurring)
    availability_day: Optional[Weekday] = Field(default=None, index=True)

    # For exception availability (availability_type = Exception)
    availability_date: Optional[date] = Field(default=None, index=True)

    availability_type: AvailabilityType = Field(
        default=AvailabilityType.Recurring, index=True
    )
    status: AvailabilityStatus = Field(
        default=AvailabilityStatus.Unavailable, index=True
    )
    notes: Optional[str] = None

    # Relationships
    organization: "Organization" = Relationship(
        sa_relationship=relationship(
            "Organization",
            back_populates="availability",
            foreign_keys="Availability.organization_id",
        )
    )
    user: "User" = Relationship(
        sa_relationship=relationship(
            "User", back_populates="availability", foreign_keys="Availability.user_id"
        )
    )
    shift: "Shift" = Relationship(
        sa_relationship=relationship(
            "Shift", back_populates="availability", foreign_keys="Availability.shift_id"
        )
    )

    __table_args__ = (
        UniqueConstraint(
            "organization_id",
            "user_id",
            "availability_date",
            "availability_day",
            "availability_type",
            "shift_id",
            name="uq_avail_uniqueness",
        ),
    )


class TimeOffRequest(BaseModel, table=True):
    """
    TimeOffRequest model for time off requests.
    """

    __tablename__ = "time_off_requests"

    organization_id: UUID = Field(foreign_key="organizations.id", index=True)
    user_id: UUID = Field(foreign_key="users.id", index=True)
    shift_id: UUID = Field(foreign_key="shifts.id", index=True)

    start_dt: datetime = Field(index=True)
    end_dt: datetime = Field(index=True)
    status: RequestStatus = Field(index=True)
    reason: Optional[str] = None

    approver_id: Optional[UUID] = Field(foreign_key="users.id", index=True)
    approved_at: Optional[datetime] = Field(index=True)
    rejection_reason: Optional[str] = None

    # Relationships
    organization: "Organization" = Relationship(
        sa_relationship=relationship("Organization", back_populates="time_off_requests")
    )
    # User who approved (optional)
    approver: "User" = Relationship(
        sa_relationship=relationship(
            "User",
            back_populates="approved_time_off_requests",
            foreign_keys="TimeOffRequest.approver_id",
        )
    )
    # Requesting user
    user: "User" = Relationship(
        sa_relationship=relationship(
            "User",
            back_populates="time_off_requests",
            foreign_keys="TimeOffRequest.user_id",
        )
    )
    shift: "Shift" = Relationship(
        sa_relationship=relationship("Shift", back_populates="time_off_requests")
    )
