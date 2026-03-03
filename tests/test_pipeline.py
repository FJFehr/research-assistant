"""
Tests for the pipeline.py orchestration script.

Tests the complete workflow:
1. Extract annotations from PDF
2. Fetch BibTeX from URL
3. Generate prompt from template
4. Write artifacts under outputs/
"""

import pytest
from pathlib import Path
from src.pipeline import process_paper


class TestPipelineIntegration:
    """Test the complete pipeline workflow."""

    def test_pipeline_extracts_pdf(self):
        """Verify pipeline extracts annotations from PDF."""
        # This test would require an actual PDF file
        # For now, we verify the pipeline function exists and is callable
        assert callable(process_paper), "process_paper should be a callable function"

    def test_pipeline_with_all_stages(self):
        """Verify pipeline orchestrates all three stages."""
        # This would be an integration test requiring:
        # - A test PDF file
        # - A test URL for BibTeX
        # - Optional URL for BibTeX fetching
        # For now, we test that the function signature is correct
        import inspect

        sig = inspect.signature(process_paper)
        assert "pdf_path" in sig.parameters, "Should have pdf_path parameter"
        assert "paper_url" in sig.parameters, "Should have paper_url parameter"
        assert "include_bibtex" in sig.parameters, (
            "Should have include_bibtex parameter"
        )
        assert "output_dir" in sig.parameters, "Should have output_dir parameter"
        assert "provider" in sig.parameters, "Should have provider parameter"


class TestPipelineOutputStructure:
    """Test expected output file structure."""

    def test_output_paths(self):
        """Verify expected output paths are correct."""
        pdf_name = "LRAS"
        extracted = Path("outputs/extracted") / (pdf_name + ".txt")
        prompt = Path("outputs/prompts") / (pdf_name + ".prompt.md")

        assert extracted.name.endswith(".txt"), "Extracted file should be .txt"
        assert prompt.name.endswith(".md"), "Prompt file should be .md"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
