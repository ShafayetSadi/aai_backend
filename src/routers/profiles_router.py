"""
Profile CRUD operations router.
"""

from __future__ import annotations

from typing import Optional
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from sqlalchemy import func, and_, or_

from src.core.db import get_session
from src.core.security import get_current_user
from src.models.user import User
from src.models.profile import Profile
from src.schemas.profile import (
    ProfileUpdate,
    ProfileResponse,
    ProfileListResponse,
)

router = APIRouter(prefix="/profiles", tags=["profiles"])


@router.get("/", response_model=ProfileListResponse)
async def get_profiles(
    page: int = Query(1, ge=1, description="Page number"),
    size: int = Query(10, ge=1, le=100, description="Page size"),
    search: Optional[str] = Query(None, description="Search by name"),
    is_public: Optional[bool] = Query(None, description="Filter by public status"),
    session: AsyncSession = Depends(get_session),
    current_user: User = Depends(get_current_user),
) -> ProfileListResponse:
    """Get paginated list of profiles with optional filtering."""

    # Build query
    query = select(Profile)
    count_query = select(func.count(Profile.id))

    # Apply filters
    filters = []
    if search:
        search_filter = or_(
            Profile.first_name.ilike(f"%{search}%"),
            Profile.last_name.ilike(f"%{search}%"),
        )
        filters.append(search_filter)

    # is_public field doesn't exist in current Profile model
    # if is_public is not None:
    #     filters.append(Profile.is_public == is_public)

    if filters:
        query = query.where(and_(*filters))
        count_query = count_query.where(and_(*filters))

    # Get total count
    total_result = await session.execute(count_query)
    total = total_result.scalar()

    # Apply pagination
    offset = (page - 1) * size
    query = query.offset(offset).limit(size).order_by(Profile.created_at.desc())

    # Execute query
    result = await session.execute(query)
    profiles = result.scalars().all()

    # Calculate pages
    pages = (total + size - 1) // size

    return ProfileListResponse(
        profiles=[ProfileResponse.model_validate(profile) for profile in profiles],
        total=total,
        page=page,
        size=size,
        pages=pages,
    )


@router.get("/{profile_id}", response_model=ProfileResponse)
async def get_profile(
    profile_id: UUID,
    session: AsyncSession = Depends(get_session),
    current_user: User = Depends(get_current_user),
) -> ProfileResponse:
    """Get a specific profile by ID."""

    result = await session.execute(select(Profile).where(Profile.id == profile_id))
    profile = result.scalar_one_or_none()

    if not profile:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Profile not found"
        )

    return ProfileResponse.model_validate(profile)


@router.patch("/{profile_id}", response_model=ProfileResponse)
async def update_profile(
    profile_id: UUID,
    profile_data: ProfileUpdate,
    session: AsyncSession = Depends(get_session),
    current_user: User = Depends(get_current_user),
) -> ProfileResponse:
    """Update a profile partially."""

    # Get existing profile
    result = await session.execute(select(Profile).where(Profile.id == profile_id))
    profile = result.scalar_one_or_none()

    if not profile:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Profile not found"
        )

    # Update profile fields
    update_data = profile_data.model_dump(exclude_unset=True)

    for field, value in update_data.items():
        setattr(profile, field, value)

    await session.commit()
    await session.refresh(profile)

    return ProfileResponse.model_validate(profile)


@router.delete("/{profile_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_profile(
    profile_id: UUID,
    session: AsyncSession = Depends(get_session),
    current_user: User = Depends(get_current_user),
):
    """Delete a profile."""

    # Get existing profile
    result = await session.execute(select(Profile).where(Profile.id == profile_id))
    profile = result.scalar_one_or_none()

    if not profile:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Profile not found"
        )

    await session.delete(profile)
    await session.commit()
