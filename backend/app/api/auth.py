from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.core.security import generate_session_token, get_session_expiry, hash_session_token, verify_password
from app.database.session import get_db
from app.models.auth import AuthSession, User
from app.schemas.auth import AuthSessionResponse, LoginRequest, LoginResponse
from app.services.access_control import CurrentUser, build_access_context, get_current_user, serialize_auth_user


router = APIRouter()


@router.post("/login", response_model=LoginResponse)
def login(payload: LoginRequest, db: Session = Depends(get_db)) -> LoginResponse:
    user = db.query(User).filter(User.email == payload.email.strip().lower()).first()
    if user is None or not verify_password(payload.password, user.password_hash):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid credentials")
    if not user.is_active:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Inactive user")

    now = datetime.now(timezone.utc)
    token = generate_session_token()
    auth_session = AuthSession(
        user_id=user.id,
        token_hash=hash_session_token(token),
        expires_at=get_session_expiry(),
        last_seen_at=now,
    )
    user.last_login_at = now
    db.add(auth_session)
    db.add(user)
    db.commit()
    db.refresh(auth_session)
    db.refresh(user)

    auth_user = serialize_auth_user(build_access_context(db, user))
    return LoginResponse(access_token=token, user=auth_user)


@router.get("/me", response_model=AuthSessionResponse)
def me(current_user: CurrentUser = Depends(get_current_user)) -> AuthSessionResponse:
    return AuthSessionResponse(user=serialize_auth_user(current_user.access_context), issued_at=current_user.session.created_at)
