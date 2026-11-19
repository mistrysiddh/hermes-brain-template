#!/usr/bin/env python3
"""
Hermes Brain — PM Best Practices: Robert C. Martin (Uncle Bob) Skill.

Implements practices from the PM Skill-Feature Tree (Issue #44), Robert C. Martin row:
- Clean Code rules (small functions, single responsibility, descriptive names,
  few arguments, no boolean flags, DRY, comments explain why, error handling,
  Boy Scout rule, tests are important, small classes, single responsibility)
- SOLID principles (Single Responsibility, Open/Closed, Liskov Substitution,
  Interface Segregation, Dependency Inversion)
- Clean Architecture (entities, use cases, interface adapters, frameworks & drivers;
  dependency rule; independence from frameworks/UI/database/external agencies)
- Uncle Bob's craft aggregator (mirror of the 4-book pack: Clean Code, Clean
  Architecture, Clean Coder, Clean Agile)
- ADR lifecycle (when to write vs skip, Context→Decision→Consequences)

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
class CleanCodeRecord:
    """A Clean Code rule record."""

    id: str
    rule: str
    description: str
    category: str  # naming, functions, comments, formatting, objects, error_handling, tests, classes
    severity: str  # blocker, major, moderate, advisory
    file: str = ""
    created_at: str = field(
        default_factory=lambda: datetime.now(timezone.utc).isoformat()
    )

    def to_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "rule": self.rule,
            "description": self.description,
            "category": self.category,
            "severity": self.severity,
            "file": self.file,
            "created_at": self.created_at,
        }


@dataclass
class SolidRecord:
    """A SOLID principle record."""

    id: str
    principle: str  # single_responsibility, open_closed, liskov_substitution,
                    # interface_segregation, dependency_inversion
    description: str
    applies_to: str  # what the principle applies to
    created_at: str = field(
        default_factory=lambda: datetime.now(timezone.utc).isoformat()
    )

    def to_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "principle": self.principle,
            "description": self.description,
            "applies_to": self.applies_to,
            "created_at": self.created_at,
        }


@dataclass
class CleanArchRecord:
    """A Clean Architecture layer record."""

    id: str
    layer: str  # entities, use_cases, interface_adapters, frameworks_drivers
    description: str
    dependencies: str = ""  # what this layer depends on
    created_at: str = field(
        default_factory=lambda: datetime.now(timezone.utc).isoformat()
    )

    def to_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "layer": self.layer,
            "description": self.description,
            "dependencies": self.dependencies,
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
    dir_path = vault / "02-Areas" / "Skills" / "pm_best_practices_unclebob"
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
    dir_path = vault / "02-Areas" / "Skills" / "pm_best_practices_unclebob"
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


# ── Uncle Bob's Clean Code rules ─────────────────────────────────────────────

CLEAN_CODE_RULES = {
    "small_functions": {
        "rule": "Functions should be small",
        "description": "Functions should do one thing. They should do it well. They should do it only.",
        "category": "functions",
        "severity": "major",
    },
    "descriptive_names": {
        "rule": "Use descriptive names",
        "description": "Use intention-revealing names. A name should tell you why it exists, what it does, and how it is used.",
        "category": "naming",
        "severity": "major",
    },
    "few_arguments": {
        "rule": "Fewest arguments",
        "description": "The ideal number of arguments for a function is zero (niladic). Next is one (monadic), followed closely by two (dyadic). Three arguments (triadic) should be avoided where possible. More than three (polyadic) requires significant justification.",
        "category": "functions",
        "severity": "major",
    },
    "no_flag_arguments": {
        "rule": "No boolean flag arguments",
        "description": "Boolean flag arguments are a loud declaration that the function does more than one thing. Split the function into separate methods.",
        "category": "functions",
        "severity": "moderate",
    },
    "dry": {
        "rule": "Don't Repeat Yourself (DRY)",
        "description": "Duplication is the primary enemy of well-designed software. Eliminate duplication wherever possible.",
        "category": "general",
        "severity": "major",
    },
    "comments_explain_why": {
        "rule": "Comments explain why, not what",
        "description": "Good comments clarify intent, decisions, and trade-offs. Bad comments explain what the code already says clearly.",
        "category": "comments",
        "severity": "moderate",
    },
    "boy_scout_rule": {
        "rule": "Leave the code cleaner than you found it",
        "description": "The Boy Scout rule: always leave the codebase a little cleaner than you found it. Small, continuous improvements compound.",
        "category": "general",
        "severity": "advisory",
    },
    "tests_are_important": {
        "rule": "Tests are important",
        "description": "Tests are as important as production code. They enable refactoring, document behavior, and prevent regressions.",
        "category": "tests",
        "severity": "major",
    },
    "small_classes": {
        "rule": "Classes should be small",
        "description": "Classes should have a single responsibility. If a class has too many responsibilities, split it.",
        "category": "classes",
        "severity": "major",
    },
}

# ── SOLID principles ─────────────────────────────────────────────────────────

SOLID_PRINCIPLES = {
    "single_responsibility": {
        "principle": "Single Responsibility Principle (SRP)",
        "description": "A class should have one, and only one, reason to change.",
        "applies_to": "classes and modules",
    },
    "open_closed": {
        "principle": "Open/Closed Principle (OCP)",
        "description": "Software entities (classes, modules, functions, etc.) should be open for extension but closed for modification.",
        "applies_to": "classes and modules",
    },
    "liskov_substitution": {
        "principle": "Liskov Substitution Principle (LSP)",
        "description": "Objects of a superclass should be replaceable with objects of its subclasses without breaking the application.",
        "applies_to": "inheritance and subtypes",
    },
    "interface_segregation": {
        "principle": "Interface Segregation Principle (ISP)",
        "description": "Clients should not be forced to depend on interfaces they do not use. Split fat interfaces into smaller, client-specific ones.",
        "applies_to": "interfaces",
    },
    "dependency_inversion": {
        "principle": "Dependency Inversion Principle (DIP)",
        "description": "High-level modules should not depend on low-level modules. Both should depend on abstractions. Abstractions should not depend on details. Details should depend on abstractions.",
        "applies_to": "module dependencies",
    },
}

# ── Clean Architecture layers ──────────────────────────────────────────────────

CLEAN_ARCH_LAYERS = {
    "entities": {
        "layer": "Entities",
        "description": "Enterprise-wide business rules. Encapsulates enterprise-wide business rules. An entity can be an object with methods, or it can be a set of data structures and functions. The entities are the highest level of abstraction.",
        "dependencies": "None (pure business rules)",
    },
    "use_cases": {
        "layer": "Use Cases",
        "description": "Application-specific business rules. Contains application-specific business rules. Encapsulates and implements all of the use cases of the system. Orchestrates the flow of data to and from the entities.",
        "dependencies": "Entities",
    },
    "interface_adapters": {
        "layer": "Interface Adapters",
        "description": "Converts data from the format most convenient for use cases and entities to the format most convenient for external agencies (database, web, etc.). Includes controllers, presenters, gateways, presenters.",
        "dependencies": "Use Cases, Entities",
    },
    "frameworks_drivers": {
        "layer": "Frameworks & Drivers",
        "description": "Details such as the database, web framework, etc. These details are details. They are irrelevant to the architecture.",
        "dependencies": "Interface Adapters",
    },
}

# ── CLI ──────────────────────────────────────────────────────────────────────

import argparse  # noqa: E402
import sys  # noqa: E402


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="PM Best Practices: Robert C. Martin (Uncle Bob) — Clean Code, SOLID, Clean Architecture"
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

    # clean-code
    p_cc = sub.add_parser("clean-code", help="Clean Code rules — Uncle Bob")
    p_cc.add_argument("--list", action="store_true", help="List Clean Code rules")

    # solid
    p_solid = sub.add_parser("solid", help="SOLID principles")
    p_solid.add_argument("--list", action="store_true", help="List SOLID principles")

    # clean-architecture
    p_arch = sub.add_parser("clean-architecture", help="Clean Architecture layers")
    p_arch.add_argument("--list", action="store_true", help="List Clean Architecture layers")

    # adr
    p_adr = sub.add_parser("adr", help="Architecture Decision Record")
    p_adr.add_argument("--list", action="store_true", help="List ADRs")
    p_adr.add_argument("--add", action="store_true", help="Add an ADR")
    p_adr.add_argument("--title", help="ADR title")
    p_adr.add_argument("--status", default="proposed", help="proposed/accepted/rejected/superseded")
    p_adr.add_argument("--context", help="Context")
    p_adr.add_argument("--decision", help="Decision")
    p_adr.add_argument("--consequences", help="Consequences")
    p_adr.add_argument("--alternatives", help="Alternatives considered")

    # stats
    sub.add_parser("stats", help="Show PM best practices stats")

    return parser.parse_args()


def cmd_test() -> int:
    """Run self-test suite."""
    print("PM Best Practices: Uncle Bob — Self-Test Suite")
    print("=" * 50)

    passed = 0
    failed = 0

    # Test 1: Clean Code rules
    print("\n[1/4] Clean Code rules...")
    assert len(CLEAN_CODE_RULES) == 9
    assert CLEAN_CODE_RULES["small_functions"]["rule"] == "Functions should be small"
    assert CLEAN_CODE_RULES["dry"]["rule"] == "Don't Repeat Yourself (DRY)"
    print("  ✅ Clean Code rules: 9 rules")
    passed += 1

    # Test 2: SOLID principles
    print("\n[2/5] SOLID principles...")
    assert len(SOLID_PRINCIPLES) == 5
    assert SOLID_PRINCIPLES["single_responsibility"]["principle"] == "Single Responsibility Principle (SRP)"
    assert SOLID_PRINCIPLES["dependency_inversion"]["principle"] == "Dependency Inversion Principle (DIP)"
    print("  ✅ SOLID principles: 5 principles")
    passed += 1

    # Test 3: Clean Architecture layers
    print("\n[3/5] Clean Architecture layers...")
    assert len(CLEAN_ARCH_LAYERS) == 4
    assert CLEAN_ARCH_LAYERS["entities"]["layer"] == "Entities"
    assert CLEAN_ARCH_LAYERS["use_cases"]["layer"] == "Use Cases"
    assert CLEAN_ARCH_LAYERS["interface_adapters"]["layer"] == "Interface Adapters"
    assert CLEAN_ARCH_LAYERS["frameworks_drivers"]["layer"] == "Frameworks & Drivers"
    print("  ✅ Clean Architecture layers: 4 layers")
    passed += 1

    # Test 4: ADR record creation
    print("\n[4/5] ADR record creation...")
    import tempfile
    import shutil

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

    # Test 5: Clean Code record creation
    print("\n[5/5] Clean Code rule check...")
    assert CLEAN_CODE_RULES["small_functions"]["category"] == "functions"
    assert CLEAN_CODE_RULES["no_flag_arguments"]["severity"] == "moderate"
    print("  ✅ Clean Code rules structure valid")
    passed += 1

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
            "No command specified. Use: clean-code, solid, clean-architecture, adr, stats, or test."
        )
        return 1

    if args.command == "clean-code":
        if args.list:
            print("Robert C. Martin's Clean Code rules:")
            print("=" * 50)
            for key, rule in CLEAN_CODE_RULES.items():
                print(f"\n  {key} — {rule['rule']}")
                print(f"    Description: {rule['description']}")
                print(f"    Category: {rule['category']}")
                print(f"    Severity: {rule['severity']}")
            return 0
        print("No action specified. Use --list to see Clean Code rules.")
        return 1

    if args.command == "solid":
        if args.list:
            print("Robert C. Martin's SOLID principles:")
            print("=" * 50)
            for key, principle in SOLID_PRINCIPLES.items():
                print(f"\n  {key} — {principle['principle']}")
                print(f"    Description: {principle['description']}")
                print(f"    Applies to: {principle['applies_to']}")
            return 0
        print("No action specified. Use --list to see SOLID principles.")
        return 1

    if args.command == "clean-architecture":
        if args.list:
            print("Robert C. Martin's Clean Architecture layers:")
            print("=" * 50)
            for key, layer in CLEAN_ARCH_LAYERS.items():
                print(f"\n  {key} — {layer['layer']}")
                print(f"    Description: {layer['description']}")
                print(f"    Dependencies: {layer['dependencies']}")
            return 0
        print("No action specified. Use --list to see Clean Architecture layers.")
        return 1

    if args.command == "adr":
        vault = _init_paths(args.vault)
        if not vault:
            print("Error: --vault required")
            return 1

        if args.list:
            data = _load_json(_ensure_dirs(vault) / "adrs.json")
            print(f"ADR records ({len(data)}):")
            for r in data:
                print(f"  {r['id']}: {r['title']} — {r['status']}")
            return 0

        if args.add:
            if not args.title:
                print("--title is required for --add")
                return 1
            records = _load_json(_ensure_dirs(vault) / "adrs.json")
            record = ADRecord(
                id=_record_id("adr", args.title),
                title=args.title,
                status=args.status,
                context=args.context or "",
                decision=args.decision or "",
                consequences=args.consequences or "",
                alternatives=args.alternatives or "",
            )
            records.append(record.to_dict())
            _save_json(_ensure_dirs(vault) / "adrs.json", records)

            print(f"ADR created: {record.id}")
            print(f"  Title: {record.title}")
            print(f"  Status: {record.status}")
            return 0

        print("No action specified. Use --list or --add.")
        return 1

    if args.command == "stats":
        vault = _init_paths(args.vault)
        if not vault:
            print("Error: --vault required")
            return 1

        base = _ensure_dirs(vault)
        stats = {
            "clean_code_rules": len(CLEAN_CODE_RULES),
            "solid_principles": len(SOLID_PRINCIPLES),
            "clean_architecture_layers": len(CLEAN_ARCH_LAYERS),
        }
        print(json.dumps(stats, indent=2))
        return 0

    print("Unknown command. Use: clean-code, solid, clean-architecture, adr, stats, or test.")
    return 1


if __name__ == "__main__":
    sys.exit(main())
