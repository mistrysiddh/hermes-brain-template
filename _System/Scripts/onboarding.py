#!/usr/bin/env python3
"""
Hermes Brain — Onboarding Skill (conversational setup, profile, interests, integrations).

Guides a new user through first-time vault setup:
- User profile (name, role, timezone, preferences)
- Interests (topics, domains, tools)
- Integrations (GitHub, Discord, Telegram, etc.)
- Vault structure verification

Multi-harness compatible:
  - --vault CLI arg for vault path (never module-level path resolution)
  - Path resolution deferred to main() after argument parsing
  - Works from any TUI agent (CLI, desktop, TUI, gateway)
  - --dry-run default / --apply for human-in-the-loop approval
  - Stdlib-only

Subcommands:
  onboarding.py setup       Run interactive onboarding setup (dry-run report)
  onboarding.py profile     Show current user profile
  onboarding.py --test      Built-in self-test suite

Exit code: 0 always (reporting tool, not a gate)
"""

import argparse
import datetime
import json
import os
import re
import sys

# ---------------------------------------------------------------------------
# Path resolution — deferred to main(), never at import time
# ---------------------------------------------------------------------------
VAULT = None
PROFILE_DIR = None
PROFILE_FILE = None


def init_paths(vault_path):
    """Resolve all vault-relative paths from the given vault root.
    Called from main() after argument parsing — never at import time.
    """
    global VAULT, PROFILE_DIR, PROFILE_FILE
    VAULT = os.path.abspath(vault_path)
    PROFILE_DIR = os.path.join(VAULT, "04-Archives", "Onboarding")
    PROFILE_FILE = os.path.join(PROFILE_DIR, "user-profile.json")


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


def walk_md(vault_dir, exclude_dirs=None, exclude_files=None):
    """Walk vault_dir yielding (full_path, rel_path, name, content) for .md files."""
    exclude_dirs = exclude_dirs or {".obsidian", ".git", ".trash"}
    exclude_files = exclude_files or {"README.md", "manifest.jsonl"}
    for root, dirs, files in os.walk(vault_dir):
        dirs[:] = [d for d in dirs if d not in exclude_dirs and not d.startswith(".")]
        for f in sorted(files):
            if not f.endswith(".md"):
                continue
            if f in exclude_files:
                continue
            full = os.path.join(root, f)
            rel = os.path.relpath(full, vault_dir).replace("\\", "/")
            content = read_file(full)
            yield full, rel, os.path.splitext(f)[0], content


# ---------------------------------------------------------------------------
# Profile management
# ---------------------------------------------------------------------------
def load_profile():
    """Load existing user profile, or return empty dict."""
    if os.path.exists(PROFILE_FILE):
        try:
            with open(PROFILE_FILE, encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            return {}
    return {}


def save_profile(profile):
    """Save user profile to vault."""
    write_file(PROFILE_FILE, json.dumps(profile, indent=2, ensure_ascii=False))


# ---------------------------------------------------------------------------
# Onboarding questions
# ---------------------------------------------------------------------------
ONBOARDING_QUESTIONS = [
    {
        "key": "name",
        "prompt": "What should I call you?",
        "type": "text",
        "required": True,
        "help": "Your name or preferred nickname.",
    },
    {
        "key": "role",
        "prompt": "What's your role? (e.g., AI builder, trainer, researcher, sysadmin)",
        "type": "text",
        "required": True,
        "help": "Helps me tailor suggestions to your work.",
    },
    {
        "key": "timezone",
        "prompt": "What's your timezone? (e.g., UTC, Asia/Kolkata, America/New_York)",
        "type": "text",
        "required": False,
        "default": "UTC",
        "help": "Used for scheduling and timestamping.",
    },
    {
        "key": "interests",
        "prompt": "What topics interest you? (comma-separated, e.g., AI, cybersecurity, Linux, self-hosting)",
        "type": "list",
        "required": False,
        "help": "Used to recommend relevant notes and skills.",
    },
    {
        "key": "github_username",
        "prompt": "What's your GitHub username? (for repo integration)",
        "type": "text",
        "required": False,
        "help": "Used to link vault notes to GitHub issues/PRs.",
    },
    {
        "key": "discord_id",
        "prompt": "What's your Discord user ID? (for notifications)",
        "type": "text",
        "required": False,
        "help": "Used to send alerts and summaries to Discord.",
    },
    {
        "key": "telegram_chat_id",
        "prompt": "What's your Telegram chat ID? (for mobile alerts)",
        "type": "text",
        "required": False,
        "help": "Used to send alerts to your phone.",
    },
    {
        "key": "preferred_editor",
        "prompt": "What's your preferred editor? (e.g., vim, nvim, vscode, emacs)",
        "type": "text",
        "required": False,
        "default": "vim",
        "help": "Used for edit commands.",
    },
]


def ask_question(q, dry_run=True):
    """Ask a single onboarding question. In dry-run, return a preview."""
    if dry_run:
        return {
            "key": q["key"],
            "question": q["prompt"],
            "type": q["type"],
            "required": q["required"],
            "default": q.get("default", ""),
            "help": q.get("help", ""),
            "applied": False,
            "reason": "dry-run preview",
        }

    # Interactive mode — read from stdin
    default_part = f" [{q.get('default', '')}]" if q.get("default") else ""
    required_part = " (required)" if q["required"] else ""
    prompt = f"{q['prompt']}{default_part}{required_part}: "

    try:
        answer = input(prompt).strip()
    except EOFError:
        answer = ""

    if not answer and q.get("default"):
        answer = q["default"]

    if q["type"] == "list":
        answer = [s.strip() for s in answer.split(",") if s.strip()]

    return {
        "key": q["key"],
        "question": q["prompt"],
        "answer": answer,
        "applied": True,
        "reason": "answered",
    }


def run_onboarding(dry_run=True):
    """Run the full onboarding setup."""
    existing = load_profile()
    results = []

    for q in ONBOARDING_QUESTIONS:
        # Skip if already answered and not forcing re-run
        if not dry_run and q["key"] in existing and existing[q["key"]]:
            results.append({
                "key": q["key"],
                "question": q["prompt"],
                "answer": existing[q["key"]],
                "applied": False,
                "reason": "already set",
            })
            continue

        result = ask_question(q, dry_run=dry_run)
        results.append(result)

        if not dry_run and result["applied"]:
            existing[q["key"]] = result["answer"]

    if not dry_run:
        existing["updated_at"] = datetime.datetime.now().isoformat()
        existing["version"] = "1.0"
        save_profile(existing)

    return results


# ---------------------------------------------------------------------------
# Vault structure check
# ---------------------------------------------------------------------------
def check_vault_structure():
    """Check that the vault has the expected PARA structure."""
    expected_dirs = [
        "01-Projects",
        "02-Areas",
        "03-Resources",
        "04-Archives",
    ]
    results = {}
    for d in expected_dirs:
        full = os.path.join(VAULT, d)
        results[d] = os.path.isdir(full)
    return results


def generate_onboarding_report(results, structure, dry_run=True):
    """Generate markdown report for onboarding."""
    now = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    lines = [
        "# Onboarding Setup",
        f"Generated: {now}",
        f"Vault: {VAULT}",
        f"Mode: {'DRY-RUN (no changes)' if dry_run else 'APPLY'}",
        "",
        "---",
        "",
    ]

    if dry_run:
        lines.append("## Questions to answer")
        lines.append("")
        lines.append("| # | Question | Type | Required | Default |")
        lines.append("|---|----------|------|----------|---------|")
        for i, r in enumerate(results, 1):
            default_val = r.get("default", "")
            lines.append(
                f"| {i} | {r['question']} | {r['type']} | "
                f"{'Yes' if r['required'] else 'No'} | {default_val} |"
            )
        lines.append("")
        lines.append("## Vault structure")
        lines.append("")
        lines.append("| Directory | Exists |")
        lines.append("|-----------|--------|")
        for d, exists in structure.items():
            lines.append(f"| {d} | {'✅' if exists else '❌'} |")
        lines.append("")
        lines.append("## Next Steps")
        lines.append("")
        lines.append("Run with `--apply` to answer the questions and save your profile.")
        lines.append("Your profile will be saved to `04-Archives/Onboarding/user-profile.json`.")
    else:
        lines.append("## Profile saved")
        lines.append("")
        lines.append("Your onboarding profile has been saved to:")
        lines.append(f"`{PROFILE_FILE}`")
        lines.append("")
        lines.append("### Your answers")
        lines.append("")
        for r in results:
            if r["applied"]:
                val = r.get("answer", "")
                if isinstance(val, list):
                    val = ", ".join(val)
                lines.append(f"- **{r['question']}**: {val}")
        lines.append("")
        lines.append("## Vault structure")
        lines.append("")
        lines.append("| Directory | Exists |")
        lines.append("|-----------|--------|")
        for d, exists in structure.items():
            lines.append(f"| {d} | {'✅' if exists else '❌'} |")
        lines.append("")
        lines.append("## Next Steps")
        lines.append("")
        lines.append("- Run `metrics.py --vault <path> snapshot --apply` to get a baseline metrics snapshot.")
        lines.append("- Run `radar.py --vault <path> scan --days 7` to start tracking sources.")
        lines.append("- Run `quiz.py --vault <path> --days 30` to test yourself from your vault notes.")

    return "\n".join(lines)


def generate_profile_show(profile):
    """Generate markdown for showing current profile."""
    if not profile:
        return "# User Profile\n\nNo profile found. Run `onboarding.py setup` to create one."

    now = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    lines = [
        "# User Profile",
        f"Generated: {now}",
        "",
        "---",
        "",
    ]

    display_keys = {
        "name": "Name",
        "role": "Role",
        "timezone": "Timezone",
        "interests": "Interests",
        "github_username": "GitHub Username",
        "discord_id": "Discord ID",
        "telegram_chat_id": "Telegram Chat ID",
        "preferred_editor": "Preferred Editor",
    }

    for key, label in display_keys.items():
        if key in profile and profile[key]:
            val = profile[key]
            if isinstance(val, list):
                val = ", ".join(val)
            lines.append(f"- **{label}**: {val}")

    if profile.get("updated_at"):
        lines.append(f"- **Last updated**: {profile['updated_at']}")

    lines.append("")
    lines.append("## Vault structure")
    lines.append("")
    structure = check_vault_structure()
    lines.append("| Directory | Exists |")
    lines.append("|-----------|--------|")
    for d, exists in structure.items():
        lines.append(f"| {d} | {'✅' if exists else '❌'} |")

    return "\n".join(lines)


def save_report(agent_name, report_md):
    """Save report to vault."""
    today = datetime.datetime.now().strftime("%Y-%m-%d")
    safe_name = slugify(agent_name)
    path = os.path.join(PROFILE_DIR, f"{safe_name}-{today}.md")
    write_file(path, report_md)
    return path


# ---------------------------------------------------------------------------
# Self-test
# ---------------------------------------------------------------------------
def run_self_test():
    import tempfile
    import shutil

    print("🧪 onboarding.py Self-Test Suite")
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

    # Test 1: load_profile returns empty dict when no file
    def test_load_empty():
        tmp = tempfile.mkdtemp()
        try:
            init_paths(tmp)
            profile = load_profile()
            assert profile == {}
        finally:
            shutil.rmtree(tmp)
    check("load_profile returns empty when no file", test_load_empty)

    # Test 2: save_profile and load_profile round-trip
    def test_save_load():
        tmp = tempfile.mkdtemp()
        try:
            init_paths(tmp)
            profile = {"name": "Test User", "role": "AI builder", "interests": ["AI", "Linux"]}
            save_profile(profile)
            loaded = load_profile()
            assert loaded["name"] == "Test User"
            assert loaded["role"] == "AI builder"
            assert loaded["interests"] == ["AI", "Linux"]
        finally:
            shutil.rmtree(tmp)
    check("save_profile and load_profile round-trip", test_save_load)

    # Test 3: run_onboarding dry-run returns questions
    def test_onboarding_dryrun():
        tmp = tempfile.mkdtemp()
        try:
            init_paths(tmp)
            results = run_onboarding(dry_run=True)
            assert len(results) == len(ONBOARDING_QUESTIONS)
            assert all(not r["applied"] for r in results)
            assert results[0]["key"] == "name"
        finally:
            shutil.rmtree(tmp)
    check("onboarding dry-run returns questions", test_onboarding_dryrun)

    # Test 4: run_onboarding apply saves profile
    def test_onboarding_apply():
        tmp = tempfile.mkdtemp()
        try:
            init_paths(tmp)
            # Simulate stdin input
            import io
            sys.stdin = io.StringIO("Test User\nAI builder\nUTC\nAI, Linux\nsiddh\n\n\nvim\n")
            results = run_onboarding(dry_run=False)
            sys.stdin = sys.__stdin__
            applied = [r for r in results if r["applied"]]
            assert len(applied) >= 1
            profile = load_profile()
            assert profile["name"] == "Test User"
            assert profile["role"] == "AI builder"
        finally:
            sys.stdin = sys.__stdin__
            shutil.rmtree(tmp)
    check("onboarding apply saves profile", test_onboarding_apply)

    # Test 5: check_vault_structure
    def test_structure():
        tmp = tempfile.mkdtemp()
        try:
            init_paths(tmp)
            os.makedirs(os.path.join(tmp, "01-Projects"), exist_ok=True)
            structure = check_vault_structure()
            assert structure["01-Projects"] is True
            assert structure["02-Areas"] is False
        finally:
            shutil.rmtree(tmp)
    check("check_vault_structure works", test_structure)

    print("=" * 50)
    print(f"🎉 Self-tests: {passed} passed, {failed} failed")
    return failed == 0


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------
def parse_args():
    parser = argparse.ArgumentParser(
        description="Hermes Brain Onboarding — conversational setup, profile, interests, integrations.",
    )
    parser.add_argument("--vault", help="Path to the Hermes Brain vault root")
    sub = parser.add_subparsers(dest="command", help="Command to run")

    p_setup = sub.add_parser("setup", help="Run interactive onboarding setup (dry-run report)")
    p_setup.add_argument("--apply", action="store_true", help="Apply setup (overrides --dry-run)")

    sub.add_parser("profile", help="Show current user profile")

    parser.add_argument("--save", action="store_true", help="Save report to vault")
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

    if args.command == "setup":
        results = run_onboarding(dry_run=dry_run)
        structure = check_vault_structure()
        report = generate_onboarding_report(results, structure, dry_run=dry_run)
        print(report)
        if args.save:
            saved = save_report("onboarding-setup", report)
            print(f"\n📄 Saved to {saved}")

    elif args.command == "profile":
        profile = load_profile()
        report = generate_profile_show(profile)
        print(report)

    else:
        print("Error: No command specified. Use 'setup' or 'profile'.", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
