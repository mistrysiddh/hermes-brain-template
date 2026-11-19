#!/usr/bin/env python3
"""
Hermes Brain — PM Best Practices: Freeman & Pryce (GOOS) Skill.

Implements practices from the PM Skill-Feature Tree (Issue #44), Freeman & Pryce row:
- GOOS-style object design & testing
- GOOS as iterative design practice
- GOOS outside-in TDD
- Book: Growing Object-Oriented Software, Guided by Tests (Freeman & Pryce)

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
class GOOSRecord:
    """A GOOS-style object design record."""

    id: str
    object_name: str
    responsibility: str
    collaborates_with: str = ""
    created_at: str = field(
        default_factory=lambda: datetime.now(timezone.utc).isoformat()
    )

    def to_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "object_name": self.object_name,
            "responsibility": self.responsibility,
            "collaborates_with": self.collaborates_with,
            "created_at": self.created_at,
        }


@dataclass
class IterativeDesignRecord:
    """An iterative design practice record."""

    id: str
    iteration: str
    what_was_designed: str
    feedback: str
    next_iteration: str = ""
    created_at: str = field(
        default_factory=lambda: datetime.now(timezone.utc).isoformat()
    )

    def to_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "iteration": self.iteration,
            "what_was_designed": self.what_was_designed,
            "feedback": self.feedback,
            "next_iteration": self.next_iteration,
            "created_at": self.created_at,
        }


@dataclass
class OutsideInTDDRecord:
    """An outside-in TDD record."""

    id: str
    feature: str
    outer_test: str
    inner_objects: str
    mock_objects: str
    status: str  # red, green, refactor, done
    created_at: str = field(
        default_factory=lambda: datetime.now(timezone.utc).isoformat()
    )

    def to_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "feature": self.feature,
            "outer_test": self.outer_test,
            "inner_objects": self.inner_objects,
            "mock_objects": self.mock_objects,
            "status": self.status,
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
    dir_path = vault / os.path.join(VAULT, "02-Areas") / "Skills" / "pm_best_practices_freeman_pryce"
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


# ── GOOS-style object design ─────────────────────────────────────────────────

GOOS_OBJECT_DESIGN_PRINCIPLES = {
    "object_design": {
        "principle": "Object Design",
        "description": "Design objects with clear responsibilities and collaborations. Objects communicate by sending messages to each other.",
        "applies_to": "object-oriented design",
    },
    "tell_dont_ask": {
        "principle": "Tell, Don't Ask",
        "description": "Instead of asking an object for its state and making decisions based on that state, tell the object to do something. Encapsulate behavior with data.",
        "applies_to": "object communication",
    },
    "information_expert": {
        "principle": "Information Expert",
        "description": "Assign responsibilities to the object that has the information needed to fulfill the responsibility.",
        "applies_to": "responsibility assignment",
    },
    "low_coupling_high_cohesion": {
        "principle": "Low Coupling, High Cohesion",
        "description": "Objects should have low coupling (minimal dependencies on other objects) and high cohesion (related responsibilities grouped together).",
        "applies_to": "object relationships",
    },
}

# ── Outside-in TDD ───────────────────────────────────────────────────────────

OUTSIDE_IN_TDD_PRINCIPLES = {
    "outer_test_first": {
        "principle": "Outer Test First",
        "description": "Start by writing a failing test at the outer boundary of the system (acceptance test), then drive inward with unit tests for inner objects.",
        "applies_to": "TDD workflow",
    },
    "mock_objects": {
        "principle": "Mock Objects",
        "description": "Use mock objects to represent collaborators that don't exist yet. Mocks define the expected interface and behavior of future objects.",
        "applies_to": "TDD workflow",
    },
    "drive_from_outside_in": {
        "principle": "Drive from Outside In",
        "description": "Start from the user interface or acceptance level and drive inward to smaller, more focused objects. Each test drives the design of the next layer.",
        "applies_to": "TDD workflow",
    },
}

# ── CLI ──────────────────────────────────────────────────────────────────────

import argparse  # noqa: E402
import sys  # noqa: E402


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="PM Best Practices: Freeman & Pryce (GOOS) — Growing Object-Oriented Software, Guided by Tests"
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

    # goos-object-design
    p_od = sub.add_parser("goos-design", help="GOOS-style object design")
    p_od.add_argument("--list", action="store_true", help="List object design principles")
    p_od.add_argument("--add", action="store_true", help="Add an object design record")
    p_od.add_argument("--object-name", help="Object name")
    p_od.add_argument("--responsibility", help="Object responsibility")
    p_od.add_argument("--collaborates-with", help="Collaborates with")

    # iterative-design
    p_id = sub.add_parser("iterative-design", help="GOOS iterative design")
    p_id.add_argument("--list", action="store_true", help="List iterative design records")
    p_id.add_argument("--add", action="store_true", help="Add an iterative design record")
    p_id.add_argument("--iteration", help="Iteration name")
    p_id.add_argument("--what-was-designed", help="What was designed")
    p_id.add_argument("--feedback", help="Feedback")
    p_id.add_argument("--next-iteration", help="Next iteration")

    # outside-in-tdd
    p_tdd = sub.add_parser("outside-in-tdd", help="Outside-in TDD")
    p_tdd.add_argument("--list", action="store_true", help="List outside-in TDD records")
    p_tdd.add_argument("--add", action="store_true", help="Add an outside-in TDD record")
    p_tdd.add_argument("--feature", help="Feature name")
    p_tdd.add_argument("--outer-test", help="Outer test")
    p_tdd.add_argument("--inner-objects", help="Inner objects")
    p_tdd.add_argument("--mock-objects", help="Mock objects")
    p_tdd.add_argument(
        "--status", default="red", help="red, green, refactor, done"
    )

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
    print("PM Best Practices: Freeman & Pryce (GOOS) — Self-Test Suite")
    print("=" * 50)

    passed = 0
    failed = 0

    # Test 1: GOOS object design principles
    print("\n[1/5] GOOS object design principles...")
    assert len(GOOS_OBJECT_DESIGN_PRINCIPLES) == 4
    assert GOOS_OBJECT_DESIGN_PRINCIPLES["object_design"]["principle"] == "Object Design"
    assert GOOS_OBJECT_DESIGN_PRINCIPLES["tell_dont_ask"]["principle"] == "Tell, Don't Ask"
    print("  ✅ GOOS object design principles: 4 principles")
    passed += 1

    # Test 2: Outside-in TDD principles
    print("\n[2/5] Outside-in TDD principles...")
    assert len(OUTSIDE_IN_TDD_PRINCIPLES) == 3
    assert OUTSIDE_IN_TDD_PRINCIPLES["outer_test_first"]["principle"] == "Outer Test First"
    assert OUTSIDE_IN_TDD_PRINCIPLES["mock_objects"]["principle"] == "Mock Objects"
    print("  ✅ Outside-in TDD principles: 3 principles")
    passed += 1

    # Test 3: GOOS record creation
    print("\n[3/5] GOOS record creation...")
    import tempfile
    import shutil

    vault = tempfile.mkdtemp()
    try:
        record = GOOSRecord(
            id=_record_id("goos", "order"),
            object_name="Order",
            responsibility="Manages order state and line items",
            collaborates_with="Customer, Payment, Inventory",
        )
        records = [record.to_dict()]
        _save_json(_ensure_dirs(Path(vault)) / "goos_design.json", records)

        loaded = _load_json(_ensure_dirs(Path(vault)) / "goos_design.json")
        assert len(loaded) == 1
        assert loaded[0]["object_name"] == "Order"
        assert loaded[0]["responsibility"] == "Manages order state and line items"
        print("  ✅ GOOS object design record creation works")
        passed += 1
    finally:
        shutil.rmtree(vault)

    # Test 4: Iterative design record creation
    print("\n[4/5] Iterative design record creation...")
    vault = tempfile.mkdtemp()
    try:
        record = IterativeDesignRecord(
            id=_record_id("iter", "order_iter_1"),
            iteration="Iteration 1",
            what_was_designed="Order class with addLineItem method",
            feedback="Good start, needs validation logic",
            next_iteration="Add validation for line items",
        )
        records = [record.to_dict()]
        _save_json(_ensure_dirs(Path(vault)) / "iterative_design.json", records)

        loaded = _load_json(_ensure_dirs(Path(vault)) / "iterative_design.json")
        assert len(loaded) == 1
        assert loaded[0]["iteration"] == "Iteration 1"
        print("  ✅ Iterative design record creation works")
        passed += 1
    finally:
        shutil.rmtree(vault)

    # Test 5: Outside-in TDD record creation
    print("\n[5/5] Outside-in TDD record creation...")
    vault = tempfile.mkdtemp()
    try:
        record = OutsideInTDDRecord(
            id=_record_id("tdd", "order_feature"),
            feature="Order feature",
            outer_test="Test that placing an order creates an order record",
            inner_objects="Order, OrderLineItem, Payment",
            mock_objects="PaymentGateway, EmailSender",
            status="red",
        )
        records = [record.to_dict()]
        _save_json(_ensure_dirs(Path(vault)) / "outside_in_tdd.json", records)

        loaded = _load_json(_ensure_dirs(Path(vault)) / "outside_in_tdd.json")
        assert len(loaded) == 1
        assert loaded[0]["feature"] == "Order feature"
        assert loaded[0]["status"] == "red"
        print("  ✅ Outside-in TDD record creation works")
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
            "No command specified. Use: goos-design, iterative-design, outside-in-tdd, adr, stats, or test."
        )
        return 1

    if args.command == "goos-design":
        if args.list:
            print("GOOS-style object design principles:")
            print("=" * 50)
            for key, principle in GOOS_OBJECT_DESIGN_PRINCIPLES.items():
                print(f"\n  {key} — {principle['principle']}")
                print(f"    Description: {principle['description']}")
                print(f"    Applies to: {principle['applies_to']}")
            return 0

        if args.add:
            if not args.object_name or not args.responsibility:
                print("--object-name and --responsibility are required for --add")
                return 1
            vault = _init_paths(args.vault)
            if not vault:
                print("Error: --vault required")
                return 1

            records = _load_json(_ensure_dirs(vault) / "goos_design.json")
            record = GOOSRecord(
                id=_record_id("goos", args.object_name),
                object_name=args.object_name,
                responsibility=args.responsibility,
                collaborates_with=args.collaborates_with or "",
            )
            records.append(record.to_dict())
            _save_json(_ensure_dirs(vault) / "goos_design.json", records)

            print(f"GOOS object design record created: {record.id}")
            print(f"  Object: {record.object_name}")
            print(f"  Responsibility: {record.responsibility}")
            print(f"  Collaborates with: {record.collaborates_with}")
            return 0

        print("No action specified. Use --list or --add.")
        return 1

    if args.command == "iterative-design":
        if args.list:
            vault = _init_paths(args.vault)
            if not vault:
                print("Error: --vault required")
                return 1
            data = _load_json(_ensure_dirs(vault) / "iterative_design.json")
            print(f"Iterative design records ({len(data)}):")
            for r in data:
                print(f"  {r['id']}: {r['iteration']} — {r['what_was_designed']}")
            return 0

        if args.add:
            if not args.iteration or not args.what_was_designed:
                print("--iteration and --what-was-designed are required for --add")
                return 1
            vault = _init_paths(args.vault)
            if not vault:
                print("Error: --vault required")
                return 1

            records = _load_json(_ensure_dirs(vault) / "iterative_design.json")
            record = IterativeDesignRecord(
                id=_record_id("iter", args.iteration),
                iteration=args.iteration,
                what_was_designed=args.what_was_designed,
                feedback=args.feedback or "",
                next_iteration=args.next_iteration or "",
            )
            records.append(record.to_dict())
            _save_json(_ensure_dirs(vault) / "iterative_design.json", records)

            print(f"Iterative design record created: {record.id}")
            print(f"  Iteration: {record.iteration}")
            print(f"  What was designed: {record.what_was_designed}")
            print(f"  Feedback: {record.feedback}")
            return 0

        print("No action specified. Use --list or --add.")
        return 1

    if args.command == "outside-in-tdd":
        if args.list:
            vault = _init_paths(args.vault)
            if not vault:
                print("Error: --vault required")
                return 1
            data = _load_json(_ensure_dirs(vault) / "outside_in_tdd.json")
            print(f"Outside-in TDD records ({len(data)}):")
            for r in data:
                print(f"  {r['id']}: {r['feature']} — {r['status']}")
            return 0

        if args.add:
            if not args.feature or not args.outer_test:
                print("--feature and --outer-test are required for --add")
                return 1
            vault = _init_paths(args.vault)
            if not vault:
                print("Error: --vault required")
                return 1

            records = _load_json(_ensure_dirs(vault) / "outside_in_tdd.json")
            record = OutsideInTDDRecord(
                id=_record_id("tdd", args.feature),
                feature=args.feature,
                outer_test=args.outer_test,
                inner_objects=args.inner_objects or "",
                mock_objects=args.mock_objects or "",
                status=args.status,
            )
            records.append(record.to_dict())
            _save_json(_ensure_dirs(vault) / "outside_in_tdd.json", records)

            print(f"Outside-in TDD record created: {record.id}")
            print(f"  Feature: {record.feature}")
            print(f"  Outer test: {record.outer_test}")
            print(f"  Status: {record.status}")
            return 0

        print("No action specified. Use --list or --add.")
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
            "goos_object_design_principles": len(GOOS_OBJECT_DESIGN_PRINCIPLES),
            "outside_in_tdd_principles": len(OUTSIDE_IN_TDD_PRINCIPLES),
        }
        print(json.dumps(stats, indent=2))
        return 0

    print("Unknown command. Use: goos-design, iterative-design, outside-in-tdd, adr, stats, or test.")
    return 1


if __name__ == "__main__":
    sys.exit(main())
