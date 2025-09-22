"""
Contact CRUD operations router.
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
from src.models.profile import Contact
from src.schemas.contact import (
    ContactCreate,
    ContactUpdate,
    ContactResponse,
    ContactListResponse,
)

router = APIRouter(prefix="/contacts", tags=["contacts"])


@router.get("/", response_model=ContactListResponse)
async def get_contacts(
    page: int = Query(1, ge=1, description="Page number"),
    size: int = Query(10, ge=1, le=100, description="Page size"),
    profile_id: Optional[UUID] = Query(None, description="Filter by profile ID"),
    type: Optional[str] = Query(None, description="Filter by contact type"),
    session: AsyncSession = Depends(get_session),
    current_user: User = Depends(get_current_user),
) -> ContactListResponse:
    """Get paginated list of contacts with optional filtering."""

    # Build query
    query = select(Contact)
    count_query = select(func.count(Contact.id))

    # Apply filters
    filters = []
    if profile_id:
        filters.append(Contact.profile_id == profile_id)

    if type:
        filters.append(Contact.type == type)

    if filters:
        query = query.where(and_(*filters))
        count_query = count_query.where(and_(*filters))

    # Get total count
    total_result = await session.execute(count_query)
    total = total_result.scalar()

    # Apply pagination
    offset = (page - 1) * size
    query = query.offset(offset).limit(size).order_by(Contact.created_at.desc())

    # Execute query
    result = await session.execute(query)
    contacts = result.scalars().all()

    # Calculate pages
    pages = (total + size - 1) // size

    return ContactListResponse(
        contacts=[ContactResponse.model_validate(contact) for contact in contacts],
        total=total,
        page=page,
        size=size,
        pages=pages,
    )


@router.get("/{contact_id}", response_model=ContactResponse)
async def get_contact(
    contact_id: UUID,
    session: AsyncSession = Depends(get_session),
    current_user: User = Depends(get_current_user),
) -> ContactResponse:
    """Get a specific contact by ID."""

    result = await session.execute(select(Contact).where(Contact.id == contact_id))
    contact = result.scalar_one_or_none()

    if not contact:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Contact not found"
        )

    return ContactResponse.model_validate(contact)


@router.post("/", response_model=ContactResponse, status_code=status.HTTP_201_CREATED)
async def create_contact(
    contact_data: ContactCreate,
    session: AsyncSession = Depends(get_session),
    current_user: User = Depends(get_current_user),
) -> ContactResponse:
    """Create a new contact."""

    # Create new contact
    contact = Contact(
        profile_id=contact_data.profile_id,
        type=contact_data.type,
        value=contact_data.value,
        is_primary=contact_data.is_primary,
    )

    session.add(contact)
    await session.commit()
    await session.refresh(contact)

    return ContactResponse.model_validate(contact)


@router.put("/{contact_id}", response_model=ContactResponse)
async def update_contact(
    contact_id: UUID,
    contact_data: ContactUpdate,
    session: AsyncSession = Depends(get_session),
    current_user: User = Depends(get_current_user),
) -> ContactResponse:
    """Update a contact."""

    # Get existing contact
    result = await session.execute(select(Contact).where(Contact.id == contact_id))
    contact = result.scalar_one_or_none()

    if not contact:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Contact not found"
        )

    # Update contact fields
    update_data = contact_data.model_dump(exclude_unset=True)

    for field, value in update_data.items():
        setattr(contact, field, value)

    await session.commit()
    await session.refresh(contact)

    return ContactResponse.model_validate(contact)


@router.delete("/{contact_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_contact(
    contact_id: UUID,
    session: AsyncSession = Depends(get_session),
    current_user: User = Depends(get_current_user),
):
    """Delete a contact."""

    # Get existing contact
    result = await session.execute(select(Contact).where(Contact.id == contact_id))
    contact = result.scalar_one_or_none()

    if not contact:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Contact not found"
        )

    await session.delete(contact)
    await session.commit()
