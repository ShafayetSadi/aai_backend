"""
Schedule CRUD operations router for workforce scheduling.
"""

from __future__ import annotations

from typing import Optional
from uuid import UUID
from datetime import date

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import func, and_, select
from sqlalchemy.orm import selectinload

from src.core.db import get_session
from src.core.security import get_current_user
from src.dependencies.roles import require_role
from src.models.user import User
from src.models.schedule import (
    Schedule,
    ScheduleStatus,
    ScheduleDay,
    RoleSlot,
)
from src.models.assignment import Assignment
from src.models.role import Role
from src.models.membership import MembershipRole
from src.schemas.schedule import (
    ScheduleCreate,
    ScheduleUpdate,
    ScheduleResponse,
    ScheduleWithDays,
    ScheduleByRoleView,
    ScheduleByStaffView,
    AutoAssignResult,
    ScheduleListResponse,
)

router = APIRouter(prefix="/organizations/{org_id}/schedules", tags=["schedules"])


@router.get("/", response_model=ScheduleListResponse)
async def get_schedules(
    org_id: UUID,
    page: int = Query(1, ge=1, description="Page number"),
    size: int = Query(10, ge=1, le=100, description="Page size"),
    location_id: Optional[UUID] = Query(None, description="Filter by location"),
    status: Optional[ScheduleStatus] = Query(None, description="Filter by status"),
    week_start: Optional[date] = Query(None, description="Filter by week start"),
    session: AsyncSession = Depends(get_session),
    current_user: User = Depends(get_current_user),
) -> ScheduleListResponse:
    """Get paginated list of schedules with optional filtering."""

    # Build query
    query = select(Schedule).where(Schedule.organization_id == org_id)
    count_query = select(func.count(Schedule.id)).where(
        Schedule.organization_id == org_id
    )

    # Apply filters
    filters = []
    if location_id:
        filters.append(Schedule.location_id == location_id)

    if status:
        filters.append(Schedule.status == status)

    if week_start:
        filters.append(Schedule.week_start == week_start)

    if filters:
        query = query.where(and_(*filters))
        count_query = count_query.where(and_(*filters))

    # Get total count
    total_result = await session.execute(count_query)
    total = total_result.scalar()

    # Apply pagination
    offset = (page - 1) * size
    query = query.offset(offset).limit(size).order_by(Schedule.created_at.desc())

    # Execute query
    result = await session.execute(query)
    schedules = result.scalars().all()

    # Calculate pages
    pages = (total + size - 1) // size

    return ScheduleListResponse(
        schedules=[ScheduleResponse.model_validate(schedule) for schedule in schedules],
        total=total,
        page=page,
        size=size,
        pages=pages,
    )


@router.get("/{schedule_id}", response_model=ScheduleWithDays)
async def get_schedule(
    org_id: UUID,
    schedule_id: UUID,
    session: AsyncSession = Depends(get_session),
    current_user: User = Depends(get_current_user),
) -> ScheduleWithDays:
    """Get a specific schedule with its days."""

    # Get schedule
    schedule_result = await session.execute(
        select(Schedule)
        .where(Schedule.id == schedule_id, Schedule.organization_id == org_id)
        .options(selectinload(Schedule.days))
    )
    schedule = schedule_result.scalar_one_or_none()

    if not schedule:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Schedule not found"
        )

    schedule_data = ScheduleResponse.model_validate(schedule)
    # days relationship is loaded via selectinload; return as-is
    return ScheduleWithDays(
        **schedule_data.model_dump(),
        days=[
            # convert ORM to response via model_validate of ScheduleDayResponse is implicit in pydantic v2 with from_attributes
            d  # FastAPI will use Config.from_attributes
            for d in schedule.days
        ],
    )


@router.post("/", response_model=ScheduleResponse, status_code=status.HTTP_201_CREATED)
async def create_schedule(
    org_id: UUID,
    schedule_data: ScheduleCreate,
    session: AsyncSession = Depends(get_session),
    current_user: User = Depends(require_role(MembershipRole.manager)),
) -> ScheduleResponse:
    """Create a new schedule."""

    # Create new schedule
    schedule = Schedule(
        organization_id=org_id,
        name=schedule_data.name,
        week_start=schedule_data.week_start,
        status=ScheduleStatus.Draft,
        notes=schedule_data.notes,
    )

    session.add(schedule)
    await session.commit()
    await session.refresh(schedule)

    return ScheduleResponse.model_validate(schedule)


@router.patch("/{schedule_id}", response_model=ScheduleResponse)
async def update_schedule(
    org_id: UUID,
    schedule_id: UUID,
    schedule_data: ScheduleUpdate,
    session: AsyncSession = Depends(get_session),
    current_user: User = Depends(require_role(MembershipRole.manager)),
) -> ScheduleResponse:
    """Update a schedule partially."""

    # Get existing schedule
    result = await session.execute(
        select(Schedule).where(
            Schedule.id == schedule_id, Schedule.organization_id == org_id
        )
    )
    schedule = result.scalar_one_or_none()

    if not schedule:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Schedule not found"
        )

    # Update schedule fields
    update_data = schedule_data.model_dump(exclude_unset=True)

    for field, value in update_data.items():
        setattr(schedule, field, value)

    await session.commit()
    await session.refresh(schedule)

    return ScheduleResponse.model_validate(schedule)


@router.delete("/{schedule_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_schedule(
    org_id: UUID,
    schedule_id: UUID,
    session: AsyncSession = Depends(get_session),
    current_user: User = Depends(require_role(MembershipRole.manager)),
):
    """Delete a schedule (soft delete by setting is_active=False)."""

    # Get existing schedule
    result = await session.execute(
        select(Schedule).where(
            Schedule.id == schedule_id, Schedule.organization_id == org_id
        )
    )
    schedule = result.scalar_one_or_none()

    if not schedule:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Schedule not found"
        )

    # Soft delete by setting is_active to False
    schedule.is_active = False
    await session.commit()


# Auto-assignment and Publishing


@router.post("/{schedule_id}/auto-assign", response_model=AutoAssignResult)
async def auto_assign_schedule(
    org_id: UUID,
    schedule_id: UUID,
    session: AsyncSession = Depends(get_session),
    current_user: User = Depends(require_role(MembershipRole.manager)),
) -> AutoAssignResult:
    """Run auto-assignment for a schedule."""

    # Get schedule
    schedule_result = await session.execute(
        select(Schedule).where(
            Schedule.id == schedule_id, Schedule.organization_id == org_id
        )
    )
    schedule = schedule_result.scalar_one_or_none()

    if not schedule:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Schedule not found"
        )

    # TODO: Implement auto-assignment logic
    # This is a placeholder implementation
    return AutoAssignResult(
        schedule_id=schedule_id,
        total_slots=0,
        filled_slots=0,
        fill_rate=0.0,
        assignments_made=0,
        shortfalls=[],
        fairness_index=0.0,
    )


@router.post("/{schedule_id}/publish", response_model=ScheduleResponse)
async def publish_schedule(
    org_id: UUID,
    schedule_id: UUID,
    session: AsyncSession = Depends(get_session),
    current_user: User = Depends(require_role(MembershipRole.manager)),
) -> ScheduleResponse:
    """Publish a schedule."""

    # Get existing schedule
    result = await session.execute(
        select(Schedule).where(
            Schedule.id == schedule_id, Schedule.organization_id == org_id
        )
    )
    schedule = result.scalar_one_or_none()

    if not schedule:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Schedule not found"
        )

    # Update status to published
    schedule.status = ScheduleStatus.published
    await session.commit()
    await session.refresh(schedule)

    return ScheduleResponse.model_validate(schedule)


@router.get("/{schedule_id}/by-role", response_model=list[ScheduleByRoleView])
async def get_schedule_by_role(
    org_id: UUID,
    schedule_id: UUID,
    session: AsyncSession = Depends(get_session),
    current_user: User = Depends(get_current_user),
) -> list[ScheduleByRoleView]:
    """Get schedule view organized by role."""

    # Get schedule
    schedule_result = await session.execute(
        select(Schedule).where(
            Schedule.id == schedule_id, Schedule.organization_id == org_id
        )
    )
    schedule = schedule_result.scalar_one_or_none()

    if not schedule:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Schedule not found"
        )

    # Get slots with roles and assignments
    # Get days -> role slots
    days_result = await session.execute(
        select(ScheduleDay).where(ScheduleDay.schedule_id == schedule_id)
    )
    days = days_result.scalars().all()
    by_role_views = []
    for day in days:
        role_slots_result = await session.execute(
            select(RoleSlot)
            .join(Role, RoleSlot.role_id == Role.id)
            .where(RoleSlot.schedule_day_id == day.id)
        )
        role_slots = role_slots_result.scalars().all()
        for rs in role_slots:
            assignments_result = await session.execute(
                select(Assignment).where(Assignment.role_slot_id == rs.id)
            )
            assigned_count = len(assignments_result.scalars().all())
            shortfall = max(0, rs.required_count - assigned_count)
            by_role_views.append(
                ScheduleByRoleView(
                    role_name=(await session.get(Role, rs.role_id)).name,
                    day=day.schedule_date.strftime("%A"),
                    date=day.schedule_date,
                    shift="N/A",  # No shift concept in current model
                    assigned=assigned_count,
                    shortfall=shortfall,
                )
            )
    return by_role_views


@router.get("/{schedule_id}/by-staff", response_model=list[ScheduleByStaffView])
async def get_schedule_by_staff(
    org_id: UUID,
    schedule_id: UUID,
    session: AsyncSession = Depends(get_session),
    current_user: User = Depends(get_current_user),
) -> list[ScheduleByStaffView]:
    """Get schedule view organized by staff."""

    # Get schedule
    schedule_result = await session.execute(
        select(Schedule).where(
            Schedule.id == schedule_id, Schedule.organization_id == org_id
        )
    )
    schedule = schedule_result.scalar_one_or_none()

    if not schedule:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Schedule not found"
        )

    # Get assignments with profiles and roles
    # Gather by traversing days -> role slots -> assignments
    days_result = await session.execute(
        select(ScheduleDay).where(ScheduleDay.schedule_id == schedule_id)
    )
    days = days_result.scalars().all()
    assignments = []
    for day in days:
        role_slots = (
            (
                await session.execute(
                    select(RoleSlot).where(RoleSlot.schedule_day_id == day.id)
                )
            )
            .scalars()
            .all()
        )
        for rs in role_slots:
            assigns = (
                (
                    await session.execute(
                        select(Assignment).where(Assignment.role_slot_id == rs.id)
                    )
                )
                .scalars()
                .all()
            )
            for a in assigns:
                assignments.append((a, day, rs))

    # Build by-staff view
    by_staff_views = []
    for a, day, rs in assignments:
        user = await session.get(User, a.user_id)
        role = await session.get(Role, rs.role_id)
        by_staff_views.append(
            ScheduleByStaffView(
                staff_name=user.username,
                role_name=role.name,
                day=day.schedule_date.strftime("%A"),
                date=day.schedule_date,
                shift="N/A",  # No shift concept in current model
            )
        )

    return by_staff_views


# Staff-specific endpoints


@router.get(
    "/profiles/{profile_id}/my-assignments", response_model=list[ScheduleByStaffView]
)
async def get_my_assignments(
    org_id: UUID,
    profile_id: UUID,
    from_date: Optional[date] = Query(None, description="Filter from date"),
    to_date: Optional[date] = Query(None, description="Filter to date"),
    session: AsyncSession = Depends(get_session),
    current_user: User = Depends(get_current_user),
) -> list[ScheduleByStaffView]:
    """Get assignments for a specific profile."""

    # Build query via role slots and schedule days
    query = (
        select(Assignment)
        .join(RoleSlot, Assignment.role_slot_id == RoleSlot.id)
        .join(ScheduleDay, RoleSlot.schedule_day_id == ScheduleDay.id)
        .where(Assignment.user_id == profile_id)  # profile_id is actually user_id
    )

    # Apply date filters
    if from_date:
        query = query.where(ScheduleDay.schedule_date >= from_date)
    if to_date:
        query = query.where(ScheduleDay.schedule_date <= to_date)

    assignments_result = await session.execute(query)
    assignments_only = assignments_result.scalars().all()

    # enrich with related entities
    assignments = []
    for a in assignments_only:
        rs = await session.get(RoleSlot, a.role_slot_id)
        day = await session.get(ScheduleDay, rs.schedule_day_id)
        role = await session.get(Role, rs.role_id)
        assignments.append((a, day, role))

    # Build by-staff view
    by_staff_views = []
    for a, day, role in assignments:
        user = await session.get(User, a.user_id)
        by_staff_views.append(
            ScheduleByStaffView(
                staff_name=user.username,
                role_name=role.name,
                day=day.schedule_date.strftime("%A"),
                date=day.schedule_date,
                shift="N/A",  # No shift concept in current model
            )
        )

    return by_staff_views
