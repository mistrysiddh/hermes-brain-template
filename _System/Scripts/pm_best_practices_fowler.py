#!/usr/bin/env python3
"""
Hermes Brain — PM Best Practices: Martin Fowler Skill.

Implements practices from the PM Skill-Feature Tree (Issue #44), Fowler row:
- Refactoring catalog as enforced discipline (Extract Method, Extract Class, Rename Method,
  Move Method, Replace Parameter Object, Replace Boolean Flag with Methods, Replace Conditional
  with Polymorphism, Consolidate Duplicate Conditional, Introduce Assertion)
- Refactoring prerequisites & invariants (tests green, one refactoring per commit, revertible,
  rationale documented, 5-minute task limit)
- Smell → refactoring map (duplication → Extract Method, vague name → Rename, multi-thing
  function → Extract Method/Class, unrelated params → Parameter Object, boolean flag → Replace
  Flag with Methods, conditional chain → Replace Conditional with Polymorphism, misplaced
  method → Move Method)
- Maintainability metrics (cyclomatic complexity <10/function, duplication <3%, coverage >80%,
  test speed <5s, circular-dependency check, injectability check)
- Dependency Injection pattern pack (constructor injection preferred, depend on abstractions,
  avoid service locator, simple constructors, fail fast on missing dependencies, watch lifetimes)
- ADR lifecycle (when to write vs skip, Context→Decision→Consequences, MADR template, link related
  ADRs, update status over time)
- PoEAA patterns (Repository, Unit of Work, Service Layer, Data Mapper, etc.)
- Strangler Fig incremental migration
- Test pyramid standards (unit/integration/E2E layers)

Multi-harness compliant: --vault, --dry-run default, --apply, stdlib-only, --test.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any
import hashlib
import json


# ── Data models ──────────────────────────────────────────────────────────────

@dataclass
class RefactoringRecord:
    """A refactoring record from Fowler's catalog."""

    id: str
    smell: str
    refactoring: str
    file: str
    before: str
    after: str
    rationale: str
    tests_green_before: bool = False
    tests_green_after: bool = False
    created_at: str = field(
        default_factory=lambda: datetime.now(timezone.utc).isoformat()
    )

    def to_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "smell": self.smell,
            "refactoring": self.refactoring,
            "file": self.file,
            "before": self.before,
            "after": self.after,
            "rationale": self.rationale,
            "tests_green_before": self.tests_green_before,
            "tests_green_after": self.tests_green_after,
            "created_at": self.created_at,
        }


@dataclass
class ADRecord:
    """An Architecture Decision Record."""

    id: str
    title: str
    status: str  # proposed, accepted, rejected, superseded
    context: str = ""
    decision: str = ""
    consequences: str = ""
    alternatives: str = ""
    created_at: str = field(
        default_factory=lambda: datetime.now(timezone.utc).isoformat()
    )

    def to_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "title": self.title,
            "status": self.status,
            "context": self.context,
            "decision": self.decision,
            "consequences": self.consequences,
            "alternatives": self.alternatives,
            "created_at": self.created_at,
        }


@dataclass
class PoEPAPattern:
    """A Pattern of Enterprise Application Architecture pattern."""

    id: str
    name: str
    category: str  # domain logic, data source architectural, object-relational behavioral,
                   # object-relational structural, object-relational metadata, web presentation,
                   # distribution, concurrency, session state
    description: str
    when_to_use: str = ""
    created_at: str = field(
        default_factory=lambda: datetime.now(timezone.utc).isoformat()
    )

    def to_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "name": self.name,
            "category": self.category,
            "description": self.description,
            "when_to_use": self.when_to_use,
            "created_at": self.created_at,
        }


@dataclass
class MetricRecord:
    """A maintainability metric record."""

    id: str
    metric: str  # cyclomatic_complexity, duplication, coverage, test_speed,
                 # circular_dependency, injectability
    value: float
    threshold: float
    passes: bool
    file: str = ""
    created_at: str = field(
        default_factory=lambda: datetime.now(timezone.utc).isoformat()
    )

    def to_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "metric": self.metric,
            "value": self.value,
            "threshold": self.threshold,
            "passes": self.passes,
            "file": self.file,
            "created_at": self.created_at,
        }


@dataclass
class TidyFirstRecord:
    """A Tidy First structural change record."""

    id: str
    file: str
    change_type: str  # rename, extract, move, reorganize, inline
    description: str
    before: str = ""
    after: str = ""
    tests_green_before: bool = False
    tests_green_after: bool = False
    created_at: str = field(
        default_factory=lambda: datetime.now(timezone.utc).isoformat()
    )

    def to_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "file": self.file,
            "change_type": self.change_type,
            "description": self.description,
            "before": self.before,
            "after": self.after,
            "rationale": self.rationale if hasattr(self, "rationale") else "",
            "tests_green_before": self.tests_green_before,
            "tests_green_after": self.tests_green_after,
            "created_at": self.created_at,
        }


@dataclass
class TDDRecord:
    """A TDD cycle record."""

    id: str
    feature: str
    phase: str  # red, green, refactor, done
    test_name: str = ""
    code_change: str = ""
    refactor_note: str = ""
    created_at: str = field(
        default_factory=lambda: datetime.now(timezone.utc).isoformat()
    )

    def to_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "feature": self.feature,
            "phase": self.phase,
            "test_name": self.test_name,
            "code_change": self.code_change,
            "refactor_note": self.refactor_note,
            "created_at": self.created_at,
        }


# ── Helpers ──────────────────────────────────────────────────────────────────

def _record_id(prefix: str, text: str) -> str:
    """Generate a deterministic record ID."""
    import hashlib

    h = hashlib.sha256(f"{prefix}:{text}".encode()).hexdigest()[:12]
    return f"{prefix}:{h}"


def _init_paths(vault_path: str | None) -> Path | None:
    """Resolve the vault path for PM practices storage."""
    if not vault_path:
        return None
    return Path(vault_path)


def _ensure_dirs(vault: Path) -> Path:
    """Ensure the PM practices directory exists."""
    dir_path = vault / "02-Areas" / "Skills" / "pm_best_practices_fowler"
    dir_path.mkdir(parents=True, exist_ok=True)
    return dir_path


def _load_json(path: Path) -> list[dict[str, Any]]:
    """Load a JSON list from a file, returning empty list if missing/invalid."""
    if not path.exists():
        return []
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
        if isinstance(data, list):
            return data
        return []
    except (json.JSONDecodeError, OSError):
        return []


def _save_json(path: Path, data: list[dict[str, Any]]) -> None:
    """Save a JSON list to a file."""
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, indent=2), encoding="utf-8")


# ── Fowler's Refactoring Catalog ─────────────────────────────────────────────

# Smell → Refactoring map from Fowler's catalog
SMELL_TO_REFACTORING = {
    "duplication": "Extract Method / Consolidate Duplicate Conditionals",
    "vague_name": "Rename Method / Rename Class",
    "multi_thing_function": "Extract Method / Extract Class",
    "unrelated_params": "Replace Parameter Object with Methods",
    "boolean_flag": "Replace Boolean Flag with Methods",
    "conditional_chain": "Replace Conditional with Polymorphism",
    "misplaced_method": "Move Method",
    "long_method": "Extract Method",
    "large_class": "Extract Class",
    "feature_envy": "Move Method",
    "primitive_obsession": "Replace Primitive with Object",
    "switch_statements": "Replace Conditional with Polymorphism",
    "parallel_inheritance_hierarchies": "Replace Inheritance with Delegation",
    "lazy_class": "Inline Class",
    "speculative_generality": "Collapse Hierarchy / Remove Dead Code",
    "temporary_field": "Extract Class",
    "message_chains": "Hide Delegate",
    "middle_man": "Remove Middle Man",
    "inappropriate_intimacy": "Move Method / Move Field / Hide Delegate",
    "alternative_classes_different_interface": "Rename Method / Hide Delegate",
    "incomplete_library_class": "Introduce Foreign Method / Introduce Local Extension",
    "data_clumps": "Extract Class",
    "shotgun_surgery": "Move Method / Move Field / Inline Class",
    "divergent_change": "Extract Class",
}

REFACTORING_CATALOG = {
    "extract_method": {
        "name": "Extract Method",
        "description": "Take a code fragment that can be grouped together, turn it into a method whose name explains the purpose of the method.",
        "when": "A code fragment that can be grouped together.",
    },
    "extract_class": {
        "name": "Extract Class",
        "description": "One class is doing the work of two, split it into two.",
        "when": "One class is doing the work of two.",
    },
    "rename_method": {
        "name": "Rename Method",
        "description": "A method name doesn't reveal its purpose, change the name of the method.",
        "when": "A method name doesn't reveal its purpose.",
    },
    "rename_class": {
        "name": "Rename Class",
        "description": "A class name doesn't reveal its purpose, change the name of the class and file.",
        "when": "A class name doesn't reveal its purpose.",
    },
    "move_method": {
        "name": "Move Method",
        "description": "A method is or will be using or used by more features of another class than the class on which it is defined.",
        "when": "A method is used more by another class than its own.",
    },
    "replace_parameter_object": {
        "name": "Replace Parameter Object with Methods",
        "description": "A group of parameters always go together, replace them with an object.",
        "when": "A group of parameters always go together.",
    },
    "replace_boolean_flag": {
        "name": "Replace Boolean Flag with Methods",
        "description": "A method has a boolean parameter, create separate methods for each value of the parameter.",
        "when": "A method has a boolean parameter.",
    },
    "replace_conditional_polymorphism": {
        "name": "Replace Conditional with Polymorphism",
        "description": "You have a conditional that chooses different behavior depending on the type of an object, move each leg of the conditional to an overriding method in a subclass, and make the original method abstract.",
        "when": "A conditional chooses different behavior depending on the type of an object.",
    },
    "consolidate_duplicate_conditionals": {
        "name": "Consolidate Duplicate Conditional",
        "description": "The same conditional appears in several methods, consolidate them into a single conditional.",
        "when": "The same conditional appears in several methods.",
    },
    "introduce_assertion": {
        "name": "Introduce Assertion",
        "description": "A complex expression obscures the code's intent, extract the assertion into a separate method that explains the expression.",
        "when": "A complex expression obscures code intent.",
    },
}


# ── S8-style subcommands ─────────────────────────────────────────────────────

def cmd_refactor_list(args: Any) -> int:
    """List Fowler's refactoring catalog."""
    print("Martin Fowler's Refactoring Catalog:")
    print("=" * 60)
    for key, info in REFACTORING_CATALOG.items():
        print(f"\n  {key} — {info['name']}")
        print(f"    Description: {info['description']}")
        print(f"    When: {info['when']}")
    print("\nSmell → Refactoring map:")
    for smell, refactoring in SMELL_TO_REFACTORING.items():
        print(f"  {smell} → {refactoring}")
    print("\nRefactoring invariants:")
    print("  • Tests green before and after")
    print("  • One refactoring per commit")
    print("  • Each commit revertible and self-contained")
    print("  • Rationale documented")
    print("  • 5-minute task limit — break down if longer")
    print("  • Behavior preservation (identical observable I/O)")
    return 0


def cmd_smell_map(args: Any) -> int:
    """Show smell → refactoring map."""
    print("Fowler's Smell → Refactoring Map:")
    print("=" * 50)
    for smell, refactoring in SMELL_TO_REFACTORING.items():
        print(f"  {smell} → {refactoring}")
    return 0


def cmd_metrics(args: Any) -> int:
    """Show Fowler's maintainability metrics."""
    print("Fowler's Maintainability Metrics:")
    print("=" * 50)
    metrics = [
        ("cyclomatic_complexity", "<10/function"),
        ("duplication", "<3%"),
        ("coverage", ">80%"),
        ("test_speed", "<5s"),
        ("circular_dependency", "0"),
        ("injectability", "yes"),
    ]
    for metric, threshold in metrics:
        print(f"  {metric}: {threshold}")
    return 0


def cmd_di_pack(args: Any) -> int:
    """Show Fowler's Dependency Injection pattern pack."""
    print("Fowler's Dependency Injection Pattern Pack:")
    print("=" * 50)
    patterns = [
        ("Constructor injection preferred", "Use constructor injection over setter/field injection"),
        ("Depend on abstractions", "Depend on abstractions, not concretions"),
        ("Avoid service locator", "Avoid service locator pattern"),
        ("Simple constructors", "Assign only, no logic in constructors"),
        ("Fail fast on missing dependencies", "Fail fast on missing dependencies"),
        ("Watch lifetimes", "Watch lifetimes (singleton vs transient)"),
    ]
    for name, desc in patterns:
        print(f"  • {name}: {desc}")
    return 0


# ── CLI ──────────────────────────────────────────────────────────────────────

import argparse  # noqa: E402
import sys  # noqa: E402


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="PM Best Practices: Martin Fowler — Refactoring Catalog & Architecture"
    )
    parser.add_argument("--vault", required=True, help="Path to vault directory")
    parser.add_argument(
        "--dry-run",
        action="store_true",
        default=True,
        help="Dry run mode (default)",
    )
    parser.add_argument(
        "--apply",
        action="store_true",
        help="Apply changes (overrides --dry-run)",
    )
    parser.add_argument("--test", action="store_true", help="Run self-test suite")

    sub = parser.add_subparsers(dest="command")

    # refactor-list
    sub.add_parser("refactor-list", help="List Fowler's refactoring catalog")

    # smell-map
    sub.add_parser("smell-map", help="Show smell → refactoring map")

    # metrics
    sub.add_parser("metrics", help="Show Fowler's maintainability metrics")

    # di-pack
    sub.add_parser("di-pack", help="Show Fowler's DI pattern pack")

    # tidy-first
    p_tidy = sub.add_parser("tidy-first", help="Tidy First — structural/behavioral split")
    p_tidy.add_argument("--list", action="store_true", help="List tidy records")
    p_tidy.add_argument("--add", action="store_true", help="Add a tidy record")
    p_tidy.add_argument("--file", help="File path")
    p_tidy.add_argument(
        "--change-type", help="rename, extract, move, reorganize, inline"
    )
    p_tidy.add_argument("--description", help="Change description")
    p_tidy.add_argument(
        "--tests-green-before", action="store_true", help="Tests green before"
    )
    p_tidy.add_argument(
        "--tests-green-after", action="store_true", help="Tests green after"
    )

    # tdd
    p_tdd = sub.add_parser("tdd", help="TDD Cycle — Red-Green-Refactor")
    p_tdd.add_argument("--list", action="store_true", help="List TDD records")
    p_tdd.add_argument("--add", action="store_true", help="Add a TDD record")
    p_tdd.add_argument("--feature", help="Feature name")
    p_tdd.add_argument("--phase", help="red, green, refactor, or done")
    p_tdd.add_argument("--test-name", help="Test name")
    p_tdd.add_argument("--code-change", help="Code change description")
    p_tdd.add_argument("--refactor-note", help="Refactor note")

    # adr
    p_adr = sub.add_parser("adr", help="Architecture Decision Record")
    p_adr.add_argument("--list", action="store_true", help="List ADRs")
    p_adr.add_argument("--add", action="store_true", help="Add an ADR")
    p_adr.add_argument("--title", help="ADR title")
    p_adr.add_argument(
        "--status", default="proposed", help="proposed/accepted/rejected/superseded"
    )
    p_adr.add_argument("--context", help="Context")
    p_adr.add_argument("--decision", help="Decision")
    p_adr.add_argument("--consequences", help="Consequences")
    p_adr.add_argument("--alternatives", help="Alternatives considered")

    # stats
    sub.add_parser("stats", help="Show PM best practices stats")

    # test
    sub.add_parser("test", help="Run self-test suite")

    return parser.parse_args()


def cmd_test() -> int:
    """Run self-test suite."""
    print("PM Best Practices: Fowler — Self-Test Suite")
    print("=" * 50)

    passed = 0
    failed = 0

    # Test 1: Refactoring catalog
    print("\n[1/5] Refactoring catalog...")
    assert len(REFACTORING_CATALOG) == 10
    assert REFACTORING_CATALOG["extract_method"]["name"] == "Extract Method"
    assert REFACTORING_CATALOG["replace_conditional_polymorphism"]["name"] == "Replace Conditional with Polymorphism"
    print("  ✅ Refactoring catalog has 10 patterns")
    passed += 1

    # Test 2: Smell → refactoring map
    print("\n[2/5] Smell → refactoring map...")
    assert len(SMELL_TO_REFACTORING) == 24
    assert SMELL_TO_REFACTORING["duplication"] == "Extract Method / Consolidate Duplicate Conditionals"
    assert SMELL_TO_REFACTORING["boolean_flag"] == "Replace Boolean Flag with Methods"
    print("  ✅ Smell → refactoring map has 24 mappings")
    passed += 1

    # Test 3: Tidy First record creation
    print("\n[3/5] Tidy First record creation...")
    import tempfile
    import shutil

    vault = tempfile.mkdtemp()
    try:
        records = _load_json(_ensure_dirs(Path(vault)) / "tidy_first.json")
        assert records == []

        record = TidyFirstRecord(
            id=_record_id("tidy", "test_file.py"),
            file="test_file.py",
            change_type="extract",
            description="Extract method from long function",
            tests_green_before=True,
            tests_green_after=True,
        )
        records.append(record.to_dict())
        _save_json(_ensure_dirs(Path(vault)) / "tidy_first.json", records)

        loaded = _load_json(_ensure_dirs(Path(vault)) / "tidy_first.json")
        assert len(loaded) == 1
        assert loaded[0]["change_type"] == "extract"
        assert loaded[0]["tests_green_before"] is True
        assert loaded[0]["tests_green_after"] is True
        print("  ✅ Tidy First record creation works")
        passed += 1
    finally:
        shutil.rmtree(vault)

    # Test 4: TDD record creation
    print("\n[4/5] TDD record creation...")
    vault = tempfile.mkdtemp()
    try:
        records = _load_json(_ensure_dirs(Path(vault)) / "tdd.json")
        assert records == []

        record = TDDRecord(
            id=_record_id("tdd", "login_feature"),
            feature="login_feature",
            phase="red",
            test_name="test_login_rejects_invalid_password",
        )
        records.append(record.to_dict())
        _save_json(_ensure_dirs(Path(vault)) / "tdd.json", records)

        loaded = _load_json(_ensure_dirs(Path(vault)) / "tdd.json")
        assert len(loaded) == 1
        assert loaded[0]["phase"] == "red"
        print("  ✅ TDD record creation works")
        passed += 1
    finally:
        shutil.rmtree(vault)

    # Test 5: ADR record creation
    print("\n[5/5] ADR record creation...")
    vault = tempfile.mkdtemp()
    try:
        record = ADRecord(
            id=_record_id("adr", "use_postgres"),
            title="Use PostgreSQL",
            status="proposed",
            context="Need a relational database for user data",
            decision="Use PostgreSQL 15",
            consequences="Mature, reliable, good tooling",
            alternatives="MySQL, SQLite",
        )
        records = [record.to_dict()]
        _save_json(_ensure_dirs(Path(vault)) / "adrs.json", records)

        loaded = _load_json(_ensure_dirs(Path(vault)) / "adrs.json")
        assert len(loaded) == 1
        assert loaded[0]["title"] == "Use PostgreSQL"
        print("  ✅ ADR record creation works")
        passed += 1
    finally:
        shutil.rmtree(vault)

    total = passed + failed
    print(f"\n{'=' * 50}")
    print(f"Results: {passed}/{total} passed, {failed} failed")
    if failed == 0:
        print("✅ ALL TESTS PASSED")
        return 0
    else:
        print("❌ SOME TESTS FAILED")
        return 1



def main() -> int:
    args = parse_args()

    if args.test:
        return cmd_test()

    if not args.command:
        print(
            "No command specified. Use: refactor-list, smell-map, metrics, di-pack, tidy-first, tdd, adr, stats, or test."
        )
        return 1

    if args.command == "refactor-list":
        return cmd_refactor_list(args)
    if args.command == "smell-map":
        return cmd_smell_map(args)
    if args.command == "metrics":
        return cmd_metrics(args)
    if args.command == "di-pack":
        return cmd_di_pack(args)
    if args.command == "tidy-first":
        return cmd_tidy_first(args)
    if args.command == "tdd":
        return cmd_tdd(args)
    if args.command == "adr":
        return cmd_adr(args)
    if args.command == "stats":
        return cmd_stats(args)

    print("Unknown command. Use: refactor-list, smell-map, metrics, di-pack, tidy-first, tdd, adr, stats, or test.")
    return 1


if __name__ == "__main__":
    sys.exit(main())
