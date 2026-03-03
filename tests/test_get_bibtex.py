"""
Tests for get_bibtex.py

Tests the BibTeX fetching functionality for various paper sources:
- ACL Anthology
- NeurIPS/Conference papers
- OpenReview
- arXiv
"""

import pytest
from src.get_bibtex import (
    get_bibtex_from_url,
    try_arxiv,
    try_aclanthology,
    make_bibkey,
)


class TestACLAnthology:
    """Test ACL Anthology URL handling."""

    def test_acl_coret_2025(self):
        """Fetch CoRet paper from ACL 2025."""
        url = "https://aclanthology.org/2025.acl-short.62/"
        bib = get_bibtex_from_url(url)

        assert bib is not None, "Should fetch BibTeX for ACL paper"
        assert "@inproceedings" in bib.lower(), "Should be @inproceedings"
        assert "coret" in bib.lower() or "fehr" in bib.lower(), (
            "Should contain paper or author name"
        )
        assert "2025" in bib, "Should contain year 2025"
        assert "code" in bib.lower(), "Should mention code/retrieval"


class TestOpenReview:
    """Test OpenReview URL handling."""

    def test_openreview_vareg_2024(self):
        """Fetch Nonparametric Variational Regularisation paper from OpenReview."""
        url = "https://openreview.net/forum?id=Zu8OWNUC0u"
        bib = get_bibtex_from_url(url)

        assert bib is not None, "Should fetch BibTeX for OpenReview paper"
        assert "@inproceedings" in bib or "@misc" in bib, "Should be valid entry type"
        assert "nonparametric" in bib.lower() or "fehr" in bib.lower(), (
            "Should contain paper or author name"
        )
        assert "2024" in bib, "Should contain year 2024"


class TestNeurIPS:
    """Test NeurIPS/conference proceedings handling."""

    def test_neurips_transformer_2017(self):
        """Fetch Transformer paper from NeurIPS proceedings."""
        url = "https://papers.nips.cc/paper_files/paper/2017/hash/3f5ee243547dee91fbd053c1c4a845aa-Abstract.html"
        bib = get_bibtex_from_url(url)

        assert bib is not None, "Should fetch BibTeX for NeurIPS paper"
        assert "@inproceedings" in bib or "@article" in bib, (
            "Should be valid entry type"
        )
        assert "attention" in bib.lower(), "Should mention 'Attention is All You Need'"
        assert "2017" in bib, "Should contain year 2017"
        assert "vaswani" in bib.lower(), "Should contain Vaswani as author"


class TestArXiv:
    """Test arXiv URL handling."""

    def test_arxiv_direct_url(self):
        """Fetch paper from arXiv using full URL."""
        url = "https://arxiv.org/abs/1706.03762"
        bib = try_arxiv(url)

        assert bib is not None, "Should fetch BibTeX from arXiv"
        assert "@misc" in bib or "@article" in bib, "Should be valid entry type"
        assert "1706.03762" in bib, "Should contain arXiv ID"
        assert "vaswani" in bib.lower(), "Should contain Vaswani author"

    def test_arxiv_bare_id(self):
        """Test arXiv fetching with bare ID (not used in try_arxiv but for reference)."""
        url = "https://arxiv.org/pdf/2601.07296"
        bib = try_arxiv(url)

        assert bib is not None, "Should fetch BibTeX from arXiv PDF link"
        assert "@misc" in bib or "@article" in bib, "Should be valid entry type"
        assert "2601.07296" in bib, "Should contain arXiv ID"


class TestBibKeyGeneration:
    """Test BibTeX citation key generation."""

    def test_bibkey_full_authors(self):
        """Test key generation with multiple authors."""
        authors = "Fabio James Fehr and James Henderson"
        year = "2024"
        title = "Nonparametric Variational Regularisation"

        key = make_bibkey(authors, year, title)

        assert key.startswith("fehr"), "Should use first author's last name"
        assert "2024" in key, "Should contain year"
        assert len(key) <= 60, "Should be reasonable length"

    def test_bibkey_single_author(self):
        """Test key generation with single author."""
        authors = "Ashish Vaswani"
        year = "2017"
        title = "Attention is All You Need"

        key = make_bibkey(authors, year, title)

        assert key.startswith("vaswani"), "Should use author's last name"
        assert "2017" in key, "Should contain year"

    def test_bibkey_no_authors(self):
        """Test key generation with no authors."""
        authors = ""
        year = "2020"
        title = "Some Paper"

        key = make_bibkey(authors, year, title)

        assert key.startswith("anon"), "Should default to 'anon'"
        assert "2020" in key, "Should contain year"


class TestACLAnthologyDirect:
    """Test ACL Anthology .bib endpoint directly."""

    def test_acl_bib_endpoint(self):
        """Test fetching from ACL .bib endpoint."""
        url = "https://aclanthology.org/2025.acl-short.62/"
        bib = try_aclanthology(url)

        assert bib is not None, "Should fetch .bib from ACL endpoint"
        assert "@inproceedings" in bib.lower(), "Should be @inproceedings"


class TestBibTexValidity:
    """Test that returned BibTeX is valid format."""

    def test_bibtex_structure_acl(self):
        """Verify BibTeX structure for ACL paper."""
        url = "https://aclanthology.org/2025.acl-short.62/"
        bib = get_bibtex_from_url(url)

        assert bib is not None
        # Should start with @ entry type
        assert bib.strip().startswith("@"), "Should start with @"
        # Should have key in braces
        assert "{" in bib and "}" in bib, "Should have proper braces"
        # Should have required fields
        assert "title" in bib.lower(), "Should have title field"
        assert "author" in bib.lower(), "Should have author field"
        assert "year" in bib.lower(), "Should have year field"

    def test_bibtex_structure_openreview(self):
        """Verify BibTeX structure for OpenReview paper."""
        url = "https://openreview.net/forum?id=Zu8OWNUC0u"
        bib = get_bibtex_from_url(url)

        assert bib is not None
        assert bib.strip().startswith("@"), "Should start with @"
        assert "title" in bib.lower(), "Should have title field"
        assert "author" in bib.lower(), "Should have author field"
        assert "year" in bib.lower(), "Should have year field"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
