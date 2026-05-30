"""Authorization helpers — translate (role, page) into allowed actions."""

from __future__ import annotations

import uuid

from fastapi import Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.auth import CurrentUser, get_current_user
from app.db.session import get_db
from app.models import ContentBlock, Page, RolePagePermission, UserRole

# Roles that, when granted access to a page, may also edit its content.
_EDIT_CAPABLE_ROLES = {UserRole.editor_chief, UserRole.editor_a, UserRole.editor_b}
# Roles that, when granted access to a page, may also delete blocks.
_DELETE_CAPABLE_ROLES = {UserRole.editor_chief}


def has_page_access(db: Session, user: CurrentUser, page_id: uuid.UUID) -> bool:
    """Admins always have access. Non-admin roles need an explicit row."""
    if user.role is UserRole.admin:
        return True
    return (
        db.scalar(
            select(RolePagePermission.role).where(
                RolePagePermission.role == user.role,
                RolePagePermission.page_id == page_id,
            )
        )
        is not None
    )


def can_view(db: Session, user: CurrentUser, page_id: uuid.UUID) -> bool:
    return has_page_access(db, user, page_id)


def can_edit(db: Session, user: CurrentUser, page_id: uuid.UUID) -> bool:
    if user.role is UserRole.admin:
        return True
    if user.role not in _EDIT_CAPABLE_ROLES:
        return False
    return has_page_access(db, user, page_id)


def can_delete(db: Session, user: CurrentUser, page_id: uuid.UUID) -> bool:
    if user.role is UserRole.admin:
        return True
    if user.role not in _DELETE_CAPABLE_ROLES:
        return False
    return has_page_access(db, user, page_id)


def can_create_pages(user: CurrentUser) -> bool:
    return user.role is UserRole.admin


def can_access_settings(user: CurrentUser) -> bool:
    return user.role is UserRole.admin


# ---------- FastAPI dependency factories ----------


def require_admin(user: CurrentUser = Depends(get_current_user)) -> CurrentUser:
    if user.role is not UserRole.admin:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Admin only")
    return user


def _resolve_page_id_from_block(db: Session, block_id: uuid.UUID) -> uuid.UUID:
    page_id = db.scalar(
        select(ContentBlock.page_id).where(ContentBlock.id == block_id)
    )
    if page_id is None:
        raise HTTPException(status_code=404, detail="Block not found")
    return page_id


def require_edit_block(
    block_id: uuid.UUID,
    user: CurrentUser = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> CurrentUser:
    page_id = _resolve_page_id_from_block(db, block_id)
    if not can_edit(db, user, page_id):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You don't have edit permission on this page",
        )
    return user


def require_delete_block(
    block_id: uuid.UUID,
    user: CurrentUser = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> CurrentUser:
    page_id = _resolve_page_id_from_block(db, block_id)
    if not can_delete(db, user, page_id):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You don't have delete permission on this page",
        )
    return user


def require_view_page(
    page_id: uuid.UUID,
    user: CurrentUser = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> CurrentUser:
    if not can_view(db, user, page_id):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You don't have access to this page",
        )
    return user
