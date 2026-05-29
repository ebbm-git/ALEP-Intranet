"""content block versioning: lineage_id, version, is_current

Revision ID: a1afe2a8d505
Revises: 70cddf6adcaf
Create Date: 2026-05-29 19:39:34.285955

Adds three columns to `content_blocks` so that each row represents one
*version* of a logical block:

- `lineage_id` (UUID, NOT NULL)   stable id shared across all versions of a block
- `version`    (INTEGER, NOT NULL) increases by 1 on each edit
- `is_current` (BOOLEAN, NOT NULL) TRUE for the visible row, FALSE for history

Existing rows are backfilled with lineage_id = id, version = 1, is_current = TRUE.
"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "a1afe2a8d505"
down_revision: Union[str, None] = "70cddf6adcaf"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # 1. Add columns as nullable so existing rows keep working.
    op.add_column(
        "content_blocks", sa.Column("lineage_id", postgresql.UUID(as_uuid=True), nullable=True)
    )
    op.add_column(
        "content_blocks",
        sa.Column("version", sa.Integer(), nullable=False, server_default="1"),
    )
    op.add_column(
        "content_blocks",
        sa.Column(
            "is_current", sa.Boolean(), nullable=False, server_default=sa.text("true")
        ),
    )

    # 2. Backfill lineage_id = id for every existing row (each is its own lineage).
    op.execute("UPDATE content_blocks SET lineage_id = id WHERE lineage_id IS NULL")

    # 3. Enforce NOT NULL on lineage_id now that it's populated.
    op.alter_column("content_blocks", "lineage_id", nullable=False)

    # 4. Indexes for the two most common access paths.
    op.create_index(
        "ix_content_blocks_lineage_version", "content_blocks", ["lineage_id", "version"]
    )
    op.create_index(
        "ix_content_blocks_page_current", "content_blocks", ["page_id", "is_current"]
    )


def downgrade() -> None:
    op.drop_index("ix_content_blocks_page_current", table_name="content_blocks")
    op.drop_index("ix_content_blocks_lineage_version", table_name="content_blocks")
    op.drop_column("content_blocks", "is_current")
    op.drop_column("content_blocks", "version")
    op.drop_column("content_blocks", "lineage_id")
