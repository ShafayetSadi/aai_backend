"""
Requirement CRUD operations router for workforce scheduling.
"""

from __future__ import annotations

from datetime import date
from typing import Optional
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status, Response
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import func, and_, select, delete
from sqlalchemy.exc import IntegrityError
from src.models.role import Role
from src.models.shift import Shift
try:  # psycopg3 SQLSTATE codes for better error discrimination
    from psycopg.errors import UniqueViolation, ForeignKeyViolation  # type: ignore
except Exception:  # pragma: no cover
    UniqueViolation = ForeignKeyViolation = None  # type: ignore

from src.core.db import get_session
from src.core.security import get_current_user
from src.dependencies.roles import require_role
from src.models.user import User
from src.models.requirements import (
    RequirementDay,
    RequirementDayItem,
)
from src.models.base import Weekday
from src.models.membership import MembershipRole
from src.schemas.requirement import (
    RequirementDayCreate,
    RequirementDayUpdate,
    RequirementDayResponse,
    RequirementDayItemCreate,
    RequirementDayItemUpdate,
    RequirementDayItemResponse,
    RequirementDayItemCreateSingle,
    RequirementDayWithItems,
    RequirementDayListResponse,
)

router = APIRouter(
    prefix="/organizations/{org_id}/requirement-days", tags=["requirements"]
)


def resolve_weekday_from_date(target_date: date) -> Weekday:
    return Weekday(target_date.strftime("%A").lower())


async def get_requirement_day(
    session: AsyncSession, org_id: UUID, day_id: UUID
) -> RequirementDay:
    result = await session.execute(
        select(RequirementDay).where(
            RequirementDay.id == day_id,
            RequirementDay.organization_id == org_id,
        )
    )
    day = result.scalar_one_or_none()
    if not day:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Requirement day not found",
        )
    return day


@router.get("/", response_model=RequirementDayListResponse)
async def get_requirement_days(
    org_id: UUID,
    page: int = Query(1, ge=1, description="Page number"),
    size: int = Query(10, ge=1, le=100, description="Page size"),
    from_date: Optional[date] = Query(None, description="Filter from date"),
    to_date: Optional[date] = Query(None, description="Filter to date"),
    session: AsyncSession = Depends(get_session),
    current_user: User = Depends(get_current_user),
) -> RequirementDayListResponse:
    """Get paginated list of requirement days including their items."""

    query = select(RequirementDay).where(RequirementDay.organization_id == org_id)
    count_query = select(func.count(RequirementDay.id)).where(
        RequirementDay.organization_id == org_id
    )

    filters = []
    if from_date:
        filters.append(RequirementDay.requirement_date >= from_date)
    if to_date:
        filters.append(RequirementDay.requirement_date <= to_date)

    if filters:
        query = query.where(and_(*filters))
        count_query = count_query.where(and_(*filters))

    total = (await session.execute(count_query)).scalar()

    offset = (page - 1) * size
    query = (
        query.offset(offset)
        .limit(size)
        .order_by(RequirementDay.requirement_date.desc())
    )

    days = (await session.execute(query)).scalars().all()

    # Fetch all items for these days in one query to avoid N+1
    if days:
        day_ids = [d.id for d in days]
        items_result = await session.execute(
            select(RequirementDayItem).where(
                RequirementDayItem.organization_id == org_id,
                RequirementDayItem.requirement_day_id.in_(day_ids),
            )
        )
        all_items = items_result.scalars().all()
        items_by_day: dict[UUID, list[RequirementDayItem]] = {}
        for item in all_items:
            items_by_day.setdefault(item.requirement_day_id, []).append(item)
    else:
        items_by_day = {}

    pages = (total + size - 1) // size

    enriched_days = []
    for day in days:
        day_resp = RequirementDayResponse.model_validate(day)
        items = [
            RequirementDayItemResponse.model_validate(it)
            for it in items_by_day.get(day.id, [])
        ]
        enriched_days.append(
            RequirementDayWithItems(
                **day_resp.model_dump(),
                items=items,
            )
        )

    return RequirementDayListResponse(
        requirement_days=enriched_days,
        total=total,
        page=page,
        size=size,
        pages=pages,
    )


@router.get("/{day_id}", response_model=RequirementDayWithItems)
async def get_requirement_day_with_items(
    org_id: UUID,
    day_id: UUID,
    session: AsyncSession = Depends(get_session),
    current_user: User = Depends(get_current_user),
) -> RequirementDayWithItems:
    """Get a requirement day with its items."""

    day = await get_requirement_day(session, org_id, day_id)

    items_result = await session.execute(
        select(RequirementDayItem).where(
            RequirementDayItem.requirement_day_id == day_id,
            RequirementDayItem.organization_id == org_id,
        )
    )
    items = items_result.scalars().all()

    day_data = RequirementDayResponse.model_validate(day)
    return RequirementDayWithItems(
        **day_data.model_dump(),
        items=[RequirementDayItemResponse.model_validate(item) for item in items],
    )


@router.post(
    "/",
    response_model=RequirementDayResponse,
    status_code=status.HTTP_201_CREATED,
)
async def create_requirement_day(
    org_id: UUID,
    payload: RequirementDayCreate,
    session: AsyncSession = Depends(get_session),
    current_user: User = Depends(require_role(MembershipRole.manager)),
) -> RequirementDayResponse:
    """Create a requirement day record."""

    existing_day = await session.scalar(
        select(RequirementDay).where(
            RequirementDay.organization_id == org_id,
            RequirementDay.requirement_date == payload.requirement_date,
        )
    )
    if existing_day:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Requirement day already exists for this date",
        )

    day = RequirementDay(
        organization_id=org_id,
        requirement_date=payload.requirement_date,
        requirement_day=resolve_weekday_from_date(payload.requirement_date),
        notes=payload.notes,
    )
    session.add(day)
    await session.commit()
    await session.refresh(day)

    return RequirementDayResponse.model_validate(day)


@router.patch("/{day_id}", response_model=RequirementDayResponse)
async def update_requirement_day(
    org_id: UUID,
    day_id: UUID,
    payload: RequirementDayUpdate,
    session: AsyncSession = Depends(get_session),
    current_user: User = Depends(require_role(MembershipRole.manager)),
) -> RequirementDayResponse:
    """Update a requirement day."""

    day = await get_requirement_day(session, org_id, day_id)

    update_data = payload.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(day, field, value)

    await session.commit()
    await session.refresh(day)

    return RequirementDayResponse.model_validate(day)


@router.delete(
    "/{day_id}",
    response_class=Response,
)
async def delete_requirement_day(
    org_id: UUID,
    day_id: UUID,
    session: AsyncSession = Depends(get_session),
    current_user: User = Depends(require_role(MembershipRole.manager)),
):
    """Delete a requirement day."""

    day = await get_requirement_day(session, org_id, day_id)
    await session.delete(day)
    await session.commit()
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.put("/{day_id}/items", response_model=list[RequirementDayItemResponse])
async def bulk_upsert_requirement_day_items(
    org_id: UUID,
    day_id: UUID,
    items_data: list[RequirementDayItemCreate],
    session: AsyncSession = Depends(get_session),
    current_user: User = Depends(require_role(MembershipRole.manager)),
) -> list[RequirementDayItemResponse]:
    """Replace the items for a requirement day."""

    day = await get_requirement_day(session, org_id, day_id)

    await session.execute(
        delete(RequirementDayItem).where(
            RequirementDayItem.requirement_day_id == day_id,
            RequirementDayItem.organization_id == org_id,
        )
    )

    new_items: list[RequirementDayItem] = []
    for item_data in items_data:
        expected_weekday = resolve_weekday_from_date(item_data.requirement_date)
        if item_data.weekday != expected_weekday:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="weekday does not match requirement_date",
            )

        day_item = RequirementDayItem(
            organization_id=org_id,
            requirement_day_id=day.id,
            role_id=item_data.role_id,
            shift_id=item_data.shift_id,
            weekday=item_data.weekday,
            required_count=item_data.required_count,
            notes=item_data.notes,
        )
        session.add(day_item)
        new_items.append(day_item)

    await session.commit()

    for item in new_items:
        await session.refresh(item)

    return [RequirementDayItemResponse.model_validate(item) for item in new_items]


# --------------------- Requirement Day Item CRUD ---------------------

async def _get_requirement_day_item(
    session: AsyncSession, org_id: UUID, day_id: UUID, item_id: UUID
) -> RequirementDayItem:
    result = await session.execute(
        select(RequirementDayItem).where(
            RequirementDayItem.id == item_id,
            RequirementDayItem.organization_id == org_id,
            RequirementDayItem.requirement_day_id == day_id,
        )
    )
    item = result.scalar_one_or_none()
    if not item:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Requirement day item not found"
        )
    return item


@router.get(
    "/{day_id}/items", response_model=list[RequirementDayItemResponse], summary="List items for a requirement day"
)
async def list_requirement_day_items(
    org_id: UUID,
    day_id: UUID,
    session: AsyncSession = Depends(get_session),
    current_user: User = Depends(get_current_user),
) -> list[RequirementDayItemResponse]:
    """List all requirement items for a given requirement day."""
    await get_requirement_day(session, org_id, day_id)
    result = await session.execute(
        select(RequirementDayItem).where(
            RequirementDayItem.organization_id == org_id,
            RequirementDayItem.requirement_day_id == day_id,
        )
    )
    items = result.scalars().all()
    return [RequirementDayItemResponse.model_validate(i) for i in items]


@router.post(
    "/{day_id}/items",
    response_model=RequirementDayItemResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create a requirement day item",
)
async def create_requirement_day_item(
    org_id: UUID,
    day_id: UUID,
    payload: RequirementDayItemCreateSingle,
    session: AsyncSession = Depends(get_session),
    current_user: User = Depends(require_role(MembershipRole.manager)),
) -> RequirementDayItemResponse:
    """Create a single requirement day item.

    Validates weekday consistency and uniqueness (role_id + shift_id per day).
    """
    day = await get_requirement_day(session, org_id, day_id)

    expected_weekday = resolve_weekday_from_date(payload.requirement_date)
    if payload.weekday != expected_weekday:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="weekday does not match requirement_date",
        )

    # Validate role & shift exist within the organization to avoid opaque FK errors
    role_obj = await session.scalar(
        select(Role).where(Role.id == payload.role_id, Role.organization_id == org_id)
    )
    if not role_obj:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Role not found for this organization",
        )

    shift_obj = await session.scalar(
        select(Shift).where(Shift.id == payload.shift_id, Shift.organization_id == org_id)
    )
    if not shift_obj:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Shift not found for this organization",
        )

    item = RequirementDayItem(
        organization_id=org_id,
        requirement_day_id=day.id,
        role_id=payload.role_id,
        shift_id=payload.shift_id,
        weekday=payload.weekday,
        required_count=payload.required_count,
        notes=payload.notes,
    )

    session.add(item)
    try:
        await session.commit()
    except IntegrityError as e:
        await session.rollback()
        sqlstate = getattr(getattr(e, "orig", None), "sqlstate", None)
        if sqlstate == "23505":  # unique_violation
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Requirement day item already exists for this role & shift",
            ) from e
        if sqlstate == "23503":  # foreign_key_violation
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Foreign key violation (role or shift does not exist)",
            ) from e
        raise

    await session.refresh(item)
    return RequirementDayItemResponse.model_validate(item)


@router.get(
    "/{day_id}/items/{item_id}",
    response_model=RequirementDayItemResponse,
    summary="Get a requirement day item",
)
async def get_requirement_day_item(
    org_id: UUID,
    day_id: UUID,
    item_id: UUID,
    session: AsyncSession = Depends(get_session),
    current_user: User = Depends(get_current_user),
) -> RequirementDayItemResponse:
    item = await _get_requirement_day_item(session, org_id, day_id, item_id)
    return RequirementDayItemResponse.model_validate(item)


@router.patch(
    "/{day_id}/items/{item_id}",
    response_model=RequirementDayItemResponse,
    summary="Update a requirement day item",
)
async def update_requirement_day_item(
    org_id: UUID,
    day_id: UUID,
    item_id: UUID,
    payload: RequirementDayItemUpdate,
    session: AsyncSession = Depends(get_session),
    current_user: User = Depends(require_role(MembershipRole.manager)),
) -> RequirementDayItemResponse:
    item = await _get_requirement_day_item(session, org_id, day_id, item_id)

    update_data = payload.model_dump(exclude_unset=True)

    # If role_id or shift_id are being changed, validate they exist in this org
    if "role_id" in update_data:
        role_obj = await session.scalar(
            select(Role).where(Role.id == update_data["role_id"], Role.organization_id == org_id)
        )
        if not role_obj:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Role not found for this organization",
            )
    if "shift_id" in update_data:
        shift_obj = await session.scalar(
            select(Shift).where(Shift.id == update_data["shift_id"], Shift.organization_id == org_id)
        )
        if not shift_obj:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Shift not found for this organization",
            )

    for field, value in update_data.items():
        setattr(item, field, value)

    # Enforce weekday consistency if weekday changed (cannot verify date—no date field in update)
    # Optionally we could compare with parent day's requirement_day.
    parent_day = await get_requirement_day(session, org_id, day_id)
    if item.weekday != parent_day.requirement_day:
        # Keep logic consistent with creation rule that weekday must match derived date.
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="weekday does not match parent requirement day",
        )

    try:
        await session.commit()
    except IntegrityError as e:
        await session.rollback()
        sqlstate = getattr(getattr(e, "orig", None), "sqlstate", None)
        if sqlstate == "23505":
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Requirement day item already exists for this role & shift",
            ) from e
        if sqlstate == "23503":
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Foreign key violation (role or shift does not exist)",
            ) from e
        raise
    await session.refresh(item)
    return RequirementDayItemResponse.model_validate(item)


@router.delete(
    "/{day_id}/items/{item_id}",
    summary="Delete a requirement day item",
    response_class=Response,
)
async def delete_requirement_day_item(
    org_id: UUID,
    day_id: UUID,
    item_id: UUID,
    session: AsyncSession = Depends(get_session),
    current_user: User = Depends(require_role(MembershipRole.manager)),
) -> None:
    item = await _get_requirement_day_item(session, org_id, day_id, item_id)
    await session.delete(item)
    await session.commit()
    return Response(status_code=status.HTTP_204_NO_CONTENT)
