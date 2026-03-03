# Paper Reading Assistant

A two-stage pipeline that turns annotated PDFs into structured personal research notes.

1. **Extraction** — parses highlights (by colour) and margin notes from a PDF and writes them inline with the source text, producing an annotated `.txt` file.
2. **Summarisation** — feeds the annotated text to Claude with a crafted prompt and produces a personal research note in the reader's voice, driven by their own margin comments.

## Quickstart

```bash
uv sync
./run.sh LRAS
```

`ANTHROPIC_API_KEY` must be set in your environment before the summarise step runs (see [Configuration](#configuration)).

## Folder structure

| Folder | Purpose |
|---|---|
| `annotated papers/` | Input: annotated PDFs |
| `extracted/` | Intermediate: annotated `.txt` files, one per paper |
| `summaries/` | Output: structured research notes, one per paper |
| `prompts/` | Versioned prompt templates |
| `src/` | Extraction and summarisation source code |

## Annotation format

The intermediate `.txt` files interleave source text with inline markers:

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

Set `ANTHROPIC_API_KEY` in your environment before running the summarise step:

```bash
export ANTHROPIC_API_KEY=sk-ant-...
```

## Running tests

```bash
uv run pytest
```

Integration tests require `annotated papers/LRAS.pdf` to be present and are skipped automatically if the file is missing.
