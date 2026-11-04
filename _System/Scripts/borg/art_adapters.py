"""Hermes Brain — Borg ART Absorption Adapters (§5.1).

Generic adapters that convert source artifacts into typed catalog records:

| Source | → Records | Mapping |
|--------|-----------|---------|
| Hook/event config | Trigger (+ Policy if blocks) | fires-on; veto → conflicts-with |
| Slash command | Skill entry or Orchestration entry | Thin wrapper → alias |
| Script/binary | Resource + Tool-binding if callable | Static scan + sandbox → class/RV |
| MCP/function/API | Tool-binding | Signature, auth, rate limit, perms, effects |
| Permission/config | Policy | Split allow/deny/budget/escalation |
| Ref/doc/URL | Resource | Freshness, source, slot |
| Template/example | Resource | Slots → inputs; +/- tag |
| Test/eval | Oracle Resource ↔ Skill | Golden test; record limits |
| Memory | Resource | Scope, freshness, retention |
| Skill folder | Skill + Resources + Tool-bindings | Split by kind; description → activation |
| Workflow/playbook | Orchestration DAG | Parallel → antichains; explicit joins/failures |
| Subagent | Role + Loadout | Inline procedure → Skill |
| Rule file | Policy and/or Role default | One rule/record; absolutes → TACIT+ADV |
| Plugin/bundle | Container | Unpack; members derived-from |

All absorption rules:
- One record = one kind (split + link)
- Classify invocation (procedure / alias / orchestration entry)
- Keep verbatim original = golden = R0
- Sandbox-validate per kind
- Dedup within-kind first
- Propagate a risk profile (not one vague score)
- Resources never execute
- Merges leave redirects
- Pin harness version in envelope

Stdlib-only. Multi-harness compliant.
"""

import os
import json
from typing import Any

from .models import (
    make_record,
    init_role,
    init_skill,
    init_orchestration,
    init_trigger,
    init_policy,
    init_resource,
    init_tool_binding,
    KIND_INITIALIZERS,
    validate_record,
)
from . import trust_scanner

# Deferred vault path — resolved at runtime
VAULT = None


def init_paths(vault_path: str) -> None:
    """Resolve the vault root path from the given vault path."""
    global VAULT
    VAULT = os.path.abspath(vault_path)


# ---------------------------------------------------------------------------
# Generic adapters
# ---------------------------------------------------------------------------

def adapt_hook_event(config: dict[str, Any], pack: str = "", path: str = "") -> dict[str, Any]:
    """Hook/event config → Trigger record (+ Policy if blocks)."""
    event = config.get("event", "")
    matcher = config.get("matcher", "")
    action = config.get("action", "")
    blocking = config.get("blocking", False)

    rec = make_record(
        "Trigger",
        pref_label=f"Hook: {event}",
        family="F1",
        layer="L1",
        pack=pack,
        path=path,
    )
    rec["trigger"] = {
        "event": event,
        "matcher": matcher,
        "action": action,
        "blocking": blocking,
        "order": config.get("order", 0),
        "timeout": config.get("timeout", 0),
        "observed_block_behavior": "",
    }
    if blocking:
        rec["policy"] = {
            "deny": [f"Block on {event}"],
            "escalation": "Gate G2",
        }
    return rec


def adapt_slash_command(cmd: dict[str, Any], pack: str = "", path: str = "") -> dict[str, Any]:
    """Slash command → Skill entry or Orchestration entry."""
    name = cmd.get("name", "")
    args = cmd.get("args", [])
    description = cmd.get("description", "")

    rec = make_record(
        "Skill",
        pref_label=f"Slash command: {name}",
        family="F1",
        layer="L1",
        pack=pack,
        path=path,
    )
    rec["procedure"] = {
        "steps": [f"Parse args: {', '.join(args)}", f"Execute: {description}"],
        "io": {"input": "command arguments", "output": "command result"},
        "postconditions": [],
        "validation": [],
    }
    rec["target_model"] = ""
    return rec


def adapt_script_binary(spec: dict[str, Any], pack: str = "", path: str = "") -> list[dict[str, Any]]:
    """Script/binary → Resource + Tool-binding if callable.

    Returns list of records (may be 1 or 2).
    """
    name = spec.get("name", "")
    is_callable = spec.get("callable", False)

    records: list[dict[str, Any]] = []

    # Resource record (always)
    res = make_record(
        "Resource",
        pref_label=f"Script: {name}",
        family="F1",
        layer="L1",
        pack=pack,
        path=path,
    )
    res["resources"] = {
        "refs": [path] if path else [],
        "templates": [],
        "positive_examples": [],
        "negative_examples": [],
    }
    res["execution"] = {
        "side_effect_class": "Non-idempotent/external",
        "rv": "RV3",
        "blast": "",
        "conc_verdict": "SEQ-ONLY",
        "cost": 0.0,
        "latency": 0.0,
    }
    records.append(res)

    # Tool-binding if callable
    if is_callable:
        tb = make_record(
            "Tool-binding",
            pref_label=f"Tool-binding: {name}",
            family="F1",
            layer="L1",
            pack=pack,
            path=path,
        )
        tb["tool_binding"] = {
            "signature": spec.get("signature", ""),
            "auth": spec.get("auth", ""),
            "side_effect_class": "Non-idempotent/external",
            "rv": "RV3",
            "rate_limit": "",
            "idempotency_key": "",
            "sandbox": True,
        }
        records.append(tb)

    return records


def adapt_mcp_function(server_config: dict[str, Any], pack: str = "", path: str = "") -> dict[str, Any]:
    """MCP/function/API → Tool-binding record."""
    name = server_config.get("name", "")

    rec = make_record(
        "Tool-binding",
        pref_label=f"MCP tool: {name}",
        family="F1",
        layer="L1",
        pack=pack,
        path=path,
    )
    rec["tool_binding"] = {
        "signature": server_config.get("signature", ""),
        "auth": server_config.get("auth", ""),
        "side_effect_class": server_config.get("side_effect_class", "Pure"),
        "rv": server_config.get("rv", "RV0"),
        "rate_limit": server_config.get("rate_limit", ""),
        "idempotency_key": "",
        "sandbox": True,
    }
    return rec


def adapt_permission_config(perm: dict[str, Any], pack: str = "", path: str = "") -> dict[str, Any]:
    """Permission/config → Policy record."""
    name = perm.get("name", "")

    rec = make_record(
        "Policy",
        pref_label=f"Policy: {name}",
        family="F1",
        layer="L1",
        pack=pack,
        path=path,
    )
    rec["policy"] = {
        "allow": perm.get("allow", []),
        "deny": perm.get("deny", []),
        "budgets": perm.get("budgets", {}),
        "escalation": perm.get("escalation", ""),
        "tie_breaker_override": "",
    }
    return rec


def adapt_ref_doc(ref: dict[str, Any], pack: str = "", path: str = "") -> dict[str, Any]:
    """Ref/doc/URL → Resource record."""
    title = ref.get("title", "")

    rec = make_record(
        "Resource",
        pref_label=f"Reference: {title}",
        family="F2",
        layer="L1",
        pack=pack,
        path=path,
    )
    rec["resources"] = {
        "refs": [ref.get("url", ""), path],
        "templates": [],
        "positive_examples": [],
        "negative_examples": [],
    }
    rec["execution"] = {
        "side_effect_class": "Pure",
        "rv": "RV0",
        "blast": "",
        "conc_verdict": "PAR-SAFE",
        "cost": 0.0,
        "latency": 0.0,
    }
    return rec


def adapt_template_example(tmpl: dict[str, Any], pack: str = "", path: str = "") -> dict[str, Any]:
    """Template/example → Resource record with slots → inputs."""
    title = tmpl.get("title", "")

    rec = make_record(
        "Resource",
        pref_label=f"Template: {title}",
        family="F2",
        layer="L1",
        pack=pack,
        path=path,
    )
    rec["resources"] = {
        "refs": [path] if path else [],
        "templates": [tmpl.get("content", "")],
        "positive_examples": tmpl.get("positive_examples", []),
        "negative_examples": tmpl.get("negative_examples", []),
    }
    rec["execution"] = {
        "side_effect_class": "Pure",
        "rv": "RV0",
        "blast": "",
        "conc_verdict": "PAR-SAFE",
        "cost": 0.0,
        "latency": 0.0,
    }
    return rec


def adapt_test_eval(test: dict[str, Any], pack: str = "", path: str = "") -> dict[str, Any]:
    """Test/eval → Oracle Resource ↔ Skill link."""
    name = test.get("name", "")

    rec = make_record(
        "Resource",
        pref_label=f"Test oracle: {name}",
        family="F2",
        layer="L1",
        pack=pack,
        path=path,
    )
    rec["resources"] = {
        "refs": [path] if path else [],
        "templates": [],
        "positive_examples": [test.get("golden_test", "")],
        "negative_examples": [],
    }
    rec["execution"] = {
        "side_effect_class": "Read-only",
        "rv": "RV0",
        "blast": "",
        "conc_verdict": "PAR-SAFE",
        "cost": 0.0,
        "latency": 0.0,
    }
    return rec


def adapt_memory(mem: dict[str, Any], pack: str = "", path: str = "") -> dict[str, Any]:
    """Memory → Resource record."""
    name = mem.get("name", "")

    rec = make_record(
        "Resource",
        pref_label=f"Memory: {name}",
        family="F2",
        layer="L1",
        pack=pack,
        path=path,
    )
    rec["resources"] = {
        "refs": [path] if path else [],
        "templates": [],
        "positive_examples": [],
        "negative_examples": [],
    }
    rec["execution"] = {
        "side_effect_class": "Idempotent write",
        "rv": "RV1",
        "blast": "",
        "conc_verdict": "PAR-LOCKED",
        "cost": 0.0,
        "latency": 0.0,
    }
    return rec


def adapt_skill_folder(folder: dict[str, Any], pack: str = "", path: str = "") -> dict[str, Any]:
    """Skill folder → Skill + Resources + Tool-bindings (split by kind)."""
    name = folder.get("name", "")
    description = folder.get("description", "")

    rec = make_record(
        "Skill",
        pref_label=f"Skill: {name}",
        family="F3",
        layer="L1",
        pack=pack,
        path=path,
    )
    rec["procedure"] = {
        "steps": [description] if description else [],
        "io": {"input": "", "output": ""},
        "postconditions": [],
        "validation": [],
    }
    rec["target_model"] = ""
    rec["activation"] = description
    return rec


def adapt_workflow_playbook(wf: dict[str, Any], pack: str = "", path: str = "") -> dict[str, Any]:
    """Workflow/playbook → Orchestration DAG record."""
    name = wf.get("name", "")

    rec = make_record(
        "Orchestration",
        pref_label=f"Workflow: {name}",
        family="F3",
        layer="L2",
        pack=pack,
        path=path,
    )
    rec["orchestration"] = {
        "nodes": wf.get("nodes", []),
        "edges": wf.get("edges", []),
        "branches": wf.get("branches", []),
        "joins": wf.get("joins", []),
        "barriers": wf.get("barriers", []),
        "failure_containment": wf.get("failure_containment", ""),
    }
    return rec


def adapt_subagent(agent: dict[str, Any], pack: str = "", path: str = "") -> dict[str, Any]:
    """Subagent → Role + Loadout record."""
    name = agent.get("name", "")

    rec = make_record(
        "Role",
        pref_label=f"Role: {name}",
        family="F3",
        layer="L3",
        pack=pack,
        path=path,
    )
    rec["role"] = {
        "tone": agent.get("tone", ""),
        "decision_rules": agent.get("decision_rules", []),
        "loadout": agent.get("loadout", []),
        "isolation": agent.get("isolation", ""),
        "max_fan_out": agent.get("max_fan_out", 0),
        "preferred_model": agent.get("preferred_model", ""),
    }
    return rec


def adapt_rule_file(rule: dict[str, Any], pack: str = "", path: str = "") -> dict[str, Any]:
    """Rule file → Policy and/or Role default record."""
    name = rule.get("name", "")

    rec = make_record(
        "Policy",
        pref_label=f"Rule: {name}",
        family="F1",
        layer="L1",
        pack=pack,
        path=path,
    )
    rec["policy"] = {
        "allow": rule.get("allow", []),
        "deny": rule.get("deny", []),
        "budgets": {},
        "escalation": "",
        "tie_breaker_override": "",
    }
    return rec


def adapt_plugin_bundle(bundle: dict[str, Any], pack: str = "", path: str = "") -> list[dict[str, Any]]:
    """Plugin/bundle → Container record, unpack members.

    Returns list of records (container + unpacked members).
    """
    name = bundle.get("name", "")

    records: list[dict[str, Any]] = []

    # Container record
    container = make_record(
        "Orchestration",
        pref_label=f"Plugin bundle: {name}",
        family="F3",
        layer="L2",
        pack=pack,
        path=path,
    )
    container["orchestration"] = {
        "nodes": bundle.get("members", []),
        "edges": [],
        "branches": [],
        "joins": [],
        "barriers": [],
        "failure_containment": "",
    }
    records.append(container)

    # Unpack members as derived-from
    for member in bundle.get("members", []):
        member_rec = make_record(
            "Skill",
            pref_label=f"Member: {member}",
            family="F3",
            layer="L1",
            pack=pack,
            path=path,
        )
        member_rec["audit"] = {
            "advice": [],
            "adrs": [],
            "web_facts": [],
            "gaps": [],
            "analogies": [],
            "reception": "",
            "articulation": "",
            "sunset": "",
        }
        records.append(member_rec)

    return records


# ---------------------------------------------------------------------------
# Absorption pipeline entry point
# ---------------------------------------------------------------------------

ADAPTERS = {
    "hook": adapt_hook_event,
    "slash_command": adapt_slash_command,
    "script_binary": adapt_script_binary,
    "mcp_function": adapt_mcp_function,
    "permission_config": adapt_permission_config,
    "ref_doc": adapt_ref_doc,
    "template_example": adapt_template_example,
    "test_eval": adapt_test_eval,
    "memory": adapt_memory,
    "skill_folder": adapt_skill_folder,
    "workflow_playbook": adapt_workflow_playbook,
    "subagent": adapt_subagent,
    "rule_file": adapt_rule_file,
    "plugin_bundle": adapt_plugin_bundle,
}


def absorb_artifact(
    source_type: str,
    artifact: dict[str, Any],
    pack: str = "",
    path: str = "",
    content: str = "",
    dry_run: bool = True,
) -> dict[str, Any]:
    """Absorb a single artifact through the appropriate adapter + TRUST scan.

    Returns:
        {
            "records": list[dict],
            "trust": dict,           # from trust_scanner.scan_record
            "quarantine": bool,
            "g2_required": bool,
        }

    """
    adapter = ADAPTERS.get(source_type)
    if not adapter:
        return {
            "records": [],
            "trust": trust_scanner.scan_record({}, content),
            "quarantine": True,
            "g2_required": True,
            "error": f"Unknown source type: {source_type}",
        }

    # Run adapter
    if source_type in ("script_binary", "plugin_bundle"):
        records = adapter(artifact, pack=pack, path=path)
    else:
        records = [adapter(artifact, pack=pack, path=path)]

    # Validate each record
    for rec in records:
        errors = validate_record(rec)
        if errors:
            return {
                "records": records,
                "trust": trust_scanner.scan_record({}, content),
                "quarantine": True,
                "g2_required": True,
                "error": f"Validation errors: {'; '.join(errors)}",
            }

    # TRUST scan on the primary record (first record)
    primary = records[0] if records else {}
    trust_result = trust_scanner.scan_record(primary, content)

    return {
        "records": records,
        "trust": trust_result,
        "quarantine": trust_result["quarantine"],
        "g2_required": trust_result["g2_required"],
    }
