# Paper Reading Assistant

A lightweight repository for turning annotated PDFs into structured, personal research notes.

## Repository overview

This project focuses on a clean, local-first workflow:

1. **Extraction** — parse highlights and margin notes from an annotated PDF and preserve them inline with source text.
2. **BibTeX retrieval (optional)** — fetch BibTeX from arXiv/venue URLs and store it as a sidecar.
3. **Prompt generation** — inject extracted text into a versioned prompt template for manual or local model use.

The default flow does not call hosted LLM APIs; it generates ready-to-run prompts.

## Quickstart

```bash
uv sync
uv run pipeline --paper papers/LRAS.pdf --url https://arxiv.org/abs/2601.07296
```

Shortcut wrapper (extract + prompt generation):

```bash
./run.sh LRAS
```

## Folder structure

| Folder | Purpose |
|---|---|
| `papers/` | Input: annotated PDFs |
| `outputs/extracted/` | Extracted `.txt` files |
| `outputs/prompts/` | Prompt files ready for manual/local models |
| `outputs/summaries/` | Optional final summaries |
| `outputs/bibtex/` | Optional BibTeX sidecars |
| `prompts/templates/` | Runtime prompt templates |
| `docs/prompts/` | Archived prompt-engineering notes |
| `src/` | Extraction and summarisation source code |

## Interface

Main CLI:

```bash
uv run pipeline --paper papers/<name>.pdf --url <paper-url-or-id>
```

Equivalent direct invocation:

```bash
uv run python src/pipeline.py --paper papers/<name>.pdf --url <paper-url-or-id>
```

### Common usage

Full pipeline:

```bash
uv run pipeline --paper papers/LRAS.pdf --url 2601.07296
```

Local-model-targeted prompt:

```bash
uv run pipeline \
  --paper papers/LRAS.pdf \
  --url https://arxiv.org/abs/2601.07296 \
  --provider local \
  --model llama3.1:8b
```

Skip BibTeX:

```bash
uv run pipeline --paper papers/LRAS.pdf --no-bibtex
```

### CLI options

| Option | Effect |
|---|---|
| `--paper` | Path to input PDF (canonical flag) |
| `--papers` | Deprecated alias for `--paper` |
| `--url` | URL or arXiv ID for BibTeX fetching |
| `--no-bibtex` | Skip BibTeX retrieval |
| `--provider` | `manual` or `local` |
| `--model` | Optional model label in generated prompt |
| `--output-dir` | Output root directory (default: `outputs`) |

## Outputs

```text
outputs/extracted/LRAS.txt      # extracted annotated text
outputs/bibtex/LRAS.bib         # fetched BibTeX (if available)
outputs/prompts/LRAS.prompt.md  # model-ready prompt
```

Pipeline flow:

```text
Input PDF (papers/*.pdf)
	↓
[STEP 1: extract.py] → outputs/extracted/<paper>.txt
	↓
[STEP 2: get_bibtex.py] → outputs/bibtex/<paper>.bib (optional)
	↓
[STEP 3: summarise.py + template] → outputs/prompts/<paper>.prompt.md
```

## Annotation format

Extracted `.txt` files interleave source text with inline markers:

```
--- Page 3 ---
[SECTION: "3 Method"]
The proposed approach uses a two-stage training pipeline.
[HIGHLIGHT yellow: "two-stage training pipeline"]
[NOTE right: "Is this different from RLHF?"]
Each stage optimises a different objective.
[EQUATION]
--- Page 4 ---
[FIGURE 2: "Overview of the training framework."]
```

- `[HIGHLIGHT <colour>: "..."]` — text the reader highlighted, with colour preserved.
- `[NOTE <position>: "..."]` — the reader's own words, at the point they were written. Position is `left`, `right`, or `inline`.
- `[SECTION: "..."]` / `[SUBSECTION: "..."]` — structural headings detected from font size and boldness.
- `[EQUATION]` / `[FIGURE N: "..."]` / `[TABLE]` — non-text elements.
- The References section is removed; appendix sections without annotations are dropped.

## Configuration

No API key is required for the default workflow (manual/local prompt generation).

```bash
uv run pipeline --paper papers/LRAS.pdf --url https://arxiv.org/abs/2601.07296
```

Prompt template location:

- Runtime template: `prompts/templates/summary.md`
- Prompt-engineering history/notes: `docs/prompts/`

## Running tests

```bash
uv run pytest
```

Integration tests require `papers/LRAS.pdf` to be present and are skipped automatically if the file is missing.
