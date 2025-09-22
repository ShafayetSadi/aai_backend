from __future__ import annotations

from contextlib import asynccontextmanager
from typing import AsyncIterator

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlmodel import SQLModel

from .config import settings


engine = create_async_engine(settings.database_url, echo=False, future=True)
SessionLocal = async_sessionmaker(bind=engine, class_=AsyncSession, expire_on_commit=False)


async def init_db() -> None:
	# Import models so SQLModel metadata is populated
	from src import models  # noqa: F401
	async with engine.begin() as conn:
		await conn.run_sync(SQLModel.metadata.create_all)


@asynccontextmanager
async def lifespan(app):
	# Place for startup/shutdown tasks if needed
	yield


async def get_session() -> AsyncIterator[AsyncSession]:
	async with SessionLocal() as session:
		yield session
