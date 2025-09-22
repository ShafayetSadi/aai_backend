from __future__ import annotations

from datetime import datetime
from typing import Optional
from sqlmodel import Field
from sqlalchemy import Column, String

from src.models.base import BaseModel


class User(BaseModel, table=True):
    __tablename__ = "users"

    username: str = Field(
        sa_column=Column(String(150), unique=True, index=True, nullable=False)
    )
    email: str = Field(
        sa_column=Column(String(320), unique=True, index=True, nullable=False)
    )
    password_hash: str = Field(sa_column=Column(String(255), nullable=False))
    is_super_admin: bool = Field(default=False, nullable=False)
    last_login_at: Optional[datetime] = Field(default=None, nullable=True)
