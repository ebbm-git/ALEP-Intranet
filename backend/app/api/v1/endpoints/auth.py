from __future__ import annotations

from fastapi import APIRouter, Depends
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.auth import CurrentUser, get_current_user
from app.db.session import get_db
from app.models import RolePagePermission, UserRole
from app.schemas import CurrentUserRead

router = APIRouter()


@router.get("/me", response_model=CurrentUserRead)
def me(
    user: CurrentUser = Depends(get_current_user), db: Session = Depends(get_db)
) -> CurrentUserRead:
    """Return the authenticated user + the list of page IDs they may access.
    Admins get every page id (implicit access)."""
    if user.role is UserRole.admin:
        from app.models import Page  # local import to avoid cycle

        accessible = list(db.scalars(select(Page.id)))
    else:
        accessible = list(
            db.scalars(
                select(RolePagePermission.page_id).where(
                    RolePagePermission.role == user.role
                )
            )
        )
    return CurrentUserRead(
        user_id=user.id,
        email=user.email,
        full_name=user.full_name,
        role=user.role,
        accessible_page_ids=accessible,
    )
