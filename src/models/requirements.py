from __future__ import annotations

from datetime import date
from typing import Optional, TYPE_CHECKING
from typing_extensions import List
from uuid import UUID

from sqlmodel import Field, Relationship, UniqueConstraint
from sqlalchemy.orm import relationship
from sqlalchemy import Index

from src.models.base import BaseModel, Weekday

if TYPE_CHECKING:
    from .organization import Organization
    from .role import Role
    from .shift import Shift


class RequirementDay(BaseModel, table=True):
    """
    Requirement day model for daily requirement management.
    This is the main daily requirement container.
    """

    __tablename__ = "requirement_days"

    organization_id: UUID = Field(foreign_key="organizations.id", index=True)

    requirement_date: date = Field(index=True)
    requirement_day: Weekday = Field(index=True)
    notes: Optional[str] = None

    requirement_day_items: List["RequirementDayItem"] = Relationship(
        sa_relationship=relationship(
            "RequirementDayItem",
            back_populates="requirement_day",
            cascade="all, delete-orphan",
        )
    )

    # Relationships
    organization: "Organization" = Relationship(
        sa_relationship=relationship("Organization", back_populates="requirement_days")
    )

    __table_args__ = (
        UniqueConstraint(
            "organization_id", "requirement_date", name="uq_req_day_org_date"
        ),
        Index("idx_req_day_org", "organization_id"),
        Index("idx_req_day_date", "requirement_date"),
    )


class RequirementDayItem(BaseModel, table=True):
    __tablename__ = "requirement_day_items"

    requirement_day_id: UUID = Field(foreign_key="requirement_days.id", index=True)
    organization_id: UUID = Field(foreign_key="organizations.id", index=True)

    role_id: UUID = Field(foreign_key="roles.id", index=True)
    shift_id: UUID = Field(foreign_key="shifts.id", index=True)
    weekday: Weekday = Field(index=True)
    required_count: int = Field(index=True)
    notes: Optional[str] = None

    # Relationships
    requirement_day: "RequirementDay" = Relationship(
        sa_relationship=relationship(
            "RequirementDay", back_populates="requirement_day_items"
        )
    )
    organization: "Organization" = Relationship(
        sa_relationship=relationship(
            "Organization", back_populates="requirement_day_items"
        )
    )
    role: "Role" = Relationship(
        sa_relationship=relationship("Role", back_populates="requirement_day_items")
    )
    shift: "Shift" = Relationship(
        sa_relationship=relationship("Shift", back_populates="requirement_day_items")
    )

    __table_args__ = (
        UniqueConstraint(
            "requirement_day_id", "role_id", "shift_id", name="uq_req_day_item_unique"
        ),
        Index("idx_req_day_item_org", "organization_id"),
        Index("idx_req_day_item_role", "role_id"),
        Index("idx_req_day_item_shift", "shift_id"),
    )
