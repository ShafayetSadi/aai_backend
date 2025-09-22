from __future__ import annotations

from fastapi import APIRouter, Depends, Response
from pydantic import BaseModel

from src.core.security import get_current_user
from src.models.user import User


router = APIRouter(prefix="/staff", tags=["staff"])


class ScheduleItem(BaseModel):
	day: str
	start: str
	end: str


@router.get("/me/schedule", response_model=list[ScheduleItem])
async def my_schedule(user: User = Depends(get_current_user)) -> list[ScheduleItem]:
	# Placeholder response; in real app, fetch from DB with role check
	return []


class AvailabilityRequest(BaseModel):
	day: str
	available: bool


@router.post("/me/availability", status_code=204, response_model=None)
async def update_availability(payload: AvailabilityRequest, user: User = Depends(get_current_user)) -> Response:
	# Placeholder for updating availability
	return Response(status_code=204)
