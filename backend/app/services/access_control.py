from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.orm import Query, Session, joinedload

from app.core.security import hash_session_token
from app.database.session import get_db
from app.models.auth import AuthSession, ClientAssignment, Permission, Role, RolePermission, User, UserRole
from app.models.client import Client
from app.models.delivery import DeliveryNote
from app.models.invoice import Invoice
from app.models.order import Order


ROLE_LABELS = {
    "direccion_general": "Dirección General",
    "comercial": "Comercial",
    "finanzas": "Finanzas",
    "admin": "Administrador",
    "operaciones": "Operaciones",
}

security_scheme = HTTPBearer(auto_error=False)


@dataclass
class AccessContext:
    user: User
    primary_role: str
    roles: set[str]
    permissions: set[str]
    client_ids: set[int] | None

    @property
    def has_global_scope(self) -> bool:
        return self.client_ids is None

    def has_permission(self, permission: str) -> bool:
        return permission in self.permissions


class CurrentUser:
    def __init__(self, session: AuthSession, access_context: AccessContext):
        self.session = session
        self.access_context = access_context
        self.user = access_context.user



def get_primary_role(user: User, role_codes: set[str]) -> str:
    if user.default_role_code and user.default_role_code in role_codes:
        return user.default_role_code
    if "admin" in role_codes:
        return "admin"
    if "direccion_general" in role_codes:
        return "direccion_general"
    if "finanzas" in role_codes:
        return "finanzas"
    if "comercial" in role_codes:
        return "comercial"
    return next(iter(role_codes), "")



def build_access_context(db: Session, user: User) -> AccessContext:
    role_rows = (
        db.query(Role.code)
        .join(UserRole, UserRole.role_id == Role.id)
        .filter(UserRole.user_id == user.id)
        .all()
    )
    role_codes = {code for (code,) in role_rows}
    primary_role = get_primary_role(user, role_codes)

    permission_rows = (
        db.query(Permission.code)
        .join(RolePermission, RolePermission.permission_id == Permission.id)
        .join(Role, Role.id == RolePermission.role_id)
        .join(UserRole, UserRole.role_id == Role.id)
        .filter(UserRole.user_id == user.id)
        .all()
    )
    permissions = {code for (code,) in permission_rows}

    client_ids: set[int] | None = None
    if primary_role == "comercial" and "admin" not in role_codes and "direccion_general" not in role_codes:
        assignment_rows = (
            db.query(ClientAssignment.client_id)
            .filter(ClientAssignment.user_id == user.id)
            .all()
        )
        client_ids = {client_id for (client_id,) in assignment_rows}

    return AccessContext(
        user=user,
        primary_role=primary_role,
        roles=role_codes,
        permissions=permissions,
        client_ids=client_ids,
    )



def serialize_auth_user(access_context: AccessContext) -> dict[str, object]:
    user = access_context.user
    return {
        "id": user.id,
        "email": user.email,
        "full_name": user.full_name,
        "primary_role": access_context.primary_role,
        "roles": sorted(access_context.roles),
        "permissions": sorted(access_context.permissions),
        "is_active": user.is_active,
    }



def _get_bearer_token(credentials: HTTPAuthorizationCredentials | None) -> str:
    if credentials is None or not credentials.credentials:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Authentication required")
    return credentials.credentials



def get_current_user(
    credentials: HTTPAuthorizationCredentials | None = Depends(security_scheme),
    db: Session = Depends(get_db),
) -> CurrentUser:
    token = _get_bearer_token(credentials)
    session = (
        db.query(AuthSession)
        .options(joinedload(AuthSession.user))
        .filter(AuthSession.token_hash == hash_session_token(token))
        .first()
    )
    if session is None or session.user is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid session")
    if session.revoked_at is not None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Session revoked")
    expires_at = session.expires_at
    if expires_at.tzinfo is None:
        expires_at = expires_at.replace(tzinfo=timezone.utc)
    if expires_at <= datetime.now(timezone.utc):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Session expired")
    if not session.user.is_active:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Inactive user")

    session.last_seen_at = datetime.now(timezone.utc)
    db.add(session)
    db.commit()
    db.refresh(session)

    return CurrentUser(session=session, access_context=build_access_context(db, session.user))



def require_authenticated_user(current_user: CurrentUser = Depends(get_current_user)) -> CurrentUser:
    return current_user



def require_permission(permission: str):
    def dependency(current_user: CurrentUser = Depends(get_current_user)) -> CurrentUser:
        if not current_user.access_context.has_permission(permission):
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=f"Missing permission: {permission}")
        return current_user

    return dependency



def apply_client_scope(query: Query, access_context: AccessContext) -> Query:
    if access_context.has_global_scope:
        return query
    if not access_context.client_ids:
        return query.filter(Client.id == -1)
    return query.filter(Client.id.in_(access_context.client_ids))



def apply_order_scope(query: Query, access_context: AccessContext) -> Query:
    if access_context.has_global_scope:
        return query
    if not access_context.client_ids:
        return query.filter(Order.id == -1)
    return query.filter(Order.client_id.in_(access_context.client_ids))



def apply_delivery_scope(query: Query, access_context: AccessContext) -> Query:
    if access_context.has_global_scope:
        return query
    if not access_context.client_ids:
        return query.filter(DeliveryNote.id == -1)
    return query.join(Order, Order.id == DeliveryNote.order_id).filter(Order.client_id.in_(access_context.client_ids))



def apply_invoice_scope(query: Query, access_context: AccessContext) -> Query:
    if access_context.has_global_scope:
        return query
    if not access_context.client_ids:
        return query.filter(Invoice.id == -1)
    return query.join(Order, Order.id == Invoice.order_id).filter(Order.client_id.in_(access_context.client_ids))



def require_order_access(db: Session, access_context: AccessContext, order: Order | None) -> None:
    if order is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Order not found")
    if access_context.has_global_scope:
        return
    if order.client_id not in (access_context.client_ids or set()):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Access denied for this order")
