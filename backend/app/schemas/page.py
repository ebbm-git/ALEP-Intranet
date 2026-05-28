from __future__ import annotations

import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class PageBase(BaseModel):
    slug: str = Field(..., max_length=120)
    title: str = Field(..., max_length=255)


class PageCreate(PageBase):
    parent_id: uuid.UUID | None = None
    position: int | None = None


class PageUpdate(BaseModel):
    title: str | None = Field(default=None, max_length=255)
    slug: str | None = Field(default=None, max_length=120)
    position: int | None = None


class PageRead(PageBase):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    parent_id: uuid.UUID | None
    position: int
    created_at: datetime
    updated_at: datetime


class PageTreeNode(PageRead):
    children: list["PageTreeNode"] = Field(default_factory=list)


PageTreeNode.model_rebuild()
