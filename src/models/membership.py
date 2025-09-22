from __future__ import annotations

from datetime import datetime
from enum import Enum
from uuid import UUID, uuid4

from sqlmodel import SQLModel, Field


class MembershipRole(str, Enum):
	owner = "owner"
	manager = "manager"
	staff = "staff"


class OrganizationMembership(SQLModel, table=True):
	__tablename__ = "organization_members"

	id: UUID = Field(default_factory=uuid4, primary_key=True, index=True)
	organization_id: UUID = Field(foreign_key="organizations.id", nullable=False, index=True)
	user_id: UUID = Field(foreign_key="users.id", nullable=False, index=True)
	role: MembershipRole = Field(default=MembershipRole.staff, nullable=False)
	is_active: bool = Field(default=True, nullable=False)
	created_at: datetime = Field(default_factory=datetime.utcnow, nullable=False)
	updated_at: datetime = Field(default_factory=datetime.utcnow, nullable=False)
