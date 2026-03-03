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

`papers/` is intentionally versioned for reproducible examples. `papers/ContextualJudge.pdf` is the canonical annotated sample in this repository.

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

Full pipeline (canonical example):

```bash
uv run pipeline --paper papers/ContextualJudge.pdf --url https://aclanthology.org/2025.acl-long.470/
```

Alternative example (arXiv paper):

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

## Example: ContextualJudge walkthrough

The canonical example in this repository is **ContextualJudge**, a benchmark paper from ACL 2025. Running the full pipeline produces three outputs:

```bash
uv run pipeline --paper papers/ContextualJudge.pdf --url https://aclanthology.org/2025.acl-long.470/
```

This generates:

1. **Extracted text** (`outputs/extracted/ContextualJudge.txt`) — annotated source text with margin notes and highlights preserved inline:
   ```
   [TITLE: "Does Context Matter? ContextualJudgeBench for Evaluating LLM-based Judges in Contextual Settings"]
   [AUTHORS: "Austin Xu⋆, Srijan Bansal⋆, Yifei Ming, Semih Yavuz, Shafiq Joty Salesforce AI Research"]
   ...
   The large language model (LLM)-as-judge paradigm has been used to meet the demand for a cheap, reliable, and fast evaluation of model outputs...
   [HIGHLIGHT yellow: "approach"]
   [NOTE right: "Evaluated from externally provided context."]
   ...
   ```

2. **BibTeX entry** (`outputs/bibtex/ContextualJudge.bib`) — fetched from ACL Anthology:
   ```bibtex
   @inproceedings{xu-etal-2025-context,
       title = "Does Context Matter? {C}ontextual{J}udge{B}ench for Evaluating {LLM}-based Judges in Contextual Settings",
       author = "Xu, Austin and Bansal, Srijan and Ming, Yifei and Yavuz, Semih and Joty, Shafiq",
       booktitle = "Proceedings of the 63rd Annual Meeting of the Association for Computational Linguistics",
       year = "2025",
       url = "https://aclanthology.org/2025.acl-long.470/",
       pages = "9541--9564"
   }
   ```

3. **Model-ready prompt** (`outputs/prompts/ContextualJudge.prompt.md`) — template + annotated text, ready for a local or manual model invocation:
   ```markdown
   You are helping a researcher create a precise personal reading note for their research archive...
   
   [Full annotated text inserted here]
   ```

4. **Final summary** (`summaries/ContextualJudge_summary.md`) — example output from processing the prompt, structured as:
   - What was the paper about?
   - What problem did they solve?
   - How did they solve it?
   - Models and data
   - Experimental results
   - What did they conclude?
   - Limitations
   - My take
   - Summary (exactly 5 sentences)
   - BibTeX

(The summary is generated externally — the pipeline produces steps 1–3 only; step 4 is manual or via a hosted LLM.)

## Outputs

```text
outputs/extracted/ContextualJudge.txt      # extracted annotated text
outputs/bibtex/ContextualJudge.bib         # fetched BibTeX (if available)
outputs/prompts/ContextualJudge.prompt.md  # model-ready prompt
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
