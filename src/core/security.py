from __future__ import annotations

from datetime import datetime, timedelta, timezone
from typing import Any, Dict, Optional
from uuid import UUID

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from jose import JWTError, jwt
from passlib.context import CryptContext
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from src.core.config import settings
from src.core.db import get_session
from src.models.user import User


pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
http_bearer = HTTPBearer(auto_error=False)


def verify_password(plain_password: str, password_hash: str) -> bool:
	return pwd_context.verify(plain_password, password_hash)


def get_password_hash(password: str) -> str:
	return pwd_context.hash(password)


def _create_token(data: Dict[str, Any], expires_delta: timedelta) -> str:
	to_encode = data.copy()
	expire = datetime.now(timezone.utc) + expires_delta
	to_encode.update({"exp": expire})
	token = jwt.encode(to_encode, settings.jwt_secret, algorithm=settings.algorithm)
	return token


def create_access_token(subject: str | None, extra: Optional[Dict[str, Any]] = None) -> str:
	minutes = settings.access_token_expire_minutes
	payload = {"sub": subject, "type": "access"}
	if extra:
		payload.update(extra)
	return _create_token(payload, timedelta(minutes=minutes))


def create_refresh_token(subject: str | None, extra: Optional[Dict[str, Any]] = None) -> str:
	days = settings.refresh_token_expire_days
	payload = {"sub": subject, "type": "refresh"}
	if extra:
		payload.update(extra)
	return _create_token(payload, timedelta(days=days))


def decode_token(token: str) -> Dict[str, Any]:
	return jwt.decode(token, settings.jwt_secret, algorithms=[settings.algorithm])


async def get_current_user(
	cred: HTTPAuthorizationCredentials | None = Depends(http_bearer),
	session: AsyncSession = Depends(get_session),
) -> User:
	if cred is None or not cred.scheme.lower() == "bearer":
		raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Not authenticated")
	try:
		payload = decode_token(cred.credentials)
		token_type = payload.get("type")
		if token_type != "access":
			raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token type")
		sub = payload.get("sub")
		if not sub:
			raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token payload")
		try:
			user_uuid = UUID(sub)
		except (TypeError, ValueError):
			raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid user id in token")
		result = await session.execute(select(User).where(User.id == user_uuid))
		user = result.scalar_one_or_none()
		if user is None or not user.is_active:
			raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Inactive or not found user")
		return user
	except JWTError:
		raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token")
