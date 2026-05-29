from __future__ import annotations

import uuid
from datetime import datetime

from sqlalchemy import (
    Boolean,
    DateTime,
    ForeignKey,
    Index,
    Integer,
    String,
    Text,
    func,
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base


class ContentBlock(Base):
    """
    A single editable unit on a page.

    Versioning model: each row is one *version* of a logical block.
    - `lineage_id` is the stable identifier shared by all versions of the same
      logical block. External programs should reference this when they want a
      stable link across edits.
    - `version` increases by 1 on each edit (1, 2, 3...).
    - `is_current` is the easy filter for external programs: WHERE is_current = TRUE
      gives the visible-on-the-page content. Exactly one current row per lineage.
    - Up to 5 versions per lineage are kept; oldest are pruned on edit.
    - Position is shared across all versions of a lineage (a reorder moves the
      whole history together).
    """

    __tablename__ = "content_blocks"
    __table_args__ = (
        Index("ix_content_blocks_page_position", "page_id", "position"),
        Index("ix_content_blocks_lineage_version", "lineage_id", "version"),
        Index("ix_content_blocks_page_current", "page_id", "is_current"),
    )

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, server_default=func.gen_random_uuid()
    )
    page_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("pages.id", ondelete="CASCADE"),
        nullable=False,
    )
    lineage_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), nullable=False, index=True
    )
    version: Mapped[int] = mapped_column(Integer, nullable=False, default=1)
    is_current: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    position: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    block_type: Mapped[str] = mapped_column(String(32), nullable=False, default="markdown")
    body: Mapped[str] = mapped_column(Text, nullable=False, default="")
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )

    page: Mapped["Page"] = relationship("Page", back_populates="blocks")  # noqa: F821
