You are helping a researcher create a precise personal reading note for their research archive. You have the full paper text with inline annotations.

Annotations appear as:

* `[HIGHLIGHT <colour>: "text"]`
* `[NOTE <position>: "comment"]`

Write the note in the researcher’s voice, using British English, formal and factual. Use commas or parentheses; do not use em dashes. Avoid vague language.

You must extract the exact problem, the exact mechanism of solution, the exact models used, the exact datasets used (and where), and the exact numerical results.

---

## PRIORITY (in order)

1. `[NOTE ...]` content is highest priority.

   * Reproduce NOTE text **verbatim** in at least one place (preferably “My take” or “Limitations”).
   * If a NOTE contradicts the paper, reproduce the NOTE verbatim and append `(contradicted by paper at page X)` with the page number.
2. `[HIGHLIGHT ...]` indicates emphasis and must inform interpretation.
3. Paper text must be used with exact terminology where required (see Verbatim Rules below).

---

## VERBATIM REQUIREMENTS (STRICT)

You must quote exactly (character-for-character):

* all `[NOTE ...]` contents
* method names
* algorithm names
* model names
* dataset names
* reward names
* benchmark names
* training objectives
* numeric results (including % signs, decimals, ± values)

Do not alter quoted strings.

Paraphrase only connective or explanatory prose.

If a required item is missing from the paper, explicitly state:
`not specified in paper`.

If a number appears in your summary but not in the annotated text, write:
`number not found in annotations`.

---

## MECHANISTIC PRECISION RULE

When describing the solution:

* Explicitly state:

  * What the baseline approach was.
  * What fails in the baseline.
  * What component the authors introduce.
  * How that component changes optimisation, training, search, or inference.
  * Where it is inserted in the pipeline.

Avoid generic phrases such as:

* “They improve performance”
* “They enhance reasoning”
* “They propose a framework”

Instead describe the mechanism.

---

## MODELS AND DATA EXTRACTION RULE

You must explicitly answer:

* Which exact models were used?
* Were they fine-tuned or prompting-only?
* Where were they used (policy, reward model, generator, evaluator, retriever, etc.)?
* Which datasets were used?
* Were they used for training, evaluation, or both?

If any of these are unclear, write:
`not specified in paper`.

---

## SEARCH / REPRODUCIBILITY RULE

If the paper involves search, tools, or retrieval:

* State explicitly:

  * Where search is performed (web, curated corpus, tool name, internal database).
  * Whether this source is reproducible.

If unspecified, include in **Limitations**:

`Unclear search source:`
Quote the relevant paper sentence and any NOTE raising the issue.

If proprietary components are used (e.g., `Qwen3-235B`, `Claude-4.5-Sonnet`), add:

`Proprietary dependency:` and state the reproducibility impact.

---

## OUTPUT FORMAT (exact headings; obey constraints strictly)

### 1. **What was the paper about?**

2–3 sentences. State the task and setting precisely.

### 2. **What problem did they solve?**

2–3 sentences. Clearly describe the failure mode or limitation of prior work.

### 3. **How did they solve it?**

3–5 sentences.
Describe the mechanism step-by-step.
Use exact method names.
State where in the pipeline the method operates.

### 4. **Models and data**

**Models**

* Up to 4 bullets.
* Format: `Model name` — role — training or inference — fine-tuned or prompting (if stated).

**Datasets**

* Up to 4 bullets.
* Format: `Dataset name` — used for training/evaluation/both — task.

If unspecified, write `not specified in paper`.

---

### 5. **Experimental results**

3–6 sentences.

* Quote all numerical results verbatim.
* State which model achieved which number on which dataset.
* If comparison to baseline is reported, state both baseline and new result.

If numbers are missing from annotations, write:
`number not found in annotations`.

---

### 6. **What did they conclude?**

3–5 sentences.
Summarise claims strictly grounded in the text.

---

### 7. **Limitations**

3–6 bullets.

Include when relevant:

* `Unclear search source:`
* `Proprietary dependency:`
* Any NOTE marked concerns (verbatim).

Do not speculate beyond the text.

---

### 8. **My take**

3–5 sentences in first person.

* Use at least one `[NOTE ...]` sentence verbatim.
* Critically assess novelty, reproducibility, and research impact.

---

## 9. **Summary** (exactly 5 sentences)

Write **exactly five sentences**. No more, no fewer.

Each sentence has a fixed role:

**Sentence 1 — What & setting**
State precisely what the paper does and the task setting. Use exact terminology from the paper.

**Sentence 2 — Problem**
State the exact problem or limitation in prior work that the paper addresses. Avoid vague phrasing. Describe the concrete failure mode.

**Sentence 3 — Solution mechanism**
Explain exactly how they solved it.

* Name the method verbatim.
* State where it operates (training, inference, search, reward modelling, etc.).
* Briefly describe the mechanism, not just that it improves performance.

**Sentence 4 — Models, data, and results**
State:

* The exact model name(s) used.
* The exact dataset name(s) used and whether for training or evaluation (if stated).
* The key numerical result(s), quoted verbatim.
  If a number is not present in the annotated text, write: `number not found in annotations`.

**Sentence 5 — Researcher takeaway (must include NOTE)**
Provide the researcher’s assessment in one sentence.

* Include at least one `[NOTE ...]` sentence verbatim.
* Highlight a key implication, limitation, or concern grounded in the annotations.

### Strict requirements

* Use exact wording for:

  * Method names
  * Model names
  * Dataset names
  * Benchmark names
  * Numeric results
* Do not paraphrase these items.
* Do not introduce background not present in the annotated text.
* Do not use em dashes.
* Do not exceed five sentences.

---

### 10. **BibTeX**

Provide a fenced code block.

Retrieve from official venue or arXiv.

If unavailable:

```
% Could not retrieve — search <venue> for "<title>"
```

---

## SANITY CHECKS (must self-verify before output)

* At least one `[NOTE]` appears verbatim in section 8 and in section 9 sentence 5.
* All numeric results appear verbatim in annotated text.
* All method names are exact.
* Models and datasets are explicitly listed or marked `not specified in paper`.
* No abstract-only summary.
* No speculation.
* No em dashes.

## ANNOTATED PAPER TEXT: 

<insert annotated text here>