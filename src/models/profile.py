from __future__ import annotations

from datetime import datetime, date
from typing import Optional
from uuid import UUID, uuid4

from sqlmodel import SQLModel, Field
from sqlalchemy import Column, String, Text, Date, Enum
import enum


class Gender(str, enum.Enum):
    male = "male"
    female = "female"
    other = "other"
    prefer_not_to_say = "prefer_not_to_say"


class Profile(SQLModel, table=True):
    __tablename__ = "profiles"

    id: UUID = Field(default_factory=uuid4, primary_key=True, index=True)
    user_id: UUID = Field(foreign_key="users.id", nullable=False, unique=True, index=True)
    
    # Personal Information
    first_name: Optional[str] = Field(default=None, sa_column=Column(String(100), nullable=True))
    last_name: Optional[str] = Field(default=None, sa_column=Column(String(100), nullable=True))
    middle_name: Optional[str] = Field(default=None, sa_column=Column(String(100), nullable=True))
    date_of_birth: Optional[date] = Field(default=None, sa_column=Column(Date, nullable=True))
    gender: Optional[Gender] = Field(default=None, sa_column=Column(Enum(Gender), nullable=True))
    
    # Contact Information
    phone_number: Optional[str] = Field(default=None, sa_column=Column(String(20), nullable=True))
    alternate_email: Optional[str] = Field(default=None, sa_column=Column(String(320), nullable=True))
    
    # Location Information
    country: Optional[str] = Field(default=None, sa_column=Column(String(100), nullable=True))
    state_province: Optional[str] = Field(default=None, sa_column=Column(String(100), nullable=True))
    city: Optional[str] = Field(default=None, sa_column=Column(String(100), nullable=True))
    postal_code: Optional[str] = Field(default=None, sa_column=Column(String(20), nullable=True))
    
    # Professional Information
    job_title: Optional[str] = Field(default=None, sa_column=Column(String(150), nullable=True))
    company: Optional[str] = Field(default=None, sa_column=Column(String(150), nullable=True))
    industry: Optional[str] = Field(default=None, sa_column=Column(String(100), nullable=True))
    bio: Optional[str] = Field(default=None, sa_column=Column(Text, nullable=True))
    
    
    # Profile Settings
    profile_picture_url: Optional[str] = Field(default=None, sa_column=Column(String(500), nullable=True))
    is_public: bool = Field(default=True, nullable=False)
    allow_contact: bool = Field(default=True, nullable=False)
    
    # Timestamps
    created_at: datetime = Field(default_factory=datetime.utcnow, nullable=False)
    updated_at: datetime = Field(default_factory=datetime.utcnow, nullable=False)
    last_login_at: Optional[datetime] = Field(default=None, nullable=True)
