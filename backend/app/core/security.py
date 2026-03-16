from __future__ import annotations

import hashlib
import secrets
from datetime import datetime, timedelta, timezone

from passlib.context import CryptContext

from app.core.config import AUTH_TOKEN_EXPIRE_HOURS


pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def verify_password(plain_password: str, password_hash: str) -> bool:
    return pwd_context.verify(plain_password, password_hash)


def hash_password(password: str) -> str:
    return pwd_context.hash(password)


def generate_session_token() -> str:
    return secrets.token_urlsafe(32)


def hash_session_token(token: str) -> str:
    return hashlib.sha256(token.encode("utf-8")).hexdigest()


def get_session_expiry() -> datetime:
    return datetime.now(timezone.utc) + timedelta(hours=AUTH_TOKEN_EXPIRE_HOURS)
