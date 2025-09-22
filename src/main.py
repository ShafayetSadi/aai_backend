from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from src.core.config import settings
from src.core.db import lifespan
from src.routers.auth_router import router as auth_router
from src.routers.organizations_router import router as orgs_router
from src.routers.staff_router import router as staff_router


app = FastAPI(title=settings.app_name, lifespan=lifespan)

# CORS
origins = settings.cors_origins if settings.cors_origins else ["*"]
app.add_middleware(
	CORSMiddleware,
	allow_origins=origins,
	allow_credentials=True,
	allow_methods=["*"],
	allow_headers=["*"],
)

app.include_router(auth_router)
app.include_router(orgs_router)
app.include_router(staff_router)


@app.get("/")
async def root() -> dict[str, str]:
	return {"app": settings.app_name}


@app.get("/health")
async def health() -> dict[str, str]:
	return {"status": "ok"}
