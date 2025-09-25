"""
Router setup and configuration for the FastAPI application.
"""

from fastapi import FastAPI
from src.routers.auth_router import router as auth_router
from src.routers.organizations_router import router as organizations_router
from src.routers.me_router import router as me_router
from src.routers.users_router import router as users_router
from src.routers.profiles_router import router as profiles_router

# Scheduling routers
from src.routers.roles_router import router as roles_router
from src.routers.shifts_router import router as shifts_router
from src.routers.availability_router import router as availability_router
from src.routers.requirements_router import router as requirements_router
from src.routers.schedules_router import router as schedules_router


def setup_routers(app: FastAPI) -> None:
    """
    Configure all application routers.

    Args:
        app: FastAPI application instance
    """

    # API v1 routers
    api_prefix = "/api/v1"

    app.include_router(auth_router, prefix=api_prefix)
    app.include_router(organizations_router, prefix=api_prefix)
    app.include_router(me_router, prefix=api_prefix)
    app.include_router(users_router, prefix=api_prefix)
    app.include_router(profiles_router, prefix=api_prefix)

    # Scheduling routers
    app.include_router(roles_router, prefix=api_prefix)
    app.include_router(shifts_router, prefix=api_prefix)
    app.include_router(availability_router, prefix=api_prefix)
    app.include_router(requirements_router, prefix=api_prefix)
    app.include_router(schedules_router, prefix=api_prefix)
