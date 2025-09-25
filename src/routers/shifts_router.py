"""
Shift CRUD operations router for workforce scheduling.
"""

from __future__ import annotations

from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, and_

from src.core.db import get_session
from src.core.security import get_current_user
from src.models.user import User
from src.models.shift import Shift
from src.schemas.shift import (
    ShiftCreate,
    ShiftUpdate,
    ShiftResponse,
    ShiftListResponse,
)

router = APIRouter(
    prefix="/organizations/{org_id}/shifts",
    tags=["shifts"],
)


@router.get("/", response_model=ShiftListResponse)
async def get_shifts(
    org_id: UUID,
    page: int = Query(1, ge=1, description="Page number"),
    size: int = Query(10, ge=1, le=100, description="Page size"),
    search: str = Query(None, description="Search by shift name"),
    session: AsyncSession = Depends(get_session),
    current_user: User = Depends(get_current_user),
) -> ShiftListResponse:
    """Get shifts for an organization with pagination and filtering."""

    # Build query
    query = select(Shift).where(Shift.organization_id == org_id)
    count_query = select(func.count(Shift.id)).where(Shift.organization_id == org_id)

    # Apply filters
    filters = []
    if search:
        filters.append(Shift.name.ilike(f"%{search}%"))

    if filters:
        query = query.where(and_(*filters))
        count_query = count_query.where(and_(*filters))

    # Get total count
    total_result = await session.execute(count_query)
    total = total_result.scalar()

    # Apply pagination
    offset = (page - 1) * size
    query = query.offset(offset).limit(size).order_by(Shift.name)

    # Execute query
    result = await session.execute(query)
    shifts = result.scalars().all()

    # Calculate pages
    pages = (total + size - 1) // size

    return ShiftListResponse(
        shifts=[ShiftResponse.model_validate(shift) for shift in shifts],
        total=total,
        page=page,
        size=size,
        pages=pages,
    )


@router.get("/{shift_id}", response_model=ShiftResponse)
async def get_shift(
    org_id: UUID,
    shift_id: UUID,
    session: AsyncSession = Depends(get_session),
    current_user: User = Depends(get_current_user),
) -> ShiftResponse:
    """Get a specific shift."""

    result = await session.execute(
        select(Shift).where(
            Shift.id == shift_id,
            Shift.organization_id == org_id,
        )
    )
    shift = result.scalar_one_or_none()

    if not shift:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Shift not found"
        )

    return ShiftResponse.model_validate(shift)


@router.post("/", response_model=ShiftResponse, status_code=status.HTTP_201_CREATED)
async def create_shift(
    org_id: UUID,
    shift_data: ShiftCreate,
    session: AsyncSession = Depends(get_session),
    current_user: User = Depends(get_current_user),
) -> ShiftResponse:
    """Create a new shift."""

    # Check if shift name already exists in organization
    existing = await session.execute(
        select(Shift).where(
            Shift.organization_id == org_id,
            Shift.name == shift_data.name,
        )
    )
    if existing.scalar_one_or_none():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Shift with this name already exists in organization",
        )

    # Create new shift
    shift = Shift(
        organization_id=org_id,
        name=shift_data.name,
        start_time=shift_data.start_time,
        end_time=shift_data.end_time,
    )

    session.add(shift)
    await session.commit()
    await session.refresh(shift)

    return ShiftResponse.model_validate(shift)


@router.patch("/{shift_id}", response_model=ShiftResponse)
async def update_shift(
    org_id: UUID,
    shift_id: UUID,
    shift_data: ShiftUpdate,
    session: AsyncSession = Depends(get_session),
    current_user: User = Depends(get_current_user),
) -> ShiftResponse:
    """Update a shift."""

    # Get existing shift
    result = await session.execute(
        select(Shift).where(
            Shift.id == shift_id,
            Shift.organization_id == org_id,
        )
    )
    shift = result.scalar_one_or_none()

    if not shift:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Shift not found"
        )

    # Check for name conflicts if name is being updated
    update_data = shift_data.model_dump(exclude_unset=True)
    if "name" in update_data:
        existing = await session.execute(
            select(Shift).where(
                Shift.organization_id == org_id,
                Shift.name == update_data["name"],
                Shift.id != shift_id,
            )
        )
        if existing.scalar_one_or_none():
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Shift with this name already exists in organization",
            )

    # Update shift fields
    for field, value in update_data.items():
        setattr(shift, field, value)

    await session.commit()
    await session.refresh(shift)

    return ShiftResponse.model_validate(shift)


@router.delete("/{shift_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_shift(
    org_id: UUID,
    shift_id: UUID,
    session: AsyncSession = Depends(get_session),
    current_user: User = Depends(get_current_user),
):
    """Delete a shift."""

    # Get existing shift
    result = await session.execute(
        select(Shift).where(
            Shift.id == shift_id,
            Shift.organization_id == org_id,
        )
    )
    shift = result.scalar_one_or_none()

    if not shift:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Shift not found"
        )

    await session.delete(shift)
    await session.commit()
