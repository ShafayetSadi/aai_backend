"""
Job CRUD operations router.
"""

from __future__ import annotations

from typing import Optional
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import func, and_, select

from src.core.db import get_session
from src.core.security import get_current_user
from src.models.user import User
from src.models.profile import Job
from src.schemas.job import (
    JobCreate,
    JobUpdate,
    JobResponse,
    JobListResponse,
)

router = APIRouter(prefix="/jobs", tags=["jobs"])


@router.get("/", response_model=JobListResponse)
async def get_jobs(
    page: int = Query(1, ge=1, description="Page number"),
    size: int = Query(10, ge=1, le=100, description="Page size"),
    profile_id: Optional[UUID] = Query(None, description="Filter by profile ID"),
    company: Optional[str] = Query(None, description="Filter by company"),
    industry: Optional[str] = Query(None, description="Filter by industry"),
    session: AsyncSession = Depends(get_session),
    current_user: User = Depends(get_current_user),
) -> JobListResponse:
    """Get paginated list of jobs with optional filtering."""

    # Build query
    query = select(Job)
    count_query = select(func.count(Job.id))

    # Apply filters
    filters = []
    if profile_id:
        filters.append(Job.profile_id == profile_id)

    if company:
        filters.append(Job.company.ilike(f"%{company}%"))

    if industry:
        filters.append(Job.industry.ilike(f"%{industry}%"))

    if filters:
        query = query.where(and_(*filters))
        count_query = count_query.where(and_(*filters))

    # Get total count
    total_result = await session.execute(count_query)
    total = total_result.scalar()

    # Apply pagination
    offset = (page - 1) * size
    query = query.offset(offset).limit(size).order_by(Job.created_at.desc())

    # Execute query
    result = await session.execute(query)
    jobs = result.scalars().all()

    # Calculate pages
    pages = (total + size - 1) // size

    return JobListResponse(
        jobs=[JobResponse.model_validate(job) for job in jobs],
        total=total,
        page=page,
        size=size,
        pages=pages,
    )


@router.get("/{job_id}", response_model=JobResponse)
async def get_job(
    job_id: UUID,
    session: AsyncSession = Depends(get_session),
    current_user: User = Depends(get_current_user),
) -> JobResponse:
    """Get a specific job by ID."""

    result = await session.execute(select(Job).where(Job.id == job_id))
    job = result.scalar_one_or_none()

    if not job:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Job not found"
        )

    return JobResponse.model_validate(job)


@router.post("/", response_model=JobResponse, status_code=status.HTTP_201_CREATED)
async def create_job(
    job_data: JobCreate,
    session: AsyncSession = Depends(get_session),
    current_user: User = Depends(get_current_user),
) -> JobResponse:
    """Create a new job."""

    # Create new job
    job = Job(
        profile_id=job_data.profile_id,
        title=job_data.title,
        company=job_data.company,
        industry=job_data.industry,
        start_date=job_data.start_date,
        end_date=job_data.end_date,
    )

    session.add(job)
    await session.commit()
    await session.refresh(job)

    return JobResponse.model_validate(job)


@router.put("/{job_id}", response_model=JobResponse)
async def update_job(
    job_id: UUID,
    job_data: JobUpdate,
    session: AsyncSession = Depends(get_session),
    current_user: User = Depends(get_current_user),
) -> JobResponse:
    """Update a job."""

    # Get existing job
    result = await session.execute(select(Job).where(Job.id == job_id))
    job = result.scalar_one_or_none()

    if not job:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Job not found"
        )

    # Update job fields
    update_data = job_data.model_dump(exclude_unset=True)

    for field, value in update_data.items():
        setattr(job, field, value)

    await session.commit()
    await session.refresh(job)

    return JobResponse.model_validate(job)


@router.delete("/{job_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_job(
    job_id: UUID,
    session: AsyncSession = Depends(get_session),
    current_user: User = Depends(get_current_user),
):
    """Delete a job."""

    # Get existing job
    result = await session.execute(select(Job).where(Job.id == job_id))
    job = result.scalar_one_or_none()

    if not job:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Job not found"
        )

    await session.delete(job)
    await session.commit()
