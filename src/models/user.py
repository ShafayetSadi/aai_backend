from __future__ import annotations

from datetime import datetime
from typing import Optional
from uuid import uuid4, UUID

from sqlmodel import SQLModel, Field
from sqlalchemy import Column, String


class User(SQLModel, table=True):
	__tablename__ = "users"

	id: UUID = Field(default_factory=uuid4, primary_key=True, index=True)
	username: str = Field(sa_column=Column(String(150), unique=True, index=True, nullable=False))
	email: str = Field(sa_column=Column(String(320), unique=True, index=True, nullable=False))
	password_hash: str = Field(sa_column=Column(String(255), nullable=False))
	is_active: bool = Field(default=True, nullable=False)
	is_super_admin: bool = Field(default=False, nullable=False)
	created_at: datetime = Field(default_factory=datetime.utcnow, nullable=False)
	updated_at: datetime = Field(default_factory=datetime.utcnow, nullable=False)

	# relationships (optional backrefs set in other models)
