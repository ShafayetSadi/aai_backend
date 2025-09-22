"""
Location CRUD operations router.
"""

from __future__ import annotations

from typing import Optional
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import func, and_, or_, select

from src.core.db import get_session
from src.core.security import get_current_user
from src.models.user import User
from src.models.profile import Location
from src.schemas.location import (
    LocationCreate,
    LocationUpdate,
    LocationResponse,
    LocationListResponse,
)

router = APIRouter(prefix="/locations", tags=["locations"])


@router.get("/", response_model=LocationListResponse)
async def get_locations(
    page: int = Query(1, ge=1, description="Page number"),
    size: int = Query(10, ge=1, le=100, description="Page size"),
    search: Optional[str] = Query(None, description="Search by country or city"),
    session: AsyncSession = Depends(get_session),
    current_user: User = Depends(get_current_user),
) -> LocationListResponse:
    """Get paginated list of locations with optional filtering."""

    # Build query
    query = select(Location)
    count_query = select(func.count(Location.id))

    # Apply filters
    filters = []
    if search:
        search_filter = or_(
            Location.country.ilike(f"%{search}%"),
            Location.city.ilike(f"%{search}%"),
        )
        filters.append(search_filter)

    if filters:
        query = query.where(and_(*filters))
        count_query = count_query.where(and_(*filters))

    # Get total count
    total_result = await session.execute(count_query)
    total = total_result.scalar()

    # Apply pagination
    offset = (page - 1) * size
    query = query.offset(offset).limit(size).order_by(Location.created_at.desc())

    # Execute query
    result = await session.execute(query)
    locations = result.scalars().all()

    # Calculate pages
    pages = (total + size - 1) // size

    return LocationListResponse(
        locations=[LocationResponse.model_validate(location) for location in locations],
        total=total,
        page=page,
        size=size,
        pages=pages,
    )


@router.get("/{location_id}", response_model=LocationResponse)
async def get_location(
    location_id: UUID,
    session: AsyncSession = Depends(get_session),
    current_user: User = Depends(get_current_user),
) -> LocationResponse:
    """Get a specific location by ID."""

    result = await session.execute(select(Location).where(Location.id == location_id))
    location = result.scalar_one_or_none()

    if not location:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Location not found"
        )

    return LocationResponse.model_validate(location)


@router.post("/", response_model=LocationResponse, status_code=status.HTTP_201_CREATED)
async def create_location(
    location_data: LocationCreate,
    session: AsyncSession = Depends(get_session),
    current_user: User = Depends(get_current_user),
) -> LocationResponse:
    """Create a new location."""

    # Create new location
    location = Location(
        country=location_data.country,
        state_province=location_data.state_province,
        city=location_data.city,
        postal_code=location_data.postal_code,
    )

    session.add(location)
    await session.commit()
    await session.refresh(location)

    return LocationResponse.model_validate(location)


@router.put("/{location_id}", response_model=LocationResponse)
async def update_location(
    location_id: UUID,
    location_data: LocationUpdate,
    session: AsyncSession = Depends(get_session),
    current_user: User = Depends(get_current_user),
) -> LocationResponse:
    """Update a location."""

    # Get existing location
    result = await session.execute(select(Location).where(Location.id == location_id))
    location = result.scalar_one_or_none()

    if not location:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Location not found"
        )

    # Update location fields
    update_data = location_data.model_dump(exclude_unset=True)

    for field, value in update_data.items():
        setattr(location, field, value)

    await session.commit()
    await session.refresh(location)

    return LocationResponse.model_validate(location)


@router.delete("/{location_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_location(
    location_id: UUID,
    session: AsyncSession = Depends(get_session),
    current_user: User = Depends(get_current_user),
):
    """Delete a location."""

    # Get existing location
    result = await session.execute(select(Location).where(Location.id == location_id))
    location = result.scalar_one_or_none()

    if not location:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Location not found"
        )

    await session.delete(location)
    await session.commit()
