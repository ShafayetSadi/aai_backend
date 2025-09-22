from __future__ import annotations

from sqlalchemy.orm import DeclarativeBase
from sqlmodel import SQLModel


class Base(DeclarativeBase):
    metadata = SQLModel.metadata
