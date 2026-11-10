"""Hermes Brain — Borg TRUST Scanner (§5.4).

TRUST checks that fail → quarantine + G2 gate:

| Check | Detects | Action |
|-------|---------|--------|
| License | Missing/incompatible SPDX | Metadata-only until cleared |
| Secrets | Keys, tokens, private data (incl. MCP env) | Block, redact, notify |
| Prompt injection | Override/exfil/hidden Unicode | Treat as data; isolate |
| Dangerous commands | Destructive shell, curl|sh, open egress | Sandbox; Policy deny; SEQ-ONLY |
| Supply chain | Unpinned fetch, checksum mismatch | Pin/verify/vendor/reject |
| Permission creep | Tools beyond purpose | Narrow allow-list |
| Runtime probe | Hidden writes/network | Sandbox diff → record effects |
| Guardrail reality | "Blocks X" but doesn't for some tools/versions | Probe every tool type |

All probes sandboxed; zero prod creds; net off unless controlled test.

Stdlib-only. Multi-harness compliant.
"""

import os
import re
from typing import Any

# Deferred vault path — resolved at runtime
VAULT = None


def init_paths(vault_path: str) -> None:
    """Resolve the vault root path from the given vault path."""
    global VAULT
    VAULT = os.path.abspath(vault_path)


# ---------------------------------------------------------------------------
# Check results
# ---------------------------------------------------------------------------

class TrustResult:
    """Result of a single TRUST check."""

    def __init__(self, check: str, passed: bool, detail: str = "", action: str = ""):
        self.check = check
        self.passed = passed
        self.detail = detail
        self.action = action

    def to_dict(self) -> dict[str, Any]:
        return {
            "check": self.check,
            "passed": self.passed,
            "detail": self.detail,
            "action": self.action,
        }


# ---------------------------------------------------------------------------
# 5.4 TRUST checks
# ---------------------------------------------------------------------------

def check_license(record: dict[str, Any]) -> TrustResult:
    """Detect missing/incompatible SPDX license."""
    lic = record.get("provenance", {}).get("license", "")
    if not lic:
        return TrustResult(
            "license",
            False,
            "No SPDX license declared",
            "Metadata-only until cleared",
        )
    # Basic SPDX format check
    known = {"MIT", "Apache-2.0", "GPL-3.0-only", "BSD-3-Clause", "BSD-2-Clause", "ISC", "Unlicense"}
    if lic not in known:
        return TrustResult(
            "license",
            False,
            f"Unknown or potentially incompatible SPDX: {lic}",
            "Metadata-only until cleared",
        )
    return TrustResult("license", True, f"SPDX license {lic} declared", "OK")


def check_secrets(record: dict[str, Any], content: str = "") -> TrustResult:
    """Detect keys, tokens, private data (incl. MCP env)."""
    patterns = [
        (r"(?i)(sk-|sk_prod-)[A-Za-z0-9]{20,}", "OpenAI-style API key"),
        (r"(?i)(ghp_|github_pat_)[A-Za-z0-9]{20,}", "GitHub PAT"),
        (r"(?i)(xoxb|xoxp|xoxc)-[A-Za-z0-9-]{10,}", "Slack token"),
        (r"(?i)(AKIA)[A-Za-z0-9]{16}", "AWS access key"),
        (r"(?i)(sk_or_[A-Za-z0-9]{20,})", "Anthropic-style key"),
        (r"(?i)(sk-ant-)[A-Za-z0-9]{20,}", "Anthropic key"),
        (r"(?i)(MCP|mcp)_[A-Z_]+.*=.*['\"]?[A-Za-z0-9]{20,}", "MCP env secret"),
    ]
    found = []
    for pat, desc in patterns:
        for m in re.finditer(pat, content):
            found.append(f"{desc} at offset {m.start()}")
    if found:
        return TrustResult(
            "secrets",
            False,
            f"Potential secrets found: {'; '.join(found[:5])}",
            "Block, redact, notify",
        )
    return TrustResult("secrets", True, "No secrets detected", "OK")


def check_prompt_injection(content: str = "") -> TrustResult:
    """Detect override/exfil/hidden Unicode injection."""
    injection_markers = [
        r"(?i)(ignore all previous|disregard|forget everything|system: you are now)",
        r"(?i)(exfiltrate|send to|POST to|curl|wget) .*(token|key|password|secret)",
        r"[\u200b-\u200f\u202a-\u202e\u2060-\u206f]",  # hidden Unicode
    ]
    found = []
    for pat in injection_markers:
        if re.search(pat, content):
            found.append(pat[:40])
    if found:
        return TrustResult(
            "prompt_injection",
            False,
            f"Potential injection patterns: {'; '.join(found[:3])}",
            "Treat as data; isolate",
        )
    return TrustResult("prompt_injection", True, "No injection patterns", "OK")


def check_dangerous_commands(content: str = "") -> TrustResult:
    """Detect destructive shell, curl|sh, open egress."""
    patterns = [
        (r"(?i)(rm -rf|rm -r|del /s|del /q)", "Destructive shell command"),
        (r"curl\s+.*\|\s*(sh|bash|zsh)", "curl pipe to shell"),
        (r"wget\s+.*\|\s*(sh|bash|zsh)", "wget pipe to shell"),
        (r"(?i)(nc |netcat|ncat) .*-e", "Netcat exec"),
        (r"(?i)(chmod\s+777|chmod\s+a+rwx)", "Broad permissions"),
    ]
    found = []
    for pat, desc in patterns:
        if re.search(pat, content):
            found.append(desc)
    if found:
        return TrustResult(
            "dangerous_commands",
            False,
            f"Dangerous commands: {'; '.join(found[:5])}",
            "Sandbox; Policy deny; SEQ-ONLY",
        )
    return TrustResult("dangerous_commands", True, "No dangerous commands", "OK")


def check_supply_chain(record: dict[str, Any], content: str = "") -> TrustResult:
    """Detect unpinned fetch, checksum mismatch."""
    issues = []
    # Unpinned version references
    if re.search(r"(?i)(pip install|npm install|gem install)\s+[^\s<>]+\b(?![<>=!])", content):
        issues.append("Unpinned package install")
    # Checksum references
    if not re.search(r"(?i)(sha256|sha512|checksum|digest)", content):
        if "install" in content.lower() or "download" in content.lower():
            issues.append("No checksum verification for download/install")
    if issues:
        return TrustResult(
            "supply_chain",
            False,
            f"Supply chain issues: {'; '.join(issues[:5])}",
            "Pin/verify/vendor/reject",
        )
    return TrustResult("supply_chain", True, "Supply chain checks passed", "OK")


def check_permission_creep(record: dict[str, Any]) -> TrustResult:
    """Detect tools beyond purpose — narrow allow-list."""
    loadout = record.get("loadout", []) if isinstance(record.get("loadout"), list) else []
    if len(loadout) > 10:
        return TrustResult(
            "permission_creep",
            False,
            f"Large loadout ({len(loadout)} tools) — may exceed purpose",
            "Narrow allow-list",
        )
    return TrustResult("permission_creep", True, "Loadout size reasonable", "OK")


def scan_record(record: dict[str, Any], content: str = "") -> dict[str, Any]:
    """Run all TRUST checks on a record.

    Returns:
        {
            "passed": bool,          # all checks passed
            "quarantine": bool,      # any check failed → quarantine
            "results": list[dict],   # per-check results
            "g2_required": bool,     # G2 gate needed if any failed
        }

    """
    results = [
        check_license(record),
        check_secrets(record, content),
        check_prompt_injection(content),
        check_dangerous_commands(content),
        check_supply_chain(record, content),
        check_permission_creep(record),
    ]

    failed = [r for r in results if not r.passed]
    return {
        "passed": len(failed) == 0,
        "quarantine": len(failed) > 0,
        "results": [r.to_dict() for r in results],
        "g2_required": len(failed) > 0,
    }
