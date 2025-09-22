"""
User CRUD operations router.
"""

from __future__ import annotations

from typing import Optional
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlmodel import select
from sqlalchemy import func, and_, or_

from src.core.db import get_session
from src.core.security import get_current_user, get_password_hash
from src.models.user import User
from src.schemas.user import (
    UserCreate,
    UserUpdate,
    UserResponse,
    UserListResponse,
)

router = APIRouter(prefix="/users", tags=["users"])


@router.get("/", response_model=UserListResponse)
async def get_users(
    page: int = Query(1, ge=1, description="Page number"),
    size: int = Query(10, ge=1, le=100, description="Page size"),
    search: Optional[str] = Query(None, description="Search by username or email"),
    is_active: Optional[bool] = Query(None, description="Filter by active status"),
    session: AsyncSession = Depends(get_session),
    current_user: User = Depends(get_current_user),
) -> UserListResponse:
    """Get paginated list of users with optional filtering."""

    # Build query
    query = select(User)
    count_query = select(func.count(User.id))

    # Apply filters
    filters = []
    if search:
        search_filter = or_(
            User.username.ilike(f"%{search}%"), User.email.ilike(f"%{search}%")
        )
        filters.append(search_filter)

    if is_active is not None:
        filters.append(User.is_active == is_active)

    if filters:
        query = query.where(and_(*filters))
        count_query = count_query.where(and_(*filters))

    # Get total count
    total_result = await session.execute(count_query)
    total = total_result.scalar()

    # Apply pagination
    offset = (page - 1) * size
    query = query.offset(offset).limit(size).order_by(User.created_at.desc())

    # Execute query
    result = await session.execute(query)
    users = result.scalars().all()

    # Calculate pages
    pages = (total + size - 1) // size

    return UserListResponse(
        users=[UserResponse.model_validate(user) for user in users],
        total=total,
        page=page,
        size=size,
        pages=pages,
    )


@router.get("/{user_id}", response_model=UserResponse)
async def get_user(
    user_id: UUID,
    session: AsyncSession = Depends(get_session),
    current_user: User = Depends(get_current_user),
) -> UserResponse:
    """Get a specific user by ID."""

    result = await session.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()

    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="User not found"
        )

    return UserResponse.model_validate(user)


@router.post("/", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
async def create_user(
    user_data: UserCreate,
    session: AsyncSession = Depends(get_session),
    current_user: User = Depends(get_current_user),
) -> UserResponse:
    """Create a new user."""

    # Check if user already exists
    existing_user = await session.execute(
        select(User).where(
            (User.email == user_data.email) | (User.username == user_data.username)
        )
    )
    if existing_user.scalar_one_or_none():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="User with this email or username already exists",
        )

    # Create new user
    user = User(
        username=user_data.username,
        email=user_data.email,
        password_hash=get_password_hash(user_data.password),
        is_active=user_data.is_active,
        is_super_admin=user_data.is_super_admin,
    )

    session.add(user)
    await session.commit()
    await session.refresh(user)

    return UserResponse.model_validate(user)


@router.put("/{user_id}", response_model=UserResponse)
async def update_user(
    user_id: UUID,
    user_data: UserUpdate,
    session: AsyncSession = Depends(get_session),
    current_user: User = Depends(get_current_user),
) -> UserResponse:
    """Update a user."""

    # Get existing user
    result = await session.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()

    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="User not found"
        )

    # Check for conflicts if updating email or username
    if user_data.email or user_data.username:
        conflict_query = select(User).where(User.id != user_id)
        conflict_filters = []

        if user_data.email:
            conflict_filters.append(User.email == user_data.email)
        if user_data.username:
            conflict_filters.append(User.username == user_data.username)

        if conflict_filters:
            conflict_result = await session.execute(
                conflict_query.where(or_(*conflict_filters))
            )
            if conflict_result.scalar_one_or_none():
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Email or username already exists",
                )

    # Update user fields
    update_data = user_data.model_dump(exclude_unset=True)

    if "password" in update_data:
        update_data["password_hash"] = get_password_hash(update_data.pop("password"))

    for field, value in update_data.items():
        setattr(user, field, value)

    await session.commit()
    await session.refresh(user)

    return UserResponse.model_validate(user)


@router.delete("/{user_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_user(
    user_id: UUID,
    session: AsyncSession = Depends(get_session),
    current_user: User = Depends(get_current_user),
):
    """Delete a user (soft delete by setting is_active=False)."""

    # Get existing user
    result = await session.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()

    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="User not found"
        )

    # Soft delete by setting is_active to False
    user.is_active = False
    await session.commit()


@router.patch("/{user_id}/activate", response_model=UserResponse)
async def activate_user(
    user_id: UUID,
    session: AsyncSession = Depends(get_session),
    current_user: User = Depends(get_current_user),
) -> UserResponse:
    """Activate a user."""

    result = await session.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()

    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="User not found"
        )

    user.is_active = True
    await session.commit()
    await session.refresh(user)

    return UserResponse.model_validate(user)
