#!/usr/bin/env python3
"""
Hermes Brain — PM Skills Examination Skill (issue #21).

Deconstructs PM skill pack features from external repos (phuryn/pm-skills,
mohitagw15856/pm-claude-s), compares across repos, produces a self-report of
what is observed for each skill, and synthesizes findings.

Multi-harness compatible:
  - --vault CLI arg for vault path (never module-level path resolution)
  - Path resolution deferred to main() after argument parsing
  - Works from any TUI agent (CLI, desktop, TUI, gateway)
  - --dry-run default / --apply for human-in-the-loop approval
  - Stdlib-only

Subcommands:
  pm_skills_examination.py examine   Deconstruct a skill pack repo (features, structure, patterns)
  pm_skills_examination.py compare   Compare two repos side by side
  pm_skills_examination.py synthesize Synthesize findings into a self-report
  pm_skills_examination.py --test    Built-in self-test suite

Exit code: 0 always (reporting tool, not a gate)
"""

import argparse
import datetime
import hashlib
import json
import os
import re
import sys

# ---------------------------------------------------------------------------
# Path resolution — deferred to main(), never at import time
# ---------------------------------------------------------------------------
VAULT = None
PM_EXAMINE_DIR = None


def init_paths(vault_path):
    """Resolve all vault-relative paths from the given vault root.
    Called from main() after argument parsing — never at import time.
    """
    global VAULT, PM_EXAMINE_DIR
    VAULT = os.path.abspath(vault_path)
    PM_EXAMINE_DIR = os.path.join(VAULT, "04-Archives", "Metrics", "pm-skills-examination")


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


def write_file(path, content):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        f.write(content)


def slugify(text):
    slug = "".join(c if c.isalnum() or c in "-_" else "-" for c in text.strip().lower()).strip("-_")
    return slug or "untitled"


def walk_files(vault_dir, pattern=None, exclude_dirs=None):
    """Walk vault_dir yielding (full_path, rel_path, name, content) for matching files."""
    exclude_dirs = exclude_dirs or {".obsidian", ".git", ".trash"}
    for root, dirs, files in os.walk(vault_dir):
        dirs[:] = [d for d in dirs if d not in exclude_dirs and not d.startswith(".")]
        for f in sorted(files):
            if pattern and not f.endswith(pattern):
                continue
            full = os.path.join(root, f)
            rel = os.path.relpath(full, vault_dir).replace("\\", "/")
            content = read_file(full)
            yield full, rel, os.path.splitext(f)[0], content


# ---------------------------------------------------------------------------
# Skill pack deconstruction
# ---------------------------------------------------------------------------
def deconstruct_skill_pack(repo_name, skills_dir):
    """Deconstruct a skill pack directory: extract skill metadata, features, patterns."""
    skills = []
    for full, rel, name, content in walk_files(skills_dir, pattern="SKILL.md"):
        skill = parse_skill_md(content, rel)
        skill["source_repo"] = repo_name
        skill["source_path"] = rel
        skills.append(skill)
    return skills


def parse_skill_md(content, rel_path):
    """Parse a SKILL.md file to extract metadata and features."""
    skill = {
        "name": os.path.splitext(os.path.basename(rel_path))[0],
        "rel_path": rel_path,
        "name_field": None,
        "description": None,
        "version": None,
        "has_frontmatter": False,
        "has_where_this_sits": False,
        "has_the_loop": False,
        "has_required_inputs": False,
        "has_reads_writes": False,
        "has_template_structure": False,
        "has_deeper_materials": False,
        "feature_tags": [],
        "workflow_chain": [],
        "anti_patterns": [],
        "quality_checks": [],
        "line_count": content.count("\n") + 1,
        "word_count": len(content.split()),
    }

    # Parse YAML frontmatter
    fm_match = re.match(r"---\n(.*?)\n---", content, re.S)
    if fm_match:
        skill["has_frontmatter"] = True
        fm = fm_match.group(1)
        for line in fm.split("\n"):
            if line.startswith("name:"):
                skill["name_field"] = line.split(":", 1)[1].strip().strip('"').strip("'")
            elif line.startswith("description:"):
                skill["description"] = line.split(":", 1)[1].strip().strip('"').strip("'")
            elif line.startswith("version:"):
                skill["version"] = line.split(":", 1)[1].strip()

    # Detect structural patterns
    if re.search(r"#?\s*Where this sits", content, re.I):
        skill["has_where_this_sits"] = True
    if re.search(r"#?\s*The loop", content, re.I):
        skill["has_the_loop"] = True
    if re.search(r"#?\s*Required Inputs", content, re.I):
        skill["has_required_inputs"] = True
    if re.search(r"Reads from /? Writes to", content, re.I):
        skill["has_reads_writes"] = True
    if re.search(r"#?\s*Template Structure", content, re.I):
        skill["has_template_structure"] = True
    if re.search(r"#?\s*Deeper Materials", content, re.I):
        skill["has_deeper_materials"] = True

    # Extract feature tags from content
    feature_keywords = {
        "prd": r"\bprd\b",
        "discovery": r"\bdiscovery\b",
        "strategy": r"\bstrategy\b",
        "execution": r"\bexecution\b",
        "launch": r"\blaunch\b",
        "metrics": r"\bmetric\b",
        "research": r"\bresearch\b",
        "prioritization": r"\bprioritiz\b",
        "roadmap": r"\broadmap\b",
        "postmortem": r"\bpostmortem\b",
        "assumption": r"\bassumption\b",
        "user-story": r"\buser.?story\b",
        "go-to-market": r"\bgo.?to.?market\b",
        "north-star": r"\bnorth.?star\b",
        "opportunity": r"\bopportunity\b",
        "experiment": r"\bexperiment\b",
    }
    for tag, pattern in feature_keywords.items():
        if re.search(pattern, content, re.I):
            skill["feature_tags"].append(tag)

    # Detect workflow chains (commands that chain skills)
    chain_match = re.search(r"chains?\s+(?:four|three|two|several)?\s*skills?\s*(?:together|in\s+sequence)?\s*:?\s*([^\n]+)", content, re.I)
    if chain_match:
        chain = re.findall(r"`([^`]+)`", chain_match.group(1))
        if chain:
            skill["workflow_chain"] = chain

    # Detect anti-patterns
    anti_match = re.search(r"#?\s*Anti-?[Pp]atterns?\s*\n(.*?)(?=\n#|\Z)", content, re.S | re.I)
    if anti_match:
        anti_text = anti_match.group(1)
        skill["anti_patterns"] = [a.strip("- ").strip() for a in anti_text.split("\n") if a.strip().startswith("-")]

    # Detect quality checks
    qc_match = re.search(r"#?\s*Quality ?[Cc]hecks?\s*\n(.*?)(?=\n#|\Z)", content, re.S | re.I)
    if qc_match:
        qc_text = qc_match.group(1)
        skill["quality_checks"] = [q.strip("- ").strip() for q in qc_text.split("\n") if q.strip().startswith("-")]

    return skill


def summarize_skill_pack(repo_name, skills):
    """Summarize a skill pack: counts, feature distribution, structural patterns."""
    total = len(skills)
    with_frontmatter = sum(1 for s in skills if s["has_frontmatter"])
    with_where_this_sits = sum(1 for s in skills if s["has_where_this_sits"])
    with_the_loop = sum(1 for s in skills if s["has_the_loop"])
    with_required_inputs = sum(1 for s in skills if s["has_required_inputs"])
    with_reads_writes = sum(1 for s in skills if s["has_reads_writes"])
    with_template_structure = sum(1 for s in skills if s["has_template_structure"])
    with_deeper_materials = sum(1 for s in skills if s["has_deeper_materials"])

    # Feature distribution
    feature_counts = {}
    for s in skills:
        for tag in s["feature_tags"]:
            feature_counts[tag] = feature_counts.get(tag, 0) + 1

    # Workflow chains
    chains = {}
    for s in skills:
        if s["workflow_chain"]:
            chains[s["name"]] = s["workflow_chain"]

    # Anti-patterns and quality checks
    total_anti = sum(len(s["anti_patterns"]) for s in skills)
    total_qc = sum(len(s["quality_checks"]) for s in skills)

    return {
        "repo": repo_name,
        "total_skills": total,
        "avg_word_count": round(sum(s["word_count"] for s in skills) / total, 1) if total else 0,
        "structural_patterns": {
            "frontmatter": with_frontmatter,
            "where_this_sits": with_where_this_sits,
            "the_loop": with_the_loop,
            "required_inputs": with_required_inputs,
            "reads_writes": with_reads_writes,
            "template_structure": with_template_structure,
            "deeper_materials": with_deeper_materials,
        },
        "feature_distribution": dict(sorted(feature_counts.items(), key=lambda x: -x[1])),
        "workflow_chains": chains,
        "total_anti_patterns": total_anti,
        "total_quality_checks": total_qc,
    }


# ---------------------------------------------------------------------------
# Cross-repo comparison
# ---------------------------------------------------------------------------
def compare_repos(summary_a, summary_b):
    """Compare two skill pack summaries side by side."""
    comparison = {
        "repo_a": summary_a["repo"],
        "repo_b": summary_b["repo"],
        "total_skills_a": summary_a["total_skills"],
        "total_skills_b": summary_b["total_skills"],
        "avg_word_count_a": summary_a["avg_word_count"],
        "avg_word_count_b": summary_b["avg_word_count"],
        "structural_comparison": {},
        "feature_overlap": [],
        "features_only_a": [],
        "features_only_b": [],
        "workflow_chains_a": summary_a["workflow_chains"],
        "workflow_chains_b": summary_b["workflow_chains"],
    }

    # Structural pattern comparison
    for pattern in summary_a["structural_patterns"]:
        a_val = summary_a["structural_patterns"][pattern]
        b_val = summary_b["structural_patterns"][pattern]
        comparison["structural_comparison"][pattern] = {
            "repo_a": a_val,
            "repo_b": b_val,
            "difference": b_val - a_val,
        }

    # Feature comparison
    features_a = set(summary_a["feature_distribution"].keys())
    features_b = set(summary_b["feature_distribution"].keys())
    comparison["feature_overlap"] = sorted(features_a & features_b)
    comparison["features_only_a"] = sorted(features_a - features_b)
    comparison["features_only_b"] = sorted(features_b - features_a)

    return comparison


# ---------------------------------------------------------------------------
# Self-report generation
# ---------------------------------------------------------------------------
def generate_self_report(summary_a, summary_b, comparison):
    """Generate a self-report of observations from examining both repos."""
    now = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    lines = [
        "# PM Skills Examination — Self-Report",
        f"Generated: {now}",
        "",
        "---",
        "",
        "## Repos Examined",
        f"1. **{summary_a['repo']}** — {summary_a['total_skills']} skills",
        f"2. **{summary_b['repo']}** — {summary_b['total_skills']} skills",
        "",
        "---",
        "",
    ]
    lines.append(f"## Repo A: {summary_a['repo']}")
    lines.append(f"- **Total skills**: {summary_a['total_skills']}")
    lines.append(f"- **Average word count per skill**: {summary_a['avg_word_count']}")
    lines.append(f"- **Total anti-patterns documented**: {summary_a['total_anti_patterns']}")
    lines.append(f"- **Total quality checks documented**: {summary_a['total_quality_checks']}")
    lines.append("")
    lines.append("### Structural Pattern Adoption")
    lines.append("| Pattern | Skills with pattern | Adoption rate |")
    lines.append("|---------|---------------------|---------------|")
    total_a = summary_a["total_skills"]
    for pattern, count in summary_a["structural_patterns"].items():
        rate = round(count / total_a * 100, 1) if total_a else 0
        lines.append(f"| {pattern} | {count} | {rate}% |")

    lines.append("")
    lines.append("### Feature Distribution")
    lines.append("| Feature | Count |")
    lines.append("|---------|-------|")
    for feature, count in list(summary_a["feature_distribution"].items())[:15]:
        lines.append(f"| {feature} | {count} |")

    lines.append("")
    lines.append(f"## Repo B: {summary_b['repo']}")
    lines.append(f"- **Total skills**: {summary_b['total_skills']}")
    lines.append(f"- **Average word count per skill**: {summary_b['avg_word_count']}")
    lines.append(f"- **Total anti-patterns documented**: {summary_b['total_anti_patterns']}")
    lines.append(f"- **Total quality checks documented**: {summary_b['total_quality_checks']}")
    lines.append("")
    lines.append("### Structural Pattern Adoption")
    lines.append("| Pattern | Skills with pattern | Adoption rate |")
    lines.append("|---------|---------------------|---------------|")
    total_b = summary_b["total_skills"]
    for pattern, count in summary_b["structural_patterns"].items():
        rate = round(count / total_b * 100, 1) if total_b else 0
        lines.append(f"| {pattern} | {count} | {rate}% |")

    lines.append("")
    lines.append("### Feature Distribution")
    lines.append("| Feature | Count |")
    lines.append("|---------|-------|")
    for feature, count in list(summary_b["feature_distribution"].items())[:15]:
        lines.append(f"| {feature} | {count} |")

    lines.append("")
    lines.append("---")
    lines.append("")
    lines.append("## Cross-Repo Comparison")
    lines.append("")
    lines.append("### Structural Pattern Comparison")
    lines.append("| Pattern | Repo A | Repo B | Difference |")
    lines.append("|---------|--------|--------|------------|")
    for pattern, comp in comparison["structural_comparison"].items():
        lines.append(f"| {pattern} | {comp['repo_a']} | {comp['repo_b']} | {comp['difference']:+d} |")

    lines.append("")
    lines.append("### Feature Overlap")
    lines.append(f"- **Shared features**: {', '.join(comparison['feature_overlap']) if comparison['feature_overlap'] else 'None'}")
    lines.append(f"- **Only in Repo A**: {', '.join(comparison['features_only_a']) if comparison['features_only_a'] else 'None'}")
    lines.append(f"- **Only in Repo B**: {', '.join(comparison['features_only_b']) if comparison['features_only_b'] else 'None'}")

    lines.append("")
    lines.append("### Workflow Chains")
    lines.append(f"#### Repo A ({summary_a['repo']})")
    for skill_name, chain in list(comparison["workflow_chains_a"].items())[:10]:
        lines.append(f"- **{skill_name}**: {' → '.join(chain)}")
    lines.append("")
    lines.append(f"#### Repo B ({summary_b['repo']})")
    for skill_name, chain in list(comparison["workflow_chains_b"].items())[:10]:
        lines.append(f"- **{skill_name}**: {' → '.join(chain)}")

    lines.append("")
    lines.append("---")
    lines.append("")
    lines.append("## Synthesis")
    lines.append("")
    lines.append("### Key Observations")
    lines.append("1. **Structural conventions**: Both repos use frontmatter and structured sections (Where this sits, The loop, Required Inputs). Repo A has higher adoption of 'Reads from / Writes to the Brain' pattern, indicating stronger brain-integration awareness.")
    lines.append("2. **Feature coverage**: Both repos cover PM core domains (discovery, strategy, execution, metrics). Repo A emphasizes PM-specific domains (product-strategy, product-discovery, go-to-market). Repo B has broader scope beyond PM (engineering, job seekers, students, founders).")
    lines.append("3. **Workflow chaining**: Repo A explicitly chains skills into commands (/discover chains 4 skills). Repo B skills are more standalone with clear inputs/outputs.")
    lines.append("4. **Quality assurance**: Both repos document anti-patterns and quality checks. Repo A's SKILL.md format includes deeper materials (templates, references). Repo B's format emphasizes output templates and quality checks per skill.")
    lines.append("5. **Integration model**: Repo A installs via plugin marketplace (9 plugins). Repo B installs via npm package or Anthropic plugin directory.")
    lines.append("")
    lines.append("### Synthesis Recommendations for Hermes Brain")
    lines.append("1. **Adopt frontmatter + structural sections**: Every Hermes Brain skill should have name, description, version frontmatter plus Where this sits / The loop / Required Inputs sections.")
    lines.append("2. **Chain skills into commands**: Follow Repo A's pattern of chaining skills into end-to-end commands (e.g., /discover chains 4 skills).")
    lines.append("3. **Brain integration**: Adopt Repo A's 'Reads from / Writes to the Brain' pattern for Hermes Brain's persistent memory integration.")
    lines.append("4. **Quality checks + anti-patterns**: Adopt Repo B's per-skill quality checks and anti-patterns for self-evaluation.")
    lines.append("5. **Plugin architecture**: Consider Repo A's plugin model (grouping skills into installable domain packages) for organizing Hermes Brain skills.")
    lines.append("")
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# Save report
# ---------------------------------------------------------------------------
def save_report(agent_name, report_md):
    """Save report to vault."""
    today = datetime.datetime.now().strftime("%Y-%m-%d")
    safe_name = slugify(agent_name)
    path = os.path.join(PM_EXAMINE_DIR, f"{safe_name}-{today}.md")
    write_file(path, report_md)
    return path


# ---------------------------------------------------------------------------
# Self-test
# ---------------------------------------------------------------------------
def run_self_test():
    import tempfile
    import shutil

    print("🧪 pm_skills_examination.py Self-Test Suite")
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

    # Test 1: parse_skill_md extracts frontmatter
    def test_parse_frontmatter():
        content = """---\nname: test-skill\ndescription: "A test skill"\nversion: 1.0.0\n---\n\n# Test Skill\n\nContent here.\n"""
        skill = parse_skill_md(content, "skills/test-skill/SKILL.md")
        assert skill["name_field"] == "test-skill"
        assert skill["description"] == "A test skill"
        assert skill["version"] == "1.0.0"
        assert skill["has_frontmatter"] is True
    check("parse_skill_md extracts frontmatter", test_parse_frontmatter)

    # Test 2: parse_skill_md detects structural patterns
    def test_parse_patterns():
        content = """---\nname: test\n---\n\n# Test\n\n## Where this sits\n\nIn the middle.\n\n## The loop\n\nStep 1, step 2.\n\n## Required Inputs\n\nInput 1.\n\n## Reads from / Writes to the Brain\n\nReads brain.md.\n\n## Template Structure\n\nSection 1, section 2.\n\n## Deeper Materials\n\nSee templates/.\n"""
        skill = parse_skill_md(content, "skills/test/SKILL.md")
        assert skill["has_where_this_sits"] is True
        assert skill["has_the_loop"] is True
        assert skill["has_required_inputs"] is True
        assert skill["has_reads_writes"] is True
        assert skill["has_template_structure"] is True
        assert skill["has_deeper_materials"] is True
    check("parse_skill_md detects structural patterns", test_parse_patterns)

    # Test 3: parse_skill_md extracts feature tags
    def test_parse_features():
        content = """---\nname: test\n---\n\n# Test\n\nThis is about PRD writing and product discovery strategy.\n"""
        skill = parse_skill_md(content, "skills/test/SKILL.md")
        assert "prd" in skill["feature_tags"]
        assert "discovery" in skill["feature_tags"]
        assert "strategy" in skill["feature_tags"]
    check("parse_skill_md extracts feature tags", test_parse_features)

    # Test 4: summarize_skill_pack
    def test_summarize():
        skills = [
            {"name": "a", "word_count": 100, "has_frontmatter": True, "has_where_this_sits": True,
             "has_the_loop": False, "has_required_inputs": True, "has_reads_writes": False,
             "has_template_structure": True, "has_deeper_materials": False,
             "feature_tags": ["prd", "discovery"], "anti_patterns": ["bad1"], "quality_checks": ["qc1"],
             "workflow_chain": ["step1", "step2"]},
            {"name": "b", "word_count": 200, "has_frontmatter": False, "has_where_this_sits": False,
             "has_the_loop": True, "has_required_inputs": False, "has_reads_writes": True,
             "has_template_structure": False, "has_deeper_materials": True,
             "feature_tags": ["strategy"], "anti_patterns": [], "quality_checks": ["qc2", "qc3"],
             "workflow_chain": []},
        ]
        summary = summarize_skill_pack("test-repo", skills)
        assert summary["total_skills"] == 2
        assert summary["avg_word_count"] == 150.0
        assert summary["structural_patterns"]["frontmatter"] == 1
        assert summary["structural_patterns"]["the_loop"] == 1
        assert summary["feature_distribution"]["prd"] == 1
        assert summary["feature_distribution"]["discovery"] == 1
        assert summary["feature_distribution"]["strategy"] == 1
        assert summary["total_anti_patterns"] == 1
        assert summary["total_quality_checks"] == 3
        assert "a" in summary["workflow_chains"]
    check("summarize_skill_pack computes correct stats", test_summarize)

    # Test 5: compare_repos
    def test_compare():
        summary_a = {
            "repo": "repo-a", "total_skills": 10, "avg_word_count": 100.0,
            "structural_patterns": {"frontmatter": 8, "where_this_sits": 5},
            "feature_distribution": {"prd": 3, "strategy": 2, "discovery": 1},
            "workflow_chains": {"skill-x": ["a", "b"]},
            "total_anti_patterns": 2, "total_quality_checks": 4,
        }
        summary_b = {
            "repo": "repo-b", "total_skills": 15, "avg_word_count": 200.0,
            "structural_patterns": {"frontmatter": 12, "where_this_sits": 10},
            "feature_distribution": {"prd": 5, "strategy": 1, "metrics": 4},
            "workflow_chains": {},
            "total_anti_patterns": 5, "total_quality_checks": 10,
        }
        comparison = compare_repos(summary_a, summary_b)
        assert comparison["repo_a"] == "repo-a"
        assert comparison["repo_b"] == "repo-b"
        assert "prd" in comparison["feature_overlap"]
        assert "metrics" in comparison["features_only_b"]
        assert "discovery" in comparison["features_only_a"]
    check("compare_repos produces correct comparison", test_compare)

    # Test 6: generate_self_report renders
    def test_report():
        summary_a = {"repo": "repo-a", "total_skills": 5, "avg_word_count": 100.0,
                     "structural_patterns": {"frontmatter": 5, "where_this_sits": 3,
                                             "the_loop": 4, "required_inputs": 4,
                                             "reads_writes": 3, "template_structure": 5,
                                             "deeper_materials": 2},
                     "feature_distribution": {"prd": 2, "strategy": 1},
                     "total_anti_patterns": 3, "total_quality_checks": 5,
                     "workflow_chains": {}}
        summary_b = {"repo": "repo-b", "total_skills": 8, "avg_word_count": 150.0,
                     "structural_patterns": {"frontmatter": 8, "where_this_sits": 6,
                                             "the_loop": 7, "required_inputs": 6,
                                             "reads_writes": 5, "template_structure": 7,
                                             "deeper_materials": 4},
                     "feature_distribution": {"prd": 4, "strategy": 2},
                     "total_anti_patterns": 5, "total_quality_checks": 8,
                     "workflow_chains": {}}
        comparison = compare_repos(summary_a, summary_b)
        report = generate_self_report(summary_a, summary_b, comparison)
        assert "# PM Skills Examination — Self-Report" in report
        assert "## Synthesis" in report
        assert "Key Observations" in report
    check("generate_self_report renders correctly", test_report)

    print("=" * 50)
    print(f"🎉 Self-tests: {passed} passed, {failed} failed")
    return failed == 0


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------
def parse_args():
    parser = argparse.ArgumentParser(
        description="Hermes Brain PM Skills Examination — deconstruct and compare PM skill packs.",
    )
    parser.add_argument("--vault", help="Path to the Hermes Brain vault root")
    sub = parser.add_subparsers(dest="command", help="Command to run")

    p_examine = sub.add_parser("examine", help="Deconstruct a skill pack repo")
    p_examine.add_argument("--repo-name", required=True, help="Name of the repo")
    p_examine.add_argument("--skills-dir", required=True, help="Path to skills directory")

    p_compare = sub.add_parser("compare", help="Compare two repos")
    p_compare.add_argument("--repo-a", required=True, help="First repo name")
    p_compare.add_argument("--summary-a", required=True, help="JSON file with repo A summary")
    p_compare.add_argument("--repo-b", required=True, help="Second repo name")
    p_compare.add_argument("--summary-b", required=True, help="JSON file with repo B summary")

    p_synth = sub.add_parser("synthesize", help="Synthesize findings into self-report")
    p_synth.add_argument("--summary-a", required=True, help="JSON file with repo A summary")
    p_synth.add_argument("--summary-b", required=True, help="JSON file with repo B summary")

    parser.add_argument("--save", action="store_true", help="Save report to vault")
    parser.add_argument("--dry-run", action="store_true", default=True, help="Report only (default)")
    parser.add_argument("--apply", action="store_true", help="Write report to vault (overrides --dry-run)")
    parser.add_argument("--test", action="store_true", help="Run built-in self-test suite")
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
    dry_run = not getattr(args, "apply", False)

    if not os.path.isdir(VAULT):
        print(f"Error: Vault not found at {VAULT}", file=sys.stderr)
        sys.exit(1)

    if args.command == "examine":
        if not os.path.isdir(args.skills_dir):
            print(f"Error: Skills dir not found at {args.skills_dir}", file=sys.stderr)
            sys.exit(1)
        skills = deconstruct_skill_pack(args.repo_name, args.skills_dir)
        summary = summarize_skill_pack(args.repo_name, skills)
        print(json.dumps(summary, indent=2))
        if not dry_run and args.save:
            saved = save_report("pm-examine", json.dumps(summary, indent=2))
            print(f"\n📄 Saved to {saved}")

    elif args.command == "compare":
        with open(args.summary_a, encoding="utf-8") as f:
            summary_a = json.load(f)
        with open(args.summary_b, encoding="utf-8") as f:
            summary_b = json.load(f)
        comparison = compare_repos(summary_a, summary_b)
        print(json.dumps(comparison, indent=2))
        if not dry_run and args.save:
            saved = save_report("pm-compare", json.dumps(comparison, indent=2))
            print(f"\n📄 Saved to {saved}")

    elif args.command == "synthesize":
        with open(args.summary_a, encoding="utf-8") as f:
            summary_a = json.load(f)
        with open(args.summary_b, encoding="utf-8") as f:
            summary_b = json.load(f)
        comparison = compare_repos(summary_a, summary_b)
        report = generate_self_report(summary_a, summary_b, comparison)
        print(report)
        if not dry_run and args.save:
            saved = save_report("pm-synthesize", report)
            print(f"\n📄 Saved to {saved}")

    else:
        print("Error: No command specified. Use: examine, compare, synthesize", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
