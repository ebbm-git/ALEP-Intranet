"""Authentication: validate Supabase Auth JWTs and load the user's role.

We delegate token verification to Supabase by calling its `/auth/v1/user`
endpoint with the incoming bearer token. This works with both the legacy
(HS256) and the new asymmetric-key Supabase Auth setups without us needing
to manage JWT secrets ourselves.

Trade-off: one extra HTTP round-trip per request. For an internal intranet
the latency is acceptable; if it ever becomes a bottleneck we can switch to
verifying RS256 JWTs locally via the JWKS endpoint.
"""

from __future__ import annotations

import uuid

import httpx
from fastapi import Depends, HTTPException, Request, status
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.core.config import settings
from app.db.session import get_db
from app.models import UserProfile, UserRole

_supabase_url = settings.SUPABASE_URL.rstrip("/") if settings.SUPABASE_URL else ""


class CurrentUser:
    """Carrier for the authenticated user + their loaded role."""

    def __init__(self, profile: UserProfile):
        self.profile = profile
        self.id: uuid.UUID = profile.user_id
        self.email: str = profile.email
        self.role: UserRole = profile.role
        self.full_name: str | None = profile.full_name


def _extract_bearer(request: Request) -> str:
    auth = request.headers.get("Authorization", "")
    if not auth.lower().startswith("bearer "):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Missing or malformed Authorization header",
        )
    return auth.split(" ", 1)[1].strip()


def _verify_with_supabase(token: str) -> dict:
    """Ask Supabase to validate the JWT and return the user payload."""
    if not _supabase_url:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="SUPABASE_URL not configured",
        )
    try:
        r = httpx.get(
            f"{_supabase_url}/auth/v1/user",
            headers={
                "Authorization": f"Bearer {token}",
                "apikey": settings.SUPABASE_ANON_KEY or "",
            },
            timeout=10,
        )
    except httpx.HTTPError as e:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=f"Auth provider unreachable: {e}",
        ) from e
    if r.status_code != 200:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid or expired token"
        )
    return r.json()


def _get_or_create_profile(db: Session, sb_user: dict) -> UserProfile:
    """Look up the profile; create one if missing.
    The FIRST user to authenticate becomes the admin (bootstrap convenience).
    """
    user_id = uuid.UUID(sb_user["id"])
    profile = db.get(UserProfile, user_id)
    if profile:
        return profile

    # No profile yet — decide the initial role.
    n_profiles = db.scalar(select(func.count(UserProfile.user_id))) or 0
    initial_role = UserRole.admin if n_profiles == 0 else UserRole.viewer

    email = sb_user.get("email") or ""
    full_name = (
        (sb_user.get("user_metadata") or {}).get("full_name")
        or (sb_user.get("user_metadata") or {}).get("name")
        or None
    )
    profile = UserProfile(
        user_id=user_id, email=email, full_name=full_name, role=initial_role
    )
    db.add(profile)
    db.commit()
    db.refresh(profile)
    return profile


def get_current_user(
    request: Request, db: Session = Depends(get_db)
) -> CurrentUser:
    """FastAPI dependency. Returns the authenticated user + their role.
    Raises 401 if the token is missing/invalid."""
    token = _extract_bearer(request)
    sb_user = _verify_with_supabase(token)
    profile = _get_or_create_profile(db, sb_user)
    return CurrentUser(profile)


def get_optional_user(
    request: Request, db: Session = Depends(get_db)
) -> CurrentUser | None:
    """Same as get_current_user but never raises — returns None when the
    request has no usable token. Use on endpoints that change behaviour by
    role but should still respond to anonymous callers."""
    auth = request.headers.get("Authorization", "")
    if not auth.lower().startswith("bearer "):
        return None
    try:
        return get_current_user(request, db)
    except HTTPException:
        return None
