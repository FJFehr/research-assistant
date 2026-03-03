"""Generate a prompt ready for manual pasting into Claude or a local model.

Usage:
    python src/summarise.py outputs/extracted/foo.txt

Writes: outputs/prompts/foo.prompt.md (ready to paste into a model)
"""

import sys
from pathlib import Path

PROMPT_CANDIDATES = (
    Path("prompts/templates/summary.md"),
    Path("prompts/summary_prompt.md"),
)


def resolve_prompt_path() -> Path:
    for candidate in PROMPT_CANDIDATES:
        if candidate.exists():
            return candidate
    print(
        "Error: prompt template not found. Checked: "
        + ", ".join(str(path) for path in PROMPT_CANDIDATES),
        file=sys.stderr,
    )
    sys.exit(1)


def load_prompt(annotated_text: str, preface_text: str = "") -> str:
    prompt_path = resolve_prompt_path()
    template = prompt_path.read_text(encoding="utf-8")
    if "<insert annotated text here>" not in template:
        print(
            "Error: prompt template missing '<insert annotated text here>' placeholder",
            file=sys.stderr,
        )
        sys.exit(1)
    full_input = annotated_text
    if preface_text.strip():
        full_input = preface_text.strip() + "\n\n" + annotated_text
    return template.replace("<insert annotated text here>", full_input)


def summarise(input_path: Path, output_path: Path, preface_text: str = "") -> None:
    annotated_text = input_path.read_text(encoding="utf-8")
    prompt = load_prompt(annotated_text, preface_text=preface_text)

    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(prompt, encoding="utf-8")
    print(f"\n✓ Prompt written to {output_path}")
    print(
        "\nCopy the contents and paste into Claude (claude.ai) or your local model.\n"
    )


def main() -> None:
    if len(sys.argv) != 2:
        print(
            "Usage: python src/summarise.py outputs/extracted/foo.txt",
            file=sys.stderr,
        )
        sys.exit(1)

    input_path = Path(sys.argv[1])
    if not input_path.exists():
        print(f"Error: file not found: {input_path}", file=sys.stderr)
        sys.exit(1)

    output_path = Path("outputs/prompts") / f"{input_path.stem}.prompt.md"
    summarise(input_path, output_path)


if __name__ == "__main__":
    main()
