"""Hermes Brain — Skill Pack for Education (multi-harness compatible).

DIY skill packs where the second brain can question users (tutor/Socratic mode),
self-question (evaluate its own reasoning/answers), route tasks between smarter
and cheaper models based on task complexity, and maintain a persistent knowledge
graph of propositions and reasoning chains.

Sub-modules:
- manager: Skill pack loading/listing
- questions: Question generation (tutor mode)
- self_eval: Self-questioning/evaluation
- model_router: Model routing by complexity
- knowledge_graph: Knowledge graph persistence (propositions, reasoning chains)
- dependency_tree: Dependency tree/lesson map
- adaptive_practice: Adaptive practice problems
- thinking_fields: Free-text reasoning capture
- report: Report generation
- cli: CLI entry point

Multi-harness compliant:
  - --vault CLI arg, deferred path resolution via init_paths()
  - --dry-run default / --apply for human-in-the-loop approval
  - stdlib-only
  - --test built-in self-test suite
"""

from .manager import init_paths, list_skill_packs, skill_pack_dir
from .questions import generate_questions
from .self_eval import self_question
from .model_router import route_model
from .report import generate_report
from .cli import main, parse_args, run_self_test

__all__ = [
    "manager",
    "questions",
    "self_eval",
    "model_router",
    "knowledge_graph",
    "dependency_tree",
    "adaptive_practice",
    "thinking_fields",
    "report",
    "cli",
    "init_paths",
    "list_skill_packs",
    "skill_pack_dir",
    "generate_questions",
    "self_question",
    "route_model",
    "generate_report",
    "main",
    "parse_args",
    "run_self_test",
]
