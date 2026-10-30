#!/usr/bin/env python3
"""
Hermes Brain — Auto-Changelog Skill (CI/CD changelog from conventional commits).

Scans git commit history, parses conventional commits, and generates a dated
changelog markdown file grouped by release section (Features, Fixes, Docs, etc.).

Multi-harness compatible:
  - --vault CLI arg for vault path (never module-level path resolution)
  - Path resolution deferred to main() after argument parsing
  - Works from any TUI agent (CLI, desktop, TUI, gateway)

Subcommands:
  auto_changelog.py generate   Generate changelog from git history (dry-run report)
  auto_changelog.py --test     Built-in self-test suite

Conventional commit types parsed:
  feat:     → Features
  fix:      → Bug Fixes
  docs:     → Documentation
  refactor: → Refactoring
  perf:     → Performance
  test:     → Tests
  build:    → Build/CI
  chore:    → Maintenance
  sec:      → Security

Output:
  - Dated changelog file in 04-Archives/Metrics/changelog/
  - Grouped by commit type with links to commit SHAs
  - "Unreleased" section for commits since last tag

Exit code: 0 always (reporting tool, not a gate)
"""

import argparse
import datetime
import os
import re
import subprocess
import sys

# ---------------------------------------------------------------------------
# Path resolution — deferred to main(), never at import time
# ---------------------------------------------------------------------------
VAULT = None
CHANGELOG_DIR = None


def init_paths(vault_path):
    """Resolve all vault-relative paths from the given vault root.
    Called from main() after argument parsing — never at import time.
    """
    global VAULT, CHANGELOG_DIR
    VAULT = os.path.abspath(vault_path)
    CHANGELOG_DIR = os.path.join(VAULT, "04-Archives", "Metrics", "changelog")


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------
def run_cmd(cmd, cwd=None):
    """Run a shell command and return stdout, or empty string on failure."""
    try:
        result = subprocess.run(
            cmd, shell=True, cwd=cwd or VAULT,
            capture_output=True, text=True, timeout=30,
        )
        return result.stdout.strip()
    except Exception:
        return ""


def write_file(path, content):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        f.write(content)


# Conventional commit pattern: type(scope)?!: description
COMMIT_RE = re.compile(
    r"^(?P<type>feat|fix|docs|refactor|perf|test|build|ci|chore|sec)(?:\((?P<scope>[^)]+)\))?(?P<break>!)?:\s+(?P<desc>.+)$",
    re.I,
)

TYPE_LABELS = {
    "feat": "Features",
    "fix": "Bug Fixes",
    "docs": "Documentation",
    "refactor": "Refactoring",
    "perf": "Performance",
    "test": "Tests",
    "build": "Build / CI",
    "ci": "Build / CI",
    "chore": "Maintenance",
    "sec": "Security",
}


def parse_commit(subject):
    """Parse a conventional commit subject line. Returns dict or None."""
    m = COMMIT_RE.match(subject.strip())
    if not m:
        return None
    return {
        "type": m.group("type").lower(),
        "scope": m.group("scope"),
        "breaking": bool(m.group("break")),
        "desc": m.group("desc").strip(),
    }


def get_git_log(since_ref=None):
    """Get list of commits from git log."""
    if since_ref:
        cmd = f'git log {since_ref}..HEAD --pretty=format:"%H|%s|%an|%ad" --date=short'
    else:
        cmd = 'git log --pretty=format:"%H|%s|%an|%ad" --date=short'
    output = run_cmd(cmd)
    if not output:
        return []
    commits = []
    for line in output.splitlines():
        parts = line.split("|", 3)
        if len(parts) != 4:
            continue
        sha, subject, author, date = parts
        parsed = parse_commit(subject)
        commits.append({
            "sha": sha,
            "short_sha": sha[:7],
            "subject": subject,
            "author": author,
            "date": date,
            "parsed": parsed,
        })
    return commits


def get_latest_tag():
    """Get the most recent git tag."""
    tag = run_cmd("git describe --tags --abbrev=0 2>/dev/null")
    return tag or None


def get_tags():
    """Get all tags sorted by version."""
    output = run_cmd("git tag --sort=-version:refname")
    if not output:
        return []
    return output.splitlines()


def group_commits(commits):
    """Group commits by type for changelog rendering."""
    groups = {}
    others = []
    for c in commits:
        if c["parsed"]:
            t = c["parsed"]["type"]
            groups.setdefault(t, []).append(c)
        else:
            others.append(c)
    return groups, others


def render_changelog(commits, since_ref=None, unreleased_label="Unreleased"):
    """Render changelog markdown from commit list."""
    now = datetime.datetime.now().strftime("%Y-%m-%d")
    groups, others = group_commits(commits)

    lines = [
        "# Changelog",
        f"Generated: {now}",
        "",
        "All notable changes to this project will be documented in this file.",
        "",
        "The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/).",
        "",
    ]

    # Unreleased section
    unreleased = [c for c in commits if c["parsed"]]
    if since_ref:
        # Only commits since the tag are "unreleased"
        unreleased = [c for c in commits if c["parsed"]]
    else:
        unreleased = [c for c in commits if c["parsed"]]

    if unreleased:
        lines.append("## [Unreleased]")
        lines.append("")
        has_content = False
        for t in ("feat", "fix", "docs", "refactor", "perf", "test", "build", "ci", "chore", "sec"):
            if t in groups:
                lines.append(f"### {TYPE_LABELS[t]}")
                lines.append("")
                for c in groups[t]:
                    scope_part = f" ({c['parsed']['scope']})" if c["parsed"]["scope"] else ""
                    breaking_part = " 💥" if c["parsed"]["breaking"] else ""
                    lines.append(
                        f"- {c['parsed']['desc']}{scope_part}{breaking_part} "
                        f"([{c['short_sha']}](https://github.com/mistrysiddh/hermes-brain-template/commit/{c['sha']}))"
                    )
                lines.append("")
                has_content = True
        if others:
            lines.append("### Other")
            lines.append("")
            for c in others:
                lines.append(
                    f"- {c['subject']} ([{c['short_sha']}](https://github.com/mistrysiddh/hermes-brain-template/commit/{c['sha']}))"
                )
            lines.append("")
        if not has_content and not others:
            lines.append("*No changes.*")
            lines.append("")
    else:
        lines.append("## [Unreleased]")
        lines.append("")
        lines.append("*No changes.*")
        lines.append("")

    # Released sections (from tags)
    tags = get_tags()
    if tags:
        lines.append("## Released")
        lines.append("")
        for tag in tags[:10]:  # Limit to last 10 releases
            tag_commits = get_git_log(f"{tag}^..{tag}") if tag != tags[0] else get_git_log(f"{tags[0]}")
            if not tag_commits:
                continue
            tag_groups, tag_others = group_commits(tag_commits)
            lines.append(f"### [{tag}]")
            lines.append("")
            has_tag_content = False
            for t in ("feat", "fix", "docs", "refactor", "perf", "test", "build", "ci", "chore", "sec"):
                if t in tag_groups:
                    lines.append(f"#### {TYPE_LABELS[t]}")
                    lines.append("")
                    for c in tag_groups[t]:
                        scope_part = f" ({c['parsed']['scope']})" if c["parsed"]["scope"] else ""
                        breaking_part = " 💥" if c["parsed"]["breaking"] else ""
                        lines.append(
                            f"- {c['parsed']['desc']}{scope_part}{breaking_part} "
                            f"([{c['short_sha']}](https://github.com/mistrysiddh/hermes-brain-template/commit/{c['sha']}))"
                        )
                    lines.append("")
                    has_tag_content = True
            if tag_others:
                lines.append("#### Other")
                lines.append("")
                for c in tag_others:
                    lines.append(
                        f"- {c['subject']} ([{c['short_sha']}](https://github.com/mistrysiddh/hermes-brain-template/commit/{c['sha']}))"
                    )
                lines.append("")
            if not has_tag_content and not tag_others:
                lines.append("*No changes.*")
                lines.append("")

    lines.append("---")
    lines.append("")
    lines.append("Generated by `auto_changelog.py` — Hermes Brain CI/CD auto-changelog skill.")

    return "\n".join(lines)


# ---------------------------------------------------------------------------
# Self-test
# ---------------------------------------------------------------------------
def run_self_test():
    print("🧪 auto_changelog.py Self-Test Suite")
    print("=" * 50)
    passed = 0
    failed = 0

    # Test 1: parse_commit recognizes conventional commits
    try:
        c = parse_commit("feat(auth): add login endpoint")
        assert c is not None
        assert c["type"] == "feat"
        assert c["scope"] == "auth"
        assert c["desc"] == "add login endpoint"
        assert c["breaking"] is False

        c2 = parse_commit("fix!: remove deprecated API")
        assert c2 is not None
        assert c2["type"] == "fix"
        assert c2["scope"] is None
        assert c2["desc"] == "remove deprecated API"
        assert c2["breaking"] is True

        c3 = parse_commit("docs: update README")
        assert c3 is not None
        assert c3["type"] == "docs"
        assert c3["scope"] is None

        c4 = parse_commit("just a regular commit")
        assert c4 is None
        print("✅ Test 1: parse_commit recognizes conventional commits")
        passed += 1
    except Exception as e:
        print(f"❌ Test 1 failed: {e}")
        failed += 1

    # Test 2: group_commits organizes by type
    try:
        commits = [
            {"sha": "abc123", "short_sha": "abc123", "subject": "feat: add login", "author": "me", "date": "2026-01-01",
             "parsed": {"type": "feat", "scope": None, "breaking": False, "desc": "add login"}},
            {"sha": "def456", "short_sha": "def456", "subject": "fix: bug in parser", "author": "me", "date": "2026-01-02",
             "parsed": {"type": "fix", "scope": None, "breaking": False, "desc": "bug in parser"}},
            {"sha": "ghi789", "short_sha": "ghi789", "subject": "random commit", "author": "me", "date": "2026-01-03",
             "parsed": None},
        ]
        groups, others = group_commits(commits)
        assert "feat" in groups
        assert "fix" in groups
        assert len(groups["feat"]) == 1
        assert len(groups["fix"]) == 1
        assert len(others) == 1
        print("✅ Test 2: group_commits organizes by type")
        passed += 1
    except Exception as e:
        print(f"❌ Test 2 failed: {e}")
        failed += 1

    # Test 3: render_changelog produces valid markdown
    try:
        commits = [
            {"sha": "abc123def456", "short_sha": "abc123d", "subject": "feat: add login", "author": "me",
             "date": "2026-01-01",
             "parsed": {"type": "feat", "scope": "auth", "breaking": False, "desc": "add login"}},
        ]
        md = render_changelog(commits)
        assert "# Changelog" in md
        assert "## [Unreleased]" in md
        assert "### Features" in md
        assert "add login" in md
        assert "abc123d" in md
        print("✅ Test 3: render_changelog produces valid markdown")
        passed += 1
    except Exception as e:
        print(f"❌ Test 3 failed: {e}")
        failed += 1

    # Test 4: TYPE_LABELS covers all types
    try:
        expected = {
            "feat": "Features",
            "fix": "Bug Fixes",
            "docs": "Documentation",
            "refactor": "Refactoring",
            "perf": "Performance",
            "test": "Tests",
            "build": "Build / CI",
            "ci": "Build / CI",
            "chore": "Maintenance",
            "sec": "Security",
        }
        assert TYPE_LABELS == expected
        print("✅ Test 4: TYPE_LABELS covers all types")
        passed += 1
    except Exception as e:
        print(f"❌ Test 4 failed: {e}")
        failed += 1

    print("=" * 50)
    print(f"🎉 Self-tests: {passed} passed, {failed} failed")
    return failed == 0


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------
def parse_args():
    parser = argparse.ArgumentParser(
        description="Hermes Brain Auto-Changelog — CI/CD changelog from conventional commits.",
    )
    parser.add_argument("--vault", help="Path to the Hermes Brain vault root")
    parser.add_argument("--since", help="Git ref to start from (default: latest tag)")
    parser.add_argument("--output", help="Output file path (default: <vault>/04-Archives/Metrics/changelog/Changelog-<date>.md)")
    parser.add_argument("--dry-run", action="store_true", default=True, help="Report only, no file written (default)")
    parser.add_argument("--apply", action="store_true", help="Write changelog to vault (overrides --dry-run)")
    parser.add_argument("--test", action="store_true", help="Run built-in self-test suite")
    sub = parser.add_subparsers(dest="command", help="Command to run")
    sub.add_parser("generate", help="Generate changelog from git history (dry-run report)")
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

    if args.command and args.command != "generate":
        print(f"Error: Unknown command '{args.command}'. Use 'generate'.", file=sys.stderr)
        sys.exit(1)

    if not os.path.isdir(os.path.join(VAULT, ".git")):
        print(f"Error: {VAULT} is not a git repository.", file=sys.stderr)
        sys.exit(1)

    since_ref = args.since or get_latest_tag()
    commits = get_git_log(since_ref)
    print(f"📋 Found {len(commits)} commits since {since_ref or 'beginning'}")

    md = render_changelog(commits, since_ref=since_ref)

    if dry_run:
        print("\n📄 Changelog preview (dry-run — not written to vault):")
        print(md[:2500])
        if len(md) > 2500:
            print(f"\n... ({len(md) - 2500} more chars)")
    else:
        output_path = args.output
        if not output_path:
            today = datetime.datetime.now().strftime("%Y-%m-%d")
            output_path = os.path.join(CHANGELOG_DIR, f"Changelog-{today}.md")
        write_file(output_path, md)
        print(f"\n📄 Changelog written to {output_path}")


if __name__ == "__main__":
    main()
