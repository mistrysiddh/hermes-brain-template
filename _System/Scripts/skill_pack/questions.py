"""Hermes Brain — Skill Pack Question Generation.

Generates educational questions for any topic within a skill pack,
supporting tutor/Socratic mode at easy/medium/hard difficulty.

Multi-harness compliant: stdlib-only, dry-run aware.
"""

from typing import Any


def generate_questions(
    skill_pack: dict | None,
    topic: str,
    difficulty: str = "medium",
    count: int = 3,
    dry_run: bool = True,
) -> list[dict[str, Any]]:
    """Generate educational questions for a topic within a skill pack.

    Returns a list of question dicts:
        {question, type, expected_answer, hint, id, topic, difficulty}

    Args:
        skill_pack: The loaded skill pack data (dict) or None.
        topic: Topic to generate questions for.
        difficulty: Question difficulty — "easy", "medium", or "hard".
        count: Number of questions to generate.
        dry_run: If True, questions are not persisted to the vault.

    """
    pack = skill_pack.get("topic", {}).get(topic, {}) if skill_pack else {}
    pack_questions = pack.get("questions", []) if pack else []

    questions: list[dict[str, Any]] = []
    for i in range(count):
        q: dict[str, Any] = {
            "id": f"q{i + 1}",
            "topic": topic,
            "difficulty": difficulty,
            "question": f"What is {topic}? (question {i + 1} of {count})",
            "type": "open_ended",
            "expected_answer": pack.get("summary", "") if pack else "",
            "hint": f"Think about the key concepts of {topic}.",
        }
        if i < len(pack_questions):
            q["question"] = pack_questions[i].get("question", q["question"])
            q["type"] = pack_questions[i].get("type", q["type"])
            q["expected_answer"] = pack_questions[i].get("answer", q["expected_answer"])
            q["hint"] = pack_questions[i].get("hint", q["hint"])
        questions.append(q)

    return questions
