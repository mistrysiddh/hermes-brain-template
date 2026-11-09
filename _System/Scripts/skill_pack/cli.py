"""Hermes Brain — Skill Pack CLI.

Entry point for the Skill Pack for Education skill. Dispatches to
sub-modules: manager, questions, self_eval, model_router,
knowledge_graph, dependency_tree, adaptive_practice, thinking_fields,
report.

Multi-harness compliant:
  - --vault CLI arg, deferred path resolution via init_paths()
  - --dry-run default / --apply for human-in-the-loop approval
  - stdlib-only
  - --test built-in self-test suite
"""

import argparse
import json
import os
import sys

from . import manager, questions, self_eval, model_router, report
from . import knowledge_graph as kg
from . import dependency_tree as dt
from . import adaptive_practice as ap
from . import thinking_fields as tf


def parse_args():
    parser = argparse.ArgumentParser(
        description=(
            "Hermes Brain Skill Pack for Education — question users, "
            "self-evaluate, route models, and maintain a knowledge graph."
        ),
    )
    parser.add_argument("--vault", help="Path to the Hermes Brain vault root")
    parser.add_argument(
        "--dry-run",
        action="store_true",
        default=True,
        help="Preview without applying (default)",
    )
    parser.add_argument(
        "--apply",
        action="store_true",
        help="Apply changes (overrides --dry-run)",
    )
    parser.add_argument(
        "--test",
        action="store_true",
        help="Run built-in self-test suite",
    )

    # --- Core subcommands -------------------------------------------------
    parser.add_argument(
        "--topic", default="general", help="Topic to generate questions for"
    )
    parser.add_argument(
        "--difficulty",
        default="medium",
        choices=["easy", "medium", "hard"],
        help="Question difficulty level",
    )
    parser.add_argument(
        "--count", type=int, default=3, help="Number of questions to generate"
    )
    parser.add_argument(
        "--self-eval",
        action="store_true",
        help="Run self-evaluation on generated answers",
    )
    parser.add_argument(
        "--answer", default="", help="Answer text to self-evaluate"
    )
    parser.add_argument(
        "--complexity",
        type=float,
        default=0.5,
        help="Task complexity for model routing (0.0-1.0)",
    )

    # --- Knowledge graph subcommands --------------------------------------
    parser.add_argument(
        "--kg-add-proposition",
        metavar="CONTENT",
        help="Add a proposition to the knowledge graph",
    )
    parser.add_argument(
        "--kg-list",
        action="store_true",
        help="List knowledge graph propositions",
    )
    parser.add_argument(
        "--kg-add-chain",
        metavar="PREMISES",
        help="Add a reasoning chain (premises as comma-separated text)",
    )
    parser.add_argument(
        "--kg-chain-conclusion",
        metavar="CONCLUSION",
        help="Conclusion for --kg-add-chain",
    )

    # --- Dependency tree subcommands --------------------------------------
    parser.add_argument(
        "--dt-build",
        metavar="GOAL",
        help="Build a dependency tree / lesson map for a goal",
    )
    parser.add_argument(
        "--dt-list",
        action="store_true",
        help="List saved dependency trees",
    )
    parser.add_argument(
        "--dt-understanding",
        metavar="CONCEPTS",
        help="Comma-separated concepts the learner already understands",
    )

    # --- Adaptive practice subcommands ------------------------------------
    parser.add_argument(
        "--practice-gen",
        action="store_true",
        help="Generate adaptive practice problems for --topic",
    )
    parser.add_argument(
        "--practice-weaknesses",
        metavar="AREAS",
        help="Comma-separated weakness areas from thinking fields",
    )

    # --- Thinking fields subcommands --------------------------------------
    parser.add_argument(
        "--tf-capture",
        metavar="QUESTION_ID",
        help="Capture a thinking field for a question ID",
    )
    parser.add_argument(
        "--tf-answer",
        default="",
        help="Learner's answer (for --tf-capture)",
    )
    parser.add_argument(
        "--tf-reasoning",
        default="",
        help="Free-text reasoning (for --tf-capture)",
    )
    parser.add_argument(
        "--tf-confidence",
        type=float,
        default=None,
        help="Confidence score 0.0-1.0 (for --tf-capture)",
    )
    parser.add_argument(
        "--tf-list",
        action="store_true",
        help="List thinking field records",
    )
    parser.add_argument(
        "--tf-boundary",
        action="store_true",
        help="Detect understanding boundary from thinking fields",
    )

    return parser.parse_args()


def run_self_test():
    """Run built-in self-test suite across all sub-modules."""
    print("🧪 Skill Pack for Education Self-Test Suite")
    print("=" * 50)
    passed = 0
    failed = 0

    def check(name, fn):
        nonlocal passed, failed
        try:
            fn()
            print(f"✅ {name}")
            passed += 1
        except Exception as e:
            print(f"❌ {name} failed: {e}")
            failed += 1

    # --- manager tests ----------------------------------------------------
    def test_list_skill_packs_empty():
        packs = manager.list_skill_packs("/tmp/nonexistent-vault")
        assert packs == {}

    check("manager.list_skill_packs returns empty for missing dir",
          test_list_skill_packs_empty)

    # --- questions tests --------------------------------------------------
    def test_generate_questions():
        pack = {
            "topic": {
                "photosynthesis": {
                    "summary": "Process by which plants convert light to energy",
                    "questions": [
                        {
                            "question": "What is the role of chlorophyll?",
                            "type": "short_answer",
                            "answer": "Absorbs light energy",
                            "hint": "Green pigment in leaves",
                        }
                    ],
                }
            }
        }
        qs = questions.generate_questions(
            pack, "photosynthesis", difficulty="easy", count=2, dry_run=True
        )
        assert len(qs) == 2
        assert qs[0]["topic"] == "photosynthesis"
        assert qs[0]["difficulty"] == "easy"

    check("questions.generate_questions creates questions",
          test_generate_questions)

    # --- self_eval tests --------------------------------------------------
    def test_self_question():
        result = self_eval.self_question(
            "This is a good answer because it explains the concept clearly.",
            dry_run=True,
        )
        assert "score" in result
        assert "issues" in result
        assert "suggestions" in result
        assert "should_revise" in result
        assert 0.0 <= result["score"] <= 1.0

    check("self_eval.self_question evaluates answers", test_self_question)

    def test_self_question_short():
        result = self_eval.self_question("hi", dry_run=True)
        assert result["should_revise"] is True
        assert result["score"] < 0.7

    check("self_eval.self_question flags short answers",
          test_self_question_short)

    # --- model_router tests -----------------------------------------------
    def test_route_model():
        r = model_router.route_model(0.9, "complex_reasoning", dry_run=True)
        assert r["tier"] == "smarter"
        assert r["model"] == "claude-opus-4"

        r2 = model_router.route_model(0.3, "simple_fact", dry_run=True)
        assert r2["tier"] == "cheaper"
        assert r2["model"] == "claude-haiku-3.5"

    check("model_router.route_model selects appropriate model",
          test_route_model)

    # --- knowledge_graph tests --------------------------------------------
    def test_kg_add_proposition_dry_run():
        rec = kg.add_proposition(
            "Plants convert light to energy",
            session_id="s1",
            confidence=0.9,
            dry_run=True,
        )
        assert rec["type"] == "proposition"
        assert rec["content"] == "Plants convert light to energy"
        assert rec["confidence"] == 0.9
        assert "id" in rec

    check("knowledge_graph.add_proposition dry_run returns record",
          test_kg_add_proposition_dry_run)

    # --- dependency_tree tests --------------------------------------------
    def test_dt_build():
        tree = dt.build_dependency_tree(
            "understand quantum entanglement",
            ["basic physics"],
            dry_run=True,
        )
        assert tree["goal"] == "understand quantum entanglement"
        assert tree["dag_valid"] is True
        assert "mermaid" in tree

    check("dependency_tree.build_dependency_tree builds tree",
          test_dt_build)

    # --- adaptive_practice tests ------------------------------------------
    def test_ap_generate():
        problems = ap.generate_practice_problems(
            "photosynthesis",
            difficulty="medium",
            count=2,
            dry_run=True,
        )
        assert len(problems) == 2
        assert problems[0]["topic"] == "photosynthesis"

    check("adaptive_practice.generate_practice_problems generates",
          test_ap_generate)

    def test_ap_adapt_difficulty():
        assert ap.adapt_difficulty("medium", 0.9) == "hard"
        assert ap.adapt_difficulty("medium", 0.3) == "easy"
        assert ap.adapt_difficulty("medium", 0.6) == "medium"

    check("adaptive_practice.adapt_difficulty adjusts",
          test_ap_adapt_difficulty)

    # --- thinking_fields tests --------------------------------------------
    def test_tf_capture_dry_run():
        rec = tf.capture_thinking_field(
            "q1",
            "The answer is X",
            "Because Y implies Z",
            confidence=0.8,
            dry_run=True,
        )
        assert rec["type"] == "thinking_field"
        assert rec["question_id"] == "q1"
        assert rec["confidence"] == 0.8

    check("thinking_fields.capture_thinking_field dry_run",
          test_tf_capture_dry_run)

    def test_tf_detect_boundary():
        fields = [
            {
                "question_id": "q1",
                "answer": "A",
                "reasoning": "Short",
                "confidence": 0.3,
            },
            {
                "question_id": "q2",
                "answer": "B",
                "reasoning": "Because A therefore B",
                "confidence": 0.9,
            },
        ]
        result = tf.detect_understanding_boundary(fields)
        assert "boundary_indicators" in result
        assert "low_confidence_questions" in result
        assert "weak_reasoning_questions" in result
        assert "q1" in result["low_confidence_questions"]

    check("thinking_fields.detect_understanding_boundary analyzes",
          test_tf_detect_boundary)

    # --- report tests -----------------------------------------------------
    def test_report_generation():
        r = report.generate_report(
            "/tmp/test-vault",
            {},
            {},
            [],
            [],
        )
        assert "Education Skill Pack Report" in r

    check("report.generate_report produces valid markdown",
          test_report_generation)

    print("=" * 50)
    print(f"🎉 Self-tests: {passed} passed, {failed} failed")
    return failed == 0


def main():
    args = parse_args()

    if args.test:
        ok = run_self_test()
        sys.exit(0 if ok else 1)

    if not args.vault:
        args.vault = os.environ.get("HERMES_VAULT_PATH")
    if not args.vault:
        print(
            "Error: --vault <path> or HERMES_VAULT_PATH is required.",
            file=sys.stderr,
        )
        sys.exit(1)

    # Deferred path resolution — called from main(), never at import time
    manager.init_paths(args.vault)
    kg.init_paths(args.vault)
    dt.init_paths(args.vault)
    ap.init_paths(args.vault)
    tf.init_paths(args.vault)

    dry_run = not args.apply

    # Collect outputs for report
    packs = manager.list_skill_packs(args.vault)
    questions_by_topic: dict[str, list[dict]] = {}
    self_evals: list[dict] = []
    model_routes: list[dict] = []
    propositions: list[dict] | None = None
    dependency_trees: list[dict] | None = None
    practice_problems: list[dict] | None = None
    thinking_fields_list: list[dict] | None = None

    # --- Core operations --------------------------------------------------
    generated_questions = questions.generate_questions(
        packs, args.topic, args.difficulty, args.count, dry_run=dry_run
    )
    questions_by_topic[args.topic] = generated_questions

    if args.self_eval and args.answer:
        eval_result = self_eval.self_question(args.answer, dry_run=dry_run)
        self_evals.append(eval_result)

    route = model_router.route_model(
        args.complexity, args.topic, dry_run=dry_run
    )
    model_routes = [
        {"task": args.topic, "complexity": args.complexity, **route}
    ]

    # --- Knowledge graph operations ---------------------------------------
    if args.kg_add_proposition:
        rec = kg.add_proposition(
            args.kg_add_proposition,
            dry_run=dry_run,
        )
        print(f"📝 Proposition added: {rec['id']}")
        if not dry_run:
            propositions = kg.list_propositions(args.vault)
        else:
            propositions = [rec]
    elif args.kg_list:
        propositions = kg.list_propositions(args.vault)

    if args.kg_add_chain:
        premises = [p.strip() for p in args.kg_add_chain.split(",")]
        conclusion = args.kg_chain_conclusion or "derived conclusion"
        rec = kg.add_reasoning_chain(
            premises, conclusion, dry_run=dry_run
        )
        print(f"🔗 Reasoning chain added: {rec['id']}")

    # --- Dependency tree operations ---------------------------------------
    if args.dt_build:
        understanding = [
            c.strip() for c in (args.dt_understanding or "").split(",")
            if c.strip()
        ]
        tree = dt.build_dependency_tree(
            args.dt_build, understanding, dry_run=dry_run
        )
        print(f"🌳 Dependency tree built: {tree['goal']}")
        print(tree["mermaid"])
        if not dry_run:
            dependency_trees = dt.list_dependency_trees(args.vault)
        else:
            dependency_trees = [tree]
    elif args.dt_list:
        dependency_trees = dt.list_dependency_trees(args.vault)

    # --- Adaptive practice operations -------------------------------------
    if args.practice_gen:
        weaknesses = [
            w.strip() for w in (args.practice_weaknesses or "").split(",")
            if w.strip()
        ]
        practice_problems = ap.generate_practice_problems(
            args.topic,
            difficulty=args.difficulty,
            count=args.count,
            thinking_field_weaknesses=weaknesses,
            dry_run=dry_run,
        )
        print(f"📝 {len(practice_problems)} practice problems generated")
        for p in practice_problems:
            print(f"  P{p['id']} ({p['difficulty']}): {p['problem']}")

    # --- Thinking fields operations ---------------------------------------
    if args.tf_capture:
        rec = tf.capture_thinking_field(
            args.tf_capture,
            args.tf_answer,
            args.tf_reasoning,
            confidence=args.tf_confidence,
            dry_run=dry_run,
        )
        print(f"💭 Thinking field captured: {rec['id']}")
        if not dry_run:
            thinking_fields_list = tf.list_thinking_fields(args.vault)
        else:
            thinking_fields_list = [rec]
    elif args.tf_list:
        thinking_fields_list = tf.list_thinking_fields(args.vault)

    if args.tf_boundary and thinking_fields_list is not None:
        boundary = tf.detect_understanding_boundary(thinking_fields_list)
        print("🔍 Understanding boundary analysis:")
        for ind in boundary["boundary_indicators"]:
            print(f"  - {ind}")
        print(f"  Summary: {boundary['summary']}")

    # --- Generate report --------------------------------------------------
    report_md = report.generate_report(
        args.vault,
        packs,
        questions_by_topic,
        self_evals,
        model_routes,
        propositions=propositions,
        dependency_trees=dependency_trees,
        practice_problems=practice_problems,
        thinking_fields=thinking_fields_list,
    )
    report_path = os.path.join(
        args.vault, "04-Archives", "Audit-Reports",
        "Skill-Pack-Education-Report.md",
    )
    os.makedirs(os.path.dirname(report_path), exist_ok=True)
    with open(report_path, "w", encoding="utf-8") as f:
        f.write(report_md)

    # --- Print summary ----------------------------------------------------
    print(f"\n📚 Skill Pack for Education — {args.topic}")
    print(f"   Vault: {args.vault}")
    print(f"   Skill packs found: {len(packs)}")
    print(f"   Questions generated: {len(generated_questions)}")
    if self_evals:
        print(
            f"   Self-eval score: {self_evals[0]['score']:.2f} — "
            f"{'REVISE' if self_evals[0]['should_revise'] else 'OK'}"
        )
    print(f"   Model route: {model_routes[0]['model']} ({model_routes[0]['tier']})")
    print(f"   Mode: {'DRY-RUN' if dry_run else 'APPLY'}")
    print(f"   Report: {report_path}")
    if dry_run:
        print("   Run with --apply to write changes to vault.")

    print("")
    for q in generated_questions:
        print(f"  Q{q['id']} ({q['difficulty']}): {q['question']}")
        print(f"    Hint: {q['hint']}")

    return 0


if __name__ == "__main__":
    sys.exit(main())
