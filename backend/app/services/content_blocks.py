from __future__ import annotations

import uuid

from fastapi import HTTPException
from sqlalchemy import delete, func, select, update
from sqlalchemy.orm import Session

from app.models import ContentBlock, Page

MAX_VERSIONS_PER_LINEAGE = 5


# ---------- helpers ----------


def _ensure_page(session: Session, page_id: uuid.UUID) -> Page:
    page = session.get(Page, page_id)
    if page is None:
        raise HTTPException(status_code=404, detail="Page not found")
    return page


def _get_block_any_version(session: Session, block_id: uuid.UUID) -> ContentBlock:
    block = session.get(ContentBlock, block_id)
    if block is None:
        raise HTTPException(status_code=404, detail="Block not found")
    return block


def _get_current_for_lineage(session: Session, lineage_id: uuid.UUID) -> ContentBlock:
    """Return the is_current row for a given lineage."""
    current = session.scalar(
        select(ContentBlock).where(
            ContentBlock.lineage_id == lineage_id, ContentBlock.is_current.is_(True)
        )
    )
    if current is None:
        raise HTTPException(
            status_code=404, detail="No current version found for this block lineage"
        )
    return current


def _resolve_to_current(session: Session, block_id: uuid.UUID) -> ContentBlock:
    """Given any version's id (current or historical), return the current row of
    that block's lineage. Edits and inserts always operate on the current row."""
    any_version = _get_block_any_version(session, block_id)
    if any_version.is_current:
        return any_version
    return _get_current_for_lineage(session, any_version.lineage_id)


def _prune_old_versions(session: Session, lineage_id: uuid.UUID) -> int:
    """Keep at most MAX_VERSIONS_PER_LINEAGE rows for a lineage; delete the rest
    (oldest first). Returns how many rows were deleted."""
    rows = list(
        session.scalars(
            select(ContentBlock)
            .where(ContentBlock.lineage_id == lineage_id)
            .order_by(ContentBlock.version.desc())
        )
    )
    if len(rows) <= MAX_VERSIONS_PER_LINEAGE:
        return 0
    to_delete = rows[MAX_VERSIONS_PER_LINEAGE:]
    for r in to_delete:
        session.delete(r)
    return len(to_delete)


# ---------- read ----------


def list_for_page(session: Session, page_id: uuid.UUID) -> list[ContentBlock]:
    """Only the CURRENT version of each lineage on this page, ordered by position."""
    return list(
        session.scalars(
            select(ContentBlock)
            .where(ContentBlock.page_id == page_id, ContentBlock.is_current.is_(True))
            .order_by(ContentBlock.position)
        )
    )


def list_versions(session: Session, block_id: uuid.UUID) -> list[ContentBlock]:
    """All versions of the lineage that `block_id` belongs to, newest first."""
    any_version = _get_block_any_version(session, block_id)
    return list(
        session.scalars(
            select(ContentBlock)
            .where(ContentBlock.lineage_id == any_version.lineage_id)
            .order_by(ContentBlock.version.desc())
        )
    )


# ---------- write ----------


def append_block(
    session: Session,
    page_id: uuid.UUID,
    *,
    body: str = "",
    block_type: str = "markdown",
) -> ContentBlock:
    _ensure_page(session, page_id)
    max_pos = session.scalar(
        select(func.coalesce(func.max(ContentBlock.position), -1)).where(
            ContentBlock.page_id == page_id, ContentBlock.is_current.is_(True)
        )
    )
    block = ContentBlock(
        page_id=page_id,
        lineage_id=uuid.uuid4(),
        version=1,
        is_current=True,
        position=int(max_pos) + 1,
        block_type=block_type,
        body=body,
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
    """Insert a new logical block above or below the anchor block on the same page.
    Positions of all rows (current + history) >= new_pos shift by +1 — versions
    of the same lineage share a position so they move together."""
    if where not in ("above", "below"):
        raise HTTPException(status_code=400, detail="where must be 'above' or 'below'")
    anchor = _resolve_to_current(session, anchor_id)
    new_pos = anchor.position if where == "above" else anchor.position + 1

    session.execute(
        update(ContentBlock)
        .where(ContentBlock.page_id == anchor.page_id, ContentBlock.position >= new_pos)
        .values(position=ContentBlock.position + 1)
    )
    block = ContentBlock(
        page_id=anchor.page_id,
        lineage_id=uuid.uuid4(),
        version=1,
        is_current=True,
        position=new_pos,
        block_type=block_type,
        body=body,
    )
    session.add(block)
    session.commit()
    session.refresh(block)
    return block


def update_block(
    session: Session,
    block_id: uuid.UUID,
    *,
    body: str | None,
    block_type: str | None,
) -> ContentBlock:
    """Copy-on-write: insert a new is_current=True row with version+1; mark old
    current as historical (is_current=False); prune oldest if >5 versions."""
    current = _resolve_to_current(session, block_id)

    new_body = body if body is not None else current.body
    new_type = block_type if block_type is not None else current.block_type

    # No-op edit: nothing changed, return as-is (don't create a no-op version).
    if new_body == current.body and new_type == current.block_type:
        return current

    current.is_current = False
    session.flush()

    new_version = ContentBlock(
        page_id=current.page_id,
        lineage_id=current.lineage_id,
        version=current.version + 1,
        is_current=True,
        position=current.position,
        block_type=new_type,
        body=new_body,
    )
    session.add(new_version)
    session.flush()

    _prune_old_versions(session, current.lineage_id)

    session.commit()
    session.refresh(new_version)
    return new_version


def restore_version(
    session: Session, block_id: uuid.UUID, version: int
) -> ContentBlock:
    """Make the given historical version's body the new current version.
    Implemented as an edit: insert a new version with the old body, mark old
    current as historical, prune."""
    any_version = _get_block_any_version(session, block_id)
    target = session.scalar(
        select(ContentBlock).where(
            ContentBlock.lineage_id == any_version.lineage_id,
            ContentBlock.version == version,
        )
    )
    if target is None:
        raise HTTPException(
            status_code=404, detail=f"Version {version} not found for this block"
        )
    # Restore via the normal edit path (so prune + history logic apply uniformly).
    # update_block resolves any-version-id to current via _resolve_to_current.
    return update_block(
        session, any_version.id, body=target.body, block_type=target.block_type
    )


def delete_block(session: Session, block_id: uuid.UUID) -> None:
    """Delete the ENTIRE lineage (all versions). Compact positions to close
    the gap left on the page."""
    current = _resolve_to_current(session, block_id)
    page_id = current.page_id
    pos = current.position
    lineage = current.lineage_id

    session.execute(delete(ContentBlock).where(ContentBlock.lineage_id == lineage))
    session.execute(
        update(ContentBlock)
        .where(ContentBlock.page_id == page_id, ContentBlock.position > pos)
        .values(position=ContentBlock.position - 1)
    )
    session.commit()
