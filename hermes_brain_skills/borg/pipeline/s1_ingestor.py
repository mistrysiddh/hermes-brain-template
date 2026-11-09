"""Hermes Brain — Borg Pipeline: S1 Ingestor (§4.1).

S1 Ingestor — Unpack, type, provenance, trust-scan.
- Unpacks artifact bundles (F1/F2/F3)
- Classifies artifact family and kind
- Extracts provenance (pack, path, commit, checksum, license, owner)
- Runs TRUST scan before any further processing
- Emits append-only proposals for S2 profiling

Stdlib-only. Multi-harness compliant.
"""

import hashlib
import json
import os
import zipfile
import tarfile
from datetime import datetime, timezone
from typing import Any

from .. import trust_scanner, models

# Deferred vault path — resolved at runtime
VAULT = None


def init_paths(vault_path: str) -> None:
    """Resolve the vault root path from the given vault path."""
    global VAULT
    VAULT = os.path.abspath(vault_path)


# ---------------------------------------------------------------------------
# Artifact families and kinds
# ---------------------------------------------------------------------------

FAMILY_F1 = "F1"  # Executable/event
FAMILY_F2 = "F2"  # Knowledge/scaffold
FAMILY_F3 = "F3"  # Agentic/orchestration

KIND_MAP = {
    "hook": "Trigger",
    "slash_command": "Skill",
    "script_binary": "Tool-binding",
    "mcp_function": "Tool-binding",
    "permission_config": "Policy",
    "ref_doc": "Resource",
    "template_example": "Resource",
    "test_eval": "Resource",
    "memory": "Resource",
    "skill_folder": "Skill",
    "workflow_playbook": "Orchestration",
    "subagent": "Role",
    "rule_file": "Policy",
    "plugin_bundle": "Orchestration",
}

LAYER_MAP = {
    "Role": "L3",
    "Skill": "L1",
    "Orchestration": "L2",
    "Trigger": "L1",
    "Policy": "L1",
    "Resource": "L1",
    "Tool-binding": "L1",
}

FAMILY_MAP = {
    "Role": "F3",
    "Skill": "F1",
    "Orchestration": "F3",
    "Trigger": "F1",
    "Policy": "F1",
    "Resource": "F2",
    "Tool-binding": "F1",
}


# ---------------------------------------------------------------------------
# S1 Ingestor
# ---------------------------------------------------------------------------

def compute_checksum(content: str) -> str:
    """Compute SHA-256 checksum of content."""
    return hashlib.sha256(content.encode("utf-8")).hexdigest()


def unpack_artifact(source_path: str) -> dict[str, Any]:
    """Unpack a single artifact file.

    Reads the artifact, computes checksum, detects family/kind from content.
    Returns an unpacked artifact dict ready for TRUST scan and profiling.

    Args:
        source_path: Path to the artifact file.

    Returns:
        {
            "path": str,
            "checksum": str,
            "size": int,
            "detected_kind": str,
            "detected_family": str,
            "content": str,
            "provenance": dict,
            "unpacked_at": str,
        }

    """
    if not os.path.exists(source_path):
        raise FileNotFoundError(f"Artifact not found: {source_path}")

    with open(source_path, encoding="utf-8") as f:
        content = f.read()

    checksum = compute_checksum(content)
    size = len(content.encode("utf-8"))

    # Detect kind from content hints
    detected_kind = _detect_kind(content, source_path)
    detected_family = FAMILY_MAP.get(detected_kind, "F1")

    now = datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")

    return {
        "path": source_path,
        "checksum": checksum,
        "size": size,
        "detected_kind": detected_kind,
        "detected_family": detected_family,
        "content": content,
        "provenance": {
            "pack": "",
            "path": source_path,
            "commit": "",
            "checksum": checksum,
            "license": "",
            "owner": "",
            "dates": {"created": now, "modified": now},
            "ancestry_cluster": "",
        },
        "unpacked_at": now,
    }


def _detect_kind(content: str, source_path: str) -> str:
    """Detect artifact kind from content and filename.

    Heuristic detection — later refined by S2 profiling.
    """
    name = os.path.basename(source_path).lower()
    lower = content.lower()

    # Hook/event config
    if "fires-on" in lower or "event:" in lower or "matcher:" in lower:
        return "Trigger"

    # Slash command
    if name.startswith("/") or "slash" in lower or "command:" in lower:
        return "Skill"

    # MCP function
    if "mcp" in lower and ("server" in lower or "tool" in lower):
        return "Tool-binding"

    # Permission/config
    if "allow" in lower and "deny" in lower and "policy" in lower:
        return "Policy"

    # Test/eval
    if "test" in name or "eval" in name or "golden" in lower:
        return "Resource"

    # Skill folder
    if "skill" in name and ("folder" in name or "pack" in name):
        return "Skill"

    # Workflow/playbook
    if "workflow" in name or "playbook" in name or "dag" in lower:
        return "Orchestration"

    # Subagent
    if "subagent" in name or "agent" in name:
        return "Role"

    # Rule file
    if "rule" in name:
        return "Policy"

    # Plugin/bundle
    if "plugin" in name or "bundle" in name:
        return "Orchestration"

    # Default: Resource
    return "Resource"


def trust_scan_artifact(unpacked: dict[str, Any]) -> dict[str, Any]:
    """Run TRUST scan on an unpacked artifact.

    Returns:
        {
            "passed": bool,
            "quarantine": bool,
            "results": list,
            "g2_required": bool,
        }

    """
    content = unpacked.get("content", "")
    record = {
        "kind": unpacked.get("detected_kind", "Resource"),
        "family": unpacked.get("detected_family", "F1"),
        "provenance": unpacked.get("provenance", {}),
    }
    return trust_scanner.scan_record(record, content)


def build_ingestor_proposal(
    unpacked: dict[str, Any],
    trust_result: dict[str, Any],
    dry_run: bool = True,
) -> dict[str, Any]:
    """Build an S1→S2 proposal record from an unpacked + trust-scanned artifact.

    Returns a proposal dict that S2 profiling will consume.

    Args:
        unpacked: Result from unpack_artifact().
        trust_result: Result from trust_scan_artifact().
        dry_run: If True, proposal is returned but not persisted.

    Returns:
        {
            "proposal_id": str,
            "unpacked": dict,
            "trust": dict,
            "status": str,       # "pending" | "quarantined"
            "dry_run": bool,
            "created_at": str,
        }

    """
    now = datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")
    proposal_id = f"ingestor-{unpacked['checksum'][:12]}"

    status = "quarantined" if trust_result["quarantine"] else "pending"

    proposal = {
        "proposal_id": proposal_id,
        "unpacked": unpacked,
        "trust": trust_result,
        "status": status,
        "dry_run": dry_run,
        "created_at": now,
    }

    if not dry_run and VAULT:
        _persist_proposal(VAULT, proposal)

    return proposal


def _persist_proposal(vault: str, proposal: dict[str, Any]) -> None:
    """Persist an S1→S2 proposal to the borg proposals directory."""
    d = os.path.join(vault, "borg", "proposals")
    os.makedirs(d, exist_ok=True)
    path = os.path.join(d, f"{proposal['proposal_id']}.json")
    with open(path, "w", encoding="utf-8") as f:
        json.dump(proposal, f, indent=2, ensure_ascii=False)


def ingest_artifact(
    source_path: str,
    dry_run: bool = True,
) -> dict[str, Any]:
    """Full S1 ingestion pipeline for a single artifact.

    Steps:
        1. Unpack artifact (checksum, classify, provenance)
        2. TRUST scan (license, secrets, injection, dangerous commands, etc.)
        3. Build S1→S2 proposal (pending or quarantined)

    Returns the proposal dict.

    """
    unpacked = unpack_artifact(source_path)
    trust_result = trust_scan_artifact(unpacked)
    proposal = build_ingestor_proposal(unpacked, trust_result, dry_run=dry_run)
    return proposal


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def parse_args():
    import argparse

    parser = argparse.ArgumentParser(
        description="Hermes Brain Borg S1 Ingestor — unpack, classify, trust-scan artifacts.",
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
    parser.add_argument(
        "--artifact",
        help="Path to artifact file to ingest",
    )
    return parser.parse_args()


def run_self_test():
    """Run built-in self-test suite."""
    print("🧪 Borg S1 Ingestor Self-Test Suite")
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

    def test_compute_checksum():
        c1 = compute_checksum("hello")
        c2 = compute_checksum("hello")
        c3 = compute_checksum("world")
        assert c1 == c2
        assert c1 != c3
        assert len(c1) == 64  # SHA-256 hex

    check("compute_checksum produces stable 64-char hex", test_compute_checksum)

    def test_detect_kind():
        assert _detect_kind("fires-on: PreToolUse\nmatcher: shell", "/x/hook.json") == "Trigger"
        assert _detect_kind("slash command: lint", "/x/lint.md") == "Skill"
        assert _detect_kind("mcp server config", "/x/mcp.json") == "Tool-binding"
        assert _detect_kind("rule file content", "/x/rule.txt") == "Policy"
        assert _detect_kind("test eval golden", "/x/test_eval.json") == "Resource"

    check("_detect_kind classifies artifacts", test_detect_kind)

    def test_unpack_artifact():
        import tempfile

        with tempfile.NamedTemporaryFile(
            mode="w", suffix=".json", delete=False, encoding="utf-8"
        ) as f:
            f.write('{"name": "test", "version": "1.0"}')
            tmp = f.name

        try:
            unpacked = unpack_artifact(tmp)
            assert unpacked["path"] == tmp
            assert len(unpacked["checksum"]) == 64
            assert unpacked["size"] > 0
            assert "detected_kind" in unpacked
            assert "detected_family" in unpacked
            assert "content" in unpacked
            assert "provenance" in unpacked
            assert "unpacked_at" in unpacked
        finally:
            os.unlink(tmp)

    check("unpack_artifact produces complete dict", test_unpack_artifact)

    def test_trust_scan_clean():
        unpacked = {
            "content": "clean content with no secrets",
            "detected_kind": "Resource",
            "detected_family": "F2",
            "provenance": {"license": "MIT"},
        }
        result = trust_scan_artifact(unpacked)
        assert result["passed"] is True
        assert result["quarantine"] is False

    check("trust_scan_artifact passes clean content", test_trust_scan_clean)

    def test_trust_scan_secrets():
        unpacked = {
            "content": 'api_key = "sk-1234567890abcdef1234567890abcdef"',
            "detected_kind": "Resource",
            "detected_family": "F2",
            "provenance": {},
        }
        result = trust_scan_artifact(unpacked)
        assert result["quarantine"] is True
        assert result["g2_required"] is True

    check("trust_scan_artifact quarantines secrets", test_trust_scan_secrets)

    def test_build_proposal():
        unpacked = {
            "path": "/test/hook.json",
            "checksum": "abc123",
            "size": 100,
            "detected_kind": "Trigger",
            "detected_family": "F1",
            "content": "fires-on: PreToolUse",
            "provenance": {},
            "unpacked_at": "2026-01-01T00:00:00Z",
        }
        trust_result = {
            "passed": True,
            "quarantine": False,
            "results": [],
            "g2_required": False,
        }
        proposal = build_ingestor_proposal(unpacked, trust_result, dry_run=True)
        assert "proposal_id" in proposal
        assert proposal["status"] == "pending"
        assert proposal["dry_run"] is True

    check("build_ingestor_proposal creates proposal", test_build_proposal)

    def test_ingest_artifact_dry_run():
        import tempfile

        with tempfile.NamedTemporaryFile(
            mode="w", suffix=".json", delete=False, encoding="utf-8"
        ) as f:
            f.write("clean content")
            tmp = f.name

        try:
            proposal = ingest_artifact(tmp, dry_run=True)
            assert "proposal_id" in proposal
            assert "unpacked" in proposal
            assert "trust" in proposal
            assert "status" in proposal
        finally:
            os.unlink(tmp)

    check("ingest_artifact dry_run produces proposal", test_ingest_artifact_dry_run)

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

    init_paths(args.vault)
    dry_run = not args.apply

    if not args.artifact:
        print(
            "Error: --artifact <path> is required.", file=sys.stderr
        )
        sys.exit(1)

    proposal = ingest_artifact(args.artifact, dry_run=dry_run)

    print(f"📥 S1 Ingestor — {args.artifact}")
    print(f"   Vault: {args.vault}")
    print(f"   Kind: {proposal['unpacked']['detected_kind']}")
    print(f"   Family: {proposal['unpacked']['detected_family']}")
    print(f"   Checksum: {proposal['unpacked']['checksum'][:12]}...")
    print(f"   Trust: {'PASS' if proposal['trust']['passed'] else 'QUARANTINE'}")
    print(f"   Status: {proposal['status']}")
    print(f"   Mode: {'DRY-RUN' if dry_run else 'APPLY'}")
    if dry_run:
        print("   Run with --apply to persist the proposal.")

    return 0


import sys  # noqa: E402

if __name__ == "__main__":
    sys.exit(main())
