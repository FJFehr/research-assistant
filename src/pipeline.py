#!/usr/bin/env python3
"""
Pipeline: Extract annotations → Fetch BibTeX → Create Prompt → Summarise → Output

Usage:
    python src/pipeline.py --paper papers/foo.pdf --url https://arxiv.org/abs/...
    python src/pipeline.py --paper papers/foo.pdf --url 2601.07296
    python src/pipeline.py --paper papers/foo.pdf --url https://aclanthology.org/2025.acl-short.62/
    python src/pipeline.py --paper papers/foo.pdf --url https://openreview.net/forum?id=...

Options:
    --paper     Path to annotated PDF file (required)
    --url       Paper URL or arXiv ID (required)
    --no-bibtex Skip BibTeX fetching step

Outputs:
    outputs/extracted/foo.txt      (annotated text)
    outputs/bibtex/foo.bib         (fetched BibTeX, optional)
    outputs/prompts/foo.prompt.md  (prompt ready for manual or local model use)
"""

import sys
import argparse
from pathlib import Path

from src.extract import extract
from src.get_bibtex import get_bibtex_from_url
from src.summarise import summarise
from src.llm_provider import prepare_prompt_for_provider


def process_paper(
    pdf_path: str,
    paper_url: str | None = None,
    include_bibtex: bool = True,
    output_dir: Path = Path("outputs"),
    provider: str = "manual",
    model: str | None = None,
) -> None:
    """
    Complete pipeline: extract → fetch BibTeX → prepend to extracted → create prompt.

    Args:
        pdf_path: Path to annotated PDF file
        paper_url: URL or arXiv ID for BibTeX retrieval
        include_bibtex: Whether to fetch and include BibTeX
    """
    pdf_file = Path(pdf_path)
    if not pdf_file.exists():
        print(f"Error: PDF file not found: {pdf_path}", file=sys.stderr)
        sys.exit(1)

    paper_name = pdf_file.stem

    # ───────────────────────────────────────────────────────────────────────────
    # Step 1: Extract annotations from PDF
    # ───────────────────────────────────────────────────────────────────────────
    print(f"\n{'=' * 70}")
    print("STEP 1: EXTRACT ANNOTATIONS FROM PDF")
    print(f"{'=' * 70}")

    extracted_path = output_dir / "extracted" / f"{paper_name}.txt"
    bibtex_path = output_dir / "bibtex" / f"{paper_name}.bib"
    prompt_output_path = output_dir / "prompts" / f"{paper_name}.prompt.md"

    extracted_path.parent.mkdir(parents=True, exist_ok=True)
    bibtex_path.parent.mkdir(parents=True, exist_ok=True)
    prompt_output_path.parent.mkdir(parents=True, exist_ok=True)

    n_pages, n_highlights, n_notes = extract(pdf_file, extracted_path)

    print(f"✓ Extracted from {n_pages} pages")
    print(f"  - {n_highlights} highlights")
    print(f"  - {n_notes} margin notes")
    print(f"✓ Written to: {extracted_path}")

    # ───────────────────────────────────────────────────────────────────────────
    # Step 2: Fetch BibTeX and store separately
    # ───────────────────────────────────────────────────────────────────────────
    bibtex_entry: str | None = None
    if include_bibtex and paper_url:
        print(f"\n{'=' * 70}")
        print("STEP 2: FETCH BIBTEX")
        print(f"{'=' * 70}")
        print(f"Fetching from: {paper_url}")

        bibtex_entry = get_bibtex_from_url(paper_url)
        if bibtex_entry:
            print("✓ BibTeX found")
            bibtex_path.write_text(bibtex_entry + "\n", encoding="utf-8")
            print(f"✓ BibTeX written to: {bibtex_path}")
        else:
            print("⚠ Could not fetch BibTeX (proceeding without)", file=sys.stderr)
    elif not paper_url:
        print("\n⚠ No URL provided, skipping BibTeX fetch")
    else:
        print("\n⚠ --no-bibtex flag set, skipping BibTeX fetch")

    # ───────────────────────────────────────────────────────────────────────────
    # Step 3: Create prompt from template and extracted content
    # ───────────────────────────────────────────────────────────────────────────
    print(f"\n{'=' * 70}")
    print("STEP 3: CREATE PROMPT WITH EXTRACTED CONTENT")
    print(f"{'=' * 70}")

    preface_text = ""
    if bibtex_entry:
        preface_text = f"--- Known BibTeX (fetched) ---\n\n{bibtex_entry}"

    summarise(extracted_path, prompt_output_path, preface_text=preface_text)

    print("✓ Prompt created from template and extracted content")

    prepared_prompt = prompt_output_path.read_text(encoding="utf-8")
    prepared_prompt = prepare_prompt_for_provider(
        prompt=prepared_prompt,
        provider=provider,
        model=model,
    )
    prompt_output_path.write_text(prepared_prompt, encoding="utf-8")

    # ───────────────────────────────────────────────────────────────────────────
    # Done
    # ───────────────────────────────────────────────────────────────────────────
    print(f"\n{'=' * 70}")
    print("PIPELINE COMPLETE")
    print(f"{'=' * 70}")
    print(f"✓ Extracted:  {extracted_path}")
    if bibtex_entry:
        print(f"✓ BibTeX:     {bibtex_path}")
    print(f"✓ Prompt:     {prompt_output_path}")
    print(
        f"\n→ Copy the contents of {prompt_output_path} and paste into your selected model."
    )


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Complete pipeline: extract annotations → fetch BibTeX → summarise",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python src/pipeline.py --paper papers/LRAS.pdf --url 2601.07296
  python src/pipeline.py --paper papers/foo.pdf --url https://arxiv.org/abs/2301.12345
  python src/pipeline.py --paper papers/foo.pdf --url https://aclanthology.org/2025.acl-short.62/
  python src/pipeline.py --paper papers/foo.pdf --provider local --model llama3.1:8b
  python src/pipeline.py --paper papers/foo.pdf --no-bibtex
        """,
    )

    parser.add_argument(
        "--paper",
        required=False,
        help='Path to annotated PDF file (e.g., "papers/paper.pdf")',
    )

    parser.add_argument(
        "--papers",
        required=False,
        help="Deprecated alias for --paper",
    )

    parser.add_argument(
        "--url",
        default=None,
        help="Paper URL or arXiv ID for BibTeX retrieval (e.g., 2601.07296 or https://arxiv.org/abs/2601.07296)",
    )

    parser.add_argument(
        "--no-bibtex",
        action="store_true",
        help="Skip BibTeX fetching (extract and summarise only)",
    )

    parser.add_argument(
        "--provider",
        default="manual",
        choices=["manual", "local"],
        help="Target model provider for the generated prompt",
    )

    parser.add_argument(
        "--model",
        default=None,
        help="Optional model identifier (stored as metadata for manual/local use)",
    )

    parser.add_argument(
        "--output-dir",
        default="outputs",
        help="Root directory for generated artifacts",
    )

    args = parser.parse_args()

    selected_paper = args.paper or args.papers
    if not selected_paper:
        parser.error("One of --paper or --papers is required")

    if args.papers and not args.paper:
        print("⚠ --papers is deprecated; use --paper", file=sys.stderr)

    process_paper(
        pdf_path=selected_paper,
        paper_url=args.url,
        include_bibtex=not args.no_bibtex,
        output_dir=Path(args.output_dir),
        provider=args.provider,
        model=args.model,
    )


if __name__ == "__main__":
    main()
