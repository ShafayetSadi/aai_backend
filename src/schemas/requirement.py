"""
Pydantic schemas for Requirement models.
"""

from __future__ import annotations

from datetime import date, datetime
from typing import List, Optional
from uuid import UUID
from pydantic import BaseModel, Field

from src.models.base import Weekday


class RequirementDayBase(BaseModel):
    """Base schema for requirement days."""

    requirement_date: date
    notes: Optional[str] = None


class RequirementDayCreate(RequirementDayBase):
    """Schema for creating a requirement day."""
    pass


class RequirementDayUpdate(BaseModel):
    """Schema for updating a requirement day."""

    notes: Optional[str] = None


class RequirementDayResponse(RequirementDayBase):
    """Schema for requirement day response."""

    id: UUID
    organization_id: UUID
    requirement_day: Weekday
    created_at: datetime
    updated_at: datetime
    created_by: Optional[UUID] = None
    updated_by: Optional[UUID] = None

    class Config:
        from_attributes = True


# RequirementDayItem schemas
class RequirementDayItemBase(BaseModel):
    """Base schema for requirement day items."""

    role_id: UUID
    shift_id: UUID
    weekday: Weekday
    required_count: int = Field(default=1, ge=0)
    notes: Optional[str] = None


class RequirementDayItemCreate(RequirementDayItemBase):
    """Schema for creating requirement day items."""

    organization_id: UUID
    requirement_day_id: UUID
    requirement_date: date


class RequirementDayItemCreateSingle(RequirementDayItemBase):
    """Schema for creating a single requirement day item via nested items endpoint.

    organization_id and requirement_day_id are derived from path params; not supplied in body.
    """

    requirement_date: date


class RequirementDayItemUpdate(BaseModel):
    """Schema for updating requirement day items."""

    role_id: Optional[UUID] = None
    shift_id: Optional[UUID] = None
    weekday: Optional[Weekday] = None
    required_count: Optional[int] = Field(default=None, ge=0)
    notes: Optional[str] = None


class RequirementDayItemResponse(RequirementDayItemBase):
    """Schema for requirement day item response."""

    id: UUID
    organization_id: UUID
    requirement_day_id: UUID
    created_at: datetime
    updated_at: datetime
    created_by: Optional[UUID] = None
    updated_by: Optional[UUID] = None

    class Config:
        from_attributes = True


class RequirementDayWithItems(RequirementDayResponse):
    """Requirement day with items."""

    items: List[RequirementDayItemResponse] = Field(default_factory=list)


class RequirementDayListResponse(BaseModel):
    """Schema for paginated requirement days including their items."""

    requirement_days: List[RequirementDayWithItems]
    total: int
    page: int
    size: int
    pages: int
