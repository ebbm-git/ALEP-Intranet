from __future__ import annotations

import uuid

from fastapi import APIRouter, Depends, Response, status
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.schemas import ContentBlockCreate, ContentBlockRead, ContentBlockUpdate
from app.services import content_blocks as svc

router = APIRouter()


@router.post("", response_model=ContentBlockRead, status_code=status.HTTP_201_CREATED)
def create_block(payload: ContentBlockCreate, db: Session = Depends(get_db)) -> ContentBlockRead:
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
    db: Session = Depends(get_db),
) -> ContentBlockRead:
    body = (payload.body if payload else None) or ""
    block_type = (payload.block_type if payload else None) or "markdown"
    block = svc.insert_at(db, block_id, "below", body=body, block_type=block_type)
    return ContentBlockRead.model_validate(block)


@router.patch("/{block_id}", response_model=ContentBlockRead)
def update_block(
    block_id: uuid.UUID, payload: ContentBlockUpdate, db: Session = Depends(get_db)
) -> ContentBlockRead:
    block = svc.update_block(db, block_id, body=payload.body, block_type=payload.block_type)
    return ContentBlockRead.model_validate(block)


@router.delete("/{block_id}", status_code=status.HTTP_204_NO_CONTENT, response_class=Response)
def delete_block(block_id: uuid.UUID, db: Session = Depends(get_db)) -> Response:
    svc.delete_block(db, block_id)
    return Response(status_code=status.HTTP_204_NO_CONTENT)
