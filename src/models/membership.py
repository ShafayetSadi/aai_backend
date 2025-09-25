from __future__ import annotations

from uuid import UUID
from typing import TYPE_CHECKING, List

from sqlmodel import Field, Relationship, UniqueConstraint
from sqlalchemy.orm import relationship
from sqlalchemy import Index
from src.models.base import (
    BaseModel,
    MembershipRole,
    MembershipRequestType,
    MembershipRequestStatus,
)

if TYPE_CHECKING:
    from .role import Role

if TYPE_CHECKING:
    from .user import User
    from .organization import Organization


class OrganizationMembership(BaseModel, table=True):
    __tablename__ = "organization_members"

    organization_id: UUID = Field(foreign_key="organizations.id", index=True)
    user_id: UUID = Field(foreign_key="users.id", index=True)

    role: MembershipRole = Field(default=MembershipRole.staff)

    user: "User" = Relationship(
        sa_relationship=relationship(
            "User",
            back_populates="organization_memberships",
            foreign_keys="OrganizationMembership.user_id",
        )
    )
    organization: "Organization" = Relationship(
        sa_relationship=relationship(
            "Organization",
            back_populates="memberships",
            foreign_keys="OrganizationMembership.organization_id",
        )
    )

    role_assignments: List["MembershipRoleAssignment"] = Relationship(
        sa_relationship=relationship(
            "MembershipRoleAssignment",
            back_populates="membership",
            cascade="all, delete-orphan",
            foreign_keys="MembershipRoleAssignment.membership_id",
        )
    )

    __table_args__ = (
        UniqueConstraint("organization_id", "user_id", name="uq_org_membership_user"),
        Index("idx_membership_org", "organization_id"),
        Index("idx_membership_user", "user_id"),
        Index("idx_membership_role", "role"),
    )


class MembershipRoleAssignment(BaseModel, table=True):
    """Assignment of a business Role to an organization membership.

    One (and only one) assignment per membership should have is_primary=True.
    Additional roles have is_primary=False.
    """
    __tablename__ = "membership_role_assignments"

    membership_id: UUID = Field(foreign_key="organization_members.id", index=True)
    role_id: UUID = Field(foreign_key="roles.id", index=True)
    is_primary: bool = Field(default=False, index=True)

    membership: "OrganizationMembership" = Relationship(
        sa_relationship=relationship(
            "OrganizationMembership",
            back_populates="role_assignments",
            foreign_keys="MembershipRoleAssignment.membership_id",
        )
    )
    role: "Role" = Relationship(
        sa_relationship=relationship(
            "Role", foreign_keys="MembershipRoleAssignment.role_id"
        )
    )

    __table_args__ = (
        UniqueConstraint("membership_id", "role_id", name="uq_membership_role"),
        Index("idx_membership_role_assign_primary", "membership_id", "is_primary"),
    )


class MembershipRequest(BaseModel, table=True):
    """Represents an invitation or a user-initiated join request."""

    __tablename__ = "membership_requests"

    organization_id: UUID = Field(foreign_key="organizations.id", index=True)
    user_id: UUID = Field(foreign_key="users.id", index=True)
    type: MembershipRequestType = Field(
        default=MembershipRequestType.Request, index=True
    )
    status: MembershipRequestStatus = Field(
        default=MembershipRequestStatus.Pending, index=True
    )
    invited_by_user_id: UUID | None = Field(
        foreign_key="users.id", default=None, index=True
    )
    role: MembershipRole | None = Field(default=None)  # proposed permission role
    primary_role_id: UUID | None = Field(foreign_key="roles.id", default=None)

    __table_args__ = (
        UniqueConstraint(
            "organization_id",
            "user_id",
            "status",
            name="uq_active_membership_request",
        ),
        Index("idx_membership_request_org", "organization_id"),
        Index("idx_membership_request_user", "user_id"),
    )
