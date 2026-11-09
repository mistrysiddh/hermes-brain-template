"""Hermes Brain — Borg Record Schema and 7 Kinds.

Implements the record schema ⟨M,R,C,P,T,N,X,E,D⟩ (§3.3) and the seven
kinds (§3.2): Role, Skill, Orchestration, Trigger, Policy, Resource,
Tool-binding.

Every record has exactly one primary kind. Identity fields, labels,
provenance, and audit fields are universal across all kinds.

Stdlib-only. Multi-harness compliant.
"""

from datetime import datetime
from typing import Any


# ---------------------------------------------------------------------------
# Identity / universal fields
# ---------------------------------------------------------------------------

def make_record(
    kind: str,
    pref_label: str,
    *,
    family: str = "",
    layer: str = "",
    semver: str = "0.1.0",
    status: str = "draft",
    pack: str = "",
    path: str = "",
    commit: str = "",
    checksum: str = "",
    license_id: str = "",
    owner: str = "",
    alt_labels: list[str] | None = None,
    old_ids: list[str] | None = None,
) -> dict[str, Any]:
    """Create a new record with universal identity fields.

    Returns a dict with all universal fields initialized and kind-specific
    fields set to empty defaults.
    """
    now = datetime.utcnow().isoformat() + "Z"
    record: dict[str, Any] = {
        # Identity
        "id": "",
        "semver": semver,
        "status": status,          # draft | incubating | active | deprecated | quarantined | rejected
        "kind": kind,              # Role | Skill | Orchestration | Trigger | Policy | Resource | Tool-binding
        "family": family,          # F1 | F2 | F3
        "layer": layer,            # L0 | L1 | L2 | L3
        # Labels
        "prefLabel": pref_label,
        "altLabels": alt_labels or [],
        "oldIDs": old_ids or [],   # redirects
        # Provenance
        "provenance": {
            "pack": pack,
            "path": path,
            "commit": commit,
            "checksum": checksum,
            "license": license_id,
            "owner": owner,
            "dates": {"created": now, "modified": now},
            "ancestry_cluster": "",
        },
        # C — Conditions
        "conditions": {
            "jtbd": "",            # Jobs-To-Be-Done: situation + motivation + outcome
            "activation": "",
            "anti_conditions": [],
            "preconditions": [],
        },
        # M — Procedure
        "procedure": {
            "steps": [],
            "io": {"input": "", "output": ""},
            "postconditions": [],
            "validation": [],
        },
        # R — Resources
        "resources": {
            "refs": [],
            "templates": [],
            "positive_examples": [],
            "negative_examples": [],
        },
        # P — Policy
        "policy": {
            "per_skill_constraints": [],
            "governing_policies": [],
        },
        # T — Target
        "target": {
            "transfer_results": [],
            "envelope": "",
            "per_model_variants": [],
        },
        # N — Nuances
        "nuances": {
            "cues": [],
            "thresholds": [],
            "threshold_source": "",
            "exceptions": [],
            "when_not": "",
            "quality_criteria": [],
        },
        # X — Execution
        "execution": {
            "side_effect_class": "Pure",       # Pure | Read-only | Idempotent write | Non-idempotent/external
            "rv": "RV0",                       # RV0 | RV1 | RV2 | RV3 | RV4
            "blast": "",
            "conc_verdict": "UNMEASURED",      # PAR-SAFE | PAR-LOCKED | SEQ-ONLY | UNMEASURED
            "cost": 0.0,
            "latency": 0.0,
        },
        # E — Evidence
        "evidence": {
            "tests": [],
            "traces": [],
            "spans": [],
            "per_field_labels": {},
            "confidence": 0.0,
            "tested_env": "",
        },
        # D — Decision card
        "decision_card": {
            "use_avoid": "",
            "prefer": "",
            "benefit_cost": "",
            "side_effect_ledger": "",
            "rv_blast": "",
            "pre_mitigations": "",
            "envelope": "",
            "autonomy": "ask",                    # act | act+notify | ask | gate — default: ask
            "evidence_summary": "",
        },
        # Audit
        "audit": {
            "advice": [],
            "adrs": [],
            "web_facts": [],
            "gaps": [],
            "analogies": [],
            "reception": "",
            "articulation": "",
            "sunset": "",
        },
    }
    return record


# ---------------------------------------------------------------------------
# Kind-specific field initializers
# ---------------------------------------------------------------------------

def init_role() -> dict[str, Any]:
    """Role: persona + judgment + permissions + loadout (not a procedure)."""
    return {
        "tone": "",
        "decision_rules": [],
        "loadout": [],
        "isolation": "",
        "max_fan_out": 0,
        "preferred_model": "",
    }


def init_skill() -> dict[str, Any]:
    """Skill: reusable procedure with an interface (not router or persona)."""
    return {
        "procedure": {"steps": [], "io": {"input": "", "output": ""}, "postconditions": [], "validation": []},
        "target_model": "",
    }


def init_orchestration() -> dict[str, Any]:
    """Orchestration: routed composition of Skills/Roles (not a mega-skill)."""
    return {
        "nodes": [],
        "edges": [],
        "branches": [],
        "joins": [],
        "barriers": [],
        "failure_containment": "",
    }


def init_trigger() -> dict[str, Any]:
    """Trigger: event → action (not a Skill)."""
    return {
        "event": "",
        "matcher": "",
        "action": "",
        "blocking": False,
        "order": 0,
        "timeout": 0,
        "observed_block_behavior": "",
    }


def init_policy() -> dict[str, Any]:
    """Policy: standing constraint (not per-skill advice)."""
    return {
        "allow": [],
        "deny": [],
        "budgets": {},
        "escalation": "",
        "tie_breaker_override": "",
    }


def init_resource() -> dict[str, Any]:
    """Resource: non-executable content (not a callable tool)."""
    return {
        "media_type": "",
        "slots": [],
        "freshness": "",
        "dikw": "",                 # Data | Information | Knowledge | Wisdom
        "executable": False,
    }


def init_tool_binding() -> dict[str, Any]:
    """Tool-binding: callable declaration (not tool documentation)."""
    return {
        "signature": "",
        "auth": "",
        "side_effect_class": "Pure",
        "rv": "RV0",
        "rate_limit": "",
        "idempotency_key": "",
        "sandbox": False,
    }


KIND_INITIALIZERS = {
    "Role": init_role,
    "Skill": init_skill,
    "Orchestration": init_orchestration,
    "Trigger": init_trigger,
    "Policy": init_policy,
    "Resource": init_resource,
    "Tool-binding": init_tool_binding,
}

VALID_KINDS = list(KIND_INITIALIZERS.keys())
VALID_FAMILIES = ["F1", "F2", "F3"]
VALID_LAYERS = ["L0", "L1", "L2", "L3"]
VALID_STATUSES = ["draft", "incubating", "active", "deprecated", "quarantined", "rejected"]
VALID_RV = ["RV0", "RV1", "RV2", "RV3", "RV4"]
VALID_CONC = ["PAR-SAFE", "PAR-LOCKED", "SEQ-ONLY", "UNMEASURED"]
VALID_SIDE_EFFECT = ["Pure", "Read-only", "Idempotent write", "Non-idempotent/external"]
VALID_AUTONOMY = ["act", "act+notify", "ask", "gate"]


def validate_record(record: dict[str, Any]) -> list[str]:
    """Validate a record against kind-specific constraints.

    Returns a list of error messages (empty if valid).
    """
    errors: list[str] = []

    kind = record.get("kind", "")
    if kind not in VALID_KINDS:
        errors.append(f"Invalid kind: {kind!r} (must be one of {VALID_KINDS})")
        return errors

    if record.get("family") not in VALID_FAMILIES:
        errors.append(f"Invalid family: {record.get('family')!r}")

    if record.get("layer") not in VALID_LAYERS:
        errors.append(f"Invalid layer: {record.get('layer')!r}")

    if record.get("status") not in VALID_STATUSES:
        errors.append(f"Invalid status: {record.get('status')!r}")

    exec_info = record.get("execution", {})
    if exec_info.get("rv") not in VALID_RV:
        errors.append(f"Invalid RV: {exec_info.get('rv')!r}")

    if exec_info.get("conc_verdict") not in VALID_CONC:
        errors.append(f"Invalid conc_verdict: {exec_info.get('conc_verdict')!r}")

    if exec_info.get("side_effect_class") not in VALID_SIDE_EFFECT:
        errors.append(f"Invalid side_effect_class: {exec_info.get('side_effect_class')!r}")

    dc = record.get("decision_card", {})
    if dc.get("autonomy") not in VALID_AUTONOMY:
        errors.append(f"Invalid autonomy: {dc.get('autonomy')!r}")

    return errors
