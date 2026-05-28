from __future__ import annotations

import uuid

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models import Page


def list_all(session: Session) -> list[Page]:
    return list(session.scalars(select(Page).order_by(Page.parent_id, Page.position)))


def build_tree(pages: list[Page]) -> list[dict]:
    """Turn a flat list of pages into a nested tree, sorted by position."""
    by_parent: dict[uuid.UUID | None, list[Page]] = {}
    for p in pages:
        by_parent.setdefault(p.parent_id, []).append(p)

    def node(p: Page) -> dict:
        return {
            "id": p.id,
            "parent_id": p.parent_id,
            "slug": p.slug,
            "title": p.title,
            "position": p.position,
            "created_at": p.created_at,
            "updated_at": p.updated_at,
            "children": [
                node(c) for c in sorted(by_parent.get(p.id, []), key=lambda x: x.position)
            ],
        }

    roots = sorted(by_parent.get(None, []), key=lambda x: x.position)
    return [node(p) for p in roots]


def get_by_path(session: Session, path: str) -> Page | None:
    """Resolve a slash-separated slug path to a Page (e.g. 'operacao-interna/seguros')."""
    slugs = [s for s in path.strip("/").split("/") if s]
    if not slugs:
        return None
    parent_id: uuid.UUID | None = None
    page: Page | None = None
    for slug in slugs:
        if parent_id is None:
            page = session.scalar(
                select(Page).where(Page.parent_id.is_(None), Page.slug == slug)
            )
        else:
            page = session.scalar(
                select(Page).where(Page.parent_id == parent_id, Page.slug == slug)
            )
        if page is None:
            return None
        parent_id = page.id
    return page
