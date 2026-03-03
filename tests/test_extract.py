"""Tests for src/extract.py.

Unit tests cover the pure helper functions.
Integration tests run against a real annotated PDF (LRAS.pdf) and verify
that the output is correctly formatted — they are skipped if the PDF is absent.
"""

import re
from pathlib import Path

import fitz
import pytest

from src.extract import extract, note_position, rgb_to_colour

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
    """Page numbers must be consecutive starting from 1."""
    numbers = [
        int(m) for m in re.findall(r"--- Page (\d+) ---", extracted)
    ]
    assert numbers == list(range(1, len(numbers) + 1))


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
    ]
    assert len(plain_lines) > 0, "No plain text found — only markers and annotations"


def test_annotations_follow_text(extracted):
    """Annotations should never appear before the first page marker."""
    first_marker = extracted.index("--- Page 1 ---")
    before_first_page = extracted[:first_marker]
    assert "[HIGHLIGHT" not in before_first_page
    assert "[NOTE" not in before_first_page
