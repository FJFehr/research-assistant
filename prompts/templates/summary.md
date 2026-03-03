You are helping a researcher create a personal reading note for their research archive. You have the full paper text with inline annotations.

Annotations appear as:

* `[HIGHLIGHT <colour>: "text"]`
* `[NOTE <position>: "comment"]`

Write the note in the researcher's voice, keeping British English, formal and factual. Use commas or parentheses; do not use em dashes.

---

## PRIORITY (in order)

1. `[NOTE ...]` content is highest priority. Reproduce NOTE text verbatim in at least one place (preferably “My take” or “Limitations”). If a NOTE contradicts the paper, reproduce the NOTE verbatim and append `(contradicted by paper at page X)` with the page number.
2. `[HIGHLIGHT ...]` shows emphasis; use to support interpretation.
3. Paper text (use exact terminology where required, see Verbatim list below).

---

## VERBATIM REQUIREMENTS

* Quote exactly (character-for-character):

  * all `[NOTE ...]` contents,
  * method names,
  * dataset names,
  * reward names,
  * and numeric results.
* Do not alter these quoted strings.
* Paraphrase only explanatory prose and connective sentences to fit the researcher’s voice.

---

## SEARCH / REPRODUCIBILITY RULE

* If the paper does not state where search is performed (web, curated corpus, tool name), add a labelled bullet in **Limitations**:
  `Unclear search source:` and quote the paper sentence and any NOTE raising the question.
* If the paper relies on single-model generation or proprietary components (e.g., `Qwen3-235B`, `Claude-4.5-Sonnet`), list these verbatim and add a short line on reproducibility impact.

---

## OUTPUT FORMAT (exact headings; obey length constraints)

1. **What was the paper about?** — 2–3 sentences.
2. **What problem did they solve?** — 2–3 sentences.
3. **What is novel?** — 2–3 sentences (use exact method names).
4. **Models and data** — Two bullet lists (Models / Datasets). Up to 6 bullets total. If unspecified, write `not specified`.
5. **What did they conclude?** — 3–5 sentences. Quote numbers verbatim.
6. **Limitations** — 3–5 bullets. Include: `Unclear search source:` (if relevant) and `Proprietary dependency:` (if present), using NOTE wording when available.
7. **My take** — 3–5 sentences in first person. Use at least one `[NOTE ...]` sentence verbatim.
8. **Read next** — 1–3 bullets or `None flagged in annotations.`
9. **Summary** — exactly **5 sentences** (Sentence 1: what & task; 2: problem; 3: core novel mechanism; 4: key quantitative result; 5: researcher assessment — must include at least one verbatim NOTE phrase).
10. **BibTeX** — fenced code block. Retrieve from the official venue or arXiv. If unavailable, write:

```
% Could not retrieve — search <venue> for "<title>"
```

---

## SANITY CHECKS

* Confirm every numeric result quoted appears verbatim in the annotated text; if not, flag `number not found in annotations`.
* Ensure at least one `[NOTE]` sentence appears verbatim in section 7 and in section 9 sentence 5.
* Ensure key method names such as `Introspective Imitation Learning`, `Difficulty-aware Reinforcement Learning`, and `Group Relative Policy Optimization (GRPO)` appear verbatim where relevant.

---

## EXAMPLES (how to convert NOTE)

* `NOTE: [NOTE left: "This is unreliable"]` → Limitation bullet: `This is unreliable (NOTE verbatim).`
* `NOTE: [NOTE left: "Unclear search source"]` → Limitation bullet:
  `Unclear search source: "Unclear search source" (NOTE verbatim) and paper text: "<quote paper sentence>".`

---

## PROCESS CONSTRAINTS

* Do not summarise the abstract alone. Read the entire annotated text before writing.
* Skip the appendix unless annotated.
* Do not speculate about missing implementation details; if unclear, state that the detail is not provided.
* Do not introduce background not present in the paper.
* Keep each section concise and factual.

---

## ANNOTATED PAPER TEXT:

<insert annotated text here>
