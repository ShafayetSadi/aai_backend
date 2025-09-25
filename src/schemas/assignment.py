"""
Pydantic schemas for Assignment model.
"""

from __future__ import annotations

from datetime import datetime, date
from typing import Optional
from uuid import UUID
from pydantic import BaseModel, field_validator

from src.models.base import AssignmentStatus, AssignmentPriority


class AssignmentBase(BaseModel):
    """Base assignment schema with common fields."""

    status: AssignmentStatus = AssignmentStatus.Pending
    priority: AssignmentPriority = AssignmentPriority.Medium
    notes: Optional[str] = None
    cancellation_reason: Optional[str] = None
    assigned_by: Optional[UUID] = None
    approved_by: Optional[UUID] = None


class AssignmentCreate(AssignmentBase):
    """Schema for creating a new assignment."""

    role_slot_id: UUID
    user_id: UUID


class AssignmentUpdate(BaseModel):
    """Schema for updating an assignment."""

    status: Optional[AssignmentStatus] = None
    priority: Optional[AssignmentPriority] = None
    notes: Optional[str] = None
    cancellation_reason: Optional[str] = None
    confirmed_at: Optional[datetime] = None
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    assigned_by: Optional[UUID] = None
    approved_by: Optional[UUID] = None

    @field_validator("status")
    @classmethod
    def validate_status_transitions(
        cls, v: Optional[AssignmentStatus], info
    ) -> Optional[AssignmentStatus]:
        """Validate assignment status transitions."""
        if v is not None and "status" in info.data:
            current_status = info.data.get("status")
            valid_transitions = {
                AssignmentStatus.Pending: [
                    AssignmentStatus.Confirmed,
                    AssignmentStatus.Cancelled,
                ],
                AssignmentStatus.Confirmed: [
                    AssignmentStatus.InProgress,
                    AssignmentStatus.Cancelled,
                ],
                AssignmentStatus.InProgress: [
                    AssignmentStatus.Completed,
                    AssignmentStatus.Cancelled,
                    AssignmentStatus.NoShow,
                ],
                AssignmentStatus.Completed: [],  # Terminal state
                AssignmentStatus.Cancelled: [],  # Terminal state
                AssignmentStatus.NoShow: [],  # Terminal state
            }

            if (
                current_status in valid_transitions
                and v not in valid_transitions[current_status]
            ):
                raise ValueError(
                    f"Invalid status transition from {current_status} to {v}"
                )
        return v

    @field_validator("completed_at")
    @classmethod
    def validate_completion_timing(
        cls, v: Optional[datetime], info
    ) -> Optional[datetime]:
        """Validate that completion time is after start time."""
        if v is not None and "started_at" in info.data:
            started_at = info.data.get("started_at")
            if started_at is not None and v < started_at:
                raise ValueError("Completion time cannot be before start time")
        return v


class AssignmentResponse(AssignmentBase):
    """Schema for assignment response."""

    id: UUID
    organization_id: UUID
    role_slot_id: UUID
    user_id: UUID
    assigned_at: datetime
    confirmed_at: Optional[datetime] = None
    created_at: datetime
    updated_at: datetime
    created_by: Optional[UUID] = None
    updated_by: Optional[UUID] = None

    class Config:
        from_attributes = True


class AssignmentListResponse(BaseModel):
    """Schema for assignment list response with pagination."""

    assignments: list[AssignmentResponse]
    total: int
    page: int
    size: int
    pages: int


class AssignmentBulkUpdate(BaseModel):
    """Schema for bulk updating assignments."""

    assignment_ids: list[UUID]
    status: Optional[AssignmentStatus] = None
    priority: Optional[AssignmentPriority] = None
    notes: Optional[str] = None


class AssignmentValidationRequest(BaseModel):
    """Schema for validating assignment constraints."""

    user_id: UUID
    week_start: date
    organization_id: UUID


class AssignmentValidationResponse(BaseModel):
    """Schema for assignment validation response."""

    is_valid: bool
    max_shifts_per_week: int = 2
    current_assignments_count: int
    can_assign: bool
    message: Optional[str] = None
