from __future__ import annotations

import uuid

from fastapi import HTTPException
from sqlalchemy import func, select, update
from sqlalchemy.orm import Session

from app.models import ContentBlock, Page


def list_for_page(session: Session, page_id: uuid.UUID) -> list[ContentBlock]:
    return list(
        session.scalars(
            select(ContentBlock)
            .where(ContentBlock.page_id == page_id)
            .order_by(ContentBlock.position)
        )
    )


def _ensure_page(session: Session, page_id: uuid.UUID) -> Page:
    page = session.get(Page, page_id)
    if page is None:
        raise HTTPException(status_code=404, detail="Page not found")
    return page


def _get_block(session: Session, block_id: uuid.UUID) -> ContentBlock:
    block = session.get(ContentBlock, block_id)
    if block is None:
        raise HTTPException(status_code=404, detail="Block not found")
    return block


def append_block(
    session: Session, page_id: uuid.UUID, *, body: str = "", block_type: str = "markdown"
) -> ContentBlock:
    _ensure_page(session, page_id)
    max_pos = session.scalar(
        select(func.coalesce(func.max(ContentBlock.position), -1)).where(
            ContentBlock.page_id == page_id
        )
    )
    block = ContentBlock(
        page_id=page_id, position=int(max_pos) + 1, block_type=block_type, body=body
    )
    session.add(block)
    session.commit()
    session.refresh(block)
    return block


def insert_at(
    session: Session,
    anchor_id: uuid.UUID,
    where: str,
    *,
    body: str = "",
    block_type: str = "markdown",
) -> ContentBlock:
    """Insert a new block above or below the anchor block on the same page."""
    if where not in ("above", "below"):
        raise HTTPException(status_code=400, detail="where must be 'above' or 'below'")
    anchor = _get_block(session, anchor_id)
    new_pos = anchor.position if where == "above" else anchor.position + 1

    # Shift positions >= new_pos up by 1 within the same page.
    session.execute(
        update(ContentBlock)
        .where(ContentBlock.page_id == anchor.page_id, ContentBlock.position >= new_pos)
        .values(position=ContentBlock.position + 1)
    )
    block = ContentBlock(
        page_id=anchor.page_id, position=new_pos, block_type=block_type, body=body
    )
    session.add(block)
    session.commit()
    session.refresh(block)
    return block


def update_block(
    session: Session, block_id: uuid.UUID, *, body: str | None, block_type: str | None
) -> ContentBlock:
    block = _get_block(session, block_id)
    if body is not None:
        block.body = body
    if block_type is not None:
        block.block_type = block_type
    session.commit()
    session.refresh(block)
    return block


def delete_block(session: Session, block_id: uuid.UUID) -> None:
    block = _get_block(session, block_id)
    page_id = block.page_id
    pos = block.position
    session.delete(block)
    # Compact positions after the gap.
    session.execute(
        update(ContentBlock)
        .where(ContentBlock.page_id == page_id, ContentBlock.position > pos)
        .values(position=ContentBlock.position - 1)
    )
    session.commit()
