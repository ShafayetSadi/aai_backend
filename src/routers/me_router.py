"""
Personal endpoints for the current user (/me).
"""

from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from pydantic_core import ValidationError
from sqlalchemy.ext.asyncio import AsyncSession
from sqlmodel import select
from uuid import UUID

from src.core.db import get_session
from src.core.security import get_current_user, get_password_hash
from src.models.user import User
from src.models.profile import Profile
from src.models.availability import Availability
from src.models.shift import Shift
from src.schemas.user import UserUpdate, UserResponse
from src.schemas.profile import ProfileUpdate, ProfileResponse
from src.models.base import AvailabilityStatus, AvailabilityType

router = APIRouter(prefix="/me", tags=["me"])


class ScheduleItem(BaseModel):
    day: str
    start: str
    end: str


class AvailabilityItem(BaseModel):
    date: str  # Date in YYYY-MM-DD format
    shift: str  # Shift name (e.g., "Morning", "Evening", "Night")
    is_available: bool


class AvailabilityUpdateRequest(BaseModel):
    organization_id: str
    availability_items: list[AvailabilityItem]


@router.get("", response_model=UserResponse)
async def get_me(current_user: User = Depends(get_current_user)) -> UserResponse:
    """Get current user's information."""
    return UserResponse.model_validate(current_user)


@router.patch("", response_model=UserResponse)
async def update_me(
    user_data: UserUpdate,
    session: AsyncSession = Depends(get_session),
    current_user: User = Depends(get_current_user),
) -> UserResponse:
    """Update current user's information."""

    # Check for conflicts if updating email or username
    if user_data.email or user_data.username:
        conflict_query = select(User).where(User.id != current_user.id)
        conflict_filters = []

        if user_data.email:
            conflict_filters.append(User.email == user_data.email)
        if user_data.username:
            conflict_filters.append(User.username == user_data.username)

        if conflict_filters:
            from sqlalchemy import or_

            conflict_result = await session.execute(
                conflict_query.where(or_(*conflict_filters))
            )
            if conflict_result.scalar_one_or_none():
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Email or username already exists",
                )

    # Update user fields
    update_data = user_data.model_dump(exclude_unset=True)

    if "password" in update_data:
        update_data["password_hash"] = get_password_hash(update_data.pop("password"))

    try:
        for field, value in update_data.items():
            setattr(current_user, field, value)
    except ValidationError as e:
        # Convert Pydantic validation error to HTTP 400 response
        error_details = []
        for error in e.errors():
            field_name = error.get("loc", ["unknown"])[0] if error.get("loc") else "unknown"
            message = error.get("msg", "Validation error")
            error_details.append(f"{field_name}: {message}")

        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="; ".join(error_details),
        )

    await session.commit()
    await session.refresh(current_user)

    return UserResponse.model_validate(current_user)


@router.get("/profile", response_model=ProfileResponse)
async def get_my_profile(
    session: AsyncSession = Depends(get_session),
    current_user: User = Depends(get_current_user),
) -> ProfileResponse:
    """Get current user's profile."""

    result = await session.execute(
        select(Profile).where(Profile.user_id == current_user.id)
    )
    profile = result.scalar_one_or_none()

    if not profile:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Profile not found for this user",
        )

    return ProfileResponse.model_validate(profile)


@router.patch("/profile", response_model=ProfileResponse)
async def update_my_profile(
    profile_data: ProfileUpdate,
    session: AsyncSession = Depends(get_session),
    current_user: User = Depends(get_current_user),
) -> ProfileResponse:
    """Update current user's profile."""

    # Get existing profile
    result = await session.execute(
        select(Profile).where(Profile.user_id == current_user.id)
    )
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


@router.get("/schedule", response_model=list[ScheduleItem])
async def get_my_schedule(
    current_user: User = Depends(get_current_user),
) -> list[ScheduleItem]:
    """Get current user's schedule."""
    # Placeholder response; in real app, fetch from DB with role check
    return []


@router.patch("/availability", status_code=status.HTTP_204_NO_CONTENT)
async def update_my_availability(
    payload: AvailabilityUpdateRequest,
    session: AsyncSession = Depends(get_session),
    current_user: User = Depends(get_current_user)
):
    """Update current user's availability."""
    from datetime import date as date_type
    from sqlalchemy import and_

    try:
        organization_uuid = UUID(payload.organization_id)
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid organization ID format"
        )

    # Process each availability item
    for item in payload.availability_items:
        try:
            # Parse the date
            availability_date = date_type.fromisoformat(item.date)
        except ValueError:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid date format: {item.date}. Expected YYYY-MM-DD"
            )

        # Find the shift by name within the organization
        shift_result = await session.execute(
            select(Shift).where(
                and_(
                    Shift.organization_id == organization_uuid,
                    Shift.name == item.shift
                )
            )
        )
        shift = shift_result.scalar_one_or_none()

        if not shift:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Shift '{item.shift}' not found in the organization"
            )

        # Determine the availability status
        availability_status = AvailabilityStatus.Available if item.is_available else AvailabilityStatus.Unavailable

        # Check if availability record already exists
        existing_result = await session.execute(
            select(Availability).where(
                and_(
                    Availability.organization_id == organization_uuid,
                    Availability.user_id == current_user.id,
                    Availability.shift_id == shift.id,
                    Availability.availability_date == availability_date,
                    Availability.availability_type == AvailabilityType.Exception
                )
            )
        )
        existing_availability = existing_result.scalar_one_or_none()

        if existing_availability:
            # Update existing availability
            existing_availability.status = availability_status
        else:
            # Create new availability record
            new_availability = Availability(
                organization_id=organization_uuid,
                user_id=current_user.id,
                shift_id=shift.id,
                availability_date=availability_date,
                availability_type=AvailabilityType.Exception,
                status=availability_status
            )
            session.add(new_availability)

    # Commit all changes
    await session.commit()
