"""Extract highlights and margin notes from an annotated PDF.

Usage:
    python src/extract.py "papers/foo.pdf" [--url <paper_url>]

Writes: outputs/extracted/foo.txt
If --url is provided, fetches BibTeX and prepends to output.
"""

import argparse
import re
import sys
from pathlib import Path

import fitz  # pymupdf
from src.get_bibtex import get_bibtex_from_url


# ---------------------------------------------------------------------------
# Structural heading regexes
# ---------------------------------------------------------------------------

_SECTION_HEADING_RE = re.compile(
    r"^\d+\.?\s+\w|"
    r"^(?:Abstract|Introduction|Related Work|Background|Method(?:ology)?|"
    r"Experiment(?:s|al Setup)?|Results?|Discussion|Conclusion|"
    r"Limitations?|Ethical|Acknowledgements?|Appendix)\b",
    re.IGNORECASE,
)

_SUBSECTION_HEADING_RE = re.compile(r"^\d+\.\d+")


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
# References / appendix post-processing
# ---------------------------------------------------------------------------

# Matches a "References" section heading on its own line (common in ACL/NeurIPS papers)
_REFERENCES_RE = re.compile(
    r"^(?:References|REFERENCES|Bibliography)\s*$", re.MULTILINE
)

# Matches the first line of an appendix: "Appendix", "A.", "A.1", "B.1", etc.
_APPENDIX_RE = re.compile(r"^(?:Appendix\b|[A-Z]\.\d)", re.MULTILINE)


def _filter_appendix_sections(appendix_text: str) -> str:
    """Keep only appendix subsections that contain at least one annotation.

    Splits the appendix text on [SECTION: ...] / [SUBSECTION: ...] header
    lines and returns only the chunks that contain a [HIGHLIGHT ...] or
    [NOTE ...] marker. Any text before the first header is treated as a
    preamble chunk and subject to the same filter.

    Returns the filtered text joined by double newlines, or empty string if
    no chunks pass the filter.
    """
    parts = re.split(
        r"(^\[(?:SECTION|SUBSECTION):[^\n]*|^[A-Z](?:\.\d+)*\s*$)",
        appendix_text,
        flags=re.MULTILINE,
    )

    chunks: list[str] = []
    if parts[0].strip():
        chunks.append(parts[0])

    i = 1
    while i < len(parts):
        header = parts[i]
        content = parts[i + 1] if i + 1 < len(parts) else ""
        chunks.append(header + content)
        i += 2

    kept = [c for c in chunks if re.search(r"\[(HIGHLIGHT|NOTE)\b", c)]
    return "\n\n".join(kept)


def _process_references_and_appendix(text: str) -> str:
    """Remove the references section and insert an --- Appendix --- marker.

    Finds the first standalone 'References' heading, drops everything from
    that point to the start of the appendix (or end of document), and inserts
    '--- Appendix ---' before the appendix content if one is found.

    Only appendix subsections that contain at least one annotation are kept;
    unannotated subsections are dropped silently. If no subsections survive,
    the appendix marker is omitted entirely.

    Note: in two-column PDFs, a few reference entries may appear interleaved
    with the final body-text sections before the heading — those are left as-is
    since they cannot be distinguished from body text without ML-level parsing.
    """
    ref_m = _REFERENCES_RE.search(text)
    if not ref_m:
        return text

    before_refs = text[: ref_m.start()].rstrip()

    appendix_m = _APPENDIX_RE.search(text, ref_m.end())
    if appendix_m:
        filtered = _filter_appendix_sections(text[appendix_m.start() :])
        if filtered:
            return before_refs + "\n\n--- Appendix ---\n\n" + filtered
        return before_refs
    else:
        return before_refs


# ---------------------------------------------------------------------------
# Math / equation detection
# ---------------------------------------------------------------------------

MATH_SYMBOLS = set("∈≤≥≠×∑∏∫πθφσλρεϕ→←∇∂≈")


def is_display_equation(text: str) -> bool:
    """Return True if text looks like a display equation block."""
    if len(text) > 120:
        return False
    math_count = sum(1 for ch in text if ch in MATH_SYMBOLS)
    if math_count >= 2:
        return True
    if re.search(r"\(\d+\)\s*$", text) and math_count >= 1:
        return True
    return False


# ---------------------------------------------------------------------------
# Figure caption detection
# ---------------------------------------------------------------------------

FIGURE_CAPTION_RE = re.compile(r"^(Figure\s+\d+)[:\.](.+)", re.DOTALL | re.IGNORECASE)

_TABLE_CAPTION_RE = re.compile(r"^Table\s+\d+[:\.]")
_CAPTION_ITEM_RE = re.compile(r"^(\[FIGURE \d+:|Table\s+\d+[:\.])")
_SKIP_ITEM_RE = re.compile(r"^\[(HIGHLIGHT|NOTE|TABLE|EQUATION|FIGURE)\b")
_STOP_MARKER_RE = re.compile(r"^\[(SECTION|SUBSECTION|TITLE|AUTHORS):")


def _suppress_pre_caption_labels(
    items: list[tuple[float, int, str]],
) -> list[tuple[float, int, str]]:
    """Suppress short text blocks that precede figure/table captions.

    After items are y-sorted, walk backward from each figure caption
    ([FIGURE N: "..."]) or table caption (Table N: ...) and suppress
    plain-text items with fewer than 8 words (figure labels / table cells).

    Stops scanning at:
    - a long plain-text item (≥ 8 words)  — body paragraph
    - a section/subsection/title/authors marker
    - another caption item
    - the start of the list

    Annotations ([HIGHLIGHT], [NOTE]) and markers ([TABLE], [EQUATION],
    [FIGURE]) are kept regardless.
    """
    suppress: set[int] = set()

    for i, (_, _, text) in enumerate(items):
        if not _CAPTION_ITEM_RE.match(text):
            continue
        j = i - 1
        while j >= 0:
            prev_text = items[j][2]
            if _STOP_MARKER_RE.match(prev_text):
                break
            if _CAPTION_ITEM_RE.match(prev_text):
                break
            if _SKIP_ITEM_RE.match(prev_text):
                j -= 1
                continue
            if len(prev_text.split()) >= 8:
                break
            suppress.add(j)
            j -= 1

    return [(y, p, t) for i, (y, p, t) in enumerate(items) if i not in suppress]


def format_figure_caption(text: str) -> str | None:
    """If text is a figure caption, return a [FIGURE N: "..."] marker, else None."""
    m = FIGURE_CAPTION_RE.match(text.strip())
    if m:
        label = m.group(1).strip()
        caption = m.group(2).strip()
        caption = re.sub(r"\s+", " ", caption)
        return f'[{label.upper()}: "{caption}"]'
    return None


# ---------------------------------------------------------------------------
# Dict-format block helpers
# ---------------------------------------------------------------------------


def _block_text(block: dict) -> str:
    """Join span texts from a dict-format block, merging sub/superscript lines inline.

    A line whose every non-empty span is smaller than 75% of the block dominant size
    is treated as a subscript/superscript line and appended inline to the preceding
    logical line rather than starting a new one.
    """
    dominant = _block_dominant_size(block)
    sub_threshold = dominant * 0.75

    logical_lines: list[str] = []
    for line in block["lines"]:
        line_text = "".join(s["text"] for s in line["spans"])
        nonempty_sizes = [s["size"] for s in line["spans"] if s["text"].strip()]
        is_sub_super = bool(nonempty_sizes) and all(
            sz < sub_threshold for sz in nonempty_sizes
        )
        if is_sub_super and logical_lines:
            logical_lines[-1] += line_text  # attach subscript/superscript inline
        else:
            logical_lines.append(line_text)

    return "\n".join(logical_lines).strip()


def _block_dominant_size(block: dict) -> float:
    """Most common font size in the block, weighted by character count."""
    sizes: list[float] = []
    for line in block["lines"]:
        for span in line["spans"]:
            sizes.extend([round(span["size"], 1)] * max(1, len(span["text"])))
    return max(set(sizes), key=sizes.count) if sizes else 0.0


def _block_is_bold(block: dict) -> bool:
    """True if the majority of characters in the block are bold (flag bit 4)."""
    bold, total = 0, 0
    for line in block["lines"]:
        for span in line["spans"]:
            n = len(span["text"])
            total += n
            if span["flags"] & 16:
                bold += n
    return bold > total / 2 if total else False


def _page_body_size(dict_blocks: list[dict]) -> float:
    """Return the most common font size on the page (body text baseline)."""
    sizes: list[float] = []
    for block in dict_blocks:
        if block["type"] != 0:
            continue
        for line in block["lines"]:
            for span in line["spans"]:
                if len(span["text"].strip()) > 2:
                    sizes.append(round(span["size"], 1))
    return max(set(sizes), key=sizes.count) if sizes else 11.0


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


def extract_page(page: fitz.Page, page_num: int = 1) -> tuple[str, int, int]:
    """Extract text with annotations interleaved for a single page.

    Returns (annotated_text, highlight_count, note_count).
    """
    page_width = page.rect.width
    items: list[tuple[float, int, str]] = []  # (y, priority, content)
    # priority: 0 = text block, 1 = annotation (breaks y ties so text comes first)

    # Detect tables; collect markdown representations and exclusion rects so
    # that raw cell text is not also emitted as plain text blocks.
    found_tables = page.find_tables()
    table_items = []
    table_rects = []
    for t in found_tables:
        table_items.append((t.bbox[1], 1, "[TABLE]"))
        table_rects.append(fitz.Rect(t.bbox))

    # FreeText annotations (type 2) render their content as visible page text,
    # so pymupdf returns it in get_text("dict") too. Collect their rects first
    # so we can skip the duplicate plain-text blocks below.
    freetext_rects = [annot.rect for annot in page.annots() if annot.type[0] == 2]

    excluded_rects = freetext_rects + table_rects

    def overlaps_excluded(block_rect: fitz.Rect) -> bool:
        return any(block_rect.intersects(r) for r in excluded_rects)

    dict_blocks = page.get_text("dict")["blocks"]
    body_size = _page_body_size(dict_blocks)

    title_found = False
    in_author_region = False
    author_parts: list[tuple[float, str]] = []

    for block in dict_blocks:
        if block["type"] != 0:  # skip non-text blocks (images, etc.)
            continue
        text = _block_text(block)
        if not text:
            continue
        block_rect = fitz.Rect(block["bbox"])
        if overlaps_excluded(block_rect):
            continue  # skip FreeText duplicates and table cell text

        y0 = block["bbox"][1]
        size = _block_dominant_size(block)
        bold = _block_is_bold(block)

        # ── Title (first page, largest font, once only) ───────────────────
        if page_num == 1 and not title_found and size >= body_size * 1.2:
            clean = re.sub(r"\s+", " ", text).strip()
            items.append((y0, 0, f'[TITLE: "{clean}"]'))
            title_found = True
            in_author_region = True
            continue

        # ── Author region (page 1, between title and first section) ───────
        if page_num == 1 and in_author_region:
            is_section = (
                bold
                and size >= body_size * 1.05
                and _SECTION_HEADING_RE.match(text.strip())
            )
            if is_section:
                if author_parts:
                    author_text = " ".join(t for _, t in sorted(author_parts))
                    author_text = re.sub(r"\s+", " ", author_text)
                    # Strip superscript markers (digits, *, †) after each author name
                    author_text = re.sub(
                        r"(?<=[A-Za-z])[\d∗†]+(,\d+[\d∗†]*)*", "", author_text
                    )
                    y_auth = author_parts[0][0]
                    items.append((y_auth, 0, f'[AUTHORS: "{author_text}"]'))
                in_author_region = False
                # Fall through to emit this block as a section heading ↓
            else:
                author_parts.append((y0, text))
                continue

        # ── Section heading ───────────────────────────────────────────────
        if (
            bold
            and size >= body_size * 1.05
            and _SECTION_HEADING_RE.match(text.strip())
            and len(text) < 100
        ):
            clean = re.sub(r"\s+", " ", text).strip()
            items.append((y0, 0, f'[SECTION: "{clean}"]'))
            continue

        # ── Subsection heading ────────────────────────────────────────────
        if bold and _SUBSECTION_HEADING_RE.match(text.strip()) and len(text) < 100:
            clean = re.sub(r"\s+", " ", text).strip()
            items.append((y0, 0, f'[SUBSECTION: "{clean}"]'))
            continue

        # ── Figure caption / equation / plain text ────────────────────────
        figure = format_figure_caption(text)
        if figure:
            items.append((y0, 0, figure))
        elif is_display_equation(text):
            items.append((y0, 0, "[EQUATION]"))
        else:
            items.append((y0, 0, text))

    items.extend(table_items)

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
                items.append((annot.rect.y0, 1, f'[NOTE {position}: "{content}"]'))
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
    items = _suppress_pre_caption_labels(items)
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
        page_text, n_h, n_n = extract_page(page, page_num)
        if page_text:
            parts.append(page_text)
        total_highlights += n_h
        total_notes += n_n

    out_path.parent.mkdir(parents=True, exist_ok=True)
    full_text = _process_references_and_appendix("\n\n".join(parts))
    out_path.write_text(full_text, encoding="utf-8")

    return len(doc), total_highlights, total_notes


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Extract highlights and margin notes from an annotated PDF."
    )
    parser.add_argument(
        "pdf_path",
        help='Path to the annotated PDF (e.g., "papers/foo.pdf")',
    )
    parser.add_argument(
        "--url",
        type=str,
        default=None,
        help="Paper URL or arXiv ID to fetch BibTeX entry for prepending to output",
    )

    args = parser.parse_args()

    pdf_path = Path(args.pdf_path)
    if not pdf_path.exists():
        print(f"Error: file not found: {pdf_path}", file=sys.stderr)
        sys.exit(1)

    out_path = Path("outputs/extracted") / (pdf_path.stem + ".txt")
    n_pages, n_highlights, n_notes = extract(pdf_path, out_path)

    n_chars = len(out_path.read_text(encoding="utf-8"))
    n_tokens_approx = n_chars // 4

    # Fetch and prepend BibTeX if URL provided
    if args.url:
        print(f"Fetching BibTeX from: {args.url}", file=sys.stderr)
        bibtex = get_bibtex_from_url(args.url)
        if bibtex:
            existing_text = out_path.read_text(encoding="utf-8")
            bibtex_section = f"--- BibTeX ---\n\n{bibtex}\n\n"
            out_path.write_text(bibtex_section + existing_text, encoding="utf-8")
            print("BibTeX prepended to output.", file=sys.stderr)
            n_chars = len(out_path.read_text(encoding="utf-8"))
            n_tokens_approx = n_chars // 4
        else:
            print(
                f"WARNING: Could not fetch BibTeX from provided URL: {args.url}",
                file=sys.stderr,
            )

    print(f"Tokens:     ~{n_tokens_approx:,} (≈ chars/4)")
    print(f"Pages:      {n_pages}")
    print(f"Highlights: {n_highlights}")
    print(f"Notes:      {n_notes}")
    print(f"Output:     {out_path}")

    if n_highlights == 0:
        print("WARNING: no highlights found — was the PDF annotated?", file=sys.stderr)
    if n_notes == 0:
        print(
            "WARNING: no margin notes found — was the PDF annotated?", file=sys.stderr
        )


if __name__ == "__main__":
    main()
