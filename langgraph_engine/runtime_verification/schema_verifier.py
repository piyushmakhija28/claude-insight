"""Structural schema verifiers for Step 1 orchestration outputs.

A lightweight (no-LLM) check that the orchestration prompt is well-formed,
returning a list of error strings (empty = valid) for the caller to log.

This module once also covered a decomposed todo_list and an orchestrator result.
Both described the pre-2026-08-07 Step 1, which decomposed its prompt into TODOs
and executed them; neither shape is produced any more.
"""

from __future__ import annotations

from typing import List

_MIN_PROMPT_LEN = 200


def verify_orchestration_prompt(prompt: str) -> List[str]:
    """Validate structure of the orchestration prompt from prompt_gen_expert_caller.

    Returns a list of error strings. Empty list means the prompt is valid.
    """
    errors: List[str] = []
    if not prompt or not prompt.strip():
        errors.append("orchestration_prompt is empty")
        return errors
    if len(prompt) < _MIN_PROMPT_LEN:
        errors.append("orchestration_prompt too short: %d chars (min %d)" % (len(prompt), _MIN_PROMPT_LEN))
    if "Phase" not in prompt:
        errors.append("orchestration_prompt missing 'Phase' keyword -- may not be a valid orchestration prompt")
    return errors
