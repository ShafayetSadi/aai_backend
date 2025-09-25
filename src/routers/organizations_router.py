from __future__ import annotations

from typing import List
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Path, Query, status
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from src.core.db import get_session
from src.core.security import get_current_user
from src.dependencies.roles import require_role
from src.models.organization import Organization
from src.models.membership import (
    OrganizationMembership,
    MembershipRole,
    MembershipRoleAssignment,
    MembershipRequest,
)
from src.models.role import Role
from src.models.user import User
from src.schemas.organization import (
    OrganizationCreate,
    OrganizationUpdate,
    OrganizationResponse,
    OrganizationWithRole,
    OrganizationListResponse,
    InviteRequest,
)
from src.models.base import (
    MembershipRequestType,
    MembershipRequestStatus,
)


router = APIRouter(prefix="/organizations", tags=["organizations"])


@router.post("", response_model=OrganizationResponse)
async def create_organization(
    payload: OrganizationCreate,
    user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
) -> OrganizationResponse:
    # Check if slug is already taken
    if payload.slug:
        existing = await session.execute(
            select(Organization).where(Organization.slug == payload.slug)
        )
        if existing.scalar_one_or_none() is not None:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Organization with this slug already exists",
            )

    slug = payload.slug or Organization.generate_slug(payload.name)

    counter = 1
    original_slug = slug
    while True:
        existing = await session.execute(
            select(Organization).where(Organization.slug == slug)
        )
        if existing.scalar_one_or_none() is None:
            break
        slug = f"{original_slug}-{counter}"
        counter += 1

    org = Organization(
        name=payload.name,
        slug=slug,
        category=payload.category,
        subcategory=payload.subcategory,
        owner_user_id=user.id,
    )
    session.add(org)
    await session.flush()
    # owner membership
    membership = OrganizationMembership(
        organization_id=org.id,
        user_id=user.id,
        role=MembershipRole.owner,
    )
    session.add(membership)
    await session.commit()
    await session.refresh(org)
    return OrganizationResponse(
        id=org.id,
        name=org.name,
        slug=org.slug,
        category=org.category,
        subcategory=org.subcategory,
        owner_user_id=org.owner_user_id,
        created_at=org.created_at,
        updated_at=org.updated_at,
    )


@router.get("", response_model=OrganizationListResponse)
async def list_organizations(
    page: int = Query(1, ge=1, description="Page number"),
    size: int = Query(10, ge=1, le=100, description="Page size"),
    search: str | None = Query(None, description="Search by organization name or slug"),
    user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
) -> OrganizationListResponse:
    """List organizations where the user is a member."""

    # Build query to get organizations where user is a member
    query = (
        select(Organization, OrganizationMembership)
        .join(
            OrganizationMembership,
            Organization.id == OrganizationMembership.organization_id,
        )
        .where(OrganizationMembership.user_id == user.id)
    )

    # Apply search filter if provided
    if search:
        query = query.where(
            Organization.name.ilike(f"%{search}%")
            | Organization.slug.ilike(f"%{search}%")
        )

    # Get total count
    count_query = (
        select(Organization.id)
        .join(
            OrganizationMembership,
            Organization.id == OrganizationMembership.organization_id,
        )
        .where(OrganizationMembership.user_id == user.id)
    )
    if search:
        count_query = count_query.where(
            Organization.name.ilike(f"%{search}%")
            | Organization.slug.ilike(f"%{search}%")
        )

    total_result = await session.execute(count_query)
    total = len(total_result.scalars().all())

    # Calculate pagination
    pages = (total + size - 1) // size
    offset = (page - 1) * size
    query = query.offset(offset).limit(size).order_by(Organization.name)

    # Execute query
    result = await session.execute(query)
    rows = result.all()

    # Build response
    organizations = []
    for org, membership in rows:
        is_owner = org.owner_user_id == user.id
        organizations.append(
            OrganizationWithRole(
                id=org.id,
                name=org.name,
                slug=org.slug,
                category=org.category,
                subcategory=org.subcategory,
                owner_user_id=org.owner_user_id,
                created_at=org.created_at,
                updated_at=org.updated_at,
                role=membership.role.value,
                is_owner=is_owner,
            )
        )

    return OrganizationListResponse(
        organizations=organizations, total=total, page=page, size=size, pages=pages
    )


@router.get("/{org_id}", response_model=OrganizationResponse)
async def get_organization(
    org_id: UUID = Path(..., description="Organization ID"),
    user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
) -> OrganizationResponse:
    """Get organization by ID."""
    # Check if user is a member of the organization
    membership = await session.execute(
        select(OrganizationMembership).where(
            OrganizationMembership.organization_id == org_id,
            OrganizationMembership.user_id == user.id,
        )
    )
    if not membership.scalar_one_or_none():
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Organization not found or you don't have access",
        )

    org = await session.execute(select(Organization).where(Organization.id == org_id))
    org = org.scalar_one_or_none()
    if not org:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Organization not found"
        )

    return OrganizationResponse(
        id=org.id,
        name=org.name,
        slug=org.slug,
        category=org.category,
        subcategory=org.subcategory,
        owner_user_id=org.owner_user_id,
        created_at=org.created_at,
        updated_at=org.updated_at,
        deactivated_at=org.deactivated_at,
    )


@router.get("/slug/{slug}", response_model=OrganizationResponse)
async def get_organization_by_slug(
    slug: str = Path(..., description="Organization slug"),
    user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
) -> OrganizationResponse:
    """Get organization by slug."""
    # Check if user is a member of the organization
    membership = await session.execute(
        select(OrganizationMembership, Organization)
        .join(Organization, OrganizationMembership.organization_id == Organization.id)
        .where(Organization.slug == slug, OrganizationMembership.user_id == user.id)
    )
    membership_result = membership.first()
    if not membership_result:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Organization not found or you don't have access",
        )

    _, org = membership_result
    return OrganizationResponse(
        id=org.id,
        name=org.name,
        slug=org.slug,
        category=org.category,
        subcategory=org.subcategory,
        owner_user_id=org.owner_user_id,
        created_at=org.created_at,
        updated_at=org.updated_at,
        deactivated_at=org.deactivated_at,
    )


@router.put("/{org_id}", response_model=OrganizationResponse)
async def update_organization(
    payload: OrganizationUpdate,
    org_id: UUID = Path(..., description="Organization ID"),
    user: User = Depends(require_role(MembershipRole.manager)),
    session: AsyncSession = Depends(get_session),
) -> OrganizationResponse:
    """Update organization."""
    org = await session.execute(select(Organization).where(Organization.id == org_id))
    org = org.scalar_one_or_none()
    if not org:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Organization not found"
        )

    # Check slug uniqueness if slug is being updated
    if payload.slug and payload.slug != org.slug:
        existing = await session.execute(
            select(Organization).where(Organization.slug == payload.slug)
        )
        if existing.scalar_one_or_none() is not None:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Organization with this slug already exists",
            )

    # Update fields
    update_data = payload.dict(exclude_unset=True)
    for field, value in update_data.items():
        setattr(org, field, value)

    await session.commit()
    await session.refresh(org)

    return OrganizationResponse(
        id=org.id,
        name=org.name,
        slug=org.slug,
        category=org.category,
        subcategory=org.subcategory,
        owner_user_id=org.owner_user_id,
        created_at=org.created_at,
        updated_at=org.updated_at,
        deactivated_at=org.deactivated_at,
    )


@router.post("/{org_id}/invite", status_code=204)
async def invite_member(
    payload: InviteRequest,
    org_id: UUID = Path(...),
    _: User = Depends(require_role(MembershipRole.manager)),
    session: AsyncSession = Depends(get_session),
):
    # ensure not duplicate
    existing = await session.execute(
        select(OrganizationMembership).where(
            OrganizationMembership.organization_id == org_id,
            OrganizationMembership.user_id == payload.user_id,
        )
    )
    if existing.scalar_one_or_none() is not None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="Already a member"
        )
    # Validate primary role exists in org
    primary_role_result = await session.execute(
        select(Role).where(
            Role.id == payload.primary_role_id, Role.organization_id == org_id
        )
    )
    primary_role = primary_role_result.scalar_one_or_none()
    if primary_role is None:
        raise HTTPException(
            status_code=404, detail="Primary role not found in organization"
        )

    # Validate other roles (if any)
    other_roles: list[Role] = []
    if payload.other_role_ids:
        if payload.primary_role_id in payload.other_role_ids:
            raise HTTPException(
                status_code=400, detail="Primary role cannot appear in other_role_ids"
            )
        other_roles_result = await session.execute(
            select(Role).where(
                Role.id.in_(payload.other_role_ids), Role.organization_id == org_id
            )
        )
        other_roles = other_roles_result.scalars().all()
        missing = set(payload.other_role_ids) - {r.id for r in other_roles}
        if missing:
            raise HTTPException(
                status_code=404, detail=f"Some other roles not found: {missing}"
            )

    # Create membership request of type Invite
    invite_req = MembershipRequest(
        organization_id=org_id,
        user_id=payload.user_id,
        type=MembershipRequestType.Invite,
        status=MembershipRequestStatus.Pending,
        invited_by_user_id=None,  # could set to manager's user id if passed via dependency
        role=payload.role,
        primary_role_id=primary_role.id,
    )
    session.add(invite_req)
    await session.commit()


class JoinRequest(BaseModel):
    primary_role_id: UUID
    role: MembershipRole | None = None  # proposed permission level (optional)


@router.post("/{org_id}/join", status_code=202)
async def request_to_join(
    org_id: UUID,
    payload: JoinRequest,
    user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
):
    # Already a member?
    existing_member = await session.execute(
        select(OrganizationMembership).where(
            OrganizationMembership.organization_id == org_id,
            OrganizationMembership.user_id == user.id,
        )
    )
    if existing_member.scalar_one_or_none():
        raise HTTPException(status_code=400, detail="Already a member")

    # Active pending request?
    pending = await session.execute(
        select(MembershipRequest).where(
            MembershipRequest.organization_id == org_id,
            MembershipRequest.user_id == user.id,
            MembershipRequest.status == MembershipRequestStatus.Pending,
        )
    )
    if pending.scalar_one_or_none():
        raise HTTPException(status_code=400, detail="Pending request already exists")

    # Validate primary role
    role_res = await session.execute(
        select(Role).where(Role.id == payload.primary_role_id, Role.organization_id == org_id)
    )
    primary_role = role_res.scalar_one_or_none()
    if primary_role is None:
        raise HTTPException(status_code=404, detail="Primary role not found in organization")

    req = MembershipRequest(
        organization_id=org_id,
        user_id=user.id,
        type=MembershipRequestType.Request,
        status=MembershipRequestStatus.Pending,
        primary_role_id=payload.primary_role_id,
        role=payload.role or MembershipRole.staff,
    )
    session.add(req)
    await session.commit()
    return {"request_id": str(req.id), "status": req.status}


@router.post("/{org_id}/requests/{request_id}/accept", status_code=201)
async def accept_membership_request(
    org_id: UUID,
    request_id: UUID,
    _: User = Depends(require_role(MembershipRole.manager)),
    session: AsyncSession = Depends(get_session),
):
    req_res = await session.execute(
        select(MembershipRequest).where(
            MembershipRequest.id == request_id,
            MembershipRequest.organization_id == org_id,
        )
    )
    req = req_res.scalar_one_or_none()
    if req is None:
        raise HTTPException(status_code=404, detail="Request not found")
    if req.status != MembershipRequestStatus.Pending:
        raise HTTPException(status_code=400, detail="Request not pending")

    # Create membership if not exists
    existing_member = await session.execute(
        select(OrganizationMembership).where(
            OrganizationMembership.organization_id == org_id,
            OrganizationMembership.user_id == req.user_id,
        )
    )
    if existing_member.scalar_one_or_none():
        raise HTTPException(status_code=400, detail="User already a member")

    membership = OrganizationMembership(
        organization_id=org_id,
        user_id=req.user_id,
        role=req.role or MembershipRole.staff,
    )
    session.add(membership)
    await session.flush()

    # Primary assignment
    if req.primary_role_id:
        session.add(
            MembershipRoleAssignment(
                membership_id=membership.id,
                role_id=req.primary_role_id,
                is_primary=True,
            )
        )

    req.status = MembershipRequestStatus.Accepted
    await session.commit()
    return {"membership_id": str(membership.id)}


@router.post("/{org_id}/requests/{request_id}/reject", status_code=200)
async def reject_membership_request(
    org_id: UUID,
    request_id: UUID,
    _: User = Depends(require_role(MembershipRole.manager)),
    session: AsyncSession = Depends(get_session),
):
    req_res = await session.execute(
        select(MembershipRequest).where(
            MembershipRequest.id == request_id,
            MembershipRequest.organization_id == org_id,
        )
    )
    req = req_res.scalar_one_or_none()
    if req is None:
        raise HTTPException(status_code=404, detail="Request not found")
    if req.status != MembershipRequestStatus.Pending:
        raise HTTPException(status_code=400, detail="Request not pending")
    req.status = MembershipRequestStatus.Rejected
    await session.commit()
    return {"request_id": str(req.id), "status": req.status}


class MemberResponse(BaseModel):
    id: UUID
    user_id: UUID
    role: MembershipRole  # permission role
    primary_role_id: UUID | None
    other_role_ids: list[UUID]


@router.get("/{org_id}/members", response_model=List[MemberResponse])
async def list_members(
    org_id: UUID,
    _: User = Depends(require_role(MembershipRole.manager)),
    session: AsyncSession = Depends(get_session),
) -> List[MemberResponse]:
    res = await session.execute(
        select(OrganizationMembership).where(
            OrganizationMembership.organization_id == org_id
        )
    )
    memberships = res.scalars().all()
    members: list[MemberResponse] = []
    for m in memberships:
        primary = None
        others: list[UUID] = []
        for a in m.role_assignments:
            if a.is_primary:
                primary = a.role_id
            else:
                others.append(a.role_id)
        members.append(
            MemberResponse(
                id=m.id,
                user_id=m.user_id,
                role=m.role,
                primary_role_id=primary,
                other_role_ids=others,
            )
        )
    return members
