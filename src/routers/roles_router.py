"""
Role CRUD operations router for workforce scheduling.
"""

from __future__ import annotations

import re
from typing import Optional
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import func, and_, select
from sqlalchemy.exc import IntegrityError


from src.core.db import get_session
from src.core.security import get_current_user
from src.dependencies.roles import require_role
from src.models.user import User
from src.models.role import Role
from src.models.base import RoleStatus
from src.models.membership import MembershipRole
from src.schemas.role import (
    RoleCreate,
    RoleUpdate,
    RoleResponse,
    RoleListResponse,
)

router = APIRouter(prefix="/organizations/{org_id}/roles", tags=["roles"])


_slugify_pattern = re.compile(r"[^a-z0-9]+")


def _slugify_value(value: str) -> str:
    slug = _slugify_pattern.sub("-", value.lower()).strip("-")
    return slug or "role"


async def _generate_unique_slug(
    session: AsyncSession,
    org_id: UUID,
    name: str,
    *,
    exclude_role_id: UUID | None = None,
) -> str:
    base_slug = _slugify_value(name)
    slug = base_slug
    suffix = 1

    while True:
        query = select(Role.id).where(
            Role.organization_id == org_id,
            Role.slug == slug,
        )
        if exclude_role_id:
            query = query.where(Role.id != exclude_role_id)

        result = await session.execute(query)
        if result.scalar_one_or_none() is None:
            return slug

        slug = f"{base_slug}-{suffix}"
        suffix += 1


@router.get("/", response_model=RoleListResponse)
async def get_roles(
    org_id: UUID,
    page: int = Query(1, ge=1, description="Page number"),
    size: int = Query(10, ge=1, le=100, description="Page size"),
    active: Optional[bool] = Query(None, description="Filter by active status"),
    search: Optional[str] = Query(None, description="Search by name"),
    session: AsyncSession = Depends(get_session),
    current_user: User = Depends(get_current_user),
) -> RoleListResponse:
    """Get paginated list of roles with optional filtering.

    Active filter maps to RoleStatus.Active. active=False returns non-active roles.
    """

    query = select(Role).where(Role.organization_id == org_id)
    count_query = select(func.count(Role.id)).where(Role.organization_id == org_id)

    filters = []
    if active is True:
        filters.append(Role.status == RoleStatus.Active)
    elif active is False:
        filters.append(Role.status != RoleStatus.Active)

    if search:
        filters.append(Role.name.ilike(f"%{search}%"))

    if filters:
        query = query.where(and_(*filters))
        count_query = count_query.where(and_(*filters))

    total_result = await session.execute(count_query)
    total = total_result.scalar() or 0

    offset = (page - 1) * size
    query = query.offset(offset).limit(size).order_by(Role.created_at.desc())

    result = await session.execute(query)
    roles = result.scalars().all()

    pages = (total + size - 1) // size if total else 0

    role_responses = [
        RoleResponse(
            id=r.id,
            organization_id=r.organization_id,
            name=r.name,
            description=r.description,
            slug=r.slug,
            is_active=r.status == RoleStatus.Active,
            created_at=r.created_at,
            updated_at=r.updated_at,
            deactivated_at=None if r.status == RoleStatus.Active else r.updated_at,
        )
        for r in roles
    ]

    return RoleListResponse(
        roles=role_responses, total=total, page=page, size=size, pages=pages
    )


@router.get("/{role_id}", response_model=RoleResponse)
async def get_role(
    org_id: UUID,
    role_id: UUID,
    session: AsyncSession = Depends(get_session),
    current_user: User = Depends(get_current_user),
) -> RoleResponse:
    """Get a specific role by ID."""

    result = await session.execute(
        select(Role).where(Role.id == role_id, Role.organization_id == org_id)
    )
    role = result.scalar_one_or_none()

    if not role:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Role not found"
        )

    return RoleResponse(
        id=role.id,
        organization_id=role.organization_id,
        name=role.name,
        description=role.description,
        slug=role.slug,
        is_active=role.status == RoleStatus.Active,
        created_at=role.created_at,
        updated_at=role.updated_at,
        deactivated_at=None if role.status == RoleStatus.Active else role.updated_at,
    )


@router.post("/", response_model=RoleResponse, status_code=status.HTTP_201_CREATED)
async def create_role(
    org_id: UUID,
    role_data: RoleCreate,
    session: AsyncSession = Depends(get_session),
    current_user: User = Depends(require_role(MembershipRole.manager)),
) -> RoleResponse:
    """Create a new role."""

    slug = await _generate_unique_slug(session, org_id, role_data.name)

    # Create new role
    role = Role(
        organization_id=org_id,
        name=role_data.name,
        slug=slug,
        description=role_data.description,
    )

    session.add(role)
    try:
        await session.commit()
        await session.refresh(role)
    except IntegrityError:
        await session.rollback()
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Role with name '{role_data.name}' already exists in this organization.",
        )

    return RoleResponse(
        id=role.id,
        organization_id=role.organization_id,
        name=role.name,
        description=role.description,
        slug=role.slug,
        is_active=role.status == RoleStatus.Active,
        created_at=role.created_at,
        updated_at=role.updated_at,
        deactivated_at=None if role.status == RoleStatus.Active else role.updated_at,
    )


@router.patch("/{role_id}", response_model=RoleResponse)
async def update_role(
    org_id: UUID,
    role_id: UUID,
    role_data: RoleUpdate,
    session: AsyncSession = Depends(get_session),
    current_user: User = Depends(require_role(MembershipRole.manager)),
) -> RoleResponse:
    """Update a role partially."""

    # Get existing role
    result = await session.execute(
        select(Role).where(Role.id == role_id, Role.organization_id == org_id)
    )
    role = result.scalar_one_or_none()

    if not role:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Role not found"
        )

    # Update role fields
    update_data = role_data.model_dump(exclude_unset=True)

    for field, value in update_data.items():
        setattr(role, field, value)

    if "name" in update_data:
        role.slug = await _generate_unique_slug(
            session, org_id, role.name or "", exclude_role_id=role_id
        )

    await session.commit()
    await session.refresh(role)

    return RoleResponse(
        id=role.id,
        organization_id=role.organization_id,
        name=role.name,
        description=role.description,
        slug=role.slug,
        is_active=role.status == RoleStatus.Active,
        created_at=role.created_at,
        updated_at=role.updated_at,
        deactivated_at=None if role.status == RoleStatus.Active else role.updated_at,
    )


@router.delete("/{role_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_role(
    org_id: UUID,
    role_id: UUID,
    session: AsyncSession = Depends(get_session),
    current_user: User = Depends(require_role(MembershipRole.manager)),
):
    """Hard delete a role (permanently removes it)."""

    # Get existing role
    result = await session.execute(
        select(Role).where(Role.id == role_id, Role.organization_id == org_id)
    )
    role = result.scalar_one_or_none()

    if not role:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Role not found"
        )

    # Hard delete
    await session.delete(role)
    await session.commit()
