"""
Business Hours CRUD operations router for workforce scheduling.
"""

from __future__ import annotations

from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from src.core.db import get_session
from src.core.security import get_current_user
from src.models.user import User
from src.models.business_days import BusinessOpenDays
from src.schemas.business_hours import (
    BusinessOpenDaysCreate,
    BusinessOpenDaysUpdate,
    BusinessOpenDaysResponse,
)

router = APIRouter(
    prefix="/organizations/{org_id}/business-hours",
    tags=["business-hours"],
)


@router.get("/", response_model=BusinessOpenDaysResponse)
async def get_business_hours(
    org_id: UUID,
    session: AsyncSession = Depends(get_session),
    current_user: User = Depends(get_current_user),
) -> BusinessOpenDaysResponse:
    """Get business hours for an organization."""

    result = await session.execute(
        select(BusinessOpenDays).where(
            BusinessOpenDays.organization_id == org_id,
            BusinessOpenDays.is_active == True,
        )
    )
    business_hours = result.scalar_one_or_none()

    if not business_hours:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Business hours not found"
        )

    return BusinessOpenDaysResponse.model_validate(business_hours)


@router.post(
    "/", response_model=BusinessOpenDaysResponse, status_code=status.HTTP_201_CREATED
)
async def create_business_hours(
    org_id: UUID,
    business_hours_data: BusinessOpenDaysCreate,
    session: AsyncSession = Depends(get_session),
    current_user: User = Depends(get_current_user),
) -> BusinessOpenDaysResponse:
    """Create business hours for an organization."""

    # Check if business hours already exist for this organization
    existing = await session.execute(
        select(BusinessOpenDays).where(
            BusinessOpenDays.organization_id == org_id,
            BusinessOpenDays.is_active == True,
        )
    )
    if existing.scalar_one_or_none():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Business hours already exist for this organization",
        )

    # Create new business hours
    business_hours = BusinessOpenDays(
        organization_id=org_id,
        monday=business_hours_data.monday,
        tuesday=business_hours_data.tuesday,
        wednesday=business_hours_data.wednesday,
        thursday=business_hours_data.thursday,
        friday=business_hours_data.friday,
        saturday=business_hours_data.saturday,
        sunday=business_hours_data.sunday,
        notes=business_hours_data.notes,
        is_active=business_hours_data.is_active,
    )

    session.add(business_hours)
    await session.commit()
    await session.refresh(business_hours)

    return BusinessOpenDaysResponse.model_validate(business_hours)


@router.patch("/", response_model=BusinessOpenDaysResponse)
async def update_business_hours(
    org_id: UUID,
    business_hours_data: BusinessOpenDaysUpdate,
    session: AsyncSession = Depends(get_session),
    current_user: User = Depends(get_current_user),
) -> BusinessOpenDaysResponse:
    """Update business hours for an organization."""

    # Get existing business hours
    result = await session.execute(
        select(BusinessOpenDays).where(
            BusinessOpenDays.organization_id == org_id,
            BusinessOpenDays.is_active == True,
        )
    )
    business_hours = result.scalar_one_or_none()

    if not business_hours:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Business hours not found"
        )

    # Update business hours fields
    update_data = business_hours_data.model_dump(exclude_unset=True)

    for field, value in update_data.items():
        setattr(business_hours, field, value)

    await session.commit()
    await session.refresh(business_hours)

    return BusinessOpenDaysResponse.model_validate(business_hours)


@router.delete("/", status_code=status.HTTP_204_NO_CONTENT)
async def delete_business_hours(
    org_id: UUID,
    session: AsyncSession = Depends(get_session),
    current_user: User = Depends(get_current_user),
):
    """Delete business hours for an organization."""

    # Get existing business hours
    result = await session.execute(
        select(BusinessOpenDays).where(
            BusinessOpenDays.organization_id == org_id,
            BusinessOpenDays.is_active == True,
        )
    )
    business_hours = result.scalar_one_or_none()

    if not business_hours:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Business hours not found"
        )

    # Soft delete by setting is_active to False
    business_hours.is_active = False
    await session.commit()
