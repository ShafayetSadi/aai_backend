from __future__ import annotations

from datetime import datetime
from typing import Optional
from uuid import UUID, uuid4

from sqlmodel import SQLModel, Field
from sqlalchemy import text


class BaseModel(SQLModel):
    """
    Abstract base class with common fields for all models.
    """

    id: UUID = Field(
        default_factory=uuid4, primary_key=True, index=True, nullable=False
    )
    is_active: bool = Field(default=True, nullable=False)
    created_at: datetime = Field(
        default_factory=datetime.utcnow,
        nullable=False,
        sa_column_kwargs={"server_default": text("now()")},
    )
    updated_at: datetime = Field(
        default_factory=datetime.utcnow,
        nullable=False,
        sa_column_kwargs={"server_default": text("now()")},
    )
    deactivated_at: Optional[datetime] = Field(default=None, nullable=True)

    class Config:
        arbitrary_types_allowed = True
        validate_assignment = True
