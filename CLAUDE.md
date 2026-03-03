# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Overall Objective

A personal paper reading assistant that processes annotated PDFs into structured, personal research summaries. The pipeline has two stages:

1. **Annotation extraction**: Parse a PDF with highlights (by color) and margin notes → produce an annotated text file that preserves the exact positions of all annotations inline with the source text.
2. **Summary generation**: Feed the annotated text to Claude with a carefully designed prompt → produce an educated, opinionated summary in the reader's voice.

The reader's margin notes are the primary signal for voice and emphasis. Highlights tell you what was deemed important; notes tell you *what the reader thought about it*. The output summaries are for personal research use (not yet for review or paper writing).

---

## Folder Structure (target)

```
papers/          ← input: annotated PDFs
extracted/       ← intermediate: annotated .txt files (one per paper)
summaries/       ← output: structured summaries (one per paper)
prompts/         ← versioned prompt templates
src/             ← extraction and summarisation code
```

---

## Pipeline Step 1: PDF Annotation Extraction

**Goal**: Produce a `.txt` file where every highlight and margin note from the PDF is placed inline at the exact location it appears in the text.

**Annotation types to capture**:
- Highlighted text, with colour (yellow, green, red, etc.) — different colours may carry different reader intent
- Margin notes / pop-up comments — placed immediately after the text segment they are anchored to
- The spatial position of margin notes (left margin, right margin, inline) should be recorded, as position is often semantically meaningful (left = broad question, right = specific reaction, etc.)

**Recommended extraction library**: `pymupdf` (fitz) — it exposes highlight quads, annotation types, colours, and comment text.

**Annotated text format** (to be finalised in code, but the intent is):
```
...source text...
[NOTE right: "Good labels for me. What data do they use?"]
...more source text with [HIGHLIGHT yellow: "key phrase"] inline...
[NOTE left: "Its learning to search. I want to do something a bit different."]
...
```

Rules:
- Notes are inserted at the point in the text where they are anchored, not collected at the end.
- Highlight colour is always preserved.
- Page numbers are marked at each page boundary: `--- Page 3 ---`.

---

## Pipeline Step 2: Summary Generation Prompt

This is the core prompt. It should produce a summary that reads like the researcher wrote it themselves, driven by their annotations.

### Prompt design principles

1. **Annotations drive voice**: The margin notes are paramount. They contain the reader's direct reactions, questions, and connections to their own work. The summary should echo this language and framing, not the abstract's language.
2. **Highlights signal emphasis**: What was highlighted (especially in a distinct colour) tells you what the reader found important. Weight these sections more heavily.
3. **Opinionated, not neutral**: This is a personal note, not a review. Be direct. If the reader's notes express scepticism, reflect that.
4. **Structured but readable**: Answer the fixed questions, but write them as connected prose sections, not bullet dumps.

---

### Summary Prompt Template

```
You are helping a researcher create a personal reading note for their research archive.
You have been given the full text of a paper with the researcher's annotations embedded inline.
Annotations appear in two forms:
  - [HIGHLIGHT <colour>: "text"] — text the researcher highlighted while reading
  - [NOTE <position>: "comment"] — the researcher's own words, written in the margin at that point in the paper

Your job is to write a summary in the researcher's voice.

CRITICAL RULES:
- The researcher's margin notes ([NOTE ...]) are the most important input. They reveal what they found significant, surprising, or connected to their own work. Use their exact phrasing and framing wherever possible. Do not neutralise or academicise their voice.
- Highlights show emphasis; notes show thought. Prioritise notes over highlights when they conflict.
- Do not summarise the abstract. Read the full annotated text and synthesise from it.
- Write in first person ("I", "they found", "what's interesting here is..."), as if the researcher is explaining the paper to a colleague.
- Be concise but complete. Avoid padding.

Answer the following questions as labelled sections. Each section should be 2–5 sentences of flowing prose unless the content demands more.

---

**1. Main problem**
What problem were the authors trying to solve? Why does it matter?

**2. Their approach**
How did they solve it? What is the key mechanism or insight?

**3. What is novel**
What is genuinely new here compared to prior work? Be specific — what had not been done before?

**4. Models used**
What base models or architectures did they use or fine-tune?

**5. Datasets and benchmarks**
What datasets, benchmarks, or evaluation setups did they use?

**6. Key findings**
What were the main results? Include numbers where the researcher highlighted them. Note any results the researcher flagged with scepticism or particular interest.

**7. My take**
Synthesise the researcher's margin notes into a personal assessment. What did they find most interesting? What open questions did they flag? What connections to their own work did they note?

**8. Citation**
- Lead author and institution
- Full BibTeX entry (Ask for URL of the venue/year go to this url and get the bibtex entry) If the paper is from ACL, NEURIPS, ICML, ICLR, EMNLP, CVPR, ICCV, ECCV, or similar, you can get the BibTeX from the official proceedings website. For arXiv papers, you can use the arXiv ID to retrieve the BibTeX entry from arXiv's API.

---

ANNOTATED PAPER TEXT:
<insert annotated text here>
```

---

## Paper in This Repo

**LRAS.pdf** — "LRAS: Advanced Legal Reasoning with Agentic Search", Yujin Zhou et al., HKUST / Shanghai AI Lab, arXiv 2026.

- Problem: Legal LLMs have an introspection deficit — in 71.3% of failure cases they never trigger search even when tools are available, leading to confident hallucinations.
- Solution: Two mechanisms — (i) Introspective Imitation Learning to recognise knowledge boundaries; (ii) Difficulty-aware RL for multi-step exploratory search.
- Action space: `<think>` → `<search>` → `<information>` loop.
- Results: 8.2–32% over baselines on JEC-QA, LegalBench, LawBench, LexEval.
