from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from datetime import datetime

from src.core.config import settings
from src.core.db import lifespan, check_db_connection


def create_app() -> FastAPI:
    """Create and configure the FastAPI application."""
    app = FastAPI(
        title=settings.APP_NAME,
        description="FastAPI backend for AAI",
        version="0.1.0",
        docs_url="/docs" if settings.ENVIRONMENT == "development" else None,
        redoc_url="/redoc" if settings.ENVIRONMENT == "development" else None,
        openapi_url="/openapi.json" if settings.ENVIRONMENT == "development" else None,
        lifespan=lifespan,
    )

    app.add_middleware(
        CORSMiddleware,
        allow_origins=[str(origin) for origin in settings.CORS_ORIGINS],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    from src.router_setup import setup_routers

    setup_routers(app)

    return app


app = create_app()


@app.get("/")
async def root() -> dict[str, str]:
    """Root endpoint returning basic API information."""
    return {
        "message": f"Welcome to {settings.APP_NAME}",
        "version": "0.1.0",
        "environment": settings.ENVIRONMENT,
        "docs_url": "/docs"
        if settings.ENVIRONMENT == "development"
        else "Disabled in production",
    }


@app.get("/health")
async def health() -> dict:
    """Health check endpoint that verifies application and database status."""
    app_status = "ok"

    try:
        db_healthy = await check_db_connection()
        db_status = "ok" if db_healthy else "error"
    except Exception as e:
        print(e)
        db_status = "error"

    overall_status = "ok" if app_status == "ok" and db_status == "ok" else "error"

    response = {
        "status": overall_status,
        "timestamp": datetime.now().isoformat(),
        "services": {"application": app_status, "database": db_status},
    }

    return response
