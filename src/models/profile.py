from __future__ import annotations

from typing import Optional, TYPE_CHECKING
from uuid import UUID

from sqlmodel import Field, Relationship
from sqlalchemy import String, CheckConstraint
from sqlalchemy.orm import relationship
from pydantic import field_validator

from src.models.base import BaseModel

if TYPE_CHECKING:
    from .user import User


class Profile(BaseModel, table=True):
    """
    Simplified user profile for MVP.
    Contains only essential information for scheduling.
    """

    __tablename__ = "profiles"

    user_id: UUID = Field(foreign_key="users.id", unique=True, nullable=False)

    first_name: Optional[str] = Field(
        sa_column=String(100), default=None, max_length=100
    )
    last_name: Optional[str] = Field(
        sa_column=String(100), default=None, max_length=100
    )

    __table_args__ = (
        CheckConstraint("length(first_name) <= 100", name="ck_first_name_length"),
        CheckConstraint("length(last_name) <= 100", name="ck_last_name_length"),
    )

    @field_validator("first_name", "last_name")
    def validate_names(cls, v: str) -> str:
        if v and len(v.strip()) == 0:
            return None
        return v.strip() if v else None

    @property
    def full_name(self) -> str:
        """Get the user's full name."""
        if self.first_name and self.last_name:
            return f"{self.first_name} {self.last_name}"
        elif self.first_name:
            return self.first_name
        elif self.last_name:
            return self.last_name
        return "Unknown User"

    # Relationships
    user: Optional["User"] = Relationship(
        sa_relationship=relationship(
            "User", back_populates="profile", foreign_keys="Profile.user_id"
        )
    )
