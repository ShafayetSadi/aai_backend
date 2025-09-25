from __future__ import annotations

from typing import Optional, TYPE_CHECKING
from uuid import UUID

from sqlmodel import Field, Relationship, UniqueConstraint, Index
from sqlalchemy.orm import relationship
from pydantic import field_validator

from src.models.base import BaseModel, Weekday

if TYPE_CHECKING:
    from .organization import Organization


class BusinessOpenDays(BaseModel, table=True):
    """
    Business open days configuration for organizations.
    Defines which days of the week the organization is open for business.
    """

    __tablename__ = "business_open_days"

    organization_id: UUID = Field(foreign_key="organizations.id", index=True)

    monday: bool = Field(default=True, index=True)
    tuesday: bool = Field(default=True, index=True)
    wednesday: bool = Field(default=True, index=True)
    thursday: bool = Field(default=True, index=True)
    friday: bool = Field(default=True, index=True)
    saturday: bool = Field(default=False, index=True)
    sunday: bool = Field(default=False, index=True)

    notes: Optional[str] = Field(default=None)
    is_active: bool = Field(default=True, index=True)

    @field_validator("notes")
    @classmethod
    def validate_notes(cls, v: Optional[str]) -> Optional[str]:
        if v is not None and len(v.strip()) > 500:
            raise ValueError("Notes cannot exceed 500 characters")
        return v.strip() if v else None

    @field_validator(
        "monday", "tuesday", "wednesday", "thursday", "friday", "saturday", "sunday"
    )
    @classmethod
    def validate_weekday_flags(cls, v: bool) -> bool:
        return v

    organization: "Organization" = Relationship(
        sa_relationship=relationship(
            "Organization", back_populates="business_open_days"
        )
    )

    def is_open_on_day(self, weekday: Weekday) -> bool:
        """Check if the organization is open on a specific weekday."""
        day_mapping = {
            Weekday.MONDAY: self.monday,
            Weekday.TUESDAY: self.tuesday,
            Weekday.WEDNESDAY: self.wednesday,
            Weekday.THURSDAY: self.thursday,
            Weekday.FRIDAY: self.friday,
            Weekday.SATURDAY: self.saturday,
            Weekday.SUNDAY: self.sunday,
        }
        return day_mapping.get(weekday, False)

    def get_open_days(self) -> list[Weekday]:
        """Get a list of all open weekdays."""
        open_days = []
        if self.monday:
            open_days.append(Weekday.MONDAY)
        if self.tuesday:
            open_days.append(Weekday.TUESDAY)
        if self.wednesday:
            open_days.append(Weekday.WEDNESDAY)
        if self.thursday:
            open_days.append(Weekday.THURSDAY)
        if self.friday:
            open_days.append(Weekday.FRIDAY)
        if self.saturday:
            open_days.append(Weekday.SATURDAY)
        if self.sunday:
            open_days.append(Weekday.SUNDAY)
        return open_days

    def get_closed_days(self) -> list[Weekday]:
        """Get a list of all closed weekdays."""
        closed_days = []
        if not self.monday:
            closed_days.append(Weekday.MONDAY)
        if not self.tuesday:
            closed_days.append(Weekday.TUESDAY)
        if not self.wednesday:
            closed_days.append(Weekday.WEDNESDAY)
        if not self.thursday:
            closed_days.append(Weekday.THURSDAY)
        if not self.friday:
            closed_days.append(Weekday.FRIDAY)
        if not self.saturday:
            closed_days.append(Weekday.SATURDAY)
        if not self.sunday:
            closed_days.append(Weekday.SUNDAY)
        return closed_days

    __table_args__ = (
        UniqueConstraint("organization_id", name="uq_business_open_days_org"),
        Index("idx_business_open_days_org_active", "organization_id", "is_active"),
    )
