"""Upload extracted images to the Supabase Storage bucket "ALEP media"
and rewrite /intranet-images/<file> URLs in the DB to point at the bucket.

Idempotent:
- Re-uploads with `x-upsert: true` so existing objects get overwritten.
- Rewrites URLs only for blocks that still reference the local path.
"""

from __future__ import annotations

import os
import sys
import urllib.parse
from pathlib import Path

import httpx
from sqlalchemy import select, update

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from dotenv import load_dotenv  # noqa: E402

load_dotenv(Path(__file__).resolve().parent.parent / ".env", override=True)

from app.db.session import SessionLocal  # noqa: E402
from app.models import ContentBlock  # noqa: E402

BUCKET = "MediaGeral"
PREFIX = "intranet"  # path inside the bucket; full key = "intranet/<filename>"
IMG_DIR = Path(__file__).resolve().parent / "_extracted_images"

SUPA_URL = os.environ["SUPABASE_URL"].rstrip("/")
SECRET = os.environ["SUPABASE_SERVICE_ROLE_KEY"]
HEADERS = {"apikey": SECRET, "Authorization": f"Bearer {SECRET}"}


def ensure_bucket_public() -> None:
    """Flip the bucket to public so /object/public/* works."""
    r = httpx.put(
        f"{SUPA_URL}/storage/v1/bucket/{urllib.parse.quote(BUCKET, safe='')}",
        headers={**HEADERS, "Content-Type": "application/json"},
        json={"public": True},
        timeout=20,
    )
    r.raise_for_status()
    print(f"  Bucket {BUCKET!r} -> public: ok")


def upload_one(local: Path) -> str:
    """Upload one PNG, return its public URL."""
    key = f"{PREFIX}/{local.name}"
    encoded_bucket = urllib.parse.quote(BUCKET, safe="")
    encoded_key = urllib.parse.quote(key, safe="/")
    upload_url = f"{SUPA_URL}/storage/v1/object/{encoded_bucket}/{encoded_key}"
    with open(local, "rb") as f:
        r = httpx.post(
            upload_url,
            headers={
                **HEADERS,
                "Content-Type": "image/png",
                "x-upsert": "true",
            },
            content=f.read(),
            timeout=60,
        )
    if r.status_code not in (200, 201):
        raise RuntimeError(f"upload {local.name} failed: HTTP {r.status_code} {r.text}")
    public_url = f"{SUPA_URL}/storage/v1/object/public/{encoded_bucket}/{encoded_key}"
    return public_url


def rewrite_db_urls(mapping: dict[str, str]) -> int:
    """Replace each /intranet-images/<file> in content_blocks.body with new URL."""
    n_changed = 0
    with SessionLocal() as session:
        blocks = list(session.scalars(select(ContentBlock)))
        for b in blocks:
            original = b.body
            new = original
            for filename, new_url in mapping.items():
                old_url = f"/intranet-images/{filename}"
                if old_url in new:
                    new = new.replace(old_url, new_url)
            if new != original:
                b.body = new
                n_changed += 1
        session.commit()
    return n_changed


def main() -> None:
    files = sorted(IMG_DIR.glob("*.png"))
    if not files:
        print(f"No images found in {IMG_DIR}.")
        sys.exit(1)
    print(f"Uploading {len(files)} files to bucket {BUCKET!r}/{PREFIX}/ ...")

    ensure_bucket_public()

    mapping: dict[str, str] = {}
    for f in files:
        url = upload_one(f)
        mapping[f.name] = url
        print(f"  + {f.name}  ->  {url}")

    print("\nRewriting URLs in content_blocks ...")
    n = rewrite_db_urls(mapping)
    print(f"Updated {n} block(s).")

    # Verify by HEAD'ing one public URL
    sample = next(iter(mapping.values()))
    h = httpx.head(sample, timeout=15)
    print(f"\nSample HEAD {sample}\n  -> HTTP {h.status_code} ({h.headers.get('content-length','?')} bytes)")


if __name__ == "__main__":
    main()
