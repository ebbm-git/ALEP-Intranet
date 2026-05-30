from __future__ import annotations

import uuid

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.auth import CurrentUser, get_current_user
from app.core.permissions import can_view
from app.db.session import get_db
from app.models import Page, RolePagePermission, UserRole
from app.schemas import ContentBlockRead, PageRead, PageTreeNode
from app.services import content_blocks as cb_svc
from app.services import pages as page_svc

router = APIRouter()


def _accessible_page_ids(db: Session, user: CurrentUser) -> set[uuid.UUID]:
    if user.role is UserRole.admin:
        return set(db.scalars(select(Page.id)))
    return set(
        db.scalars(
            select(RolePagePermission.page_id).where(
                RolePagePermission.role == user.role
            )
        )
    )


def _filter_tree(nodes: list[dict], allowed: set[uuid.UUID]) -> list[dict]:
    """Keep a node if it (or any descendant) is in `allowed`. Drops empty branches."""
    out: list[dict] = []
    for node in nodes:
        children = _filter_tree(node.get("children", []), allowed)
        if node["id"] in allowed or children:
            new_node = {**node, "children": children}
            out.append(new_node)
    return out


@router.get("/tree", response_model=list[PageTreeNode])
def get_tree(
    user: CurrentUser = Depends(get_current_user), db: Session = Depends(get_db)
) -> list[dict]:
    full = page_svc.build_tree(page_svc.list_all(db))
    if user.role is UserRole.admin:
        return full
    allowed = _accessible_page_ids(db, user)
    return _filter_tree(full, allowed)


@router.get("/by-path/{path:path}")
def get_by_path(
    path: str,
    user: CurrentUser = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> dict:
    page = page_svc.get_by_path(db, path)
    if page is None:
        raise HTTPException(status_code=404, detail="Page not found")
    if not can_view(db, user, page.id):
        raise HTTPException(status_code=403, detail="No access to this page")
    blocks = cb_svc.list_for_page(db, page.id)
    return {
        "page": PageRead.model_validate(page),
        "blocks": [ContentBlockRead.model_validate(b) for b in blocks],
    }


@router.get("/{page_id}", response_model=PageRead)
def get_page(
    page_id: uuid.UUID,
    user: CurrentUser = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> PageRead:
    page = db.get(Page, page_id)
    if page is None:
        raise HTTPException(status_code=404, detail="Page not found")
    if not can_view(db, user, page.id):
        raise HTTPException(status_code=403, detail="No access to this page")
    return PageRead.model_validate(page)
