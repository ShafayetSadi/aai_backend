from __future__ import annotations

from typing import Optional, List, TYPE_CHECKING
from uuid import UUID

from sqlmodel import Field, UniqueConstraint, Relationship
from sqlalchemy import Index
from sqlalchemy.orm import relationship
from pydantic import field_validator

from src.models.base import BaseModel, RoleStatus, RolePriority

if TYPE_CHECKING:
    from .organization import Organization
    from .schedule import RoleSlot
    from .requirements import RequirementDayItem


class Role(BaseModel, table=True):
    """
    Role within an organization for scheduling purposes.
    Represents job positions that can be assigned to users.
    """

    __tablename__ = "roles"

    organization_id: UUID = Field(foreign_key="organizations.id", index=True)

    name: str = Field(index=True)
    slug: Optional[str] = Field(default=None, index=True)
    description: Optional[str] = Field(default=None)

    status: RoleStatus = Field(default=RoleStatus.Active, index=True)
    priority: RolePriority = Field(default=RolePriority.Medium, index=True)

    hourly_rate: Optional[float] = Field(default=None, ge=0)
    salary_range_min: Optional[float] = Field(default=None, ge=0)
    salary_range_max: Optional[float] = Field(default=None, ge=0)

    @field_validator("name")
    @classmethod
    def validate_name(cls, v: str) -> str:
        if not v or len(v.strip()) < 1:
            raise ValueError("Role name cannot be empty")
        if len(v.strip()) > 100:
            raise ValueError("Role name cannot exceed 100 characters")
        return v.strip()

    @field_validator("slug")
    @classmethod
    def validate_slug(cls, v: Optional[str]) -> Optional[str]:
        if v is not None:
            if len(v.strip()) < 1:
                raise ValueError("Role slug cannot be empty")
            if len(v.strip()) > 50:
                raise ValueError("Role slug cannot exceed 50 characters")
            if not v.replace("-", "").replace("_", "").isalnum():
                raise ValueError(
                    "Role slug can only contain letters, numbers, hyphens, and underscores"
                )
            return v.strip().lower()
        return v

    @field_validator("description")
    @classmethod
    def validate_description(cls, v: Optional[str]) -> Optional[str]:
        if v is not None and len(v.strip()) > 1000:
            raise ValueError("Description cannot exceed 1000 characters")
        return v.strip() if v else None

    @field_validator("salary_range_max")
    @classmethod
    def validate_salary_range(cls, v: Optional[float], info) -> Optional[float]:
        if v is not None and "salary_range_min" in info.data:
            min_salary = info.data.get("salary_range_min")
            if min_salary is not None and v < min_salary:
                raise ValueError("Maximum salary must be greater than minimum salary")
        return v

    # Relationships
    organization: "Organization" = Relationship(
        sa_relationship=relationship("Organization", back_populates="roles")
    )

    requirement_day_items: List["RequirementDayItem"] = Relationship(
        sa_relationship=relationship("RequirementDayItem", back_populates="role")
    )

    role_slots: List["RoleSlot"] = Relationship(
        sa_relationship=relationship("RoleSlot", back_populates="role")
    )

    __table_args__ = (
        UniqueConstraint("organization_id", "name", name="unique_role_name"),
        Index("idx_role_org_name", "organization_id", "name"),
        Index("idx_role_org_slug", "organization_id", "slug"),
        Index("idx_role_status", "status"),
        Index("idx_role_priority", "priority"),
    )
