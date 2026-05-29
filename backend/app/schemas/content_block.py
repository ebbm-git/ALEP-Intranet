from __future__ import annotations

import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class ContentBlockBase(BaseModel):
    block_type: str = Field(default="markdown", max_length=32)
    body: str = ""


class ContentBlockCreate(ContentBlockBase):
    page_id: uuid.UUID


class ContentBlockUpdate(BaseModel):
    body: str | None = None
    block_type: str | None = Field(default=None, max_length=32)


class ContentBlockRead(ContentBlockBase):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    page_id: uuid.UUID
    # Versioning fields. External programs that want the live content should
    # filter blocks by `is_current = true`. `lineage_id` is the stable identifier
    # to use across edits.
    lineage_id: uuid.UUID
    version: int
    is_current: bool
    position: int
    created_at: datetime
    updated_at: datetime
