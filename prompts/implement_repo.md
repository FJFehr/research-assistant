# Prompt: Implement the Paper Reading Assistant Repo

Use this prompt with Claude Code (or a Claude API call) to scaffold and implement the full pipeline from scratch.

---

## Context

You are implementing a **personal paper reading assistant** — a two-stage pipeline that:
1. Extracts highlights and margin notes from an annotated PDF, embedding them inline into a plain-text file.
2. Feeds that annotated text to Claude with a carefully designed prompt to produce a structured, opinionated personal research summary.

The target folder structure is:

```
papers/          ← input: annotated PDFs
extracted/       ← intermediate: annotated .txt files (one per paper)
summaries/       ← output: structured summaries (one per paper)
prompts/         ← versioned prompt templates (this folder)
src/             ← extraction and summarisation code
```

---

## Task

Implement the following, in order:

### 1. `src/extract.py` — PDF annotation extractor

- Use `pymupdf` (imported as `fitz`) to open a PDF.
- Extract all pages in order.
- For each page:
  - Extract the full text with `page.get_text("blocks")` (preserves spatial layout).
  - Extract all annotations (`page.annots()`).
  - Classify annotations:
    - **Highlight** (`annot.type[0] == 8`): record the highlighted text (from the quads, use `page.get_textbox(annot.rect)`) and the colour (map the RGB float tuple from `annot.colors["stroke"]` to a human-readable name: yellow, green, red, blue, pink, purple, orange — default to "yellow" if ambiguous).
    - **Text note / popup** (`annot.type[0] == 0`): record the comment text (`annot.info["content"]`) and the spatial position — if `annot.rect.x0 < page.rect.width * 0.35` call it `left`, if `annot.rect.x0 > page.rect.width * 0.65` call it `right`, otherwise `inline`.
  - Interleave annotations with text at the correct position. Annotations should appear immediately after the text block they spatially overlap with (match by y-coordinate range).
  - Format inline:
    - Highlights: `[HIGHLIGHT yellow: "highlighted text"]`
    - Notes: `[NOTE right: "margin comment"]`
  - Insert a page boundary marker before each page: `--- Page N ---`
- CLI: `python src/extract.py papers/foo.pdf` → writes `extracted/foo.txt`
- Print a summary to stdout: number of pages, highlights, and notes found.

### 2. `src/summarise.py` — summary generator

- Read an annotated `.txt` file from `extracted/`.
- Load the summary prompt template from `prompts/summary_prompt.md` (see below).
- Call the Claude API (`anthropic` SDK, model `claude-opus-4-6`) with the prompt, inserting the annotated text at the `<insert annotated text here>` placeholder.
- Use a system prompt: `"You are a precise research assistant helping a researcher write personal reading notes."`
- Write the response to `summaries/<stem>.md`.
- CLI: `python src/summarise.py extracted/foo.txt` → writes `summaries/foo.md`
- Stream the response to stdout as it arrives (use `client.messages.stream`).

### 3. `prompts/summary_prompt.md` — the summary prompt template

This file already exists in the repo. Do not recreate or modify it. `summarise.py` reads it at runtime and replaces the `<insert annotated text here>` placeholder with the contents of the extracted `.txt` file.

The prompt produces eight labelled sections in order: **What was the paper about**, **What problem did they solve**, **What is novel**, **Models and data**, **What did they conclude**, **My take**, **Summary** (a single ~5-sentence paragraph), and **BibTeX** (fetched from the official venue proceedings, not fabricated).

### 4. `run.sh` — convenience wrapper

A short shell script that runs both stages end-to-end:

```bash
#!/usr/bin/env bash
set -euo pipefail
PDF="$1"
STEM=$(basename "$PDF" .pdf)
python src/extract.py "papers/$STEM.pdf"
python src/summarise.py "extracted/$STEM.txt"
echo "Done — summary at summaries/$STEM.md"
```

Usage: `./run.sh LRAS`

### 5. Package management — `uv`

This project uses `uv`. A `pyproject.toml` already exists in the repo root with the correct dependencies (`pymupdf>=1.24`, `anthropic>=0.40`). Do **not** create a `requirements.txt`.

To install dependencies and run scripts:

```bash
uv sync                             # creates .venv and installs deps
uv run python src/extract.py ...   # run within the managed venv
uv run python src/summarise.py ...
```

Update `run.sh` to use `uv run`:

```bash
#!/usr/bin/env bash
set -euo pipefail
STEM="${1%.pdf}"
STEM=$(basename "$STEM")
uv run python src/extract.py "papers/$STEM.pdf"
uv run python src/summarise.py "extracted/$STEM.txt"
echo "Done — summary at summaries/$STEM.md"
```

---

## Constraints and style

- Keep each source file short and readable — this is a personal tool, not a production service.
- No classes needed; plain functions are fine.
- Fail loudly with a clear error if a file is not found or the API call fails — no silent fallbacks.
- The annotated text format must be stable: downstream prompts depend on it.
- Do not hard-code the API key; read it from the `ANTHROPIC_API_KEY` environment variable (the `anthropic` SDK does this automatically).
- Do not add a web UI, database, or any dependency beyond `pymupdf` and `anthropic`.
- Do not create `requirements.txt`; use `pyproject.toml` and `uv` only.

---

## Verification

After implementing, sync dependencies and test with the existing paper:

```bash
uv sync
./run.sh LRAS
```

Confirm:
- `extracted/LRAS.txt` exists and contains `--- Page N ---` markers, at least one `[HIGHLIGHT ...]`, and at least one `[NOTE ...]`.
- `summaries/LRAS.md` exists and contains all 8 labelled sections (Main problem, Their approach, What is novel, Models used, Datasets and benchmarks, Key findings, My take, Citation).
