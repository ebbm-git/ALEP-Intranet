"""Replace each leaf page's placeholder block with the real extracted Markdown.

Idempotent: re-running is safe. If a page already has multiple blocks,
this script does *not* touch them (it only acts when the page has exactly
1 block whose body still starts with the placeholder marker).
"""

from __future__ import annotations

import json
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from dotenv import load_dotenv  # noqa: E402

load_dotenv(Path(__file__).resolve().parent.parent / ".env")

from sqlalchemy import select  # noqa: E402

from app.db.session import SessionLocal  # noqa: E402
from app.models import ContentBlock, Page  # noqa: E402
from app.services.pages import get_by_path  # noqa: E402

BACKEND = Path(__file__).resolve().parent.parent
EXTRACTED = BACKEND / "scripts" / "_extracted_content.json"

# Image URL prefix where the frontend serves them.
IMG_URL_PREFIX = "/intranet-images/"

PLACEHOLDER_MARKERS = (
    "_Conteúdo inicial",  # what the original seed script wrote
)


def resolve_image_refs(body: str) -> str:
    """Replace `{{IMG:filename.png}}` placeholders with the served URL."""
    def repl(m: re.Match[str]) -> str:
        fname = m.group(1)
        return f"{IMG_URL_PREFIX}{fname}"

    return re.sub(r"\{\{IMG:([^}]+)\}\}", repl, body)


def main() -> None:
    if not EXTRACTED.exists():
        print("Run extract_pdf_content.py first.", file=sys.stderr)
        sys.exit(1)
    data = json.loads(EXTRACTED.read_text(encoding="utf-8"))

    n_updated = n_skipped = n_missing = 0
    with SessionLocal() as session:
        for slug_path, payload in data.items():
            page = get_by_path(session, slug_path)
            if page is None:
                print(f"  ?  no page for slug '{slug_path}'")
                n_missing += 1
                continue

            blocks = list(
                session.scalars(
                    select(ContentBlock)
                    .where(ContentBlock.page_id == page.id)
                    .order_by(ContentBlock.position)
                )
            )

            body = resolve_image_refs(payload["body"])
            if not body.strip():
                print(f"  -  {slug_path}: empty extracted body — skipping")
                n_skipped += 1
                continue

            if len(blocks) == 1 and any(m in blocks[0].body for m in PLACEHOLDER_MARKERS):
                blocks[0].body = body
                blocks[0].block_type = "markdown"
                print(f"  +  {slug_path}: replaced placeholder ({len(body)} chars)")
                n_updated += 1
            elif len(blocks) == 0:
                session.add(
                    ContentBlock(
                        page_id=page.id, position=0, block_type="markdown", body=body
                    )
                )
                print(f"  +  {slug_path}: inserted first block ({len(body)} chars)")
                n_updated += 1
            else:
                print(
                    f"  =  {slug_path}: already has {len(blocks)} block(s), no placeholder — keeping"
                )
                n_skipped += 1

        session.commit()

    print(f"\nDone. updated={n_updated} skipped={n_skipped} missing={n_missing}")


if __name__ == "__main__":
    main()
