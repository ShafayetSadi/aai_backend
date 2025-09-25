"""
Availability CRUD operations router for workforce scheduling.
"""

from __future__ import annotations

from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, and_

from src.core.db import get_session
from src.core.security import get_current_user
from src.models.user import User
from src.models.availability import Availability
from src.models.base import AvailabilityType, AvailabilityStatus
from src.schemas.availability import (
    AvailabilityCreate,
    AvailabilityUpdate,
    AvailabilityResponse,
    AvailabilityListResponse,
)

router = APIRouter(
    prefix="/organizations/{org_id}/users/{user_id}/availability",
    tags=["availability"],
)


@router.get("/", response_model=AvailabilityListResponse)
async def get_availability(
    org_id: UUID,
    user_id: UUID,
    page: int = Query(1, ge=1, description="Page number"),
    size: int = Query(10, ge=1, le=100, description="Page size"),
    availability_type: AvailabilityType | None = Query(
        None, description="Filter by availability type (Recurring/Exception)"
    ),
    status: AvailabilityStatus | None = Query(None, description="Filter by availability status"),
    session: AsyncSession = Depends(get_session),
    current_user: User = Depends(get_current_user),
) -> AvailabilityListResponse:
    """Get availability for a user with pagination and filtering."""

    # Build query
    query = select(Availability).where(
        Availability.organization_id == org_id,
        Availability.user_id == user_id,
    )
    count_query = select(func.count(Availability.id)).where(
        Availability.organization_id == org_id,
        Availability.user_id == user_id,
    )

    # Apply filters
    filters = []
    if availability_type is not None:
        filters.append(Availability.availability_type == availability_type)
    if status is not None:
        filters.append(Availability.status == status)

    if filters:
        query = query.where(and_(*filters))
        count_query = count_query.where(and_(*filters))

    # Get total count
    total_result = await session.execute(count_query)
    total = total_result.scalar()

    # Apply pagination
    offset = (page - 1) * size
    query = query.offset(offset).limit(size).order_by(Availability.created_at.desc())

    # Execute query
    result = await session.execute(query)
    availabilities = result.scalars().all()

    # Calculate pages
    pages = (total + size - 1) // size

    return AvailabilityListResponse(
        availabilities=[
            AvailabilityResponse.model_validate(av) for av in availabilities
        ],
        total=total,
        page=page,
        size=size,
        pages=pages,
    )


@router.post(
    "/",
    response_model=AvailabilityResponse,
    status_code=status.HTTP_201_CREATED,
)
async def create_availability(
    org_id: UUID,
    user_id: UUID,
    availability_data: AvailabilityCreate,
    session: AsyncSession = Depends(get_session),
    current_user: User = Depends(get_current_user),
) -> AvailabilityResponse:
    """Create availability for a user."""
    # Schema validator already enforces mutual exclusivity & infers type
    availability = Availability(
        organization_id=org_id,
        user_id=user_id,
        shift_id=availability_data.shift_id,
        availability_day=availability_data.availability_day,
        availability_date=availability_data.availability_date,
        availability_type=availability_data.availability_type,
        status=availability_data.status,
        notes=availability_data.notes,
    )

    session.add(availability)
    await session.commit()
    await session.refresh(availability)

    return AvailabilityResponse.model_validate(availability)


@router.get("/exceptions", response_model=AvailabilityListResponse)
async def get_exception_availability(
    org_id: UUID,
    user_id: UUID,
    page: int = Query(1, ge=1, description="Page number"),
    size: int = Query(10, ge=1, le=100, description="Page size"),
    status: AvailabilityStatus | None = Query(None, description="Filter by availability status"),
    session: AsyncSession = Depends(get_session),
    current_user: User = Depends(get_current_user),
) -> AvailabilityListResponse:
    """Convenience endpoint: list only Exception availability entries (paginated)."""

    base_filters = [
        Availability.organization_id == org_id,
        Availability.user_id == user_id,
        Availability.availability_type == AvailabilityType.Exception,
    ]
    if status is not None:
        base_filters.append(Availability.status == status)

    count_query = select(func.count(Availability.id)).where(*base_filters)
    total = (await session.execute(count_query)).scalar()

    offset = (page - 1) * size
    query = (
        select(Availability)
        .where(*base_filters)
        .order_by(Availability.created_at.desc())
        .offset(offset)
        .limit(size)
    )
    result = await session.execute(query)
    records = result.scalars().all()
    pages = (total + size - 1) // size

    return AvailabilityListResponse(
        availabilities=[AvailabilityResponse.model_validate(r) for r in records],
        total=total,
        page=page,
        size=size,
        pages=pages,
    )


@router.patch("/{availability_id}", response_model=AvailabilityResponse)
async def update_availability(
    org_id: UUID,
    user_id: UUID,
    availability_id: UUID,
    availability_data: AvailabilityUpdate,
    session: AsyncSession = Depends(get_session),
    current_user: User = Depends(get_current_user),
) -> AvailabilityResponse:
    """Update availability."""

    # Get existing availability
    result = await session.execute(
        select(Availability).where(
            Availability.id == availability_id,
            Availability.organization_id == org_id,
            Availability.user_id == user_id,
        )
    )
    availability = result.scalar_one_or_none()

    if not availability:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Availability not found"
        )

    # Update availability fields
    update_data = availability_data.model_dump(exclude_unset=True)

    for field, value in update_data.items():
        setattr(availability, field, value)

    # After applying updates, enforce invariant similar to create
    # Validate explicit mode
    if availability.availability_type == AvailabilityType.Recurring:
        if availability.availability_day is None or availability.availability_date is not None:
            raise HTTPException(status_code=400, detail="Recurring requires availability_day only")
        availability.availability_date = None  # normalize
    elif availability.availability_type == AvailabilityType.Exception:
        if availability.availability_date is None or availability.availability_day is not None:
            raise HTTPException(status_code=400, detail="Exception requires availability_date only")
        availability.availability_day = None  # normalize
    else:
        raise HTTPException(status_code=400, detail="Unsupported availability_type")

    # Enforce shift_id presence post-update
    if availability.shift_id is None:
        raise HTTPException(status_code=400, detail="shift_id is required for availability")

    await session.commit()
    await session.refresh(availability)

    return AvailabilityResponse.model_validate(availability)


@router.delete("/{availability_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_availability(
    org_id: UUID,
    user_id: UUID,
    availability_id: UUID,
    session: AsyncSession = Depends(get_session),
    current_user: User = Depends(get_current_user),
):
    """Delete availability."""

    # Get existing availability
    result = await session.execute(
        select(Availability).where(
            Availability.id == availability_id,
            Availability.organization_id == org_id,
            Availability.user_id == user_id,
        )
    )
    availability = result.scalar_one_or_none()

    if not availability:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Availability not found"
        )

    await session.delete(availability)
    await session.commit()
    # 204 No Content
    return None
## NOTE: Legacy recurring/exception specific endpoints removed in favor of unified explicit model.

