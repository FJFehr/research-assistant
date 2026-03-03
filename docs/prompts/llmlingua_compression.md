# Prompt: Plan LLMLingua-2 prompt compression integration

**This is a planning task — produce a detailed design document, not code.**

Think carefully about how to integrate [LLMLingua-2](https://huggingface.co/spaces/microsoft/llmlingua-2) token compression into this pipeline before the summarisation step. Return a concrete plan with trade-offs and open questions.

---

## Context

The extracted annotated text (in `extracted/*.txt`) can be large — several thousand tokens for a long paper. Before feeding it to Claude in `src/summarise.py`, we could compress the text to reduce API cost and latency.

LLMLingua-2 works differently from naïve truncation: it runs a token-level binary classifier trained via data distillation to decide which tokens to keep or drop, preserving the most task-relevant content. The model is available on HuggingFace as `microsoft/llmlingua-2-xlm-roberta-large-meetingbank`.

The key constraint: **annotations must never be dropped**. Highlights and margin notes (`[HIGHLIGHT ...]`, `[NOTE ...]`) are the highest-value content in the file — they are the reader's own words and the primary input to the summariser.

---

## Planning task

Investigate and answer the following questions in your plan:

### 1. Where does compression fit in the pipeline?

Should compression happen:
- Inside `src/summarise.py`, between reading the extracted text and building the API call?
- As a separate `src/compress.py` step that writes a compressed file to e.g. `compressed/*.txt`?
- Inside `run.sh` as an optional stage?

Consider: does it make sense to cache the compressed file, or is on-the-fly compression fast enough?

### 2. How do we protect annotations from being dropped?

LLMLingua-2's `compress_prompt` API accepts a list of `context` segments and an `instruction` string. There may be a way to mark certain spans as "must-keep".

Options to evaluate:
- **Segment splitting**: pass annotation markers as separate segments and never compress them; only compress plain-text paragraphs.
- **Force-keep tokens**: check if the llmlingua API supports pinning specific token indices.
- **Post-hoc check**: compress the whole text, then verify all `[HIGHLIGHT` and `[NOTE` markers survived; abort and fall back to uncompressed if any are missing.

### 3. What compression ratio is realistic?

For a ~12,000-token extracted paper, what target ratio would make the cost saving worth the added complexity and inference time? Consider:
- LLMLingua-2 inference runs locally (no API cost) but requires loading a ~400 MB model.
- Claude Sonnet/Opus input pricing per million tokens.
- Typical extracted text size for an ML paper.

### 4. What is the model loading overhead?

The compressor model must be loaded from HuggingFace. Options:
- Load on every `summarise.py` call (simple, slow for one-offs).
- Keep a persistent server process and call it via HTTP (complex, good for batch runs).
- Add a `--compress` flag to `summarise.py` so it is opt-in.

### 5. What new dependencies are needed?

The current `pyproject.toml` only has `pymupdf` and `anthropic`. LLMLingua-2 requires `llmlingua` (which pulls in `torch` and `transformers`). Evaluate:
- How large is the added dependency footprint?
- Should compression be an optional extra (`uv pip install paper-reading-assistant[compress]`)?

---

## Deliverable

Return a structured plan covering:
1. Recommended pipeline placement and file structure.
2. Strategy for protecting annotations.
3. Recommended compression ratio target.
4. Model loading strategy.
5. Dependency approach.
6. Any open questions or risks that need resolving before implementation.

Do **not** write any code — this is a planning step only.
