from __future__ import annotations

import uuid

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.models import Page
from app.schemas import ContentBlockRead, PageRead, PageTreeNode
from app.services import content_blocks as cb_svc
from app.services import pages as page_svc

router = APIRouter()


@router.get("/tree", response_model=list[PageTreeNode])
def get_tree(db: Session = Depends(get_db)) -> list[dict]:
    return page_svc.build_tree(page_svc.list_all(db))


@router.get("/by-path/{path:path}")
def get_by_path(path: str, db: Session = Depends(get_db)) -> dict:
    page = page_svc.get_by_path(db, path)
    if page is None:
        raise HTTPException(status_code=404, detail="Page not found")
    blocks = cb_svc.list_for_page(db, page.id)
    return {
        "page": PageRead.model_validate(page),
        "blocks": [ContentBlockRead.model_validate(b) for b in blocks],
    }


@router.get("/{page_id}", response_model=PageRead)
def get_page(page_id: uuid.UUID, db: Session = Depends(get_db)) -> PageRead:
    page = db.get(Page, page_id)
    if page is None:
        raise HTTPException(status_code=404, detail="Page not found")
    return PageRead.model_validate(page)
