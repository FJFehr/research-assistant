"""Extract highlights and margin notes from an annotated PDF.

Usage:
    python src/extract.py "annotated papers/foo.pdf"

Writes: extracted/foo.txt
"""

import re
import sys
from pathlib import Path

import fitz  # pymupdf


# ---------------------------------------------------------------------------
# Colour mapping
# ---------------------------------------------------------------------------

def rgb_to_colour(rgb: tuple | None) -> str:
    """Map an RGB float tuple (0–1 each) to a human-readable colour name."""
    if rgb is None:
        return "yellow"
    r, g, b = rgb
    if r > 0.8 and b < 0.3:
        if g > 0.7:
            return "yellow"
        if g > 0.3:
            return "orange"
    if r < 0.35 and g > 0.55 and b < 0.35:
        return "green"
    if r > 0.65 and g < 0.35 and b < 0.35:
        return "red"
    if r < 0.35 and g < 0.35 and b > 0.55:
        return "blue"
    if r > 0.55 and g < 0.35 and b > 0.55:
        return "purple"
    if r > 0.7 and g < 0.55 and b > 0.45:
        return "pink"
    return "yellow"  # default for ambiguous colours


# ---------------------------------------------------------------------------
# Spatial helpers
# ---------------------------------------------------------------------------

def note_position(rect: fitz.Rect, page_width: float) -> str:
    """Classify a note's horizontal position as left, right, or inline."""
    if rect.x0 < page_width * 0.35:
        return "left"
    if rect.x0 > page_width * 0.65:
        return "right"
    return "inline"


# ---------------------------------------------------------------------------
# Per-page extraction
# ---------------------------------------------------------------------------

def extract_page(page: fitz.Page) -> tuple[str, int, int]:
    """Extract text with annotations interleaved for a single page.

    Returns (annotated_text, highlight_count, note_count).
    """
    page_width = page.rect.width
    items: list[tuple[float, int, str]] = []  # (y, priority, content)
    # priority: 0 = text block, 1 = annotation (breaks y ties so text comes first)

    for block in page.get_text("blocks"):
        if block[6] != 0:  # skip non-text blocks (images, etc.)
            continue
        text = block[4].strip()
        if not text:
            continue
        items.append((block[1], 0, text))  # y0 as sort key

    n_highlights = 0
    n_notes = 0

    for i, annot in enumerate(page.annots()):
        atype = annot.type[0]
        try:
            if atype == 8:  # Highlight
                colours = annot.colors
                rgb = colours.get("stroke") or colours.get("fill")
                colour = rgb_to_colour(rgb)
                highlighted = page.get_textbox(annot.rect).strip()
                # Collapse internal whitespace/newlines to a single space
                highlighted = re.sub(r"\s+", " ", highlighted)
                if not highlighted:
                    print(
                        f"  WARNING: empty highlight text — page annotation index {i}",
                        file=sys.stderr,
                    )
                    continue
                items.append(
                    (annot.rect.y0, 1, f'[HIGHLIGHT {colour}: "{highlighted}"]')
                )
                n_highlights += 1

            elif atype in (0, 2):  # Text note (popup) or FreeText annotation
                content = annot.info.get("content", "").strip()
                if not content:
                    print(
                        f"  WARNING: empty note text — page annotation index {i}",
                        file=sys.stderr,
                    )
                    continue
                position = note_position(annot.rect, page_width)
                items.append(
                    (annot.rect.y0, 1, f'[NOTE {position}: "{content}"]')
                )
                n_notes += 1

            else:
                print(
                    f"  WARNING: unclassified annotation type {atype} — page annotation index {i}",
                    file=sys.stderr,
                )

        except Exception as exc:
            print(
                f"  WARNING: failed to extract annotation index {i} (type {atype}): {exc}",
                file=sys.stderr,
            )

    items.sort(key=lambda x: (x[0], x[1]))
    return "\n".join(item[2] for item in items), n_highlights, n_notes


# ---------------------------------------------------------------------------
# Main extraction loop
# ---------------------------------------------------------------------------

def extract(pdf_path: Path, out_path: Path) -> tuple[int, int, int]:
    """Extract annotations from pdf_path and write to out_path.

    Returns (page_count, total_highlights, total_notes).
    """
    doc = fitz.open(pdf_path)
    total_highlights = 0
    total_notes = 0
    parts: list[str] = []

    for page_num, page in enumerate(doc, start=1):
        parts.append(f"--- Page {page_num} ---")
        page_text, n_h, n_n = extract_page(page)
        if page_text:
            parts.append(page_text)
        total_highlights += n_h
        total_notes += n_n

    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text("\n\n".join(parts), encoding="utf-8")

    return len(doc), total_highlights, total_notes


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def main() -> None:
    if len(sys.argv) != 2:
        print("Usage: python src/extract.py \"annotated papers/foo.pdf\"", file=sys.stderr)
        sys.exit(1)

    pdf_path = Path(sys.argv[1])
    if not pdf_path.exists():
        print(f"Error: file not found: {pdf_path}", file=sys.stderr)
        sys.exit(1)

    out_path = Path("extracted") / (pdf_path.stem + ".txt")
    n_pages, n_highlights, n_notes = extract(pdf_path, out_path)

    print(f"Pages:      {n_pages}")
    print(f"Highlights: {n_highlights}")
    print(f"Notes:      {n_notes}")
    print(f"Output:     {out_path}")

    if n_highlights == 0:
        print("WARNING: no highlights found — was the PDF annotated?", file=sys.stderr)
    if n_notes == 0:
        print("WARNING: no margin notes found — was the PDF annotated?", file=sys.stderr)


if __name__ == "__main__":
    main()
