from __future__ import annotations

from typing import Callable
from uuid import UUID

from fastapi import Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from src.core.db import get_session
from src.core.security import get_current_user
from src.models.membership import OrganizationMembership, MembershipRole
from src.models.user import User


ROLE_RANK = {
	MembershipRole.staff: 1,
	MembershipRole.manager: 2,
	MembershipRole.owner: 3,
}


def require_role(required_role: MembershipRole) -> Callable[[UUID, User, AsyncSession], User]:
	async def _checker(
		org_id: UUID,
		user: User = Depends(get_current_user),
		session: AsyncSession = Depends(get_session),
	) -> User:
		# super admins bypass
		if user.is_super_admin:
			return user
		result = await session.execute(
			select(OrganizationMembership).where(
				OrganizationMembership.organization_id == org_id,
				OrganizationMembership.user_id == user.id,
				OrganizationMembership.is_active.is_(True),
			)
		)
		member = result.scalar_one_or_none()
		if member is None:
			raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not a member of organization")
		if ROLE_RANK[member.role] < ROLE_RANK[required_role]:
			raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Insufficient role")
		return user

	return _checker
