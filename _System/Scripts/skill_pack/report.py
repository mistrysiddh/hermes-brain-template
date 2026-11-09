"""Hermes Brain — Skill Pack Report Generation.

Generates markdown education skill pack reports covering skill packs,
generated questions, self-evaluations, model routing decisions,
knowledge graph entries, dependency trees, adaptive practice, and
thinking fields.

Multi-harness compliant: stdlib-only.
"""

from datetime import datetime
from typing import Any


def generate_report(
    vault: str,
    packs: dict[str, Any],
    questions_by_topic: dict[str, list[dict[str, Any]]],
    self_evals: list[dict[str, Any]],
    model_routes: list[dict[str, Any]],
    propositions: list[dict[str, Any]] | None = None,
    dependency_trees: list[dict[str, Any]] | None = None,
    practice_problems: list[dict[str, Any]] | None = None,
    thinking_fields: list[dict[str, Any]] | None = None,
) -> str:
    """Generate markdown education skill pack report.

    Args:
        vault: Vault path.
        packs: Loaded skill packs.
        questions_by_topic: Mapping of topic → list of questions.
        self_evals: List of self-evaluation results.
        model_routes: List of model routing decisions.
        propositions: Optional list of knowledge graph propositions.
        dependency_trees: Optional list of dependency trees.
        practice_problems: Optional list of practice problems.
        thinking_fields: Optional list of thinking field records.

    Returns:
        Markdown report string.

    """
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    total_packs = len(packs)
    total_questions = sum(len(qs) for qs in questions_by_topic.values())
    total_self_evals = len(self_evals)
    avg_score = (
        sum(e["score"] for e in self_evals) / total_self_evals
        if total_self_evals > 0
        else 0.0
    )

    lines = [
        "# Education Skill Pack Report",
        f"Generated: {now}",
        f"Vault: {vault}",
        "",
        "## Summary",
        f"- **Skill packs**: {total_packs}",
        f"- **Topics with questions**: {len(questions_by_topic)}",
        f"- **Total questions generated**: {total_questions}",
        f"- **Self-evaluations**: {total_self_evals}",
        f"- **Average self-eval score**: {avg_score:.2f}",
        "",
    ]

    if propositions is not None:
        lines.extend(
            [
                f"- **Knowledge graph propositions**: {len(propositions)}",
                "",
            ]
        )
    if dependency_trees is not None:
        lines.extend(
            [
                f"- **Dependency trees**: {len(dependency_trees)}",
                "",
            ]
        )
    if practice_problems is not None:
        lines.extend(
            [
                f"- **Practice problems**: {len(practice_problems)}",
                "",
            ]
        )
    if thinking_fields is not None:
        lines.extend(
            [
                f"- **Thinking fields captured**: {len(thinking_fields)}",
                "",
            ]
        )

    if packs:
        lines.append("## Skill Packs")
        lines.append("")
        lines.append("| Pack | Topics | Questions |")
        lines.append("|------|--------|-----------|")
        for name, pack in packs.items():
            topics = (
                list(pack.get("topic", {}).keys())
                if isinstance(pack.get("topic"), dict)
                else []
            )
            qcount = sum(
                len(
                    pack.get("topic", {}).get(t, {}).get("questions", [])
                )
                for t in topics
            )
            lines.append(f"| {name} | {len(topics)} | {qcount} |")
        lines.append("")

    if questions_by_topic:
        lines.append("## Generated Questions")
        lines.append("")
        for topic, qs in questions_by_topic.items():
            lines.append(f"### {topic}")
            for q in qs:
                lines.append(
                    f"- **Q{q['id']}** ({q['difficulty']}): {q['question']}"
                )
                lines.append(f"  - Type: {q['type']} | Hint: {q['hint']}")
            lines.append("")

    if self_evals:
        lines.append("## Self-Evaluations")
        lines.append("")
        for i, e in enumerate(self_evals, 1):
            status = "REVISE" if e["should_revise"] else "OK"
            lines.append(
                f"- Eval {i}: score {e['score']:.2f} [{status}] — "
                f"{', '.join(e['issues']) or 'no issues'}"
            )
        lines.append("")

    if model_routes:
        lines.append("## Model Routing Decisions")
        lines.append("")
        lines.append(
            "| Task | Complexity | Model | Tier | Cost |"
        )
        lines.append(
            "|------|------------|-------|------|------|"
        )
        for r in model_routes:
            lines.append(
                f"| {r['task']} | {r['complexity']} | {r['model']} | "
                f"{r['tier']} | {r['estimated_cost']} |"
            )
        lines.append("")

    if propositions:
        lines.append("## Knowledge Graph — Propositions")
        lines.append("")
        for p in propositions[:10]:
            lines.append(
                f"- {p.get('content', 'N/A')} "
                f"(confidence: {p.get('confidence', 'N/A')})"
            )
        if len(propositions) > 10:
            lines.append(f"- ... and {len(propositions) - 10} more")
        lines.append("")

    if dependency_trees:
        lines.append("## Dependency Trees / Lesson Maps")
        lines.append("")
        for t in dependency_trees:
            lines.append(f"### Goal: {t.get('goal', 'N/A')}")
            lines.append(f"- DAG valid: {t.get('dag_valid', False)}")
            lines.append(f"- Nodes: {len(t.get('nodes', []))}")
            lines.append(f"- Edges: {len(t.get('edges', []))}")
            lines.append("")
            lines.append("```mermaid")
            lines.append(t.get("mermaid", "graph TD\n    A[\"No data\"]"))
            lines.append("```")
            lines.append("")

    if practice_problems:
        lines.append("## Adaptive Practice Problems")
        lines.append("")
        for p in practice_problems:
            lines.append(
                f"- **P{p['id']}** ({p['difficulty']}): {p['problem']}"
            )
            lines.append(f"  - Type: {p['type']} | Hint: {p['hint']}")
        lines.append("")

    if thinking_fields:
        lines.append("## Thinking Fields")
        lines.append("")
        for tf in thinking_fields[:10]:
            lines.append(
                f"- Q{tf.get('question_id', '?')}: "
                f"{tf.get('reasoning', 'N/A')[:80]}..."
            )
        if len(thinking_fields) > 10:
            lines.append(f"- ... and {len(thinking_fields) - 10} more")
        lines.append("")

    lines.append("## Next Steps")
    lines.append("")
    lines.append(
        "- Review generated questions and add them to skill pack files"
    )
    lines.append(
        "- Use self-evaluation scores to identify answers needing revision"
    )
    lines.append(
        "- Route complex tasks to smarter models, simple tasks to cheaper ones"
    )
    lines.append(
        "- Use knowledge graph propositions to build cross-session understanding"
    )
    lines.append(
        "- Use dependency trees to plan lesson sequences"
    )
    lines.append(
        "- Use adaptive practice problems to target learner weaknesses"
    )
    lines.append("")
    lines.append(
        "The graph stores ideas and connections, not ability ratings "
        "(ideas-not-ratings principle)."
    )
    lines.append("")

    return "\n".join(lines)
