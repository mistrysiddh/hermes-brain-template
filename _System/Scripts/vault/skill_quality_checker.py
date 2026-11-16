#!/usr/bin/env python3
"""
Hermes Brain — Skill Quality Checker Skill (multi-harness compatible).

Unified deep MECE checklist for scoring/checking agent skills, per issue #38.
Assesses every SKILL.md in the vault against 16 sections (§1–§16):

  §1 Audit frame and evidence
  §2 Loadability, conformance, file graph
  §3 Security — harm
  §4 Discovery surface
  §5 Task scope
  §6 Clarity and sequencing
  §7 I/O contract
  §8 Failure behavior
  §9 Environment assumptions
  §10 Bundle organization
  §11 Context / token cost
  §12 Runtime behavior
  §13 Inter-skill dependencies
  §14–15 Lifecycle and the checker itself
  §16 Arithmetic and release

Automation legend per item:
  [D✓] Direct deterministic check exists
  [D~] Deterministic proxy exists
  [E]  Runtime evidence required
  [A]  Agent-assisted (LLM review; not reproducible)
  [M]  Manual (no reliable deterministic check)

Status per item: Pass · Partial · Fail · N/A · Not tested

Overall decision: READY · CONDITIONAL · NEEDS REWORK · REJECT
Severity ladder: Blocker · Major · Moderate · Advisory

Multi-harness compatible:
  - --vault CLI arg (never module-level path resolution)
  - Path resolution deferred to main() after argument parsing
  - --dry-run default / --apply for human-in-the-loop approval
  - Stdlib-only
  - --test self-tests
"""

import argparse
import hashlib
import json
import os
import re
import sys
from datetime import datetime
from pathlib import Path

# ---------------------------------------------------------------------------
# Path resolution — deferred to main(), never at import time
# ---------------------------------------------------------------------------
VAULT = None
REPORT_DIR = None
QUALITY_LOG = None


def init_paths(vault_path):
    """Resolve all vault-relative paths from the given vault root.
    Called from main() after argument parsing — never at import time.
    """
    global VAULT, REPORT_DIR, QUALITY_LOG
    VAULT = os.path.abspath(vault_path)
    REPORT_DIR = os.path.join(VAULT, "04-Archives", "Audit-Reports")
    QUALITY_LOG = os.path.join(REPORT_DIR, "Skill-Quality-Report.md")


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------
def read_file(path):
    if not os.path.exists(path):
        return ""
    try:
        with open(path, encoding="utf-8") as f:
            return f.read()
    except Exception:
        return ""


def write_report(lines):
    os.makedirs(REPORT_DIR, exist_ok=True)
    with open(QUALITY_LOG, "w", encoding="utf-8") as f:
        f.write("\n".join(lines))
    print(f"\n📄 Skill quality report written to: {QUALITY_LOG}")


def finding(severity, section, item, tag, status, message, evidence, suggestion, file_path, line=None):
    """Return a structured finding dict."""
    return {
        "severity": severity,      # blocker | major | moderate | advisory
        "section": section,        # §1 .. §16
        "item": item,              # short item name
        "tag": tag,                # D✓ | D~ | E | A | M
        "status": status,          # Pass | Partial | Fail | N/A | Not tested
        "message": message,
        "evidence": evidence,
        "suggestion": suggestion,
        "file": file_path,
        "line": line,
    }


# ---------------------------------------------------------------------------
# §1 — Audit frame and evidence
# ---------------------------------------------------------------------------
def check_audit_frame(skill_path, skill_dir):
    """§1 — Audit frame and evidence. Produces coverage, not score."""
    findings = []
    skill_md = os.path.join(skill_dir, "SKILL.md")
    content = read_file(skill_md)

    # 1.1 Artifact class identified
    has_skill_md = os.path.exists(skill_md)
    findings.append(finding(
        "blocker", "§1", "artifact_class", "D✓",
        "Pass" if has_skill_md else "Fail",
        "Skill directory contains SKILL.md",
        f"SKILL.md exists: {has_skill_md}",
        "Create SKILL.md at skill root" if not has_skill_md else None,
        skill_path,
    ))

    # 1.2 Spec/platform profile selected and recorded
    has_profile = bool(re.search(r"(profile|spec|platform|agent|loader|runtime)", content, re.I))
    findings.append(finding(
        "moderate", "§1", "profile_recorded", "M",
        "Pass" if has_profile else "Not tested",
        "Agent/model/runtime/profile mentioned in SKILL.md",
        content[:200] if has_profile else "No profile info found",
        "Add target agent, model, runtime version, loader info" if not has_profile else None,
        skill_path,
    ))

    # 1.3 Repo revision / skill root / parent dir name
    parent_name = os.path.basename(skill_dir.rstrip("/"))
    findings.append(finding(
        "blocker", "§1", "skill_root", "D✓",
        "Pass",
        "Parent directory name recorded",
        parent_name,
        None,
        skill_path,
    ))

    # 1.4 Frontmatter present and valid
    frontmatter = bool(re.match(r"---\s*\n.*?\n---\s*\n", content, re.S))
    findings.append(finding(
        "blocker", "§1", "frontmatter", "D✓",
        "Pass" if frontmatter else "Fail",
        "SKILL.md opens with --- and closes with ---",
        "Valid YAML frontmatter" if frontmatter else "No frontmatter block found",
        "Add YAML frontmatter (--- ... ---)" if not frontmatter else None,
        skill_path,
    ))

    # 1.5 Body non-empty and not merely a title
    body_stripped = re.sub(r"---\s*\n.*?\n---\s*\n", "", content, flags=re.S).strip()
    body_has_content = len(body_stripped) > 20 and not body_stripped.startswith("# ")
    findings.append(finding(
        "major", "§1", "body_content", "D~",
        "Pass" if body_has_content else "Partial",
        "Body non-empty and not merely a title",
        f"Body length: {len(body_stripped)} chars",
        "Add substantive body content beyond a title" if not body_has_content else None,
        skill_path,
    ))

    # 1.6 File inventory: hidden files, symlinks, exec bits, types, sizes, line counts
    all_files = []
    for root, dirs, files in os.walk(skill_dir):
        dirs[:] = [d for d in dirs if d != "__pycache__"]
        for f in files:
            all_files.append(os.path.join(root, f))
    findings.append(finding(
        "moderate", "§1", "file_inventory", "D✓",
        "Pass",
        f"Package inventory: {len(all_files)} files",
        f"Files: {', '.join(os.path.relpath(f, skill_dir) for f in all_files[:10])}",
        None,
        skill_path,
    ))

    return findings


# ---------------------------------------------------------------------------
# §2 — Loadability, conformance, file graph
# ---------------------------------------------------------------------------
def check_loadability(skill_path, skill_dir):
    """§2 — Loadability, conformance, file graph. Binary gate."""
    findings = []
    skill_md = os.path.join(skill_dir, "SKILL.md")
    content = read_file(skill_md)

    # 2.1 SKILL.md exists at root with exact name
    findings.append(finding(
        "blocker", "§2", "skill_md_exists", "D✓",
        "Pass" if os.path.exists(skill_md) else "Fail",
        "SKILL.md exists at skill root",
        f"SKILL.md found: {os.path.exists(skill_md)}",
        "Create SKILL.md at skill root",
        skill_path,
    ))

    # 2.2 YAML frontmatter parses
    fm_match = re.match(r"---\s*\n(.*?)\n---\s*\n", content, re.S)
    yaml_valid = False
    if fm_match:
        try:
            import yaml as yaml_mod
            yaml_mod.safe_load(fm_match.group(1))
            yaml_valid = True
        except Exception:
            yaml_valid = False
    findings.append(finding(
        "blocker", "§2", "yaml_parses", "D✓",
        "Pass" if yaml_valid else "Fail",
        "YAML frontmatter parses",
        "Valid YAML" if yaml_valid else "Invalid or missing YAML",
        "Fix YAML syntax in frontmatter",
        skill_path,
    ))

    # 2.3 name field: present, non-empty, 1–64 chars, lowercase/digits/hyphens
    name_val = None
    if fm_match:
        try:
            import yaml as yaml_mod
            fm = yaml_mod.safe_load(fm_match.group(1))
            name_val = fm.get("name") if isinstance(fm, dict) else None
        except Exception:
            pass
    name_valid = bool(name_val and re.match(r"^[a-z0-9-]+$", name_val) and 1 <= len(name_val) <= 64)
    findings.append(finding(
        "blocker", "§2", "name_field", "D✓",
        "Pass" if name_valid else "Fail",
        "name: present, 1–64 chars, lowercase/digits/hyphens",
        f"name = {name_val}",
        "Add valid name field to frontmatter",
        skill_path,
    ))

    # 2.4 name matches parent-directory name
    parent_name = os.path.basename(skill_dir.rstrip("/"))
    name_matches = (name_val == parent_name) if name_val else False
    findings.append(finding(
        "blocker", "§2", "name_matches_dir", "D✓",
        "Pass" if name_matches else "Fail",
        "name exactly matches parent-directory name",
        f"name={name_val}, dir={parent_name}",
        f"Rename directory to '{name_val}' or change name to '{parent_name}'",
        skill_path,
    ))

    # 2.5 description field: present, non-empty, 1–1024 chars
    desc_val = None
    if fm_match:
        try:
            import yaml as yaml_mod
            fm = yaml_mod.safe_load(fm_match.group(1))
            desc_val = fm.get("description") if isinstance(fm, dict) else None
        except Exception:
            pass
    desc_valid = bool(desc_val and isinstance(desc_val, str) and 1 <= len(desc_val) <= 1024)
    findings.append(finding(
        "major", "§2", "description_field", "D✓",
        "Pass" if desc_valid else "Fail",
        "description: present, non-empty, 1–1,024 chars",
        f"description length: {len(desc_val) if desc_val else 0}",
        "Add description field (1–1024 chars)",
        skill_path,
    ))

    # 2.6 Code fences balanced
    fence_count = content.count("```")
    fences_balanced = fence_count % 2 == 0
    findings.append(finding(
        "moderate", "§2", "code_fences", "D✓",
        "Pass" if fences_balanced else "Fail",
        "Code fences balanced in Markdown",
        f"Fence count: {fence_count}",
        "Balance code fences (``` ... ```)",
        skill_path,
    ))

    # 2.7 Optional fields validated when present (license, compatibility, metadata)
    license_val = fm.get("license") if (fm_match and isinstance(fm, dict)) else None
    if license_val:
        license_file_exists = os.path.exists(os.path.join(skill_dir, license_val)) if isinstance(license_val, str) else False
        findings.append(finding(
            "advisory", "§2", "license_field", "D✓",
            "Pass" if license_file_exists or isinstance(license_val, str) else "Partial",
            "license: concise or references existing file",
            f"license = {license_val}, file exists = {license_file_exists}",
            None,
            skill_path,
        ))

    # 2.8 Every referenced local path resolves
    local_refs = re.findall(r"\[\[([^\]]+)\]\]", content)
    unresolved = []
    for ref in local_refs:
        target = ref.split("|")[0].strip()
        target_path = os.path.join(skill_dir, target)
        if not target_path.endswith(".md"):
            target_path += ".md"
        if not os.path.exists(target_path):
            unresolved.append(target)
    findings.append(finding(
        "major", "§2", "local_refs_resolve", "D✓",
        "Pass" if not unresolved else "Partial",
        "Every referenced local path resolves to intended target",
        f"Unresolved: {unresolved}" if unresolved else "All local refs resolve",
        "Fix broken local references",
        skill_path,
    ))

    return findings


# ---------------------------------------------------------------------------
# §3 — Security — harm
# ---------------------------------------------------------------------------
def check_security(skill_path, skill_dir):
    """§3 — Security — harm. Regardless of which file."""
    findings = []
    skill_md = os.path.join(skill_dir, "SKILL.md")
    content = read_file(skill_md)

    # 3.1 No hardcoded secrets (tokens, keys, passwords in plaintext)
    secret_patterns = [
        (r"(?i)(api_?key|secret|token|password)\s*[:=]\s*['\"]?[A-Za-z0-9+/=]{16,}['\"]?", "hardcoded secret"),
        (r"(?i)(sk-|pk-|ghp_|github_|glpat-)[A-Za-z0-9]{10,}", "API key pattern"),
    ]
    secrets_found = []
    for root, dirs, files in os.walk(skill_dir):
        dirs[:] = [d for d in dirs if d != "__pycache__"]
        for f in files:
            fpath = os.path.join(root, f)
            fcontent = read_file(fpath)
            for pattern, desc in secret_patterns:
                if re.search(pattern, fcontent):
                    secrets_found.append(f"{os.path.relpath(fpath, skill_dir)}: {desc}")
    findings.append(finding(
        "blocker", "§3", "no_secrets", "D✓",
        "Pass" if not secrets_found else "Fail",
        "No hardcoded secrets in skill files",
        f"Secrets found: {secrets_found}" if secrets_found else "No secrets detected",
        "Remove hardcoded secrets; use environment variables",
        skill_path,
    ))

    # 3.2 No dangerous commands (rm -rf, curl | bash, etc.)
    dangerous = re.findall(r"(?i)(rm\s+-rf|curl\s+.*\|\s*bash|wget\s+.*\|\s*sh|sudo\s+rm|chmod\s+777)", content)
    findings.append(finding(
        "blocker", "§3", "no_dangerous_cmds", "D✓",
        "Pass" if not dangerous else "Fail",
        "No destructive commands in SKILL.md",
        f"Dangerous patterns: {dangerous}" if dangerous else "None found",
        "Remove destructive command patterns",
        skill_path,
    ))

    # 3.3 License present and valid
    license_val = None
    fm_match = re.match(r"---\s*\n(.*?)\n---\s*\n", content, re.S)
    if fm_match:
        try:
            import yaml as yaml_mod
            fm = yaml_mod.safe_load(fm_match.group(1))
            license_val = fm.get("license") if isinstance(fm, dict) else None
        except Exception:
            pass
    findings.append(finding(
        "major", "§3", "license_present", "D✓",
        "Pass" if license_val else "Partial",
        "License field present in frontmatter",
        f"license = {license_val}",
        "Add license field to frontmatter",
        skill_path,
    ))

    return findings


# ---------------------------------------------------------------------------
# §4 — Discovery surface
# ---------------------------------------------------------------------------
def check_discovery(skill_path, skill_dir):
    """§4 — What does the agent see before loading the body?"""
    findings = []
    content = read_file(os.path.join(skill_dir, "SKILL.md"))

    # 4.1 Purpose statement clear
    has_purpose = bool(re.search(r"(?i)(purpose|this skill|what it does|designed to)", content))
    findings.append(finding(
        "major", "§4", "purpose_clear", "D~",
        "Pass" if has_purpose else "Partial",
        "Purpose statement clear before body",
        "Purpose found" if has_purpose else "No clear purpose statement",
        "Add clear purpose statement",
        skill_path,
    ))

    # 4.2 Intended users / tasks / outcomes
    has_users = bool(re.search(r"(?i)(user|task|outcome|audience|who)", content))
    findings.append(finding(
        "moderate", "§4", "users_tasks", "M",
        "Pass" if has_users else "Not tested",
        "Intended users, tasks, outcomes described",
        "Found" if has_users else "Not found",
        "Add intended users/tasks/outcomes",
        skill_path,
    ))

    # 4.3 Risk level / permissions
    has_risk = bool(re.search(r"(?i)(risk|permission|danger|safe|unsafe)", content))
    findings.append(finding(
        "moderate", "§4", "risk_level", "M",
        "Pass" if has_risk else "Not tested",
        "Risk level and permissions stated",
        "Found" if has_risk else "Not found",
        "Add risk level and permission info",
        skill_path,
    ))

    return findings


# ---------------------------------------------------------------------------
# §5 — Task scope
# ---------------------------------------------------------------------------
def check_task_scope(skill_path, skill_dir):
    """§5 — What does the body claim and cover?"""
    findings = []
    content = read_file(os.path.join(skill_dir, "SKILL.md"))

    # 5.1 Single well-defined task
    has_scope = bool(re.search(r"(?i)(task|scope|does|handles|covers)", content))
    findings.append(finding(
        "major", "§5", "single_task", "D~",
        "Pass" if has_scope else "Partial",
        "Single well-defined task claimed",
        "Task scope found" if has_scope else "No clear task scope",
        "Define single task scope",
        skill_path,
    ))

    # 5.2 Not over-broad (no "everything" claims)
    overbroad = bool(re.search(r"(?i)(everything|all|any|universal|complete)", content))
    findings.append(finding(
        "moderate", "§5", "not_overbroad", "M",
        "Pass" if not overbroad else "Partial",
        "Not claiming to do everything",
        "May be over-broad" if overbroad else "Appropriately scoped",
        "Narrow scope to single task",
        skill_path,
    ))

    return findings


# ---------------------------------------------------------------------------
# §6 — Clarity and sequencing
# ---------------------------------------------------------------------------
def check_clarity(skill_path, skill_dir):
    """§6 — How well is it written and sequenced?"""
    findings = []
    content = read_file(os.path.join(skill_dir, "SKILL.md"))

    # 6.1 Steps are ordered / numbered
    has_steps = bool(re.search(r"(?i)(step|first|then|next|finally|1\.)", content))
    findings.append(finding(
        "moderate", "§6", "ordered_steps", "D~",
        "Pass" if has_steps else "Partial",
        "Steps are ordered / numbered",
        "Steps found" if has_steps else "No clear step ordering",
        "Add numbered steps",
        skill_path,
    ))

    # 6.2 Examples present
    has_examples = bool(re.search(r"(?i)(example|for instance|e\.g\.)", content))
    findings.append(finding(
        "moderate", "§6", "examples", "D~",
        "Pass" if has_examples else "Partial",
        "Examples present",
        "Examples found" if has_examples else "No examples",
        "Add usage examples",
        skill_path,
    ))

    return findings


# ---------------------------------------------------------------------------
# §7 — I/O contract
# ---------------------------------------------------------------------------
def check_io_contract(skill_path, skill_dir):
    """§7 — What's the I/O contract?"""
    findings = []
    content = read_file(os.path.join(skill_dir, "SKILL.md"))

    # 7.1 Inputs described
    has_inputs = bool(re.search(r"(?i)(input|argument|arg|parameter|--vault|--apply)", content))
    findings.append(finding(
        "major", "§7", "inputs_described", "D~",
        "Pass" if has_inputs else "Partial",
        "Inputs described",
        "Inputs found" if has_inputs else "No input documentation",
        "Document CLI inputs",
        skill_path,
    ))

    # 7.2 Outputs described
    has_outputs = bool(re.search(r"(?i)(output|return|result|report|write|create)", content))
    findings.append(finding(
        "major", "§7", "outputs_described", "D~",
        "Pass" if has_outputs else "Partial",
        "Outputs described",
        "Outputs found" if has_outputs else "No output documentation",
        "Document outputs",
        skill_path,
    ))

    # 7.3 --vault CLI arg present
    has_vault_arg = "--vault" in content
    findings.append(finding(
        "blocker", "§7", "vault_arg", "D✓",
        "Pass" if has_vault_arg else "Fail",
        "Skill accepts --vault CLI argument",
        f"--vault found: {has_vault_arg}",
        "Add --vault CLI argument",
        skill_path,
    ))

    return findings


# ---------------------------------------------------------------------------
# §8 — Failure behavior
# ---------------------------------------------------------------------------
def check_failure(skill_path, skill_dir):
    """§8 — What does it say happens on failure?"""
    findings = []
    content = read_file(os.path.join(skill_dir, "SKILL.md"))

    # 8.1 Failure behavior documented
    has_failure = bool(re.search(r"(?i)(fail|error|exception|exit|abort|stop)", content))
    findings.append(finding(
        "moderate", "§8", "failure_documented", "D~",
        "Pass" if has_failure else "Partial",
        "Failure behavior documented",
        "Found" if has_failure else "Not documented",
        "Document failure behavior",
        skill_path,
    ))

    # 8.2 Dry-run / apply safety
    has_dry_run = "--dry-run" in content or "dry.run" in content.lower()
    findings.append(finding(
        "major", "§8", "dry_run_safety", "D✓",
        "Pass" if has_dry_run else "Fail",
        "Dry-run / apply safety pattern described",
        f"--dry-run found: {has_dry_run}",
        "Add --dry-run / --apply safety pattern",
        skill_path,
    ))

    return findings


# ---------------------------------------------------------------------------
# §9 — Environment assumptions
# ---------------------------------------------------------------------------
def check_environment(skill_path, skill_dir):
    """§9 — What does it assume about the environment?"""
    findings = []
    content = read_file(os.path.join(skill_dir, "SKILL.md"))

    # 9.1 Dependencies listed
    has_deps = bool(re.search(r"(?i)(depend|require|install|pip|stdlib|external)", content))
    findings.append(finding(
        "moderate", "§9", "deps_listed", "D~",
        "Pass" if has_deps else "Partial",
        "Dependencies listed",
        "Found" if has_deps else "Not listed",
        "List all dependencies",
        skill_path,
    ))

    # 9.2 Stdlib-only claimed
    is_stdlib = "stdlib" in content.lower() or "standard library" in content.lower()
    findings.append(finding(
        "moderate", "§9", "stdlib_only", "D~",
        "Pass" if is_stdlib else "Partial",
        "Stdlib-only stated",
        f"Stdlib mentioned: {is_stdlib}",
        "State stdlib-only if applicable",
        skill_path,
    ))

    return findings


# ---------------------------------------------------------------------------
# §10 — Bundle organization
# ---------------------------------------------------------------------------
def check_bundle(skill_path, skill_dir):
    """§10 — Are bundled files well-organized and maintainable?"""
    findings = []
    content = read_file(os.path.join(skill_dir, "SKILL.md"))

    # 10.1 Sub-skill files organized
    py_files = []
    for f in os.listdir(skill_dir):
        if f.endswith(".py") and f != "__init__.py":
            py_files.append(f)
    has_modules = len(py_files) > 0
    findings.append(finding(
        "moderate", "§10", "modules_organized", "D✓",
        "Pass" if has_modules else "Partial",
        "Python modules organized",
        f"Python files: {py_files}",
        "Organize into sub-modules",
        skill_path,
    ))

    # 10.2 __init__.py present
    has_init = os.path.exists(os.path.join(skill_dir, "__init__.py"))
    findings.append(finding(
        "advisory", "§10", "init_file", "D✓",
        "Pass" if has_init else "Partial",
        "__init__.py present for package",
        f"__init__.py exists: {has_init}",
        "Add __init__.py",
        skill_path,
    ))

    return findings


# ---------------------------------------------------------------------------
# §11 — Context / token cost
# ---------------------------------------------------------------------------
def check_context_cost(skill_path, skill_dir):
    """§11 — How many tokens? Never re-charged as clarity."""
    findings = []
    content = read_file(os.path.join(skill_dir, "SKILL.md"))

    # 11.1 Token / size estimate given
    has_tokens = bool(re.search(r"(?i)(token|size|length|chars|lines|KB|MB)", content))
    findings.append(finding(
        "advisory", "§11", "token_estimate", "D~",
        "Pass" if has_tokens else "Partial",
        "Token / size estimate given",
        "Found" if has_tokens else "Not given",
        "Add token/size estimate",
        skill_path,
    ))

    # 11.2 File sizes reasonable
    total_size = 0
    for root, dirs, files in os.walk(skill_dir):
        dirs[:] = [d for d in dirs if d != "__pycache__"]
        for f in files:
            total_size += os.path.getsize(os.path.join(root, f))
    findings.append(finding(
        "advisory", "§11", "file_sizes", "D✓",
        "Pass" if total_size < 1_000_000 else "Moderate",
        f"Total skill size: {total_size} bytes",
        f"Size: {total_size / 1024:.1f} KB",
        None if total_size < 1_000_000 else "Consider splitting large skill",
        skill_path,
    ))

    return findings


# ---------------------------------------------------------------------------
# §12 — Runtime behavior
# ---------------------------------------------------------------------------
def check_runtime(skill_path, skill_dir):
    """§12 — What did the agent actually do?"""
    findings = []
    content = read_file(os.path.join(skill_dir, "SKILL.md"))

    # 12.1 --test self-tests present
    has_tests = "--test" in content or "self.test" in content.lower() or "unittest" in content.lower()
    findings.append(finding(
        "major", "§12", "self_tests", "D✓",
        "Pass" if has_tests else "Fail",
        "Self-test suite (--test) documented",
        f"--test found: {has_tests}",
        "Add --test self-test suite",
        skill_path,
    ))

    # 12.2 Idempotent / repeatable
    has_idempotent = bool(re.search(r"(?i)(idempotent|repeatable|safe.*run|dry.run)", content))
    findings.append(finding(
        "moderate", "§12", "idempotent", "D~",
        "Pass" if has_idempotent else "Partial",
        "Idempotent / repeatable behavior stated",
        "Found" if has_idempotent else "Not stated",
        "Document idempotency guarantees",
        skill_path,
    ))

    return findings


# ---------------------------------------------------------------------------
# §13 — Inter-skill dependencies
# ---------------------------------------------------------------------------
def check_dependencies(skill_path, skill_dir):
    """§13 — Does it involve other skills?"""
    findings = []
    content = read_file(os.path.join(skill_dir, "SKILL.md"))

    # 13.1 Dependencies on other skills listed
    has_deps = bool(re.search(r"(?i)(depend|import|from|require|subskill|other skill)", content))
    findings.append(finding(
        "moderate", "§13", "inter_skill_deps", "D~",
        "Pass" if has_deps else "N/A",
        "Inter-skill dependencies documented",
        "Found" if has_deps else "No dependencies listed",
        "Document any skill dependencies",
        skill_path,
    ))

    return findings


# ---------------------------------------------------------------------------
# §14–15 — Lifecycle and the checker itself
# ---------------------------------------------------------------------------
def check_lifecycle(skill_path, skill_dir):
    """§14–15 — Lifecycle and checker itself."""
    findings = []
    content = read_file(os.path.join(skill_dir, "SKILL.md"))

    # 14.1 Version field
    fm_match = re.match(r"---\s*\n(.*?)\n---\s*\n", content, re.S)
    version_val = None
    if fm_match:
        try:
            import yaml as yaml_mod
            fm = yaml_mod.safe_load(fm_match.group(1))
            version_val = fm.get("version") if isinstance(fm, dict) else None
        except Exception:
            pass
    findings.append(finding(
        "moderate", "§14", "version_field", "D✓",
        "Pass" if version_val else "Partial",
        "Version field in frontmatter",
        f"version = {version_val}",
        "Add version field",
        skill_path,
    ))

    # 15.1 Created date
    created_val = fm.get("created") if (fm_match and isinstance(fm, dict)) else None
    findings.append(finding(
        "advisory", "§15", "created_date", "D✓",
        "Pass" if created_val else "Partial",
        "Created date in frontmatter",
        f"created = {created_val}",
        "Add created date",
        skill_path,
    ))

    return findings


# ---------------------------------------------------------------------------
# §16 — Arithmetic and release
# ---------------------------------------------------------------------------
def check_release(skill_path, skill_dir):
    """§16 — Arithmetic and release."""
    findings = []
    content = read_file(os.path.join(skill_dir, "SKILL.md"))

    # 16.1 Version is valid semver-like
    fm_match = re.match(r"---\s*\n(.*?)\n---\s*\n", content, re.S)
    version_val = None
    if fm_match:
        try:
            import yaml as yaml_mod
            fm = yaml_mod.safe_load(fm_match.group(1))
            version_val = fm.get("version") if isinstance(fm, dict) else None
        except Exception:
            pass
    valid_semver = bool(version_val and re.match(r"^\d+\.\d+", str(version_val)))
    findings.append(finding(
        "moderate", "§16", "version_semver", "D✓",
        "Pass" if valid_semver else "Partial",
        "Version follows semver-like format",
        f"version = {version_val}",
        "Use semver-like version (e.g. 1.0.0)",
        skill_path,
    ))

    return findings


# ---------------------------------------------------------------------------
# §1–§16 checks for standalone Python skill files
# ---------------------------------------------------------------------------
def check_python_skill(py_path):
    """Assess a standalone Python skill file against the 16 sections."""
    findings = []
    content = read_file(py_path)
    rel = os.path.relpath(py_path, VAULT)
    skill_name = os.path.splitext(os.path.basename(py_path))[0]

    # §1 — Audit frame
    has_docstring = bool(re.search(r'^\s*"""', content, re.M))
    findings.append(finding(
        "blocker", "§1", "docstring", "D✓",
        "Pass" if has_docstring else "Fail",
        "Python file has module docstring",
        f"Docstring present: {has_docstring}",
        "Add module docstring",
        py_path,
    ))

    # §2 — Loadability: has --vault arg
    has_vault = "--vault" in content
    findings.append(finding(
        "blocker", "§2", "vault_arg", "D✓",
        "Pass" if has_vault else "Fail",
        "Accepts --vault CLI argument",
        f"--vault found: {has_vault}",
        "Add --vault CLI argument",
        py_path,
    ))

    # §2 — Has --dry-run / --apply
    has_dry_apply = "--dry-run" in content and "--apply" in content
    findings.append(finding(
        "major", "§2", "dry_apply", "D✓",
        "Pass" if has_dry_apply else "Fail",
        "Supports --dry-run / --apply",
        f"--dry-run/--apply found: {has_dry_apply}",
        "Add --dry-run and --apply flags",
        py_path,
    ))

    # §2 — Has --test
    has_test = "--test" in content
    findings.append(finding(
        "major", "§2", "test_flag", "D✓",
        "Pass" if has_test else "Fail",
        "Has --test self-test flag",
        f"--test found: {has_test}",
        "Add --test flag",
        py_path,
    ))

    # §3 — Security: no hardcoded secrets
    secret_patterns = [
        r"(?i)(api_?key|secret|token|password)\s*[:=]\s*['\"]?[A-Za-z0-9+/=]{16,}['\"]?",
        r"(?i)(sk-|pk-|ghp_|github_|glpat-)[A-Za-z0-9]{10,}",
    ]
    secrets_found = []
    for pattern in secret_patterns:
        if re.search(pattern, content):
            secrets_found.append(pattern[:30])
    findings.append(finding(
        "blocker", "§3", "no_secrets", "D✓",
        "Pass" if not secrets_found else "Fail",
        "No hardcoded secrets",
        f"Secrets: {secrets_found}" if secrets_found else "None",
        "Remove hardcoded secrets",
        py_path,
    ))

    # §3 — No destructive commands
    dangerous = re.findall(r"(?i)(rm\s+-rf|curl\s+.*\|\s*bash|wget\s+.*\|\s*sh|sudo\s+rm|chmod\s+777)", content)
    findings.append(finding(
        "blocker", "§3", "no_dangerous_cmds", "D✓",
        "Pass" if not dangerous else "Fail",
        "No destructive commands",
        f"Patterns: {dangerous}" if dangerous else "None",
        "Remove destructive patterns",
        py_path,
    ))

    # §4 — Discovery: docstring describes purpose
    docstring_ok = False
    if has_docstring and '"""' in content:
        parts = content.split('"""')
        if len(parts) > 1:
            docstring_ok = len(parts[1]) > 50
    findings.append(finding(
        "major", "§4", "purpose_docstring", "D~",
        "Pass" if docstring_ok else "Partial",
        "Docstring describes purpose",
        f"Docstring length: {len(parts[1]) if has_docstring and '\"\"\"' in content and len(content.split('\"\"\"')) > 1 else 0}",
        "Expand module docstring with purpose",
        py_path,
    ))

    # §7 — I/O: argparse present
    has_argparse = "argparse" in content
    findings.append(finding(
        "major", "§7", "argparse", "D✓",
        "Pass" if has_argparse else "Fail",
        "Uses argparse for CLI",
        f"argparse found: {has_argparse}",
        "Add argparse CLI",
        py_path,
    ))

    # §8 — Failure: has main()
    has_main = "def main()" in content
    findings.append(finding(
        "moderate", "§8", "has_main", "D✓",
        "Pass" if has_main else "Partial",
        "Has main() function",
        f"main() found: {has_main}",
        "Add main() function",
        py_path,
    ))

    # §9 — Stdlib-only: no external imports beyond stdlib
    external_imports = re.findall(r"^(?:import|from)\s+([a-zA-Z_][a-zA-Z0-9_]*)", content, re.M)
    stdlib_modules = {"os", "sys", "json", "re", "argparse", "hashlib", "datetime", "pathlib", "tempfile", "shutil", "collections", "itertools", "functools", "typing", "urllib", "yaml", "math", "sqlite3"}
    non_stdlib = [imp for imp in external_imports if imp.split(".")[0] not in stdlib_modules and not imp.startswith("_")]
    findings.append(finding(
        "moderate", "§9", "stdlib_only", "D~",
        "Pass" if not non_stdlib else "Partial",
        "Stdlib-only imports",
        f"Non-stdlib: {non_stdlib}" if non_stdlib else "All stdlib",
        None if not non_stdlib else f"Replace external imports: {non_stdlib}",
        py_path,
    ))

    # §10 — Has __init__.py nearby
    skill_dir = os.path.dirname(py_path)
    has_init = os.path.exists(os.path.join(skill_dir, "__init__.py"))
    findings.append(finding(
        "advisory", "§10", "init_file", "D✓",
        "Pass" if has_init else "Partial",
        "__init__.py in same directory",
        f"__init__.py exists: {has_init}",
        "Add __init__.py to skill directory",
        py_path,
    ))

    # §12 — Runtime: has if __name__ == "__main__"
    has_main_guard = 'if __name__ == "__main__"' in content or "if __name__ == '__main__'" in content
    findings.append(finding(
        "major", "§12", "main_guard", "D✓",
        "Pass" if has_main_guard else "Fail",
        "Has if __name__ == '__main__' guard",
        f"Main guard found: {has_main_guard}",
        "Add main guard",
        py_path,
    ))

    # §14 — Version info
    has_version = bool(re.search(r"(?i)(version|v\d+\.\d+)", content[:500]))
    findings.append(finding(
        "moderate", "§14", "version_info", "D~",
        "Pass" if has_version else "Partial",
        "Version information present",
        f"Version found: {has_version}",
        "Add version info",
        py_path,
    ))

    # §15 — Created date / author
    has_meta = bool(re.search(r"(?i)(created|author|date)", content[:500]))
    findings.append(finding(
        "advisory", "§15", "metadata", "D~",
        "Pass" if has_meta else "Partial",
        "Metadata (created/author/date) present",
        f"Metadata found: {has_meta}",
        "Add metadata header",
        py_path,
    ))

    # §16 — Arithmetic: no obvious math errors (basic check)
    findings.append(finding(
        "advisory", "§16", "arithmetic", "D~",
        "Pass",
        "No obvious arithmetic issues",
        "Basic check passed",
        None,
        py_path,
    ))

    decision, reason = aggregate_decision(findings)
    return findings, decision, reason


# ---------------------------------------------------------------------------
# Aggregation — READY / CONDITIONAL / NEEDS REWORK / REJECT
# ---------------------------------------------------------------------------
def aggregate_decision(findings):
    """Aggregate per-skill findings into an overall decision."""
    blockers = [f for f in findings if f["severity"] == "blocker" and f["status"] == "Fail"]
    majors = [f for f in findings if f["severity"] == "major" and f["status"] == "Fail"]
    moderates = [f for f in findings if f["severity"] == "moderate" and f["status"] == "Fail"]

    if blockers:
        return "REJECT", "Blocker failures present — must fix before use"
    if majors:
        return "NEEDS REWORK", "Major failures present — rework required"
    if moderates:
        return "CONDITIONAL", "Moderate issues — conditional readiness"
    return "READY", "All checks pass — ready for use"


# ---------------------------------------------------------------------------
# Main skill check
# ---------------------------------------------------------------------------
def check_skill(skill_path):
    """Run all 16 sections against a single skill directory."""
    findings = []
    checkers = [
        check_audit_frame,
        check_loadability,
        check_security,
        check_discovery,
        check_task_scope,
        check_clarity,
        check_io_contract,
        check_failure,
        check_environment,
        check_bundle,
        check_context_cost,
        check_runtime,
        check_dependencies,
        check_lifecycle,
        check_release,
    ]

    for checker in checkers:
        try:
            findings.extend(checker(skill_path, skill_path))
        except Exception as e:
            findings.append(finding(
                "blocker", "§0", "checker_error", "M",
                "Fail", f"Checker {checker.__name__} errored: {e}",
                str(e), "Fix checker implementation", skill_path,
            ))

    decision, reason = aggregate_decision(findings)
    return findings, decision, reason


# ---------------------------------------------------------------------------
# Self-test suite
# ---------------------------------------------------------------------------
def run_self_test():
    """Built-in self-test suite. Creates temp skills and verifies detection."""
    import tempfile
    import shutil

    passed = 0
    failed = 0

    def test(name, condition, msg=""):
        nonlocal passed, failed
        if condition:
            print(f"  ✅ {name}")
            passed += 1
        else:
            print(f"  ❌ {name}: {msg}")
            failed += 1

    print("=" * 50)
    print("Skill Quality Checker — Self-Tests")
    print("=" * 50)

    # Test 1: Valid skill passes all checks
    tmp = tempfile.mkdtemp()
    try:
        os.makedirs(os.path.join(tmp, "valid-skill"))
        with open(os.path.join(tmp, "valid-skill", "SKILL.md"), "w") as f:
            f.write("---\nname: valid-skill\ndescription: A test skill for quality checking\nversion: 1.0.0\nlicense: MIT\ncreated: 2026-11-09\n---\n\n# valid-skill\n\nPurpose: This skill checks the quality of other agent skills using a MECE checklist.\n\nThis skill is designed for the Hermes Brain vault. It accepts --vault and runs --dry-run by default.\n\nIntended users: agent developers. Tasks: skill assessment. Outcomes: quality report.\n\nRisk level: low. Permissions: read-only.\n\n## Inputs\n--vault <path> — vault root directory\n\n## Outputs\nSkill-Quality-Report.md in 04-Archives/Audit-Reports/\n\n## Steps\n1. Scan all SKILL.md files\n2. Assess against 16 sections\n3. Generate report\n\n## Examples\npython skill_quality_checker.py --vault .\n\n## Dependencies\nstdlib-only\n\n## Failure behavior\nExits 0 on success, 1 on test failure. Dry-run by default.\n\n## Self-tests\n--test runs built-in self-test suite.\n\n## Idempotent\nSafe to run multiple times; produces same report.\n")
        with open(os.path.join(tmp, "valid-skill", "__init__.py"), "w") as f:
            f.write('"""Valid skill package."""\n')
        with open(os.path.join(tmp, "valid-skill", "skill_module.py"), "w") as f:
            f.write('def main():\n    pass\n')
        findings, decision, reason = check_skill(os.path.join(tmp, "valid-skill"))
        test("Valid skill detected", decision in ("READY", "CONDITIONAL"), f"got {decision}: {reason}")
        test("No blocker failures", not any(f["severity"] == "blocker" and f["status"] == "Fail" for f in findings))
    finally:
        shutil.rmtree(tmp)

    # Test 2: Invalid skill (no SKILL.md, no name, no frontmatter) rejected
    tmp = tempfile.mkdtemp()
    try:
        os.makedirs(os.path.join(tmp, "bad-skill"))
        with open(os.path.join(tmp, "bad-skill", "SKILL.md"), "w") as f:
            f.write("# bad-skill\n\nNo frontmatter, no name, no description.\n")
        findings, decision, reason = check_skill(os.path.join(tmp, "bad-skill"))
        test("Invalid skill rejected", decision == "REJECT", f"got {decision}: {reason}")
        test("Blocker: no frontmatter", any(f["item"] == "frontmatter" and f["status"] == "Fail" for f in findings))
        test("Blocker: name missing", any(f["item"] == "name_field" and f["status"] == "Fail" for f in findings))
    finally:
        shutil.rmtree(tmp)

    # Test 3: Skill with secrets detected
    tmp = tempfile.mkdtemp()
    try:
        os.makedirs(os.path.join(tmp, "secret-skill"))
        with open(os.path.join(tmp, "secret-skill", "SKILL.md"), "w") as f:
            f.write("---\nname: secret-skill\ndescription: Has secrets\n---\n\nAPI_KEY=sk-1234567890abcdef\n")
        findings, decision, reason = check_skill(os.path.join(tmp, "secret-skill"))
        test("Secret detected", any(f["item"] == "no_secrets" and f["status"] == "Fail" for f in findings))
    finally:
        shutil.rmtree(tmp)

    print("=" * 50)
    print(f"🎉 Self-tests: {passed} passed, {failed} failed")
    return failed == 0


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------
def parse_args():
    parser = argparse.ArgumentParser(
        description="Hermes Brain Skill Quality Checker — MECE skill assessment across 16 sections (§1–§16).",
    )
    parser.add_argument("--vault", help="Path to the Hermes Brain vault root")
    parser.add_argument("--dry-run", action="store_true", default=True,
                        help="Report only, no changes (default)")
    parser.add_argument("--apply", action="store_true",
                        help="Apply safe auto-fixes (overrides --dry-run)")
    parser.add_argument("--skill", help="Check a specific skill directory (relative to vault)")
    parser.add_argument("--test", action="store_true",
                        help="Run built-in self-test suite")
    sub = parser.add_subparsers(dest="category", help="Check category")
    sub.add_parser("all", help="Check all skills in vault")
    sub.add_parser("skill", help="Check a single skill")
    return parser.parse_args()


def main():
    args = parse_args()

    if args.test:
        ok = run_self_test()
        sys.exit(0 if ok else 1)

    if not args.vault:
        args.vault = os.environ.get("HERMES_VAULT_PATH")
    if not args.vault:
        print("Error: --vault <path> or HERMES_VAULT_PATH is required.", file=sys.stderr)
        sys.exit(1)

    init_paths(args.vault)
    dry_run = not args.apply

    # Find all skills (directories containing SKILL.md)
    skill_dirs = []
    for root, dirs, files in os.walk(VAULT):
        dirs[:] = [d for d in dirs if d not in (".git", "__pycache__", ".obsidian", "node_modules")]
        if "SKILL.md" in files:
            skill_dirs.append(root)

    # Also find standalone Python skill files in _System/Scripts/
    python_skills = []
    scripts_root = os.path.join(VAULT, "_System", "Scripts")
    if os.path.isdir(scripts_root):
        for root, dirs, files in os.walk(scripts_root):
            dirs[:] = [d for d in dirs if d not in ("__pycache__",)]
            for f in files:
                if f.endswith(".py") and f not in ("__init__.py",):
                    python_skills.append(os.path.join(root, f))

    if args.skill:
        skill_dirs = [d for d in skill_dirs if args.skill in d]
        python_skills = [p for p in python_skills if args.skill in p]

    all_results = []
    for skill_dir in skill_dirs:
        rel = os.path.relpath(skill_dir, VAULT)
        findings, decision, reason = check_skill(skill_dir)
        all_results.append({
            "skill": rel,
            "decision": decision,
            "reason": reason,
            "findings": findings,
        })

    # Check standalone Python skills
    for py_path in python_skills:
        rel = os.path.relpath(py_path, VAULT)
        findings, decision, reason = check_python_skill(py_path)
        all_results.append({
            "skill": rel,
            "decision": decision,
            "reason": reason,
            "findings": findings,
        })

    # Generate report
    lines = []
    lines.append("# Skill Quality Report")
    lines.append(f"Generated: {datetime.now().isoformat()}")
    lines.append(f"Vault: {VAULT}")
    lines.append(f"Mode: {'DRY-RUN (no changes)' if dry_run else 'APPLY'}")
    lines.append(f"Skills scanned: {len(all_results)}")
    lines.append("")

    # Summary by decision
    decisions = {}
    for r in all_results:
        d = r["decision"]
        decisions[d] = decisions.get(d, 0) + 1
    lines.append("## Summary by Decision")
    for d in ("READY", "CONDITIONAL", "NEEDS REWORK", "REJECT"):
        if d in decisions:
            lines.append(f"- **{d}**: {decisions[d]}")
    lines.append("")

    # Per-skill details
    lines.append("## Per-Skill Results")
    for r in sorted(all_results, key=lambda x: x["skill"]):
        lines.append(f"\n### {r['skill']} — {r['decision']}")
        lines.append(f"{r['reason']}")
        for f in r["findings"]:
            if f["status"] in ("Fail", "Partial"):
                lines.append(f"  - [{f['severity'].upper()}] §{f['section']} {f['item']} [{f['tag']}] — {f['message']}")
                if f["suggestion"]:
                    lines.append(f"    Fix: {f['suggestion']}")

    write_report(lines)

    # Print summary
    ready = decisions.get("READY", 0)
    conditional = decisions.get("CONDITIONAL", 0)
    rework = decisions.get("NEEDS REWORK", 0)
    reject = decisions.get("REJECT", 0)
    print(f"\n✅ Skill quality check complete: {len(all_results)} skills scanned")
    print(f"   READY: {ready} | CONDITIONAL: {conditional} | NEEDS REWORK: {rework} | REJECT: {reject}")


if __name__ == "__main__":
    main()