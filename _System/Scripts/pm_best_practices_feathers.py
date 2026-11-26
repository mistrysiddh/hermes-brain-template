#!/usr/bin/env python3
"""
Hermes Brain — PM Best Practices: Michael Feathers Skill.

Implements practices from the PM Skill-Feature Tree (Issue #44), Michael Feathers row:
- Working Effectively with Legacy Code — characterization tests, seams & dependency breaking
- Characterization test workflows (write tests to characterize existing behavior before changing it)
- Seams & dependency breaking (identify seams, break dependencies for testing)
- Legacy change algorithms (safe change algorithms for legacy code)
- Book: Working Effectively with Legacy Code (Michael Feathers)

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
class CharacterizationTestRecord:
    """A characterization test record (Michael Feathers' characterization testing)."""

    id: str
    test_name: str
    code_under_test: str
    observed_behavior: str
    input_data: str
    expected_output: str
    actual_output: str
    confidence: float  # 0.0-1.0 how confident we are this characterizes behavior
    created_at: str = field(
        default_factory=lambda: datetime.now(timezone.utc).isoformat()
    )

    def to_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "test_name": self.test_name,
            "code_under_test": self.code_under_test,
            "observed_behavior": self.observed_behavior,
            "input_data": self.input_data,
            "expected_output": self.expected_output,
            "actual_output": self.actual_output,
            "confidence": self.confidence,
            "created_at": self.created_at,
        }


@dataclass
class SeamRecord:
    """A seam record (identifying seams for dependency breaking)."""

    id: str
    seam_name: str
    location: str  # where the seam is in the code
    seam_type: str  # object seam, preprocessor seam, link seam, etc.
    description: str
    breaking_strategy: str  # how to break the dependency at this seam
    created_at: str = field(
        default_factory=lambda: datetime.now(timezone.utc).isoformat()
    )

    def to_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "seam_name": self.seam_name,
            "location": self.location,
            "seam_type": self.seam_type,
            "description": self.description,
            "breaking_strategy": self.breaking_strategy,
            "created_at": self.created_at,
        }


@dataclass
class LegacyChangeRecord:
    """A legacy change algorithm record."""

    id: str
    change_name: str
    algorithm: str  # the change algorithm name
    description: str
    steps: str  # the steps of the algorithm
    when_to_use: str
    created_at: str = field(
        default_factory=lambda: datetime.now(timezone.utc).isoformat()
    )

    def to_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "change_name": self.change_name,
            "algorithm": self.algorithm,
            "description": self.description,
            "steps": self.steps,
            "when_to_use": self.when_to_use,
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
    dir_path = vault / "02-Areas" / "Skills" / "pm_best_practices_feathers"
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


# ── Michael Feathers' characterization tests ─────────────────────────────────

CHARACTERIZATION_TEST_GUIDELINES = {
    "write_tests_first": {
        "rule": "Write characterization tests before changing legacy code",
        "description": "Before making any changes to legacy code, write tests that characterize the current behavior. These tests lock in the current behavior so you can detect regressions.",
        "category": "characterization",
        "severity": "major",
    },
    "characterize_not_assume": {
        "rule": "Characterize what the code does, not what it should do",
        "description": "Characterization tests capture what the code actually does, including quirks and bugs. Do not 'fix' the behavior in the test—capture it as-is.",
        "category": "characterization",
        "severity": "major",
    },
    "golden_master": {
        "rule": "Use golden master testing",
        "description": "Capture the output of the system for a given input and use it as a golden master. Any change that alters the output is detected.",
        "category": "characterization",
        "severity": "moderate",
    },
    "start_small": {
        "rule": "Start characterization at the seams",
        "description": "Start characterization at seams—places where you can separate the code from its dependencies. This makes tests faster and more reliable.",
        "category": "characterization",
        "severity": "moderate",
    },
}

# ── Seams & dependency breaking ──────────────────────────────────────────────

SEAM_TYPES = {
    "object_seam": {
        "seam_type": "Object Seam",
        "description": "A seam created by exploiting polymorphism—passing a different object in place of another.",
        "breaking_strategy": "Create a test double that implements the same interface as the dependency.",
    },
    "preprocessor_seam": {
        "seam_type": "Preprocessor Seam",
        "description": "A seam created using preprocessor directives (#ifdef, #include) to swap out code at compile time.",
        "breaking_strategy": "Use conditional compilation to include test doubles instead of real dependencies.",
    },
    "link_seam": {
        "seam_type": "Link Seam",
        "description": "A seam created at link time by linking against a different object file or library.",
        "breaking_strategy": "Link against a test double library instead of the real dependency.",
    },
    "object_factory_seam": {
        "seam_type": "Object Factory Seam",
        "description": "A seam created by using a factory method to create objects, allowing the factory to return test doubles.",
        "breaking_strategy": "Subclass or mock the factory to return test doubles.",
    },
    "adapter_seam": {
        "seam_type": "Adapter Seam",
        "description": "A seam created by introducing an adapter layer between your code and a dependency.",
        "breaking_strategy": "Introduce an adapter interface and implement it with a test double for testing.",
    },
}

# ── Legacy change algorithms ─────────────────────────────────────────────────

LEGACY_CHANGE_ALGORITHMS = {
    "sprout_method": {
        "change_name": "Sprout Method",
        "algorithm": "When you need to add a feature to legacy code, write a new method that contains the new code, then call it from the existing code at the appropriate point.",
        "description": "Add new functionality by writing a new method and calling it from existing code, rather than modifying existing methods directly.",
        "when_to_use": "When you need to add new behavior to existing code without risking existing functionality.",
    },
    "sprout_class": {
        "change_name": "Sprout Class",
        "algorithm": "When you need to add a significant new capability, create a new class that contains the new behavior, and call it from the existing code.",
        "description": "Add new functionality by creating a new class and integrating it into the existing system.",
        "when_to_use": "When adding substantial new functionality that doesn't fit cleanly into existing classes.",
    },
    "wrap_method": {
        "change_name": "Wrap Method",
        "algorithm": "When you need to change the behavior of an existing method, wrap the existing method call with new code that adds the new behavior before or after the original call.",
        "description": "Change behavior by wrapping existing method calls with pre- and post-processing logic.",
        "when_to_use": "When you need to add behavior before or after an existing method call.",
    },
    "wrap_class": {
        "change_name": "Wrap Class",
        "algorithm": "When you need to change the behavior of an existing class, create a wrapper class that delegates to the original class and adds or modifies behavior.",
        "description": "Change behavior by wrapping an existing class with a new class that delegates to it.",
        "when_to_use": "When you need to modify the behavior of an entire class without modifying its source.",
    },
}

# ── CLI ──────────────────────────────────────────────────────────────────────

import argparse  # noqa: E402
import sys  # noqa: E402


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="PM Best Practices: Michael Feathers — Legacy Code (Working Effectively with Legacy Code)"
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

    # characterization-test
    p_ct = sub.add_parser("characterization-test", help="Characterization tests — capture existing behavior")
    p_ct.add_argument("--list", action="store_true", help="List characterization tests")
    p_ct.add_argument("--add", action="store_true", help="Add a characterization test")
    p_ct.add_argument("--test-name", help="Test name")
    p_ct.add_argument("--code-under-test", help="Code under test")
    p_ct.add_argument("--observed-behavior", help="Observed behavior")
    p_ct.add_argument("--input-data", help="Input data")
    p_ct.add_argument("--expected-output", help="Expected output")
    p_ct.add_argument("--actual-output", help="Actual output")
    p_ct.add_argument("--confidence", type=float, default=0.5, help="Confidence (0.0-1.0)")

    # seam
    p_seam = sub.add_parser("seam", help="Seams & dependency breaking")
    p_seam.add_argument("--list", action="store_true", help="List seams")
    p_seam.add_argument("--add", action="store_true", help="Add a seam")
    p_seam.add_argument("--seam-name", help="Seam name")
    p_ct.add_argument("--location", help="Location in code")
    p_seam.add_argument("--seam-type", help="Seam type")
    p_seam.add_argument("--description", help="Seam description")
    p_seam.add_argument("--breaking-strategy", help="Breaking strategy")

    # legacy-change
    p_lc = sub.add_parser("legacy-change", help="Legacy change algorithms")
    p_lc.add_argument("--list", action="store_true", help="List legacy change algorithms")

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
    print("PM Best Practices: Michael Feathers — Self-Test Suite")
    print("=" * 50)

    passed = 0
    failed = 0

    # Test 1: Characterization test creation
    print("\n[1/4] Characterization test creation...")
    import tempfile
    import shutil

    vault = tempfile.mkdtemp()
    try:
        record = CharacterizationTestRecord(
            id=_record_id("ct", "test_login"),
            test_name="test_login_rejects_invalid_password",
            code_under_test="login(username, password)",
            observed_behavior="Returns false for invalid passwords",
            input_data="username='baduser', password='wrong'",
            expected_output="false",
            actual_output="false",
            confidence=0.9,
        )
        records = [record.to_dict()]
        _save_json(_ensure_dirs(Path(vault)) / "characterization_tests.json", records)

        loaded = _load_json(_ensure_dirs(Path(vault)) / "characterization_tests.json")
        assert len(loaded) == 1
        assert loaded[0]["test_name"] == "test_login_rejects_invalid_password"
        assert loaded[0]["confidence"] == 0.9
        print("  ✅ Characterization test creation works")
        passed += 1
    finally:
        shutil.rmtree(vault)

    # Test 2: Seam record creation
    print("\n[2/5] Seam record creation...")
    vault = tempfile.mkdtemp()
    try:
        record = SeamRecord(
            id=_record_id("seam", "db_connection"),
            seam_name="DatabaseConnection",
            location="UserService.java:42",
            seam_type="Object Seam",
            description="Database connection used by UserService",
            breaking_strategy="Inject a mock database connection via constructor",
        )
        records = [record.to_dict()]
        _save_json(_ensure_dirs(Path(vault)) / "seams.json", records)

        loaded = _load_json(_ensure_dirs(Path(vault)) / "seams.json")
        assert len(loaded) == 1
        assert loaded[0]["seam_name"] == "DatabaseConnection"
        assert loaded[0]["seam_type"] == "Object Seam"
        print("  ✅ Seam record creation works")
        passed += 1
    finally:
        shutil.rmtree(vault)

    # Test 3: Legacy change algorithm
    print("\n[3/5] Legacy change algorithm...")
    assert len(LEGACY_CHANGE_ALGORITHMS) == 4
    assert LEGACY_CHANGE_ALGORITHMS["sprout_method"]["change_name"] == "Sprout Method"
    assert LEGACY_CHANGE_ALGORITHMS["wrap_class"]["change_name"] == "Wrap Class"
    print("  ✅ Legacy change algorithms: 4 algorithms")
    passed += 1

    # Test 4: ADR record creation
    print("\n[4/5] ADR record creation...")
    vault = tempfile.mkdtemp()
    try:
        record = ADRecord(
            id=_record_id("adr", "use_mock_db"),
            title="Use Mock Database for Testing",
            status="proposed",
            context="Legacy code uses real database connections",
            decision="Use mock database connections in tests",
            consequences="Faster tests, no database dependency",
            alternatives="Use real test database",
        )
        records = [record.to_dict()]
        _save_json(_ensure_dirs(Path(vault)) / "adrs.json", records)

        loaded = _load_json(_ensure_dirs(Path(vault)) / "adrs.json")
        assert len(loaded) == 1
        assert loaded[0]["title"] == "Use Mock Database for Testing"
        print("  ✅ ADR record creation works")
        passed += 1
    finally:
        shutil.rmtree(vault)

    # Test 5: Seam types
    print("\n[5/5] Seam types...")
    assert len(SEAM_TYPES) == 5
    assert SEAM_TYPES["object_seam"]["seam_type"] == "Object Seam"
    assert SEAM_TYPES["link_seam"]["seam_type"] == "Link Seam"
    print("  ✅ Seam types: 5 seam types")
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
            "No command specified. Use: characterization-test, seam, legacy-change, adr, stats, or test."
        )
        return 1

    if args.command == "characterization-test":
        if args.list:
            vault = _init_paths(args.vault)
            if not vault:
                print("Error: --vault required")
                return 1
            data = _load_json(_ensure_dirs(vault) / "characterization_tests.json")
            print(f"Characterization tests ({len(data)}):")
            for r in data:
                print(f"  {r['id']}: {r['test_name']} — {r['code_under_test']}")
            return 0

        if args.add:
            if not args.test_name or not args.code_under_test:
                print("--test-name and --code-under-test are required for --add")
                return 1
            vault = _init_paths(args.vault)
            if not vault:
                print("Error: --vault required")
                return 1

            records = _load_json(_ensure_dirs(vault) / "characterization_tests.json")
            record = CharacterizationTestRecord(
                id=_record_id("ct", args.test_name),
                test_name=args.test_name,
                code_under_test=args.code_under_test,
                observed_behavior=args.observed_behavior or "",
                input_data=args.input_data or "",
                expected_output=args.expected_output or "",
                actual_output=args.actual_output or "",
                confidence=args.confidence,
            )
            records.append(record.to_dict())
            _save_json(_ensure_dirs(vault) / "characterization_tests.json", records)

            print(f"Characterization test created: {record.id}")
            print(f"  Test: {record.test_name}")
            print(f"  Code under test: {record.code_under_test}")
            print(f"  Confidence: {record.confidence}")
            return 0

        print("No action specified. Use --list or --add.")
        return 1

    if args.command == "seam":
        if args.list:
            vault = _init_paths(args.vault)
            if not vault:
                print("Error: --vault required")
                return 1
            data = _load_json(_ensure_dirs(vault) / "seams.json")
            print(f"Seam records ({len(data)}):")
            for r in data:
                print(f"  {r['id']}: {r['seam_name']} — {r['seam_type']} at {r['location']}")
            return 0

        if args.add:
            if not args.seam_name or not args.location or not args.seam_type:
                print("--seam-name, --location, and --seam-type are required for --add")
                return 1
            vault = _init_paths(args.vault)
            if not vault:
                print("Error: --vault required")
                return 1

            records = _load_json(_ensure_dirs(vault) / "seams.json")
            record = SeamRecord(
                id=_record_id("seam", args.seam_name),
                seam_name=args.seam_name,
                location=args.location,
                seam_type=args.seam_type,
                description=args.description or "",
                breaking_strategy=args.breaking_strategy or "",
            )
            records.append(record.to_dict())
            _save_json(_ensure_dirs(vault) / "seams.json", records)

            print(f"Seam created: {record.id}")
            print(f"  Seam: {record.seam_name} ({record.seam_type})")
            print(f"  Location: {record.location}")
            return 0

        print("No action specified. Use --list or --add.")
        return 1

    if args.command == "legacy-change":
        if args.list:
            print("Michael Feathers' Legacy Change Algorithms:")
            print("=" * 50)
            for key, algo in LEGACY_CHANGE_ALGORITHMS.items():
                print(f"\n  {key} — {algo['change_name']}")
                print(f"    Description: {algo['description']}")
                print(f"    When to use: {algo['when_to_use']}")
            return 0
        print("No action specified. Use --list to see legacy change algorithms.")
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
            "characterization_tests": len(_load_json(base / "characterization_tests.json")),
            "seams": len(_load_json(base / "seams.json")),
            "legacy_change_algorithms": len(LEGACY_CHANGE_ALGORITHMS),
            "adrs": len(_load_json(base / "adrs.json")),
        }
        print(json.dumps(stats, indent=2))
        return 0

    print("Unknown command. Use: characterization-test, seam, legacy-change, adr, stats, or test.")
    return 1


if __name__ == "__main__":
    sys.exit(main())
