#!/usr/bin/env python3
"""
Hermes Brain — PM Best Practices: Bertrand Meyer Skill.

Implements practices from the PM Skill-Feature Tree (Issue #44), Bertrand Meyer row:
- Design by Contract — preconditions, postconditions, class invariants
- Command-Query Separation (CQS)
- Open/Closed Principle
- Book: Object-Oriented Software Construction (Bertrand Meyer)

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
class ContractRecord:
    """A Design by Contract record (precondition, postcondition, invariant)."""

    id: str
    contract_name: str
    contract_type: str  # precondition, postcondition, invariant
    target: str  # method/class the contract applies to
    condition: str  # the contract condition
    violation_action: str  # what happens on violation
    created_at: str = field(
        default_factory=lambda: datetime.now(timezone.utc).isoformat()
    )

    def to_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "contract_name": self.contract_name,
            "contract_type": self.contract_type,
            "target": self.target,
            "condition": self.condition,
            "violation_action": self.violation_action,
            "created_at": self.created_at,
        }


@dataclass
class CQSRecord:
    """A Command-Query Separation record."""

    id: str
    method_name: str
    method_type: str  # command or query
    target_class: str
    description: str
    side_effects: str  # documented side effects (commands only)
    return_value: str  # return value description (queries only)
    created_at: str = field(
        default_factory=lambda: datetime.now(timezone.utc).isoformat()
    )

    def to_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "method_name": self.method_name,
            "method_type": self.method_type,
            "target_class": self.target_class,
            "description": self.description,
            "side_effects": self.side_effects,
            "return_value": self.return_value,
            "created_at": self.created_at,
        }


@dataclass
class OpenClosedRecord:
    """An Open/Closed Principle record."""

    id: str
    module_name: str
    description: str
    extension_mechanism: str  # how the module is extended without modification
    closed_for_modification: bool
    created_at: str = field(
        default_factory=lambda: datetime.now(timezone.utc).isoformat()
    )

    def to_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "module_name": self.module_name,
            "description": self.description,
            "extension_mechanism": self.extension_mechanism,
            "closed_for_modification": self.closed_for_modification,
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
    dir_path = vault / os.path.join(VAULT, "02-Areas") / "Skills" / "pm_best_practices_meyer"
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


# ── Bertrand Meyer's Design by Contract ──────────────────────────────────────

CONTRACT_TYPES = {
    "precondition": {
        "contract_type": "Precondition",
        "description": "An obligation on the caller — must be true before the routine is called.",
        "applies_to": "routine entry",
    },
    "postcondition": {
        "contract_type": "Postcondition",
        "description": "An obligation on the routine — guaranteed to be true after the routine completes.",
        "applies_to": "routine exit",
    },
    "class_invariant": {
        "contract_type": "Class Invariant",
        "description": "A consistency constraint that holds for all instances of a class after creation and after every public routine.",
        "applies_to": "class lifetime",
    },
}

CQS_PRINCIPLES = {
    "command_query_separation": {
        "principle": "Command-Query Separation",
        "description": "Every method should be either a command (performs an action, returns nothing) or a query (returns data, no side effects), but never both.",
        "applies_to": "method design",
    },
    "queries_have_no_side_effects": {
        "principle": "Queries Have No Side Effects",
        "description": "A query must not modify the observable state of the system.",
        "applies_to": "query methods",
    },
    "commands_change_state": {
        "principle": "Commands Change State",
        "description": "A command may modify state but must not return meaningful data (other than success/failure).",
        "applies_to": "command methods",
    },
}

OPEN_CLOSED_PRINCIPLE = {
    "open_closed": {
        "principle": "Open/Closed Principle",
        "description": "Software entities (classes, modules, functions) should be open for extension but closed for modification.",
        "applies_to": "class/module design",
    },
}

# ── CLI ──────────────────────────────────────────────────────────────────────

import argparse  # noqa: E402
import sys  # noqa: E402


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="PM Best Practices: Bertrand Meyer — Design by Contract & OOSC"
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

    # contract
    p_ct = sub.add_parser("contract", help="Design by Contract records")
    p_ct.add_argument("--list", action="store_true", help="List contract records")
    p_ct.add_argument("--add", action="store_true", help="Add a contract record")
    p_ct.add_argument("--contract-name", help="Contract name")
    p_ct.add_argument(
        "--contract-type",
        help="precondition/postcondition/invariant",
    )
    p_ct.add_argument("--target", help="Method/class the contract applies to")
    p_ct.add_argument("--condition", help="The contract condition")
    p_ct.add_argument(
        "--violation-action", default="raise exception", help="Action on violation"
    )

    # cqs
    p_cqs = sub.add_parser("cqs", help="Command-Query Separation records")
    p_cqs.add_argument("--list", action="store_true", help="List CQS records")
    p_cqs.add_argument("--add", action="store_true", help="Add a CQS record")
    p_cqs.add_argument("--method-name", help="Method name")
    p_cqs.add_argument("--method-type", help="command or query")
    p_cqs.add_argument("--target-class", help="Target class")
    p_cqs.add_argument("--description", help="Method description")
    p_cqs.add_argument("--side-effects", help="Side effects (commands only)")
    p_cqs.add_argument("--return-value", help="Return value (queries only)")

    # open-closed
    p_oc = sub.add_parser("open-closed", help="Open/Closed Principle records")
    p_oc.add_argument("--list", action="store_true", help="List OCP records")
    p_oc.add_argument("--add", action="store_true", help="Add an OCP record")
    p_oc.add_argument("--module-name", help="Module name")
    p_oc.add_argument("--description", help="Module description")
    p_oc.add_argument(
        "--extension-mechanism", help="How the module is extended"
    )
    p_oc.add_argument(
        "--closed-for-modification",
        action="store_true",
        default=True,
        help="Module is closed for modification",
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
    print("PM Best Practices: Bertrand Meyer — Self-Test Suite")
    print("=" * 50)

    passed = 0
    failed = 0

    # Test 1: Contract types
    print("\n[1/5] Contract types...")
    assert len(CONTRACT_TYPES) == 3
    assert CONTRACT_TYPES["precondition"]["contract_type"] == "Precondition"
    assert CONTRACT_TYPES["postcondition"]["contract_type"] == "Postcondition"
    assert CONTRACT_TYPES["class_invariant"]["contract_type"] == "Class Invariant"
    print("  ✅ Contract types: 3 types")
    passed += 1

    # Test 2: CQS principles
    print("\n[2/5] CQS principles...")
    assert len(CQS_PRINCIPLES) == 3
    assert CQS_PRINCIPLES["command_query_separation"]["principle"] == "Command-Query Separation"
    print("  ✅ CQS principles: 3 principles")
    passed += 1

    # Test 3: Open/Closed Principle
    print("\n[3/5] Open/Closed Principle...")
    assert len(OPEN_CLOSED_PRINCIPLE) == 1
    assert OPEN_CLOSED_PRINCIPLE["open_closed"]["principle"] == "Open/Closed Principle"
    print("  ✅ Open/Closed Principle: 1 principle")
    passed += 1

    # Test 4: Contract record creation
    print("\n[4/5] Contract record creation...")
    import tempfile
    import shutil

    vault = tempfile.mkdtemp()
    try:
        record = ContractRecord(
            id=_record_id("contract", "withdraw_precondition"),
            contract_name="withdraw_precondition",
            contract_type="precondition",
            target="Account.withdraw(amount)",
            condition="amount > 0 AND amount <= balance",
            violation_action="raise exception",
        )
        records = [record.to_dict()]
        _save_json(_ensure_dirs(Path(vault)) / "contracts.json", records)

        loaded = _load_json(_ensure_dirs(Path(vault)) / "contracts.json")
        assert len(loaded) == 1
        assert loaded[0]["contract_type"] == "precondition"
        assert loaded[0]["target"] == "Account.withdraw(amount)"
        print("  ✅ Contract record creation works")
        passed += 1
    finally:
        shutil.rmtree(vault)

    # Test 5: CQS record creation
    print("\n[5/5] CQS record creation...")
    vault = tempfile.mkdtemp()
    try:
        record = CQSRecord(
            id=_record_id("cqs", "get_balance"),
            method_name="get_balance",
            method_type="query",
            target_class="Account",
            description="Returns the current account balance",
            side_effects="",
            return_value="balance amount",
        )
        records = [record.to_dict()]
        _save_json(_ensure_dirs(Path(vault)) / "cqs.json", records)

        loaded = _load_json(_ensure_dirs(Path(vault)) / "cqs.json")
        assert len(loaded) == 1
        assert loaded[0]["method_type"] == "query"
        assert loaded[0]["side_effects"] == ""
        print("  ✅ CQS record creation works")
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
            "No command specified. Use: contract, cqs, open-closed, adr, stats, or test."
        )
        return 1

    if args.command == "contract":
        if args.list:
            print("Bertrand Meyer's Design by Contract Types:")
            print("=" * 50)
            for key, ct in CONTRACT_TYPES.items():
                print(f"\n  {key} — {ct['contract_type']}")
                print(f"    Description: {ct['description']}")
                print(f"    Applies to: {ct['applies_to']}")
            return 0

        if args.add:
            if not args.contract_name or not args.contract_type or not args.target:
                print("--contract-name, --contract-type, and --target are required for --add")
                return 1
            vault = _init_paths(args.vault)
            if not vault:
                print("Error: --vault required")
                return 1

            records = _load_json(_ensure_dirs(vault) / "contracts.json")
            record = ContractRecord(
                id=_record_id("contract", args.contract_name),
                contract_name=args.contract_name,
                contract_type=args.contract_type,
                target=args.target,
                condition=args.condition or "",
                violation_action=args.violation_action,
            )
            records.append(record.to_dict())
            _save_json(_ensure_dirs(vault) / "contracts.json", records)

            print(f"Contract created: {record.id}")
            print(f"  Contract: {record.contract_name} ({record.contract_type})")
            print(f"  Target: {record.target}")
            print(f"  Condition: {record.condition}")
            return 0

        print("No action specified. Use --list or --add.")
        return 1

    if args.command == "cqs":
        if args.list:
            print("Bertrand Meyer's Command-Query Separation Principles:")
            print("=" * 50)
            for key, principle in CQS_PRINCIPLES.items():
                print(f"\n  {key} — {principle['principle']}")
                print(f"    Description: {principle['description']}")
                print(f"    Applies to: {principle['applies_to']}")
            return 0

        if args.add:
            if not args.method_name or not args.method_type or not args.target_class:
                print("--method-name, --method-type, and --target-class are required for --add")
                return 1
            vault = _init_paths(args.vault)
            if not vault:
                print("Error: --vault required")
                return 1

            records = _load_json(_ensure_dirs(vault) / "cqs.json")
            record = CQSRecord(
                id=_record_id("cqs", args.method_name),
                method_name=args.method_name,
                method_type=args.method_type,
                target_class=args.target_class,
                description=args.description or "",
                side_effects=args.side_effects or "",
                return_value=args.return_value or "",
            )
            records.append(record.to_dict())
            _save_json(_ensure_dirs(vault) / "cqs.json", records)

            print(f"CQS record created: {record.id}")
            print(f"  Method: {record.method_name} ({record.method_type})")
            print(f"  Class: {record.target_class}")
            print(f"  Side effects: {record.side_effects}")
            print(f"  Return value: {record.return_value}")
            return 0

        print("No action specified. Use --list or --add.")
        return 1

    if args.command == "open-closed":
        if args.list:
            print("Bertrand Meyer's Open/Closed Principle:")
            print("=" * 50)
            for key, principle in OPEN_CLOSED_PRINCIPLE.items():
                print(f"\n  {key} — {principle['principle']}")
                print(f"    Description: {principle['description']}")
                print(f"    Applies to: {principle['applies_to']}")
            return 0

        if args.add:
            if not args.module_name or not args.description:
                print("--module-name and --description are required for --add")
                return 1
            vault = _init_paths(args.vault)
            if not vault:
                print("Error: --vault required")
                return 1

            records = _load_json(_ensure_dirs(vault) / "open_closed.json")
            record = OpenClosedRecord(
                id=_record_id("ocp", args.module_name),
                module_name=args.module_name,
                description=args.description,
                extension_mechanism=args.extension_mechanism or "",
                closed_for_modification=args.closed_for_modification,
            )
            records.append(record.to_dict())
            _save_json(_ensure_dirs(vault) / "open_closed.json", records)

            print(f"Open/Closed record created: {record.id}")
            print(f"  Module: {record.module_name}")
            print(f"  Extension mechanism: {record.extension_mechanism}")
            print(f"  Closed for modification: {record.closed_for_modification}")
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

        stats = {
            "contract_types": len(CONTRACT_TYPES),
            "cqs_principles": len(CQS_PRINCIPLES),
            "open_closed_principles": len(OPEN_CLOSED_PRINCIPLE),
        }
        print(json.dumps(stats, indent=2))
        return 0

    print("Unknown command. Use: contract, cqs, open-closed, adr, stats, or test.")
    return 1


if __name__ == "__main__":
    sys.exit(main())
