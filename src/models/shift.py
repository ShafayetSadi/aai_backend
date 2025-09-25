from __future__ import annotations

from typing import List, TYPE_CHECKING
from datetime import time
from uuid import UUID

from sqlmodel import Field, Relationship, UniqueConstraint, Index
from sqlalchemy.orm import relationship
from sqlalchemy import CheckConstraint
from src.models.base import BaseModel

if TYPE_CHECKING:
    from .organization import Organization
    from .availability import Availability, TimeOffRequest
    from .requirements import RequirementDayItem
    from .schedule import RoleSlot


class Shift(BaseModel, table=True):
    __tablename__ = "shifts"

    organization_id: UUID = Field(foreign_key="organizations.id", index=True)

    name: str = Field(index=True)
    start_time: time = Field(index=True)
    end_time: time = Field(index=True)

    # Relationships
    organization: "Organization" = Relationship(
        sa_relationship=relationship(
            "Organization",
            back_populates="shifts",
            foreign_keys="Shift.organization_id",
        )
    )
    availability: List["Availability"] = Relationship(
        sa_relationship=relationship("Availability", back_populates="shift")
    )
    requirement_day_items: List["RequirementDayItem"] = Relationship(
        sa_relationship=relationship("RequirementDayItem", back_populates="shift")
    )
    role_slots: List["RoleSlot"] = Relationship(
        sa_relationship=relationship("RoleSlot", back_populates="shift")
    )
    time_off_requests: List["TimeOffRequest"] = Relationship(
        sa_relationship=relationship("TimeOffRequest", back_populates="shift")
    )

    __table_args__ = (
        UniqueConstraint("organization_id", "name", name="unique_shift_name_per_org"),
        CheckConstraint("start_time < end_time", name="check_shift_time_order"),
        Index("idx_shift_org", "organization_id"),
        Index("idx_shift_name", "name"),
        Index(
            "idx_shift_org_start_end_time", "organization_id", "start_time", "end_time"
        ),
    )
