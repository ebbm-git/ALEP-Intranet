"""Extract real content from the ALEP Onboarding PDF, one Markdown body per section.

Outputs:
    scripts/_extracted_images/<slug-as-path>__N.png   image files
    scripts/_extracted_content.json                   { slug -> {body, images} }

Image URLs in the Markdown body are placeholders of the form
`{{IMG:relative/path.png}}`. A later step replaces them with the public
Supabase Storage URLs after upload.
"""

from __future__ import annotations

import json
import logging
import re
import sys
from pathlib import Path

import fitz  # PyMuPDF — for image extraction
import pdfplumber  # for text + table extraction (best layout fidelity)

# Silence pdfminer's noisy FontBBox warnings.
logging.getLogger("pdfminer").setLevel(logging.ERROR)

BACKEND = Path(__file__).resolve().parent.parent
PDF_PATH = BACKEND.parent / "docs" / "ALEP_Manual_Onboarding_2026_v1.pdf"
SECTION_MAP = BACKEND / "scripts" / "_section_map.json"
OUT_JSON = BACKEND / "scripts" / "_extracted_content.json"
IMG_DIR = BACKEND / "scripts" / "_extracted_images"


HEADER_FOOTER_PATTERNS = [
    re.compile(r"^ALEP\s*[—-]\s*Manual de Onboarding", re.IGNORECASE),
    re.compile(r"^Confidencial\s*[—-]\s*Uso Interno", re.IGNORECASE),
    re.compile(r"^\s*\d+\s*$"),  # bare page numbers
]

SUBSECTION_HEADING = re.compile(r"^([1-9]\.\d+)\s+(.+)$")
NUMBERED_LIST_ITEM = re.compile(r"^(\d+)\.\s+(.+)$")
BULLET_LIST_ITEM = re.compile(r"^[•●◦·]\s+(.+)$")


def is_header_footer(line: str) -> bool:
    s = line.strip()
    return any(p.match(s) for p in HEADER_FOOTER_PATTERNS)


def clean_text_block(text: str) -> str:
    """Drop header/footer + zero-width chars; merge soft line wraps within
    paragraphs but preserve list/heading structure."""
    raw_lines = [ln.replace("​", "").rstrip() for ln in text.split("\n")]
    raw_lines = [ln for ln in raw_lines if not is_header_footer(ln)]

    paragraphs: list[str] = []
    current: list[str] = []

    def flush() -> None:
        if current:
            paragraphs.append(" ".join(current).strip())
            current.clear()

    for line in raw_lines:
        s = line.strip()
        if not s:
            flush()
            continue
        # Sub-section heading like "6.1 Tipos..." → its own paragraph (level-2 heading)
        m = SUBSECTION_HEADING.match(s)
        if m:
            flush()
            paragraphs.append(f"## {m.group(1)} {m.group(2)}")
            continue
        # List item starts a fresh "paragraph"
        if NUMBERED_LIST_ITEM.match(s) or BULLET_LIST_ITEM.match(s):
            flush()
            current.append(s)
            continue
        # Plain continuation
        current.append(s)
    flush()

    # Normalize bullets: keep numbered items "1. Foo"; convert "• Foo" to "- Foo"
    normalized: list[str] = []
    for p in paragraphs:
        m = BULLET_LIST_ITEM.match(p)
        if m:
            normalized.append(f"- {m.group(1)}")
        else:
            normalized.append(p)
    return "\n\n".join(normalized).strip()


def markdownify_table(rows: list[list[str | None]]) -> str:
    """Turn a 2D list into a GFM Markdown table. Returns '' for degenerate cases."""
    cleaned = []
    for row in rows:
        cells = [(c or "").strip().replace("\n", " ").replace("|", "\\|") for c in row]
        if any(cells):
            cleaned.append(cells)
    if not cleaned:
        return ""
    n_cols = max(len(r) for r in cleaned)
    # Skip "tables" that are really just a single styled cell — render as blockquote
    if n_cols == 1:
        return "> **" + cleaned[0][0] + "**\n>\n" + "\n".join(
            f"> {r[0]}" for r in cleaned[1:]
        )
    cleaned = [r + [""] * (n_cols - len(r)) for r in cleaned]
    header, *body = cleaned
    md = "| " + " | ".join(header) + " |\n"
    md += "| " + " | ".join(["---"] * n_cols) + " |\n"
    for row in body:
        md += "| " + " | ".join(row) + " |\n"
    return md.rstrip()


def text_in_bboxes(words: list[dict], bboxes: list[tuple[float, float, float, float]]) -> bool:
    """Helper not currently used (kept for clarity)."""
    return False


def page_to_markdown(page) -> str:
    """Use pdfplumber to render a page as Markdown: text (masked) + tables in order."""
    tables = page.find_tables()
    table_bboxes = [t.bbox for t in tables]

    # Extract words excluding any inside a table bbox
    def in_any_bbox(word: dict) -> bool:
        for x0, top, x1, bottom in table_bboxes:
            if (
                word["x0"] >= x0 - 1
                and word["x1"] <= x1 + 1
                and word["top"] >= top - 1
                and word["bottom"] <= bottom + 1
            ):
                return True
        return False

    # Reconstruct text from non-table words, line by line by Y position
    words = [w for w in page.extract_words(use_text_flow=True) if not in_any_bbox(w)]

    # Track table positions by their top Y so we interleave them with text correctly
    table_positions = sorted(
        [(t.bbox[1], i) for i, t in enumerate(tables)], key=lambda x: x[0]
    )

    # Group words into lines by approximate Y, then reassemble paragraphs
    if words:
        words.sort(key=lambda w: (round(w["top"]), w["x0"]))
        lines_by_y: list[tuple[float, str]] = []
        current_y: float | None = None
        current_words: list[str] = []
        for w in words:
            y = round(w["top"])
            if current_y is None or abs(y - current_y) <= 2:
                current_words.append(w["text"])
                current_y = current_y if current_y is not None else y
            else:
                lines_by_y.append((current_y, " ".join(current_words)))
                current_y = y
                current_words = [w["text"]]
        if current_words:
            lines_by_y.append((current_y, " ".join(current_words)))
    else:
        lines_by_y = []

    # Interleave: emit text lines, and when we cross a table's Y, emit the table
    parts: list[tuple[float, str]] = []
    for y, line in lines_by_y:
        parts.append((y, ("TEXT", line)))
    for top_y, ti in table_positions:
        extracted = tables[ti].extract()
        md = markdownify_table(extracted)
        if md:
            parts.append((top_y, ("TABLE", md)))
    parts.sort(key=lambda x: x[0])

    # Glue text lines back into paragraphs (run of TEXTs), then tables interleaved
    out_parts: list[str] = []
    text_buf: list[str] = []

    def flush_text() -> None:
        if text_buf:
            md_text = clean_text_block("\n".join(text_buf))
            if md_text:
                out_parts.append(md_text)
            text_buf.clear()

    for _, payload in parts:
        kind, content = payload
        if kind == "TEXT":
            text_buf.append(content)
        else:
            flush_text()
            out_parts.append(content)
    flush_text()
    return "\n\n".join(out_parts).strip()


def slice_markdown_for_section(
    page_md: str, *, heading: str, next_heading: str | None, is_first_page: bool
) -> str:
    """If multiple sections share a page, trim to just the current section's slice."""
    text = page_md
    if is_first_page and heading:
        idx = text.find(heading)
        if idx >= 0:
            text = text[idx:]
            # Drop the heading line itself — the DB already has the page title.
            nl = text.find("\n")
            if nl >= 0:
                text = text[nl + 1 :].lstrip()
    if next_heading:
        idx = text.find(next_heading)
        if idx >= 0:
            text = text[:idx].rstrip()
    return text


def heading_text_only(heading: str) -> str:
    """'1.1 História e Percurso da ALEP' -> match string for find()."""
    return heading


def main() -> None:
    if not SECTION_MAP.exists():
        print("Run the mapping step first.", file=sys.stderr)
        sys.exit(1)
    sections = json.loads(SECTION_MAP.read_text(encoding="utf-8"))

    IMG_DIR.mkdir(exist_ok=True)
    for f in IMG_DIR.glob("*.png"):
        f.unlink()

    doc = fitz.open(PDF_PATH)
    pdf = pdfplumber.open(PDF_PATH)

    by_idx = sorted(enumerate(sections), key=lambda kv: kv[1]["start_page_idx"])
    nexts = {}
    for pos, (_, sec) in enumerate(by_idx):
        nxt = by_idx[pos + 1][1] if pos + 1 < len(by_idx) else None
        nexts[sec["slug"]] = nxt["heading"] if nxt else None

    extracted: dict[str, dict] = {}
    used_images: set[tuple[int, int]] = set()

    # Pre-render each page once (expensive)
    page_markdowns: dict[int, str] = {}

    for sec in sections:
        slug = sec["slug"]
        start = sec["start_page_idx"]
        end = max(sec["end_page_idx"], start)
        heading = sec["heading"]
        next_heading = nexts[slug]
        image_refs: list[str] = []
        parts: list[str] = []

        for pidx in range(start, end + 1):
            if pidx not in page_markdowns:
                page_markdowns[pidx] = page_to_markdown(pdf.pages[pidx])
            page_md = page_markdowns[pidx]

            slice_md = slice_markdown_for_section(
                page_md,
                heading=heading,
                next_heading=next_heading if next_heading and next_heading in page_md else None,
                is_first_page=(pidx == start),
            )
            if slice_md:
                parts.append(slice_md)

            # Images (PyMuPDF), deduped, with safety against rendering same image twice.
            for n, img in enumerate(doc[pidx].get_images(full=True), start=1):
                xref = img[0]
                if (pidx, xref) in used_images:
                    continue
                used_images.add((pidx, xref))
                try:
                    pix = fitz.Pixmap(doc, xref)
                    if pix.n - pix.alpha >= 4:
                        pix = fitz.Pixmap(fitz.csRGB, pix)
                    safe_slug = slug.replace("/", "__")
                    fname = f"{safe_slug}__p{pidx+1}_n{n}.png"
                    (IMG_DIR / fname).parent.mkdir(parents=True, exist_ok=True)
                    pix.save(str(IMG_DIR / fname))
                    pix = None
                    image_refs.append(fname)
                    parts.append(f"![{slug}]({{{{IMG:{fname}}}}})")
                except Exception as e:
                    print(f"  warn: image xref={xref} on p{pidx+1}: {e}")

        body = "\n\n".join(parts).strip()
        extracted[slug] = {"body": body, "images": image_refs, "page_range": [start + 1, end + 1]}
        print(f"  {slug:<55}  {len(body):>5} chars  {len(image_refs):>2} img")

    pdf.close()
    doc.close()

    OUT_JSON.write_text(
        json.dumps(extracted, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    print(f"\nWrote {OUT_JSON.relative_to(BACKEND)}  ({len(extracted)} sections)")


if __name__ == "__main__":
    main()
