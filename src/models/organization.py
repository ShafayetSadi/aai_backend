from __future__ import annotations

from datetime import datetime
from typing import Optional
from uuid import UUID, uuid4

from sqlmodel import SQLModel, Field
from sqlalchemy import Column, String


class Organization(SQLModel, table=True):
	__tablename__ = "organizations"

	id: UUID = Field(default_factory=uuid4, primary_key=True, index=True)
	name: str = Field(sa_column=Column(String(255), nullable=False))
	category: Optional[str] = Field(default=None, sa_column=Column(String(255), nullable=True))
	subcategory: Optional[str] = Field(default=None, sa_column=Column(String(255), nullable=True))
	owner_user_id: UUID = Field(foreign_key="users.id", nullable=False, index=True)
	created_at: datetime = Field(default_factory=datetime.utcnow, nullable=False)
	updated_at: datetime = Field(default_factory=datetime.utcnow, nullable=False)
