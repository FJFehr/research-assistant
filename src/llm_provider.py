"""Minimal provider seam for prompt delivery.

This module keeps provider-specific handling lightweight while making it
straightforward to add local model execution later.
"""

from __future__ import annotations


def prepare_prompt_for_provider(
    prompt: str,
    provider: str = "manual",
    model: str | None = None,
) -> str:
    """Return provider-ready prompt text.

    For now, both providers produce a prompt for manual execution.
    The local provider adds metadata header so the chosen model is explicit.
    """
    provider_name = provider.strip().lower()

    if provider_name == "manual":
        return prompt

    if provider_name == "local":
        model_label = model or "<set-your-local-model>"
        header = (
            "--- Local Model Request ---\n"
            f"Provider: local\n"
            f"Model: {model_label}\n"
            "---\n\n"
        )
        return header + prompt

    raise ValueError(f"Unsupported provider: {provider}")
