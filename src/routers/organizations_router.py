from __future__ import annotations

from typing import List
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Path, status, Response
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from src.core.db import get_session
from src.core.security import get_current_user
from src.dependencies.roles import require_role
from src.models.organization import Organization
from src.models.membership import OrganizationMembership, MembershipRole
from src.models.user import User


router = APIRouter(prefix="/organizations", tags=["organizations"])


class OrganizationCreate(BaseModel):
	name: str
	category: str | None = None
	subcategory: str | None = None


class OrganizationResponse(BaseModel):
	id: UUID
	name: str
	category: str | None = None
	subcategory: str | None = None


@router.post("", response_model=OrganizationResponse)
async def create_organization(
	payload: OrganizationCreate,
	user: User = Depends(get_current_user),
	session: AsyncSession = Depends(get_session),
) -> OrganizationResponse:
	org = Organization(
		name=payload.name,
		category=payload.category,
		subcategory=payload.subcategory,
		owner_user_id=user.id,
	)
	session.add(org)
	await session.flush()
	# owner membership
	membership = OrganizationMembership(
		organization_id=org.id, user_id=user.id, role=MembershipRole.owner, is_active=True
	)
	session.add(membership)
	await session.commit()
	await session.refresh(org)
	return OrganizationResponse(id=org.id, name=org.name, category=org.category, subcategory=org.subcategory)


class InviteRequest(BaseModel):
	user_id: UUID
	role: MembershipRole


@router.post("/{org_id}/invite", status_code=204, response_model=None)
async def invite_member(
	payload: InviteRequest,
	org_id: UUID = Path(...),
	_: User = Depends(require_role(MembershipRole.manager)),
	session: AsyncSession = Depends(get_session),
) -> Response:
	# ensure not duplicate
	existing = await session.execute(
		select(OrganizationMembership).where(
			OrganizationMembership.organization_id == org_id,
			OrganizationMembership.user_id == payload.user_id,
		)
	)
	if existing.scalar_one_or_none() is not None:
		raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Already a member")
	member = OrganizationMembership(
		organization_id=org_id, user_id=payload.user_id, role=payload.role, is_active=True
	)
	session.add(member)
	await session.commit()
	return Response(status_code=204)


class MemberResponse(BaseModel):
	id: UUID
	user_id: UUID
	role: MembershipRole
	is_active: bool


@router.get("/{org_id}/members", response_model=List[MemberResponse])
async def list_members(
	org_id: UUID,
	_: User = Depends(require_role(MembershipRole.manager)),
	session: AsyncSession = Depends(get_session),
) -> List[MemberResponse]:
	res = await session.execute(
		select(OrganizationMembership).where(OrganizationMembership.organization_id == org_id)
	)
	members = [
		MemberResponse(id=m.id, user_id=m.user_id, role=m.role, is_active=m.is_active)
		for m in res.scalars().all()
	]
	return members
