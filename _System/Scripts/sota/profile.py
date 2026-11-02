#!/usr/bin/env python3
"""
Hermes Brain — SOTA Sub-Skill: profile (sota/profile.py)

Builds a capability profile of the current repo from its own evidence:
  - domains detected from folder structure
  - capabilities detected from files/dirs
  - tech stack indicators
  - doc count, test presence, CI presence, frontmatter usage

Multi-harness compatible:
  - --vault CLI arg (never module-level path resolution)
  - Path resolution deferred to main() after argument parsing
  - --dry-run default / --apply (no-op for read-only profile)
  - Stdlib-only
  - --test self-tests (4/4)

Usage:
  python sota/profile.py --vault <path>
  python sota/profile.py --vault <path> --test
"""

import argparse
import os
import sys

# ---------------------------------------------------------------------------
# Path resolution — deferred to main(), never at import time
# ---------------------------------------------------------------------------
VAULT = None


def init_paths(vault_path):
    """Resolve all vault-relative paths from the given vault root."""
    global VAULT
    VAULT = os.path.abspath(vault_path)


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


def walk_md(vault_dir, exclude_dirs=None, exclude_files=None):
    """Walk vault_dir yielding (full_path, rel_path, name, content) for .md files."""
    exclude_dirs = exclude_dirs or {".obsidian", ".git", ".trash", ".sota"}
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
# build_us_profile — build capability profile of current repo
# ---------------------------------------------------------------------------
def build_us_profile(vault_dir):
    """Build a capability profile of the current repo from its own evidence."""
    profile = {
        "domains": [],
        "capabilities": [],
        "tech_stack": [],
        "doc_count": 0,
        "has_tests": False,
        "has_ci": False,
        "has_frontmatter": 0,
        "total_notes": 0,
    }

    notes = []
    for full, rel, name, content in walk_md(vault_dir):
        notes.append({"rel_path": rel, "name": name, "content": content})

    profile["total_notes"] = len(notes)
    profile["doc_count"] = len(notes)

    # Check for CI, tests, frontmatter usage
    for full, rel, name, content in walk_md(vault_dir):
        if "---\n" in content[:10]:
            profile["has_frontmatter"] += 1
        if any(kw in content.lower() for kw in ["test", "spec", "pytest", "unittest"]):
            profile["has_tests"] = True

    ci_dirs = [
        os.path.join(vault_dir, ".github", "workflows"),
        os.path.join(vault_dir, ".gitlab"),
        os.path.join(vault_dir, ".circleci"),
    ]
    for ci_path in ci_dirs:
        if os.path.exists(ci_path):
            profile["has_ci"] = True
            break

    # Detect domain from folder structure
    if os.path.isdir(os.path.join(vault_dir, "01-Projects")):
        profile["domains"].append("agent-brain-vault")
    if os.path.isdir(os.path.join(vault_dir, "_System")):
        profile["domains"].append("agent-system")
    if os.path.isdir(os.path.join(vault_dir, ".github", "agents")):
        profile["capabilities"].append("github-agents")

    return profile


# ---------------------------------------------------------------------------
# Self-test
# ---------------------------------------------------------------------------
def run_self_test():
    import tempfile
    import shutil

    print("🧪 sota/profile.py Self-Test Suite")
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

    # Test 1: build_us_profile extracts repo profile
    def test_build_us_profile():
        tmp = tempfile.mkdtemp()
        try:
            init_paths(tmp)
            os.makedirs(os.path.join(tmp, "01-Projects"), exist_ok=True)
            os.makedirs(os.path.join(tmp, "_System"), exist_ok=True)
            os.makedirs(os.path.join(tmp, ".github", "agents"), exist_ok=True)
            write_file(os.path.join(tmp, "01-Projects", "test.md"),
                       "---\nname: test\n---\n# Test\n\nContent.")
            profile = build_us_profile(tmp)
            assert profile["total_notes"] >= 1
            assert "agent-brain-vault" in profile["domains"]
            assert "agent-system" in profile["domains"]
            assert "github-agents" in profile["capabilities"]
        finally:
            shutil.rmtree(tmp)
    check("build_us_profile extracts repo profile", test_build_us_profile)

    # Test 2: build_us_profile detects tests and CI
    def test_build_us_profile_tests_ci():
        tmp = tempfile.mkdtemp()
        try:
            init_paths(tmp)
            os.makedirs(os.path.join(tmp, ".github", "workflows"), exist_ok=True)
            write_file(os.path.join(tmp, "test_something.md"), "# Test\n\npytest is used here.")
            write_file(os.path.join(tmp, "normal.md"), "# Normal\n\nJust content.")
            profile = build_us_profile(tmp)
            assert profile["has_tests"] is True
            assert profile["has_ci"] is True
        finally:
            shutil.rmtree(tmp)
    check("build_us_profile detects tests and CI", test_build_us_profile_tests_ci)

    # Test 3: build_us_profile empty vault
    def test_build_us_profile_empty():
        tmp = tempfile.mkdtemp()
        try:
            init_paths(tmp)
            profile = build_us_profile(tmp)
            assert profile["total_notes"] == 0
            assert profile["domains"] == []
            assert profile["capabilities"] == []
            assert profile["has_frontmatter"] == 0
        finally:
            shutil.rmtree(tmp)
    check("build_us_profile empty vault", test_build_us_profile_empty)

    # Test 4: build_us_profile frontmatter count
    def test_build_us_profile_frontmatter():
        tmp = tempfile.mkdtemp()
        try:
            init_paths(tmp)
            write_file(os.path.join(tmp, "fm.md"), "---\nname: test\n---\n# Frontmatter")
            write_file(os.path.join(tmp, "nofm.md"), "# No frontmatter")
            profile = build_us_profile(tmp)
            assert profile["has_frontmatter"] == 1
        finally:
            shutil.rmtree(tmp)
    check("build_us_profile frontmatter count", test_build_us_profile_frontmatter)

    print("=" * 50)
    print(f"🎉 Self-tests: {passed} passed, {failed} failed")
    return failed == 0


def write_file(path, content):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        f.write(content)


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------
def parse_args():
    parser = argparse.ArgumentParser(
        description="Hermes Brain SOTA — profile sub-skill.",
    )
    parser.add_argument("--vault", help="Path to the Hermes Brain vault root")
    parser.add_argument("--dry-run", action="store_true", default=True, help="Report only (default)")
    parser.add_argument("--apply", action="store_true", help="No-op for read-only profile")
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
    dry_run = not args.apply

    if not os.path.isdir(VAULT):
        print(f"Error: Vault not found at {VAULT}", file=sys.stderr)
        sys.exit(1)

    profile = build_us_profile(VAULT)

    print(f"📋 Vault profile")
    print(f"   Total notes: {profile['total_notes']}")
    print(f"   Domains: {', '.join(profile['domains']) or 'none'}")
    print(f"   Capabilities: {', '.join(profile['capabilities']) or 'none'}")
    print(f"   Has tests: {profile['has_tests']}")
    print(f"   Has CI: {profile['has_ci']}")
    print(f"   Notes with frontmatter: {profile['has_frontmatter']}")

    if dry_run:
        print("\nRun with --apply to confirm (read-only profile — no changes).")


if __name__ == "__main__":
    main()
