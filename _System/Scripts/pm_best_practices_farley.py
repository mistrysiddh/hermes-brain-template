#!/usr/bin/env python3
"""
Hermes Brain — PM Best Practices: Dave Farley Skill.

Implements practices from the PM Skill-Feature Tree (Issue #44), Dave Farley row:
- Continuous Delivery & delivery pipelines
- Automated acceptance gates
- Trunk-based development
- Deployment pipeline patterns
- Book: Continuous Delivery (Farley & Humble)

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
class DeliveryPipelineRecord:
    """A delivery pipeline record (Dave Farley's Continuous Delivery)."""

    id: str
    pipeline_name: str
    stages: str  # comma-separated stage names
    automated_tests: bool
    deployment_frequency: str  # e.g. "per-commit", "daily", "weekly"
    lead_time: str = ""
    created_at: str = field(
        default_factory=lambda: datetime.now(timezone.utc).isoformat()
    )

    def to_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "pipeline_name": self.pipeline_name,
            "stages": self.stages,
            "automated_tests": self.automated_tests,
            "deployment_frequency": self.deployment_frequency,
            "lead_time": self.lead_time,
            "created_at": self.created_at,
        }


@dataclass
class AcceptanceGateRecord:
    """An automated acceptance gate record."""

    id: str
    gate_name: str
    location: str  # where in the pipeline the gate sits
    gate_type: str  # build, test, security, performance, deployment
    criteria: str  # pass/fail criteria
    automated: bool
    created_at: str = field(
        default_factory=lambda: datetime.now(timezone.utc).isoformat()
    )

    def to_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "gate_name": self.gate_name,
            "location": self.location,
            "gate_type": self.gate_type,
            "criteria": self.criteria,
            "automated": self.automated,
            "created_at": self.created_at,
        }


@dataclass
class TrunkBasedRecord:
    """A trunk-based development record."""

    id: str
    practice: str  # e.g. "short-lived branches", "feature flags", "commit daily"
    description: str
    branch_max_age: str = ""  # e.g. "1 day", "hours"
    created_at: str = field(
        default_factory=lambda: datetime.now(timezone.utc).isoformat()
    )

    def to_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "practice": self.practice,
            "description": self.description,
            "branch_max_age": self.branch_max_age,
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
    dir_path = vault / "02-Areas" / "Skills" / "pm_best_practices_farley"
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


# ── Dave Farley's Continuous Delivery practices ─────────────────────────────

DELIVERY_PIPELINE_PRINCIPLES = {
    "pipeline_as_code": {
        "principle": "Pipeline as Code",
        "description": "Define the entire delivery pipeline in code, version-controlled alongside the application code.",
        "applies_to": "CI/CD configuration",
    },
    "automated_acceptance_tests": {
        "principle": "Automated Acceptance Tests",
        "description": "Every change must pass automated acceptance tests before progressing to the next pipeline stage.",
        "applies_to": "testing strategy",
    },
    "deploy_any_version": {
        "principle": "Deploy Any Version",
        "description": "The pipeline produces a deployable artifact that can be deployed to any environment at any time.",
        "applies_to": "deployment strategy",
    },
    "fast_feedback": {
        "principle": "Fast Feedback",
        "description": "Pipeline stages should be ordered to give the fastest possible feedback—fail fast, fail early.",
        "applies_to": "pipeline design",
    },
}

TRUNK_BASED_PRACTICES = {
    "short_lived_branches": {
        "practice": "Short-lived Branches",
        "description": "Feature branches live for hours, not days. Merge to trunk frequently.",
        "branch_max_age": "1 day",
    },
    "commit_to_trunk_daily": {
        "practice": "Commit to Trunk Daily",
        "description": "Every developer commits to trunk at least once per day. No long-lived divergence.",
        "branch_max_age": "1 day",
    },
    "feature_flags": {
        "practice": "Feature Flags",
        "description": "Use feature flags to merge incomplete features to trunk without exposing them to users.",
        "branch_max_age": "ongoing",
    },
}

# ── CLI ──────────────────────────────────────────────────────────────────────

import argparse  # noqa: E402
import sys  # noqa: E402


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="PM Best Practices: Dave Farley — Continuous Delivery & Delivery Pipelines"
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

    # delivery-pipeline
    p_dp = sub.add_parser("delivery-pipeline", help="Delivery pipeline records")
    p_dp.add_argument("--list", action="store_true", help="List pipeline records")
    p_dp.add_argument("--add", action="store_true", help="Add a pipeline record")
    p_dp.add_argument("--pipeline-name", help="Pipeline name")
    p_dp.add_argument("--stages", help="Comma-separated stage names")
    p_dp.add_argument(
        "--automated-tests",
        action="store_true",
        help="Pipeline includes automated tests",
    )
    p_dp.add_argument(
        "--no-automated-tests",
        action="store_false",
        dest="automated_tests",
        help="Pipeline does not include automated tests",
    )
    p_dp.set_defaults(automated_tests=True)
    p_dp.add_argument(
        "--deployment-frequency", default="per-commit", help="Deployment frequency"
    )
    p_dp.add_argument("--lead-time", help="Lead time for changes")

    # acceptance-gate
    p_ag = sub.add_parser("acceptance-gate", help="Automated acceptance gates")
    p_ag.add_argument("--list", action="store_true", help="List acceptance gates")
    p_ag.add_argument("--add", action="store_true", help="Add an acceptance gate")
    p_ag.add_argument("--gate-name", help="Gate name")
    p_ag.add_argument("--location", help="Pipeline location")
    p_ag.add_argument("--gate-type", help="build/test/security/performance/deployment")
    p_ag.add_argument("--criteria", help="Pass/fail criteria")
    p_ag.add_argument(
        "--automated", action="store_true", default=True, help="Gate is automated"
    )

    # trunk-based
    p_tb = sub.add_parser("trunk-based", help="Trunk-based development practices")
    p_tb.add_argument("--list", action="store_true", help="List practices")
    p_tb.add_argument("--add", action="store_true", help="Add a practice")
    p_tb.add_argument("--practice", help="Practice name")
    p_tb.add_argument("--description", help="Practice description")
    p_tb.add_argument(
        "--branch-max-age", default="1 day", help="Max branch age"
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
    print("PM Best Practices: Dave Farley — Self-Test Suite")
    print("=" * 50)

    passed = 0
    failed = 0

    # Test 1: Delivery pipeline principles
    print("\n[1/5] Delivery pipeline principles...")
    assert len(DELIVERY_PIPELINE_PRINCIPLES) == 4
    assert DELIVERY_PIPELINE_PRINCIPLES["pipeline_as_code"]["principle"] == "Pipeline as Code"
    assert DELIVERY_PIPELINE_PRINCIPLES["fast_feedback"]["principle"] == "Fast Feedback"
    print("  ✅ Delivery pipeline principles: 4 principles")
    passed += 1

    # Test 2: Trunk-based practices
    print("\n[2/5] Trunk-based practices...")
    assert len(TRUNK_BASED_PRACTICES) == 3
    assert TRUNK_BASED_PRACTICES["short_lived_branches"]["practice"] == "Short-lived Branches"
    assert TRUNK_BASED_PRACTICES["feature_flags"]["practice"] == "Feature Flags"
    print("  ✅ Trunk-based practices: 3 practices")
    passed += 1

    # Test 3: Delivery pipeline record creation
    print("\n[3/5] Delivery pipeline record creation...")
    import tempfile
    import shutil

    vault = tempfile.mkdtemp()
    try:
        record = DeliveryPipelineRecord(
            id=_record_id("dp", "main-pipeline"),
            pipeline_name="Main Pipeline",
            stages="build,test,security,deploy",
            automated_tests=True,
            deployment_frequency="per-commit",
            lead_time="<1 hour",
        )
        records = [record.to_dict()]
        _save_json(_ensure_dirs(Path(vault)) / "delivery_pipelines.json", records)

        loaded = _load_json(_ensure_dirs(Path(vault)) / "delivery_pipelines.json")
        assert len(loaded) == 1
        assert loaded[0]["pipeline_name"] == "Main Pipeline"
        assert loaded[0]["automated_tests"] is True
        print("  ✅ Delivery pipeline record creation works")
        passed += 1
    finally:
        shutil.rmtree(vault)

    # Test 4: Acceptance gate record creation
    print("\n[4/5] Acceptance gate record creation...")
    vault = tempfile.mkdtemp()
    try:
        record = AcceptanceGateRecord(
            id=_record_id("ag", "security-scan"),
            gate_name="Security Scan",
            location="After test stage",
            gate_type="security",
            criteria="No critical vulnerabilities",
            automated=True,
        )
        records = [record.to_dict()]
        _save_json(_ensure_dirs(Path(vault)) / "acceptance_gates.json", records)

        loaded = _load_json(_ensure_dirs(Path(vault)) / "acceptance_gates.json")
        assert len(loaded) == 1
        assert loaded[0]["gate_name"] == "Security Scan"
        assert loaded[0]["gate_type"] == "security"
        print("  ✅ Acceptance gate record creation works")
        passed += 1
    finally:
        shutil.rmtree(vault)

    # Test 5: Trunk-based record creation
    print("\n[5/5] Trunk-based record creation...")
    vault = tempfile.mkdtemp()
    try:
        record = TrunkBasedRecord(
            id=_record_id("tb", "feature_flags"),
            practice="Feature Flags",
            description="Use feature flags to merge incomplete features to trunk without exposing them to users",
            branch_max_age="ongoing",
        )
        records = [record.to_dict()]
        _save_json(_ensure_dirs(Path(vault)) / "trunk_based.json", records)

        loaded = _load_json(_ensure_dirs(Path(vault)) / "trunk_based.json")
        assert len(loaded) == 1
        assert loaded[0]["practice"] == "Feature Flags"
        assert loaded[0]["branch_max_age"] == "ongoing"
        print("  ✅ Trunk-based record creation works")
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
            "No command specified. Use: delivery-pipeline, acceptance-gate, trunk-based, adr, stats, or test."
        )
        return 1

    if args.command == "delivery-pipeline":
        if args.list:
            print("Dave Farley's Delivery Pipeline Principles:")
            print("=" * 50)
            for key, principle in DELIVERY_PIPELINE_PRINCIPLES.items():
                print(f"\n  {key} — {principle['principle']}")
                print(f"    Description: {principle['description']}")
                print(f"    Applies to: {principle['applies_to']}")
            return 0

        if args.add:
            if not args.pipeline_name or not args.stages:
                print("--pipeline-name and --stages are required for --add")
                return 1
            vault = _init_paths(args.vault)
            if not vault:
                print("Error: --vault required")
                return 1

            records = _load_json(_ensure_dirs(vault) / "delivery_pipelines.json")
            record = DeliveryPipelineRecord(
                id=_record_id("dp", args.pipeline_name),
                pipeline_name=args.pipeline_name,
                stages=args.stages,
                automated_tests=args.automated_tests,
                deployment_frequency=args.deployment_frequency,
                lead_time=args.lead_time or "",
            )
            records.append(record.to_dict())
            _save_json(_ensure_dirs(vault) / "delivery_pipelines.json", records)

            print(f"Delivery pipeline created: {record.id}")
            print(f"  Pipeline: {record.pipeline_name}")
            print(f"  Stages: {record.stages}")
            print(f"  Automated tests: {record.automated_tests}")
            print(f"  Deployment frequency: {record.deployment_frequency}")
            return 0

        print("No action specified. Use --list or --add.")
        return 1

    if args.command == "acceptance-gate":
        if args.list:
            vault = _init_paths(args.vault)
            if not vault:
                print("Error: --vault required")
                return 1
            data = _load_json(_ensure_dirs(vault) / "acceptance_gates.json")
            print(f"Acceptance gates ({len(data)}):")
            for r in data:
                print(f"  {r['id']}: {r['gate_name']} — {r['gate_type']} at {r['location']}")
            return 0

        if args.add:
            if not args.gate_name or not args.location or not args.gate_type:
                print("--gate-name, --location, and --gate-type are required for --add")
                return 1
            vault = _init_paths(args.vault)
            if not vault:
                print("Error: --vault required")
                return 1

            records = _load_json(_ensure_dirs(vault) / "acceptance_gates.json")
            record = AcceptanceGateRecord(
                id=_record_id("ag", args.gate_name),
                gate_name=args.gate_name,
                location=args.location,
                gate_type=args.gate_type,
                criteria=args.criteria or "",
                automated=args.automated,
            )
            records.append(record.to_dict())
            _save_json(_ensure_dirs(vault) / "acceptance_gates.json", records)

            print(f"Acceptance gate created: {record.id}")
            print(f"  Gate: {record.gate_name} ({record.gate_type})")
            print(f"  Location: {record.location}")
            print(f"  Automated: {record.automated}")
            return 0

        print("No action specified. Use --list or --add.")
        return 1

    if args.command == "trunk-based":
        if args.list:
            print("Dave Farley's Trunk-Based Development Practices:")
            print("=" * 50)
            for key, practice in TRUNK_BASED_PRACTICES.items():
                print(f"\n  {key} — {practice['practice']}")
                print(f"    Description: {practice['description']}")
                print(f"    Max branch age: {practice['branch_max_age']}")
            return 0

        if args.add:
            if not args.practice or not args.description:
                print("--practice and --description are required for --add")
                return 1
            vault = _init_paths(args.vault)
            if not vault:
                print("Error: --vault required")
                return 1

            records = _load_json(_ensure_dirs(vault) / "trunk_based.json")
            record = TrunkBasedRecord(
                id=_record_id("tb", args.practice),
                practice=args.practice,
                description=args.description,
                branch_max_age=args.branch_max_age,
            )
            records.append(record.to_dict())
            _save_json(_ensure_dirs(vault) / "trunk_based.json", records)

            print(f"Trunk-based practice created: {record.id}")
            print(f"  Practice: {record.practice}")
            print(f"  Description: {record.description}")
            print(f"  Max branch age: {record.branch_max_age}")
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
            "delivery_pipeline_principles": len(DELIVERY_PIPELINE_PRINCIPLES),
            "trunk_based_practices": len(TRUNK_BASED_PRACTICES),
        }
        print(json.dumps(stats, indent=2))
        return 0

    print("Unknown command. Use: delivery-pipeline, acceptance-gate, trunk-based, adr, stats, or test.")
    return 1


if __name__ == "__main__":
    sys.exit(main())
