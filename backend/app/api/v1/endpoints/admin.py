"""Admin-only endpoints: user role management and the permissions grid."""

from __future__ import annotations

import uuid

import httpx
from fastapi import APIRouter, Body, Depends, HTTPException, Response, status
from sqlalchemy import delete, func, select
from sqlalchemy.orm import Session

from app.core.auth import CurrentUser
from app.core.config import settings
from app.core.permissions import require_admin
from app.db.session import get_db
from app.models import RolePagePermission, UserProfile, UserRole
from app.schemas import (
    PermissionCell,
    RolePagePermissionRead,
    UserCreateAdmin,
    UserProfileRead,
    UserRoleUpdate,
)

router = APIRouter()


# ---------- users ----------


@router.get("/users", response_model=list[UserProfileRead])
def list_users(
    _: CurrentUser = Depends(require_admin), db: Session = Depends(get_db)
) -> list[UserProfileRead]:
    rows = list(db.scalars(select(UserProfile).order_by(UserProfile.email)))
    return [UserProfileRead.model_validate(r) for r in rows]


@router.post("/users", response_model=UserProfileRead, status_code=201)
def create_user(
    payload: UserCreateAdmin,
    _: CurrentUser = Depends(require_admin),
    db: Session = Depends(get_db),
) -> UserProfileRead:
    """Create a new user via Supabase Auth Admin API + insert their profile.
    Email is auto-confirmed so the user can log in immediately."""
    if not settings.SUPABASE_URL or not settings.SUPABASE_SERVICE_ROLE_KEY:
        raise HTTPException(
            status_code=500,
            detail="SUPABASE_URL and SUPABASE_SERVICE_ROLE_KEY must be configured",
        )

    # 1. Create in Supabase Auth (uses service-role privileges).
    try:
        r = httpx.post(
            f"{settings.SUPABASE_URL.rstrip('/')}/auth/v1/admin/users",
            headers={
                "apikey": settings.SUPABASE_SERVICE_ROLE_KEY,
                "Authorization": f"Bearer {settings.SUPABASE_SERVICE_ROLE_KEY}",
                "Content-Type": "application/json",
            },
            json={
                "email": payload.email,
                "password": payload.password,
                "email_confirm": True,
                "user_metadata": {"full_name": payload.full_name} if payload.full_name else {},
            },
            timeout=15,
        )
    except httpx.HTTPError as e:
        raise HTTPException(status_code=503, detail=f"Auth provider error: {e}") from e

    if r.status_code not in (200, 201):
        # Surface Supabase's error message — usually "already registered".
        detail = r.json().get("msg") or r.json().get("error_description") or r.text
        raise HTTPException(status_code=400, detail=f"Supabase rejected: {detail}")

    sb_user = r.json()
    user_id = uuid.UUID(sb_user["id"])

    # 2. Insert / upsert local profile with the requested role.
    existing = db.get(UserProfile, user_id)
    if existing:
        existing.role = payload.role
        existing.full_name = payload.full_name or existing.full_name
        profile = existing
    else:
        profile = UserProfile(
            user_id=user_id,
            email=payload.email,
            full_name=payload.full_name,
            role=payload.role,
        )
        db.add(profile)
    db.commit()
    db.refresh(profile)
    return UserProfileRead.model_validate(profile)


@router.patch("/users/{user_id}", response_model=UserProfileRead)
def update_user_role(
    user_id: uuid.UUID,
    payload: UserRoleUpdate,
    current: CurrentUser = Depends(require_admin),
    db: Session = Depends(get_db),
) -> UserProfileRead:
    profile = db.get(UserProfile, user_id)
    if profile is None:
        raise HTTPException(status_code=404, detail="User not found")
    # Don't let the only remaining admin demote themselves into a locked-out state.
    if profile.user_id == current.id and payload.role is not UserRole.admin:
        n_admins = db.scalar(
            select(func.count())
            .select_from(UserProfile)
            .where(UserProfile.role == UserRole.admin)
        )
        if (n_admins or 0) <= 1:
            raise HTTPException(
                status_code=400, detail="Cannot demote the last remaining admin"
            )
    profile.role = payload.role
    db.commit()
    db.refresh(profile)
    return UserProfileRead.model_validate(profile)


@router.delete("/users/{user_id}", status_code=204, response_class=Response)
def delete_user(
    user_id: uuid.UUID,
    current: CurrentUser = Depends(require_admin),
    db: Session = Depends(get_db),
) -> Response:
    """Deletes the application profile. The Supabase Auth user record remains
    untouched (delete that separately if you want to fully revoke access)."""
    if user_id == current.id:
        raise HTTPException(status_code=400, detail="Cannot delete your own profile")
    profile = db.get(UserProfile, user_id)
    if profile is None:
        raise HTTPException(status_code=404, detail="User not found")
    db.delete(profile)
    db.commit()
    return Response(status_code=204)


# ---------- permission grid ----------


@router.get("/permissions", response_model=list[RolePagePermissionRead])
def list_permissions(
    _: CurrentUser = Depends(require_admin), db: Session = Depends(get_db)
) -> list[RolePagePermissionRead]:
    rows = list(db.scalars(select(RolePagePermission)))
    return [RolePagePermissionRead.model_validate(r) for r in rows]


@router.post("/permissions", status_code=200, response_model=PermissionCell)
def set_permission(
    payload: PermissionCell,
    _: CurrentUser = Depends(require_admin),
    db: Session = Depends(get_db),
) -> PermissionCell:
    """Grant (has_access=True) or revoke (False) one (role, page) cell.
    Admins are not stored in the grid; trying to set a cell for the admin role
    is a no-op."""
    if payload.role is UserRole.admin:
        # admin access is implicit
        return payload
    existing = db.scalar(
        select(RolePagePermission).where(
            RolePagePermission.role == payload.role,
            RolePagePermission.page_id == payload.page_id,
        )
    )
    if payload.has_access and not existing:
        db.add(RolePagePermission(role=payload.role, page_id=payload.page_id))
    elif not payload.has_access and existing:
        db.delete(existing)
    db.commit()
    return payload


@router.put("/permissions/bulk", response_model=list[RolePagePermissionRead])
def bulk_replace_permissions(
    cells: list[PermissionCell] = Body(...),
    _: CurrentUser = Depends(require_admin),
    db: Session = Depends(get_db),
) -> list[RolePagePermissionRead]:
    """Replace the entire grid with the given set of cells (only those with
    has_access=True are persisted). Use for a 'Save grid' submit button."""
    db.execute(delete(RolePagePermission))
    for c in cells:
        if c.role is UserRole.admin or not c.has_access:
            continue
        db.add(RolePagePermission(role=c.role, page_id=c.page_id))
    db.commit()
    rows = list(db.scalars(select(RolePagePermission)))
    return [RolePagePermissionRead.model_validate(r) for r in rows]
