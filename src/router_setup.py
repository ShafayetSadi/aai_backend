"""
Router setup and configuration for the FastAPI application.
"""

from fastapi import FastAPI
from src.routers.auth_router import router as auth_router
from src.routers.organizations_router import router as organizations_router
from src.routers.staff_router import router as staff_router
from src.routers.users_router import router as users_router
from src.routers.profiles_router import router as profiles_router
from src.routers.locations_router import router as locations_router
from src.routers.contacts_router import router as contacts_router
from src.routers.jobs_router import router as jobs_router


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
    app.include_router(staff_router, prefix=api_prefix)
    app.include_router(users_router, prefix=api_prefix)
    app.include_router(profiles_router, prefix=api_prefix)
    app.include_router(locations_router, prefix=api_prefix)
    app.include_router(contacts_router, prefix=api_prefix)
    app.include_router(jobs_router, prefix=api_prefix)
