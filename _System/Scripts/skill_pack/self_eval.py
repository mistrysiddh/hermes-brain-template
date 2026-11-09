"""Hermes Brain — Skill Pack Self-Evaluation.

Evaluates the agent's own answers against quality criteria
(accuracy, clarity, completeness, conciseness) using heuristic checks.

Multi-harness compliant: stdlib-only, dry-run aware.
"""

from typing import Any


def self_question(
    answer: str,
    criteria: list[str] | None = None,
    dry_run: bool = True,
) -> dict[str, Any]:
    """Self-evaluate an answer against quality criteria.

    Returns:
        {
            "score": float (0.0–1.0),
            "issues": list[str],
            "suggestions": list[str],
            "should_revise": bool,
            "criteria": list[str],
        }

    Heuristic checks:
        - Answers shorter than 10 chars are flagged as too short.
        - Answers missing reasoning connectives (because, since,
          therefore, however) are flagged.
        - Score is clamped to [0.0, 1.0].
        - should_revise is True if score < 0.7 or any issues found.

    Args:
        answer: The answer text to evaluate.
        criteria: Optional list of criteria names. Defaults to
            ["accuracy", "clarity", "completeness", "conciseness"].
        dry_run: If True, no side effects (reserved for future use).

    """
    if criteria is None:
        criteria = ["accuracy", "clarity", "completeness", "conciseness"]

    issues: list[str] = []
    suggestions: list[str] = []
    score = 1.0

    # Simple heuristic checks
    if len(answer.strip()) < 10:
        issues.append("Answer too short")
        suggestions.append("Expand with more detail")
        score -= 0.3

    if not any(
        c in answer.lower()
        for c in ["because", "since", "therefore", "however"]
    ):
        issues.append("No reasoning connective found")
        suggestions.append(
            "Add reasoning words (because, therefore, etc.)"
        )
        score -= 0.2

    if "?" not in answer and score > 0.8:
        # Reserved: could flag answers that restate without depth
        pass

    score = max(0.0, min(1.0, score))
    should_revise = score < 0.7 or len(issues) > 0

    return {
        "score": round(score, 2),
        "issues": issues,
        "suggestions": suggestions,
        "should_revise": should_revise,
        "criteria": criteria,
    }
