"""
Assignment CRUD operations router for workforce scheduling.
"""

from __future__ import annotations

from uuid import UUID
from datetime import date

from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, and_

from src.core.db import get_session
from src.core.security import get_current_user
from src.models.user import User
from src.models.assignment import Assignment
from src.models.schedule import RoleSlot, ScheduleDay
from src.schemas.assignment import (
    AssignmentCreate,
    AssignmentUpdate,
    AssignmentResponse,
    AssignmentListResponse,
    AssignmentBulkUpdate,
    AssignmentValidationRequest,
    AssignmentValidationResponse,
)

router = APIRouter(
    prefix="/organizations/{org_id}/assignments",
    tags=["assignments"],
)


@router.get("/", response_model=AssignmentListResponse)
async def get_assignments(
    org_id: UUID,
    page: int = Query(1, ge=1, description="Page number"),
    size: int = Query(10, ge=1, le=100, description="Page size"),
    user_id: UUID = Query(None, description="Filter by user"),
    status: str = Query(None, description="Filter by assignment status"),
    priority: str = Query(None, description="Filter by assignment priority"),
    session: AsyncSession = Depends(get_session),
    current_user: User = Depends(get_current_user),
) -> AssignmentListResponse:
    """Get assignments for an organization with pagination and filtering."""

    # Build query via role slots and schedule days
    query = (
        select(Assignment)
        .join(RoleSlot, Assignment.role_slot_id == RoleSlot.id)
        .join(ScheduleDay, RoleSlot.schedule_day_id == ScheduleDay.id)
        .where(ScheduleDay.organization_id == org_id)
    )
    count_query = (
        select(func.count(Assignment.id))
        .join(RoleSlot, Assignment.role_slot_id == RoleSlot.id)
        .join(ScheduleDay, RoleSlot.schedule_day_id == ScheduleDay.id)
        .where(ScheduleDay.organization_id == org_id)
    )

    # Apply filters
    filters = []
    if user_id:
        filters.append(Assignment.user_id == user_id)
    if status:
        filters.append(Assignment.status == status)
    if priority:
        filters.append(Assignment.priority == priority)

    if filters:
        query = query.where(and_(*filters))
        count_query = count_query.where(and_(*filters))

    # Get total count
    total_result = await session.execute(count_query)
    total = total_result.scalar()

    # Apply pagination
    offset = (page - 1) * size
    query = query.offset(offset).limit(size).order_by(Assignment.assigned_at.desc())

    # Execute query
    result = await session.execute(query)
    assignments = result.scalars().all()

    # Calculate pages
    pages = (total + size - 1) // size

    return AssignmentListResponse(
        assignments=[
            AssignmentResponse.model_validate(assignment) for assignment in assignments
        ],
        total=total,
        page=page,
        size=size,
        pages=pages,
    )


@router.get("/{assignment_id}", response_model=AssignmentResponse)
async def get_assignment(
    org_id: UUID,
    assignment_id: UUID,
    session: AsyncSession = Depends(get_session),
    current_user: User = Depends(get_current_user),
) -> AssignmentResponse:
    """Get a specific assignment."""

    result = await session.execute(
        select(Assignment)
        .join(RoleSlot, Assignment.role_slot_id == RoleSlot.id)
        .join(ScheduleDay, RoleSlot.schedule_day_id == ScheduleDay.id)
        .where(
            Assignment.id == assignment_id,
            ScheduleDay.organization_id == org_id,
        )
    )
    assignment = result.scalar_one_or_none()

    if not assignment:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Assignment not found"
        )

    return AssignmentResponse.model_validate(assignment)


@router.post(
    "/", response_model=AssignmentResponse, status_code=status.HTTP_201_CREATED
)
async def create_assignment(
    org_id: UUID,
    assignment_data: AssignmentCreate,
    session: AsyncSession = Depends(get_session),
    current_user: User = Depends(get_current_user),
) -> AssignmentResponse:
    """Create a new assignment."""

    # Check if assignment already exists for this role slot and user
    existing = await session.execute(
        select(Assignment).where(
            Assignment.role_slot_id == assignment_data.role_slot_id,
            Assignment.user_id == assignment_data.user_id,
        )
    )
    if existing.scalar_one_or_none():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Assignment already exists for this role slot and user",
        )

    # Create new assignment
    assignment = Assignment(
        role_slot_id=assignment_data.role_slot_id,
        user_id=assignment_data.user_id,
        status=assignment_data.status,
        priority=assignment_data.priority,
        notes=assignment_data.notes,
        assigned_by=assignment_data.assigned_by,
        approved_by=assignment_data.approved_by,
    )

    session.add(assignment)
    await session.commit()
    await session.refresh(assignment)

    return AssignmentResponse.model_validate(assignment)


@router.patch("/{assignment_id}", response_model=AssignmentResponse)
async def update_assignment(
    org_id: UUID,
    assignment_id: UUID,
    assignment_data: AssignmentUpdate,
    session: AsyncSession = Depends(get_session),
    current_user: User = Depends(get_current_user),
) -> AssignmentResponse:
    """Update an assignment."""

    # Get existing assignment
    result = await session.execute(
        select(Assignment)
        .join(RoleSlot, Assignment.role_slot_id == RoleSlot.id)
        .join(ScheduleDay, RoleSlot.schedule_day_id == ScheduleDay.id)
        .where(
            Assignment.id == assignment_id,
            ScheduleDay.organization_id == org_id,
        )
    )
    assignment = result.scalar_one_or_none()

    if not assignment:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Assignment not found"
        )

    # Update assignment fields
    update_data = assignment_data.model_dump(exclude_unset=True)

    for field, value in update_data.items():
        setattr(assignment, field, value)

    await session.commit()
    await session.refresh(assignment)

    return AssignmentResponse.model_validate(assignment)


@router.patch("/bulk", response_model=list[AssignmentResponse])
async def bulk_update_assignments(
    org_id: UUID,
    bulk_data: AssignmentBulkUpdate,
    session: AsyncSession = Depends(get_session),
    current_user: User = Depends(get_current_user),
) -> list[AssignmentResponse]:
    """Bulk update assignments."""

    # Get assignments
    result = await session.execute(
        select(Assignment)
        .join(RoleSlot, Assignment.role_slot_id == RoleSlot.id)
        .join(ScheduleDay, RoleSlot.schedule_day_id == ScheduleDay.id)
        .where(
            Assignment.id.in_(bulk_data.assignment_ids),
            ScheduleDay.organization_id == org_id,
        )
    )
    assignments = result.scalars().all()

    if len(assignments) != len(bulk_data.assignment_ids):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Some assignments not found",
        )

    # Update assignments
    update_data = bulk_data.model_dump(exclude_unset=True, exclude={"assignment_ids"})
    for assignment in assignments:
        for field, value in update_data.items():
            if value is not None:
                setattr(assignment, field, value)

    await session.commit()

    return [AssignmentResponse.model_validate(assignment) for assignment in assignments]


@router.post("/validate", response_model=AssignmentValidationResponse)
async def validate_assignment(
    org_id: UUID,
    validation_data: AssignmentValidationRequest,
    session: AsyncSession = Depends(get_session),
    current_user: User = Depends(get_current_user),
) -> AssignmentValidationResponse:
    """Validate assignment constraints."""

    # Count current assignments for the user in the specified week
    week_start = validation_data.week_start
    week_end = week_start + date.resolution * 6  # Add 6 days to get week end

    result = await session.execute(
        select(func.count(Assignment.id))
        .join(RoleSlot, Assignment.role_slot_id == RoleSlot.id)
        .join(ScheduleDay, RoleSlot.schedule_day_id == ScheduleDay.id)
        .where(
            ScheduleDay.organization_id == org_id,
            Assignment.user_id == validation_data.user_id,
            ScheduleDay.schedule_date >= week_start,
            ScheduleDay.schedule_date <= week_end,
        )
    )
    current_count = result.scalar() or 0

    max_shifts = 2  # Business rule: max 2 shifts per week
    can_assign = current_count < max_shifts

    return AssignmentValidationResponse(
        is_valid=can_assign,
        max_shifts_per_week=max_shifts,
        current_assignments_count=current_count,
        can_assign=can_assign,
        message=f"User has {current_count}/{max_shifts} assignments this week"
        if not can_assign
        else None,
    )


@router.delete("/{assignment_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_assignment(
    org_id: UUID,
    assignment_id: UUID,
    session: AsyncSession = Depends(get_session),
    current_user: User = Depends(get_current_user),
):
    """Delete an assignment."""

    # Get existing assignment
    result = await session.execute(
        select(Assignment)
        .join(RoleSlot, Assignment.role_slot_id == RoleSlot.id)
        .join(ScheduleDay, RoleSlot.schedule_day_id == ScheduleDay.id)
        .where(
            Assignment.id == assignment_id,
            ScheduleDay.organization_id == org_id,
        )
    )
    assignment = result.scalar_one_or_none()

    if not assignment:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Assignment not found"
        )

    await session.delete(assignment)
    await session.commit()
