"""Authentication routes."""

from __future__ import annotations

import uuid

from fastapi import APIRouter, Depends, Header, HTTPException, Request, status
from sqlalchemy.orm import Session

from ..config import settings
from ..db import get_db
from ..models import User
from ..schemas import (
    LoginRequest,
    PasswordChangeRequest,
    RefreshRequest,
    TokenResponse,
    UserCreate,
    UserRead,
)
from ..services.audit import log_audit
from ..services.jwt_service import (
    ExpiredTokenError,
    InvalidTokenError,
    create_token_pair,
    verify_access_token,
    verify_refresh_token,
)
from ..services.user_service import (
    InactiveUserError,
    InvalidCredentialsError,
    UserAlreadyExistsError,
    authenticate_user,
    create_user,
    get_user_by_id,
    revoke_all_user_tokens,
    revoke_refresh_token,
    store_refresh_token,
    update_user_password,
    validate_refresh_token,
)
from ..services.password import verify_password

router = APIRouter(prefix="/auth", tags=["auth"])


def get_client_info(request: Request) -> tuple[str | None, str | None]:
    """Extract client info from request."""
    user_agent = request.headers.get("user-agent")
    # Get client IP, handling proxies
    forwarded = request.headers.get("x-forwarded-for")
    if forwarded:
        ip_address = forwarded.split(",")[0].strip()
    else:
        ip_address = request.client.host if request.client else None
    return user_agent, ip_address


def get_current_user(
    authorization: str | None = Header(default=None),
    db: Session = Depends(get_db),
) -> User:
    """Dependency to get the current authenticated user from JWT token."""
    if not authorization:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Missing authorization header",
            headers={"WWW-Authenticate": "Bearer"},
        )

    # Extract token from "Bearer <token>" format
    parts = authorization.split()
    if len(parts) != 2 or parts[0].lower() != "bearer":
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authorization header format",
            headers={"WWW-Authenticate": "Bearer"},
        )

    token = parts[1]

    try:
        user_id = verify_access_token(token)
    except ExpiredTokenError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token has expired",
            headers={"WWW-Authenticate": "Bearer"},
        )
    except InvalidTokenError as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=str(e),
            headers={"WWW-Authenticate": "Bearer"},
        )

    user = get_user_by_id(db, uuid.UUID(user_id))
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found",
            headers={"WWW-Authenticate": "Bearer"},
        )

    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User account is inactive",
            headers={"WWW-Authenticate": "Bearer"},
        )

    return user


def get_current_active_user(
    current_user: User = Depends(get_current_user),
) -> User:
    """Dependency that ensures the user is active."""
    if not current_user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="User account is inactive",
        )
    return current_user


def get_current_superuser(
    current_user: User = Depends(get_current_user),
) -> User:
    """Dependency that ensures the user is a superuser."""
    if not current_user.is_superuser:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Superuser access required",
        )
    return current_user


@router.post("/register", response_model=UserRead, status_code=status.HTTP_201_CREATED)
def register(
    payload: UserCreate,
    request: Request,
    db: Session = Depends(get_db),
):
    """Register a new user.

    Note: In production, this endpoint should be protected or disabled
    for a single-user application.
    """
    # For single-user apps, you might want to check if any user exists
    # and prevent additional registrations
    try:
        user = create_user(
            db=db,
            email=payload.email,
            username=payload.username,
            password=payload.password,
            full_name=payload.full_name,
        )
    except UserAlreadyExistsError as e:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=str(e),
        )

    log_audit(
        db=db,
        actor=user.username,
        action="auth.register",
        resource_type="user",
        resource_id=str(user.id),
    )

    return user


@router.post("/login", response_model=TokenResponse)
def login(
    payload: LoginRequest,
    request: Request,
    db: Session = Depends(get_db),
):
    """Authenticate user and return JWT tokens."""
    try:
        user = authenticate_user(
            db=db,
            email_or_username=payload.email_or_username,
            password=payload.password,
        )
    except InvalidCredentialsError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email/username or password",
        )
    except InactiveUserError:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="User account is inactive",
        )

    # Create token pair
    token_pair, jti, refresh_expires = create_token_pair(user.id)

    # Store refresh token
    user_agent, ip_address = get_client_info(request)
    store_refresh_token(
        db=db,
        user_id=user.id,
        token_jti=jti,
        expires_at=refresh_expires,
        user_agent=user_agent,
        ip_address=ip_address,
    )

    log_audit(
        db=db,
        actor=user.username,
        action="auth.login",
        resource_type="user",
        resource_id=str(user.id),
        detail={"ip_address": ip_address},
    )

    return TokenResponse(
        access_token=token_pair.access_token,
        refresh_token=token_pair.refresh_token,
        token_type=token_pair.token_type,
        expires_in=token_pair.expires_in,
    )


@router.post("/refresh", response_model=TokenResponse)
def refresh_tokens(
    payload: RefreshRequest,
    request: Request,
    db: Session = Depends(get_db),
):
    """Refresh access token using refresh token."""
    try:
        user_id_str, jti = verify_refresh_token(payload.refresh_token)
        user_id = uuid.UUID(user_id_str)
    except (ExpiredTokenError, InvalidTokenError) as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=str(e),
        )

    # Validate refresh token exists and not revoked
    token_record = validate_refresh_token(db, user_id, jti)
    if not token_record:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or revoked refresh token",
        )

    # Get user
    user = get_user_by_id(db, user_id)
    if not user or not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found or inactive",
        )

    # Revoke old refresh token
    revoke_refresh_token(db, user_id, jti)

    # Create new token pair
    new_token_pair, new_jti, new_refresh_expires = create_token_pair(user.id)

    # Store new refresh token
    user_agent, ip_address = get_client_info(request)
    store_refresh_token(
        db=db,
        user_id=user.id,
        token_jti=new_jti,
        expires_at=new_refresh_expires,
        user_agent=user_agent,
        ip_address=ip_address,
    )

    log_audit(
        db=db,
        actor=user.username,
        action="auth.refresh",
        resource_type="user",
        resource_id=str(user.id),
    )

    return TokenResponse(
        access_token=new_token_pair.access_token,
        refresh_token=new_token_pair.refresh_token,
        token_type=new_token_pair.token_type,
        expires_in=new_token_pair.expires_in,
    )


@router.post("/logout", status_code=status.HTTP_204_NO_CONTENT)
def logout(
    payload: RefreshRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Logout user by revoking the refresh token."""
    try:
        user_id_str, jti = verify_refresh_token(payload.refresh_token)
        user_id = uuid.UUID(user_id_str)
    except (ExpiredTokenError, InvalidTokenError):
        # Even if token is invalid/expired, return success for security
        return

    # Only allow revoking own tokens
    if user_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Cannot revoke other user's token",
        )

    revoke_refresh_token(db, user_id, jti)

    log_audit(
        db=db,
        actor=current_user.username,
        action="auth.logout",
        resource_type="user",
        resource_id=str(current_user.id),
    )


@router.post("/logout-all", status_code=status.HTTP_204_NO_CONTENT)
def logout_all(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Logout user from all devices by revoking all refresh tokens."""
    count = revoke_all_user_tokens(db, current_user.id)

    log_audit(
        db=db,
        actor=current_user.username,
        action="auth.logout_all",
        resource_type="user",
        resource_id=str(current_user.id),
        detail={"revoked_count": count},
    )


@router.get("/me", response_model=UserRead)
def get_me(
    current_user: User = Depends(get_current_user),
):
    """Get current authenticated user profile."""
    return current_user


@router.post("/change-password", status_code=status.HTTP_204_NO_CONTENT)
def change_password(
    payload: PasswordChangeRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Change current user's password."""
    # Verify current password
    if not verify_password(payload.current_password, current_user.password_hash):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Current password is incorrect",
        )

    # Update password
    update_user_password(db, current_user, payload.new_password)

    # Revoke all refresh tokens for security
    revoke_all_user_tokens(db, current_user.id)

    log_audit(
        db=db,
        actor=current_user.username,
        action="auth.password_change",
        resource_type="user",
        resource_id=str(current_user.id),
    )
