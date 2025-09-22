from __future__ import annotations

from contextlib import asynccontextmanager
from typing import AsyncIterator

from fastapi import FastAPI
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlmodel import SQLModel

from .config import settings
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
    import logging

    logger = logging.getLogger(__name__)

    try:
        logger.info("Initializing database...")

        if not await check_db_connection():
            raise ConnectionError("Cannot connect to database")

        # Create tables
        async with engine.begin() as conn:
            await conn.run_sync(SQLModel.metadata.create_all)
        logger.info("Database tables created/verified successfully")
    except Exception as e:
        logger.error(f"Database initialization failed: {e}")
        raise


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:
    """Lifespan for the application with proper startup and shutdown handling."""
    import logging
    from datetime import datetime

    logger = logging.getLogger(__name__)
    startup_time = datetime.now()

    # Startup
    try:
        logger.info("=" * 50)
        logger.info("Starting up AAI Backend application...")
        logger.info(f"Startup time: {startup_time.isoformat()}")
        logger.info("=" * 50)

        # Initialize database
        await init_db()

        # Log successful startup
        startup_duration = (datetime.now() - startup_time).total_seconds()
        logger.info("=" * 50)
        logger.info("Application startup completed successfully")
        logger.info(f"Startup duration: {startup_duration:.2f} seconds")
        logger.info("=" * 50)

    except Exception as e:
        logger.error("=" * 50)
        logger.error("CRITICAL: Application startup failed!")
        logger.error(f"Error: {e}")
        logger.error("=" * 50)
        raise

    # Application is running
    try:
        yield
    finally:
        # Shutdown
        shutdown_time = datetime.now()
        try:
            logger.info("=" * 50)
            logger.info("Shutting down application...")
            logger.info(f"Shutdown time: {shutdown_time.isoformat()}")
            logger.info("=" * 50)

            # Close database connections gracefully
            await engine.dispose()

            shutdown_duration = (datetime.now() - shutdown_time).total_seconds()
            logger.info("=" * 50)
            logger.info("Application shutdown completed successfully")
            logger.info(f"Shutdown duration: {shutdown_duration:.2f} seconds")
            logger.info("=" * 50)

        except Exception as e:
            logger.error("=" * 50)
            logger.error("Error during application shutdown!")
            logger.error(f"Error: {e}")
            logger.error("=" * 50)


async def get_session() -> AsyncIterator[AsyncSession]:
    """Get a session for the database."""
    async with SessionLocal() as session:
        yield session
