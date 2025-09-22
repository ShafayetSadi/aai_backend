from __future__ import annotations

from contextlib import asynccontextmanager
from typing import AsyncIterator
from datetime import datetime, timezone

from fastapi import FastAPI
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlmodel import SQLModel

from src.core.config import settings
from src.core.logging import get_logger
from src.models import *  # noqa: F403, F401

engine = create_async_engine(
    settings.DATABASE_URL,
    echo=False,
    future=True,
    pool_pre_ping=True,  # Verify connections before use
    pool_recycle=3600,  # Recycle connections every hour
)
SessionLocal = async_sessionmaker(
    bind=engine, class_=AsyncSession, expire_on_commit=False
)


async def check_db_connection() -> bool:
    """Check if database connection is healthy."""
    try:
        async with engine.begin() as conn:
            await conn.execute(text("SELECT 1"))
        return True
    except Exception:
        return False


async def init_db() -> None:
    """Initialize the database with proper error handling."""
    logger = get_logger(__name__)

    try:
        logger.info("Initializing database...")

        if not await check_db_connection():
            raise ConnectionError("Cannot connect to database")

        # Create tables
        async with engine.begin() as conn:
            await conn.run_sync(SQLModel.metadata.create_all)
        logger.info("Database tables created/verified successfully")
    except Exception as e:
        logger.error("Database initialization failed", error=str(e))
        raise


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:
    """Lifespan for the application with proper startup and shutdown handling."""
    logger = get_logger(__name__)
    startup_time = datetime.now(timezone.utc)

    # Startup
    try:
        logger.info(
            "Starting up AAI Backend application...",
            startup_time=startup_time.isoformat(),
        )

        # Initialize database
        await init_db()

        # Log successful startup
        startup_duration = (datetime.now(timezone.utc) - startup_time).total_seconds()
        logger.info(
            "Application startup completed successfully",
            startup_duration=f"{startup_duration:.2f} seconds",
        )
    except Exception as e:
        logger.error("CRITICAL: Application startup failed!", error=str(e))
        raise

    # Application is running
    try:
        yield
    finally:
        # Shutdown
        shutdown_time = datetime.now(timezone.utc)
        try:
            logger.info(
                "Shutting down application...", shutdown_time=shutdown_time.isoformat()
            )

            # Close database connections gracefully
            await engine.dispose()

            shutdown_duration = (
                datetime.now(timezone.utc) - shutdown_time
            ).total_seconds()
            logger.info(
                "Application shutdown completed successfully",
                shutdown_duration=f"{shutdown_duration:.2f} seconds",
            )

        except Exception as e:
            logger.error("Error during application shutdown!", error=str(e))


async def get_session() -> AsyncIterator[AsyncSession]:
    """Get a session for the database."""
    async with SessionLocal() as session:
        yield session
