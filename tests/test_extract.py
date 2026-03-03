"""Tests for src/extract.py.

Unit tests cover the pure helper functions.
Integration tests run against a real annotated PDF (LRAS.pdf) and verify
that the output is correctly formatted — they are skipped if the PDF is absent.
"""

import re
from pathlib import Path
from unittest.mock import MagicMock

import fitz
import pytest

from src.extract import (
    _block_text,
    _filter_appendix_sections,
    _process_references_and_appendix,
    extract,
    extract_page,
    format_figure_caption,
    is_display_equation,
    note_position,
    rgb_to_colour,
)

ANNOTATED_PDF = Path("annotated papers/LRAS.pdf")


# ---------------------------------------------------------------------------
# Unit tests: rgb_to_colour
# ---------------------------------------------------------------------------

@pytest.mark.parametrize("rgb,expected", [
    ((1.0, 1.0, 0.0), "yellow"),
    ((1.0, 0.9, 0.1), "yellow"),
    ((0.0, 0.8, 0.0), "green"),
    ((0.2, 0.7, 0.1), "green"),
    ((0.9, 0.1, 0.1), "red"),
    ((0.7, 0.0, 0.0), "red"),
    ((0.0, 0.0, 0.9), "blue"),
    ((0.1, 0.2, 0.8), "blue"),
    ((0.8, 0.0, 0.8), "purple"),
    ((0.6, 0.1, 0.7), "purple"),
    ((1.0, 0.5, 0.0), "orange"),
    ((0.9, 0.4, 0.6), "pink"),
    (None,             "yellow"),  # fallback for missing colour
])
def test_rgb_to_colour(rgb, expected):
    assert rgb_to_colour(rgb) == expected


# ---------------------------------------------------------------------------
# Unit tests: note_position
# ---------------------------------------------------------------------------

@pytest.mark.parametrize("x0,page_width,expected", [
    (10,  600, "left"),    # 10 < 600 * 0.35 = 210
    (200, 600, "left"),    # 200 < 210
    (250, 600, "inline"),  # 210 < 250 < 390
    (390, 600, "inline"),  # boundary: 390 is not > 390
    (391, 600, "right"),   # 391 > 390
    (550, 600, "right"),
])
def test_note_position(x0, page_width, expected):
    rect = fitz.Rect(x0, 0, x0 + 40, 20)
    assert note_position(rect, page_width) == expected


# ---------------------------------------------------------------------------
# Integration tests: output structure
# ---------------------------------------------------------------------------

@pytest.fixture(scope="module")
def extracted(tmp_path_factory):
    """Run extraction on LRAS.pdf once per test session; return text content."""
    if not ANNOTATED_PDF.exists():
        pytest.skip(f"Annotated PDF not found: {ANNOTATED_PDF}")
    out = tmp_path_factory.mktemp("extracted") / "LRAS.txt"
    extract(ANNOTATED_PDF, out)
    return out.read_text(encoding="utf-8")


def test_page_marker_page_one(extracted):
    assert "--- Page 1 ---" in extracted


def test_multiple_page_markers(extracted):
    markers = re.findall(r"^--- Page \d+ ---$", extracted, re.MULTILINE)
    assert len(markers) > 1, f"Expected >1 page markers, got {len(markers)}"


def test_page_markers_sequential(extracted):
    """Page numbers must start at 1 and be in strictly ascending order.

    Gaps are allowed because the references section is removed, which
    eliminates the page markers for those pages.
    """
    numbers = [
        int(m) for m in re.findall(r"--- Page (\d+) ---", extracted)
    ]
    assert numbers[0] == 1, f"First page marker should be 1, got {numbers[0]}"
    assert numbers == sorted(set(numbers)), "Page markers are not in ascending order"


def test_highlight_format(extracted):
    """[HIGHLIGHT <word>: "<non-empty text>"] must appear at least once."""
    assert re.search(r'\[HIGHLIGHT \w+: ".+?"\]', extracted), \
        "No correctly-formatted HIGHLIGHT annotation found"


def test_note_format(extracted):
    """[NOTE left|right|inline: "<non-empty text>"] must appear at least once."""
    assert re.search(r'\[NOTE (left|right|inline): ".+?"\]', extracted), \
        "No correctly-formatted NOTE annotation found"


def test_highlight_colour_is_known(extracted):
    """Every HIGHLIGHT must use a known colour name."""
    known = {"yellow", "green", "red", "blue", "purple", "orange", "pink"}
    colours_found = set(re.findall(r'\[HIGHLIGHT (\w+):', extracted))
    unknown = colours_found - known
    assert not unknown, f"Unknown highlight colour(s): {unknown}"


def test_note_position_is_valid(extracted):
    """Every NOTE must use a valid position token."""
    positions_found = set(re.findall(r'\[NOTE (\w+):', extracted))
    assert positions_found <= {"left", "right", "inline"}, \
        f"Invalid note position(s): {positions_found - {'left', 'right', 'inline'}}"


def test_no_empty_highlight_text(extracted):
    empty = re.findall(r'\[HIGHLIGHT \w+: ""\]', extracted)
    assert not empty, f"Found {len(empty)} empty HIGHLIGHT(s)"


def test_no_empty_note_text(extracted):
    empty = re.findall(r'\[NOTE \w+: ""\]', extracted)
    assert not empty, f"Found {len(empty)} empty NOTE(s)"


def test_text_content_present(extracted):
    """There must be non-marker, non-annotation, non-empty lines."""
    plain_lines = [
        line for line in extracted.splitlines()
        if line.strip()
        and not line.startswith("--- Page")
        and not line.startswith("[HIGHLIGHT")
        and not line.startswith("[NOTE")
        and not line.startswith("[TITLE:")
        and not line.startswith("[AUTHORS:")
        and not line.startswith("[SECTION:")
        and not line.startswith("[SUBSECTION:")
        and not line.startswith("[TABLE")
    ]
    assert len(plain_lines) > 0, "No plain text found — only markers and annotations"


def test_annotations_follow_text(extracted):
    """Annotations should never appear before the first page marker."""
    first_marker = extracted.index("--- Page 1 ---")
    before_first_page = extracted[:first_marker]
    assert "[HIGHLIGHT" not in before_first_page
    assert "[NOTE" not in before_first_page


# ---------------------------------------------------------------------------
# Unit tests: _block_text subscript merging
# ---------------------------------------------------------------------------

def test_block_text_merges_subscript_lines():
    """Small-font-only lines (subscripts) must be merged inline with the preceding line."""
    # body text = 11pt (dominant); subscripts = 8pt (< 11*0.75=8.25)
    block = {
        "lines": [
            {"spans": [{"text": "body text here", "size": 11.0}, {"text": "think", "size": 8.0}]},
            {"spans": [{"text": "1", "size": 8.0}]},   # pure subscript line
            {"spans": [{"text": "more body text here", "size": 11.0}]},
        ]
    }
    result = _block_text(block)
    assert "bodytextherethink1" in result.replace(" ", "")
    assert "\n1\n" not in result


def test_block_text_normal_lines_unchanged():
    """Normal-size lines must still be separated by newlines."""
    block = {
        "lines": [
            {"spans": [{"text": "line one", "size": 11.0}]},
            {"spans": [{"text": "line two", "size": 11.0}]},
        ]
    }
    result = _block_text(block)
    assert result == "line one\nline two"


# ---------------------------------------------------------------------------
# Unit tests: is_display_equation
# ---------------------------------------------------------------------------

def test_is_display_equation_two_math_symbols():
    assert is_display_equation("∑ x ∈ S") is True


def test_is_display_equation_with_equation_number():
    assert is_display_equation("max x (1)") is False   # no math symbols, plain word
    assert is_display_equation("max θ ∈ S (1)") is True


def test_is_display_equation_too_long():
    long_text = "∑ ∈ " + "x" * 200
    assert is_display_equation(long_text) is False


def test_is_display_equation_plain_text():
    assert is_display_equation("This is a normal sentence.") is False


# ---------------------------------------------------------------------------
# Unit tests: format_figure_caption
# ---------------------------------------------------------------------------

def test_format_figure_caption_colon():
    result = format_figure_caption("Figure 3: The overall framework.")
    assert result == '[FIGURE 3: "The overall framework."]'


def test_format_figure_caption_dot():
    result = format_figure_caption("Figure 1. Architecture overview of the model.")
    assert result == '[FIGURE 1: "Architecture overview of the model."]'


def test_format_figure_caption_no_match():
    assert format_figure_caption("Table 1: Results on LegalBench.") is None
    assert format_figure_caption("This is plain text.") is None


# ---------------------------------------------------------------------------
# Unit tests: _process_references_and_appendix
# ---------------------------------------------------------------------------

def test_references_removed_no_appendix():
    text = "Body text.\n\nReferences\n\nAuthor A. 2024. Paper.\nAuthor B. 2023. Paper."
    result = _process_references_and_appendix(text)
    assert "References" not in result
    assert "Body text." in result


def test_references_removed_appendix_preserved():
    text = (
        "Body.\n\nReferences\n\nAuthor. 2024. Paper.\n\n"
        'A.1\nAppendix content.\n[HIGHLIGHT yellow: "key point"]'
    )
    result = _process_references_and_appendix(text)
    assert "References" not in result
    assert "--- Appendix ---" in result
    assert "Appendix content." in result


def test_no_references_heading_unchanged():
    text = "Body only.\n\nNo references here."
    assert _process_references_and_appendix(text) == text


def test_appendix_annotated_subsection_kept():
    """Annotated subsection survives; unannotated sibling is dropped."""
    text = (
        "Body text.\n\nReferences\n\nAuthor. 2024.\n\n"
        "A.1\n"
        '[SECTION: "A.1 Proofs"]\n'
        "Proof content.\n"
        '[HIGHLIGHT yellow: "key result"]\n\n'
        '[SECTION: "A.2 Extra Experiments"]\n'
        "No annotations here."
    )
    result = _process_references_and_appendix(text)
    assert '[SECTION: "A.1 Proofs"]' in result
    assert "key result" in result
    assert '[SECTION: "A.2 Extra Experiments"]' not in result


def test_appendix_fully_unannotated_dropped():
    """Appendix with no annotations is dropped entirely — no marker emitted."""
    text = (
        "Body text.\n\nReferences\n\nAuthor. 2024.\n\n"
        "A.1\n"
        '[SECTION: "A.1 Proofs"]\n'
        "Proof content only, no annotations."
    )
    result = _process_references_and_appendix(text)
    assert "--- Appendix ---" not in result


def test_appendix_all_annotated_both_kept():
    """When every subsection has annotations, all are preserved."""
    text = (
        "Body text.\n\nReferences\n\nAuthor. 2024.\n\n"
        "A.1\n"
        '[SECTION: "A.1 Proofs"]\n'
        "Proof content.\n"
        '[HIGHLIGHT yellow: "theorem 1"]\n\n'
        '[SECTION: "A.2 More Experiments"]\n'
        "Extra results.\n"
        '[NOTE right: "Interesting detail."]'
    )
    result = _process_references_and_appendix(text)
    assert '[SECTION: "A.1 Proofs"]' in result
    assert '[SECTION: "A.2 More Experiments"]' in result


# ---------------------------------------------------------------------------
# Integration tests: table, equation, figure markers
# ---------------------------------------------------------------------------

def test_table_marker_present(extracted):
    assert "[TABLE]" in extracted, "No [TABLE] marker found in extracted text"


def test_table_no_markdown_content(extracted):
    """Table markers must be plain [TABLE] placeholders — no markdown pipe rows."""
    assert "[TABLE:" not in extracted, \
        "Old-style [TABLE: ...] marker found — should be plain [TABLE]"
    assert "|---|" not in extracted, \
        "Markdown table separator found — table content should not be in output"


def test_table_cell_text_suppressed(extracted):
    """Known table cell values must not appear as bare standalone lines.

    'LRAS-SFT' is a model name that lives in table cells; the exclusion rects
    should prevent it leaking into the plain-text stream as an isolated line.
    It may still appear in body text inline (e.g. in sentences), but not alone.
    """
    standalone_model = re.compile(r'^LRAS-SFT$', re.MULTILINE)
    assert not standalone_model.search(extracted), \
        "Standalone 'LRAS-SFT' line found — table exclusion rect not working"


def test_equation_marker_present(extracted):
    assert "[EQUATION]" in extracted, "No [EQUATION] marker found in extracted text"


def test_figure_marker_present(extracted):
    assert "[FIGURE " in extracted, "No [FIGURE marker found in extracted text"


def test_figure_has_caption(extracted):
    """Figure markers must contain non-empty caption text."""
    figures = re.findall(r'\[FIGURE \d+: "(.+?)"\]', extracted)
    assert figures, "No [FIGURE N: \"...\"] markers with caption text found"


def test_figure_format(extracted):
    """Every figure marker must match the expected format."""
    markers = re.findall(r'\[FIGURE[^\]]+\]', extracted)
    assert markers, "No figure markers found"
    bad = [m for m in markers if not re.match(r'\[FIGURE \d+: ".+?"\]', m)]
    assert not bad, f"Malformed figure marker(s): {bad}"



def test_references_section_removed(extracted):
    """The 'References' section heading should not appear in the output."""
    assert not re.search(r'^References\s*$', extracted, re.MULTILINE), \
        "References section heading found — should have been removed"


def test_appendix_marker_present(extracted):
    """An appendix marker should be present since LRAS has appendix sections."""
    assert "--- Appendix ---" in extracted, \
        "--- Appendix --- marker not found — appendix detection may have failed"


# ---------------------------------------------------------------------------
# Integration tests: structural annotations
# ---------------------------------------------------------------------------

def test_title_marker_present(extracted):
    """[TITLE: ...] must appear exactly once."""
    markers = re.findall(r'^\[TITLE:', extracted, re.MULTILINE)
    assert len(markers) == 1, f"Expected exactly 1 TITLE marker, got {len(markers)}"


def test_title_format(extracted):
    """[TITLE: "..."] must match the expected format."""
    assert re.search(r'\[TITLE: ".+?"\]', extracted), \
        "No correctly-formatted TITLE marker found"


def test_authors_marker_present(extracted):
    """[AUTHORS: ...] must appear in the extracted text."""
    assert "[AUTHORS:" in extracted, "No AUTHORS marker found"


def test_authors_not_empty(extracted):
    """[AUTHORS: ""] must not appear — author text must be non-empty."""
    empty = re.findall(r'\[AUTHORS: ""\]', extracted)
    assert not empty, "Found empty AUTHORS marker"


def test_section_marker_present(extracted):
    """[SECTION: ...] must appear in the extracted text."""
    assert "[SECTION:" in extracted, "No SECTION marker found"


def test_section_format(extracted):
    """Every SECTION marker must match the expected format."""
    markers = re.findall(r'\[SECTION:[^\]]*\]', extracted)
    assert markers, "No SECTION markers found"
    bad = [m for m in markers if not re.match(r'\[SECTION: ".+?"\]', m)]
    assert not bad, f"Malformed SECTION marker(s): {bad}"


def test_known_section_tagged(extracted):
    """'Introduction' must appear inside a [SECTION: ...] marker."""
    assert re.search(r'\[SECTION: ".*Introduction.*"\]', extracted, re.IGNORECASE), \
        "'Introduction' not found inside a [SECTION: ...] marker"


def test_subsection_format(extracted):
    """Any SUBSECTION markers must match the expected format."""
    markers = re.findall(r'\[SUBSECTION:[^\]]*\]', extracted)
    if not markers:
        pytest.skip("No SUBSECTION markers found — paper may not have subsections")
    bad = [m for m in markers if not re.match(r'\[SUBSECTION: ".+?"\]', m)]
    assert not bad, f"Malformed SUBSECTION marker(s): {bad}"


def test_subscript_digits_merged_inline(extracted):
    """Subscript digits must not appear as standalone lines after their base symbol.

    The trajectory formula 'τ = (z^think_1, [z^search_1, ...)' appears on page 3.
    After merging, 'zthink1' and 'zsearch1' must be on the same line — no bare digit
    on its own line immediately following a symbol like 'zthink'.
    """
    assert re.search(r"zthink\d", extracted), \
        "'zthink<digit>' not found — subscript may not have been merged inline"
    assert re.search(r"zsearch\d", extracted), \
        "'zsearch<digit>' not found — subscript may not have been merged inline"


# ---------------------------------------------------------------------------
# Unit tests: extract_page warning paths
# ---------------------------------------------------------------------------


def _mock_page(annots=()):
    """Minimal mock fitz.Page with no text blocks and given annotations."""
    page = MagicMock()
    page.rect.width = 600.0
    page.find_tables.return_value = []
    page.get_text.return_value = {"blocks": []}
    page.annots.return_value = list(annots)
    return page


def test_extract_page_warns_empty_highlight(capsys):
    """An empty-text highlight must emit a WARNING to stderr and be skipped."""
    annot = MagicMock()
    annot.type = [8, "Highlight"]
    annot.colors = {"stroke": (1.0, 1.0, 0.0)}
    annot.rect.y0 = 100.0
    page = _mock_page([annot])
    page.get_textbox.return_value = "   "  # strips to empty string

    text, n_h, n_n = extract_page(page)
    assert "WARNING: empty highlight text" in capsys.readouterr().err
    assert n_h == 0


def test_extract_page_warns_empty_note(capsys):
    """A note with no content must emit a WARNING to stderr and be skipped."""
    annot = MagicMock()
    annot.type = [0, "Text"]
    annot.info = {"content": ""}
    annot.rect.y0 = 100.0
    page = _mock_page([annot])

    text, n_h, n_n = extract_page(page)
    assert "WARNING: empty note text" in capsys.readouterr().err
    assert n_n == 0


def test_extract_page_warns_unclassified_annotation(capsys):
    """An annotation with an unknown type number must emit a WARNING to stderr."""
    annot = MagicMock()
    annot.type = [99, "Unknown"]
    annot.rect.y0 = 100.0
    page = _mock_page([annot])

    extract_page(page)
    assert "WARNING: unclassified annotation type 99" in capsys.readouterr().err


def test_extract_page_warns_on_extraction_error(capsys):
    """An exception during annotation processing must emit a WARNING to stderr."""
    annot = MagicMock()
    annot.type = [8, "Highlight"]
    annot.rect.y0 = 100.0
    annot.colors.get.side_effect = RuntimeError("simulated error")
    page = _mock_page([annot])

    extract_page(page)
    assert "WARNING: failed to extract annotation" in capsys.readouterr().err
