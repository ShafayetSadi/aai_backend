from __future__ import annotations

from datetime import date, datetime
from typing import Optional, List
from uuid import UUID, uuid4

from sqlalchemy import String, Text, Date, Enum as SAEnum, UniqueConstraint, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship

import enum

from src.models.sa_base import Base


class Gender(str, enum.Enum):
    male = "male"
    female = "female"
    other = "other"
    prefer_not_to_say = "prefer_not_to_say"


class Location(Base):
    __tablename__ = "locations"

    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4, index=True)
    is_active: Mapped[bool] = mapped_column(default=True, nullable=False)
    created_at: Mapped[datetime] = mapped_column(default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(default=datetime.utcnow)
    deactivated_at: Mapped[Optional[datetime]] = mapped_column(default=None)

    country: Mapped[str] = mapped_column(String(100), nullable=False, index=True)
    state_province: Mapped[Optional[str]] = mapped_column(String(100), index=True)
    city: Mapped[Optional[str]] = mapped_column(String(100), index=True)
    postal_code: Mapped[Optional[str]] = mapped_column(String(20))

    # Relationships
    profiles: Mapped[List["Profile"]] = relationship(back_populates="location")


class Contact(Base):
    __tablename__ = "contacts"
    __table_args__ = (
        UniqueConstraint(
            "profile_id", "is_primary", name="unique_primary_contact_per_profile"
        ),
    )

    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4, index=True)
    is_active: Mapped[bool] = mapped_column(default=True, nullable=False)
    created_at: Mapped[datetime] = mapped_column(default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(default=datetime.utcnow)
    deactivated_at: Mapped[Optional[datetime]] = mapped_column(default=None)

    profile_id: Mapped[UUID] = mapped_column(
        ForeignKey("profiles.id"), nullable=False, index=True
    )
    type: Mapped[str] = mapped_column(String(50), nullable=False, index=True)
    value: Mapped[str] = mapped_column(String(320), nullable=False)
    is_primary: Mapped[bool] = mapped_column(default=False, nullable=False)

    # Relationships
    profile: Mapped["Profile"] = relationship(back_populates="contacts")


class Job(Base):
    __tablename__ = "jobs"

    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4, index=True)
    is_active: Mapped[bool] = mapped_column(default=True, nullable=False)
    created_at: Mapped[datetime] = mapped_column(default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(default=datetime.utcnow)
    deactivated_at: Mapped[Optional[datetime]] = mapped_column(default=None)

    profile_id: Mapped[UUID] = mapped_column(
        ForeignKey("profiles.id"), nullable=False, index=True
    )
    title: Mapped[str] = mapped_column(String(150), nullable=False, index=True)
    company: Mapped[str] = mapped_column(String(150), nullable=False, index=True)
    industry: Mapped[Optional[str]] = mapped_column(String(100), index=True)
    start_date: Mapped[Optional[date]] = mapped_column(Date, nullable=True)
    end_date: Mapped[Optional[date]] = mapped_column(Date, nullable=True)

    # Relationships
    profile: Mapped["Profile"] = relationship(back_populates="jobs")


class Profile(Base):
    __tablename__ = "profiles"

    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4, index=True)
    is_active: Mapped[bool] = mapped_column(default=True, nullable=False)
    created_at: Mapped[datetime] = mapped_column(default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(default=datetime.utcnow)
    deactivated_at: Mapped[Optional[datetime]] = mapped_column(default=None)

    user_id: Mapped[UUID] = mapped_column(
        ForeignKey("users.id"), nullable=False, unique=True, index=True
    )

    first_name: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    last_name: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    date_of_birth: Mapped[Optional[date]] = mapped_column(Date, nullable=True)
    gender: Mapped[Optional[Gender]] = mapped_column(SAEnum(Gender), nullable=True)

    location_id: Mapped[Optional[UUID]] = mapped_column(
        ForeignKey("locations.id"), nullable=True, index=True
    )

    bio: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    profile_picture_url: Mapped[Optional[str]] = mapped_column(
        String(500), nullable=True
    )
    is_public: Mapped[bool] = mapped_column(default=True, nullable=False)
    allow_contact: Mapped[bool] = mapped_column(default=True, nullable=False)

    # Relationships
    location: Mapped[Optional["Location"]] = relationship(back_populates="profiles")
    contacts: Mapped[List[Contact]] = relationship(back_populates="profile")
    jobs: Mapped[List[Job]] = relationship(back_populates="profile")
