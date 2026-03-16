from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, ConfigDict


class LoginRequest(BaseModel):
    email: str
    password: str


class AuthUser(BaseModel):
    id: int
    email: str
    full_name: str
    primary_role: str
    roles: list[str]
    permissions: list[str]
    is_active: bool

    model_config = ConfigDict(from_attributes=True)


class LoginResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: AuthUser


class AuthSessionResponse(BaseModel):
    user: AuthUser
    issued_at: datetime
