from __future__ import annotations


from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, EmailStr
from sqlalchemy.ext.asyncio import AsyncSession
from sqlmodel import select

from src.core.db import get_session
from src.core.security import (
    create_access_token,
    create_refresh_token,
    get_password_hash,
    verify_password,
)
from src.models.user import User
from src.models.profile import Profile


router = APIRouter(prefix="/auth", tags=["auth"])


class RegisterRequest(BaseModel):
    email: EmailStr
    password: str
    username: str


class TokenPair(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"


@router.post("/register", response_model=TokenPair)
async def register(
    payload: RegisterRequest, session: AsyncSession = Depends(get_session)
) -> TokenPair:
    # check if exists
    exists = await session.execute(
        select(User).where(
            (User.email == payload.email) | (User.username == payload.username)
        )
    )
    if exists.scalar_one_or_none() is not None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email or username already registered",
        )
    user = User(
        email=str(payload.email),
        username=payload.username,
        password_hash=get_password_hash(payload.password),
    )
    session.add(user)
    await session.flush()

    profile = Profile(
        user_id=user.id,
        first_name=None,
        last_name=None,
    )
    session.add(profile)

    await session.commit()
    await session.refresh(user)
    await session.refresh(profile)
    access = create_access_token(str(user.id))
    refresh = create_refresh_token(str(user.id))
    return TokenPair(access_token=access, refresh_token=refresh)


class LoginRequest(BaseModel):
    email: EmailStr
    password: str


@router.post("/login", response_model=TokenPair)
async def login(
    payload: LoginRequest, session: AsyncSession = Depends(get_session)
) -> TokenPair:
    result = await session.execute(select(User).where(User.email == payload.email))
    user = result.scalar_one_or_none()
    if user is None or not verify_password(payload.password, user.password_hash):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid credentials"
        )
    access = create_access_token(str(user.id))
    refresh = create_refresh_token(str(user.id))
    return TokenPair(access_token=access, refresh_token=refresh)


class RefreshRequest(BaseModel):
    refresh_token: str


@router.post("/refresh", response_model=TokenPair)
async def refresh(payload: RefreshRequest) -> TokenPair:
    # For simplicity, re-issue access if refresh token decodes and type is refresh
    from jose import JWTError
    from src.core.security import decode_token

    try:
        data = decode_token(payload.refresh_token)
        if data.get("type") != "refresh":
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid refresh token"
            )
        sub = data.get("sub")
        access = create_access_token(sub)
        refresh = create_refresh_token(sub)
        return TokenPair(access_token=access, refresh_token=refresh)
    except JWTError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid refresh token"
        )
