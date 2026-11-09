"""Hermes Brain — Skill Pack Adaptive Practice.

Generates varied problem streams for practice sessions, with
adaptive difficulty and small hints.

Inspired by LearnHarness's Practice phase:
- Varied problem stream — separate sessions pose problems requiring
  knowledge to come to mind without being named first.
- Adaptive difficulty — problems and hints adapt to learner's
  reasoning.
- Targeted difficulty — agent targets difficulties revealed by
  thinking fields.
- Small hints — when learner gets stuck, small hints are given.
- Recall-focused — aims for recall that succeeds with effort
  (desirable difficulty).

Multi-harness compliant: stdlib-only, --dry-run default, --apply.
"""

import os
import random
from typing import Any

VAULT = None


def init_paths(vault_path):
    """Resolve the vault root path from the given vault path."""
    global VAULT
    VAULT = os.path.abspath(vault_path)


def generate_practice_problems(
    topic: str,
    difficulty: str = "medium",
    count: int = 3,
    thinking_field_weaknesses: list[str] | None = None,
    dry_run: bool = True,
) -> list[dict[str, Any]]:
    """Generate adaptive practice problems for a topic.

    Args:
        topic: The topic to generate practice problems for.
        difficulty: "easy", "medium", or "hard".
        count: Number of problems to generate.
        thinking_field_weaknesses: Optional list of areas where the
            learner struggled (from thinking fields). Problems will
            target these areas.
        dry_run: If True, problems are returned but not written.

    Returns:
        List of problem dicts:
            {
                "id": str,
                "topic": str,
                "difficulty": str,
                "problem": str,
                "type": str,          # "recall" | "application" | "synthesis"
                "hint": str,
                "targets_weakness": bool,
            }

    """
    problem_types = ["recall", "application", "synthesis"]
    weaknesses = thinking_field_weaknesses or []

    problems: list[dict[str, Any]] = []
    for i in range(count):
        ptype = problem_types[i % len(problem_types)]
        targets = bool(weaknesses) and (i < len(weaknesses))
        hint = f"Think about the key concepts of {topic}."
        if targets and i < len(weaknesses):
            hint = f"Focus on: {weaknesses[i]}. {hint}"

        problem = {
            "id": f"p{i + 1}",
            "topic": topic,
            "difficulty": difficulty,
            "problem": (
                f"Apply {topic} to a new scenario (practice {i + 1} of {count})"
            ),
            "type": ptype,
            "hint": hint,
            "targets_weakness": targets,
        }
        problems.append(problem)

    return problems


def adapt_difficulty(
    current_difficulty: str,
    learner_performance: float,
) -> str:
    """Adapt problem difficulty based on learner performance.

    Args:
        current_difficulty: Current difficulty level.
        learner_performance: Float 0.0–1.0 (1.0 = perfect).

    Returns:
        New difficulty level ("easy", "medium", or "hard").

    """
    order = ["easy", "medium", "hard"]
    idx = order.index(current_difficulty) if current_difficulty in order else 1

    if learner_performance >= 0.8 and idx < len(order) - 1:
        return order[idx + 1]  # Increase difficulty
    if learner_performance < 0.4 and idx > 0:
        return order[idx - 1]  # Decrease difficulty
    return current_difficulty  # Keep same
