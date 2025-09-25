# flake8: noqa
# Routers package
from .auth_router import router as auth_router
from .availability_router import router as availability_router
from .assignments_router import router as assignments_router
from .business_hours_router import router as business_hours_router
from .me_router import router as me_router
from .organizations_router import router as organizations_router
from .profiles_router import router as profiles_router
from .requirements_router import router as requirements_router
from .roles_router import router as roles_router
from .schedules_router import router as schedules_router
from .shifts_router import router as shifts_router
from .users_router import router as users_router

__all__ = [
    "auth_router",
    "availability_router",
    "assignments_router",
    "business_hours_router",
    "me_router",
    "organizations_router",
    "profiles_router",
    "requirements_router",
    "roles_router",
    "schedules_router",
    "shifts_router",
    "users_router",
]
