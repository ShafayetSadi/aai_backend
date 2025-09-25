"""
Schedule model for workforce scheduling.
"""

from __future__ import annotations

from datetime import date
from typing import Optional, TYPE_CHECKING
from uuid import UUID

from sqlmodel import Field, UniqueConstraint, Relationship
from sqlalchemy.orm import relationship
from sqlalchemy import Index
from src.models.base import BaseModel, ScheduleStatus
from pydantic import field_validator

from src.models.shift import Shift

if TYPE_CHECKING:
    from .role import Role
    from .assignment import Assignment
    from .organization import Organization


class Schedule(BaseModel, table=True):
    """Schedule for a specific week."""

    __tablename__ = "schedules"

    organization_id: UUID = Field(foreign_key="organizations.id", index=True)

    name: Optional[str] = Field(default=None)
    week_start: date = Field(index=True)
    status: ScheduleStatus = Field(default=ScheduleStatus.Draft, index=True)
    notes: Optional[str] = None

    # Relationships
    organization: "Organization" = Relationship(
        sa_relationship=relationship("Organization", back_populates="schedules")
    )

    days: list["ScheduleDay"] = Relationship(
        sa_relationship=relationship(
            "ScheduleDay", back_populates="schedule", cascade="all, delete-orphan"
        )
    )

    __table_args__ = (
        UniqueConstraint(
            "organization_id",
            "week_start",
            name="unique_schedule_per_org_week",
        ),
        Index("idx_schedule_org_status", "organization_id", "status"),
        Index("idx_schedule_week_start", "week_start"),
        Index(
            "idx_schedule_org_week_status", "organization_id", "week_start", "status"
        ),
    )


class ScheduleDay(BaseModel, table=True):
    __tablename__ = "schedule_days"

    organization_id: UUID = Field(foreign_key="organizations.id", index=True)
    schedule_id: UUID = Field(foreign_key="schedules.id", index=True)

    schedule_date: date = Field(index=True)

    __table_args__ = (
        UniqueConstraint("schedule_id", "schedule_date", name="uq_day_schedule_date"),
        Index("idx_schedule_day_date", "schedule_date"),
        Index("idx_schedule_day_org_date", "organization_id", "schedule_date"),
        Index("idx_schedule_day_schedule", "schedule_id"),
    )

    # Relationships
    schedule: "Schedule" = Relationship(
        sa_relationship=relationship("Schedule", back_populates="days")
    )
    role_slots: list["RoleSlot"] = Relationship(
        sa_relationship=relationship(
            "RoleSlot", back_populates="schedule_day", cascade="all, delete-orphan"
        )
    )


class RoleSlot(BaseModel, table=True):
    __tablename__ = "role_slots"

    organization_id: UUID = Field(foreign_key="organizations.id", index=True)
    role_id: UUID = Field(foreign_key="roles.id", index=True)
    schedule_day_id: UUID = Field(foreign_key="schedule_days.id", index=True)
    shift_id: UUID = Field(foreign_key="shifts.id", index=True)

    required_count: int = Field(ge=0, default=0)
    notes: Optional[str] = None

    @field_validator("required_count")
    @classmethod
    def validate_required_count(cls, v: int) -> int:
        if v < 0:
            raise ValueError("Required count cannot be negative")
        if v > 100:  # Reasonable upper limit for role slots
            raise ValueError("Required count cannot exceed 100")
        return v

    role: "Role" = Relationship(
        sa_relationship=relationship("Role", back_populates="role_slots")
    )
    schedule_day: "ScheduleDay" = Relationship(
        sa_relationship=relationship("ScheduleDay", back_populates="role_slots")
    )
    assignments: list["Assignment"] = Relationship(
        sa_relationship=relationship(
            "Assignment", back_populates="role_slot", cascade="all, delete-orphan"
        )
    )
    shift: "Shift" = Relationship(
        sa_relationship=relationship("Shift", back_populates="role_slots")
    )

    __table_args__ = (
        UniqueConstraint("role_id", "schedule_day_id", name="uq_roleslot_role_day"),
        Index("idx_roleslot_org_role", "organization_id", "role_id"),
        Index("idx_roleslot_schedule_day", "schedule_day_id"),
        Index("idx_roleslot_required_count", "required_count"),
    )
