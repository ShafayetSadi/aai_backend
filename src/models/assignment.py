from __future__ import annotations

from typing import Optional, TYPE_CHECKING
from datetime import datetime
from uuid import UUID

from sqlmodel import Field, Relationship, UniqueConstraint, Index
from sqlalchemy.orm import relationship

from src.models.base import BaseModel, AssignmentStatus, AssignmentPriority

if TYPE_CHECKING:
    from .schedule import RoleSlot
    from .user import User
    from .organization import Organization


class Assignment(BaseModel, table=True):
    """
    Assignment of a user to a specific role slot for a scheduled shift.
    """

    __tablename__ = "assignments"

    organization_id: UUID = Field(foreign_key="organizations.id", index=True)
    role_slot_id: UUID = Field(foreign_key="role_slots.id", index=True)
    user_id: UUID = Field(foreign_key="users.id", index=True)

    # Assignment tracking fields
    assigned_by: Optional[UUID] = Field(
        default=None, foreign_key="users.id", index=True
    )
    approved_by: Optional[UUID] = Field(
        default=None, foreign_key="users.id", index=True
    )

    status: AssignmentStatus = Field(default=AssignmentStatus.Pending, index=True)
    priority: AssignmentPriority = Field(default=AssignmentPriority.Medium, index=True)

    assigned_at: datetime = Field(default_factory=datetime.utcnow, index=True)
    confirmed_at: Optional[datetime] = Field(default=None, index=True)

    notes: Optional[str] = Field(default=None)

    organization: "Organization" = Relationship(
        sa_relationship=relationship("Organization", back_populates="assignments")
    )
    role_slot: "RoleSlot" = Relationship(
        sa_relationship=relationship("RoleSlot", back_populates="assignments")
    )
    user: "User" = Relationship(
        sa_relationship=relationship(
            "User", back_populates="assignments", foreign_keys="Assignment.user_id"
        )
    )
    assigned_by_user: Optional["User"] = Relationship(
        sa_relationship=relationship(
            "User",
            back_populates="assigned_assignments",
            foreign_keys="Assignment.assigned_by",
        )
    )
    approved_by_user: Optional["User"] = Relationship(
        sa_relationship=relationship(
            "User",
            back_populates="approved_assignments",
            foreign_keys="Assignment.approved_by",
        )
    )

    __table_args__ = (
        UniqueConstraint("role_slot_id", "user_id", name="uq_assignment_slot_user"),
        Index("idx_assignment_user_status", "user_id", "status"),
        Index("idx_assignment_role_slot", "role_slot_id"),
    )
