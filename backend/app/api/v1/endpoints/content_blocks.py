from __future__ import annotations

import uuid

from fastapi import APIRouter, Depends, HTTPException, Response, status
from sqlalchemy.orm import Session

from app.core.auth import CurrentUser, get_current_user
from app.core.permissions import (
    can_edit,
    can_view,
    require_delete_block,
    require_edit_block,
)
from app.db.session import get_db
from app.schemas import ContentBlockCreate, ContentBlockRead, ContentBlockUpdate
from app.services import content_blocks as svc

router = APIRouter()


@router.post("", response_model=ContentBlockRead, status_code=status.HTTP_201_CREATED)
def create_block(
    payload: ContentBlockCreate,
    user: CurrentUser = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> ContentBlockRead:
    # Need edit permission on the target page to add a new block to it.
    if not can_edit(db, user, payload.page_id):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You don't have edit permission on this page",
        )
    block = svc.append_block(
        db, payload.page_id, body=payload.body, block_type=payload.block_type
    )
    return ContentBlockRead.model_validate(block)


@router.post(
    "/{block_id}/insert-above",
    response_model=ContentBlockRead,
    status_code=status.HTTP_201_CREATED,
)
def insert_above(
    block_id: uuid.UUID,
    payload: ContentBlockUpdate | None = None,
    _: CurrentUser = Depends(require_edit_block),
    db: Session = Depends(get_db),
) -> ContentBlockRead:
    body = (payload.body if payload else None) or ""
    block_type = (payload.block_type if payload else None) or "markdown"
    block = svc.insert_at(db, block_id, "above", body=body, block_type=block_type)
    return ContentBlockRead.model_validate(block)


@router.post(
    "/{block_id}/insert-below",
    response_model=ContentBlockRead,
    status_code=status.HTTP_201_CREATED,
)
def insert_below(
    block_id: uuid.UUID,
    payload: ContentBlockUpdate | None = None,
    _: CurrentUser = Depends(require_edit_block),
    db: Session = Depends(get_db),
) -> ContentBlockRead:
    body = (payload.body if payload else None) or ""
    block_type = (payload.block_type if payload else None) or "markdown"
    block = svc.insert_at(db, block_id, "below", body=body, block_type=block_type)
    return ContentBlockRead.model_validate(block)


@router.patch("/{block_id}", response_model=ContentBlockRead)
def update_block(
    block_id: uuid.UUID,
    payload: ContentBlockUpdate,
    _: CurrentUser = Depends(require_edit_block),
    db: Session = Depends(get_db),
) -> ContentBlockRead:
    block = svc.update_block(db, block_id, body=payload.body, block_type=payload.block_type)
    return ContentBlockRead.model_validate(block)


@router.get("/{block_id}/versions", response_model=list[ContentBlockRead])
def list_versions(
    block_id: uuid.UUID,
    user: CurrentUser = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> list[ContentBlockRead]:
    versions = svc.list_versions(db, block_id)
    if versions and not can_view(db, user, versions[0].page_id):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, detail="No access to this page"
        )
    return [ContentBlockRead.model_validate(v) for v in versions]


@router.post(
    "/{block_id}/restore/{version}",
    response_model=ContentBlockRead,
    status_code=status.HTTP_201_CREATED,
)
def restore_version(
    block_id: uuid.UUID,
    version: int,
    _: CurrentUser = Depends(require_edit_block),
    db: Session = Depends(get_db),
) -> ContentBlockRead:
    block = svc.restore_version(db, block_id, version)
    return ContentBlockRead.model_validate(block)


@router.delete(
    "/{block_id}", status_code=status.HTTP_204_NO_CONTENT, response_class=Response
)
def delete_block(
    block_id: uuid.UUID,
    _: CurrentUser = Depends(require_delete_block),
    db: Session = Depends(get_db),
) -> Response:
    svc.delete_block(db, block_id)
    return Response(status_code=status.HTTP_204_NO_CONTENT)
