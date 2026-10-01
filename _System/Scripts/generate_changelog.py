#!/usr/bin/env python3
"""
generate_changelog.py — Automated changelog generator for Hermes Brain template.

Generates release notes in your preferred format from git history.

Usage:
  python _System/Scripts/generate_changelog.py --since v1.22.21 --output release_notes.md
  python _System/Scripts/generate_changelog.py --since v1.22.21 --preview
  python _System/Scripts/generate_changelog.py --test
"""

import os
import re
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, List, Tuple, Optional

# --------------------------------------------------------------------------- #
# Configuration                                                               #
# --------------------------------------------------------------------------- #

# Commit type to section mapping (matches your release notes style)
TYPE_SECTION_MAP = {
    "feat": ("🚀 New Features", "Added"),
    "fix": ("🐞 Bug Fixes & Improvements", "Fixed"),
    "docs": ("📚 Documentation", "Added"),
    "perf": ("💡 Performance Improvements", "Improved"),
    "refactor": ("♻️ Code Refactoring", "Refactored"),
    "style": ("🎨 Style Updates", "Updated"),
    "test": ("🧪 Test Improvements", "Added"),
    "chore": ("🔧 Maintenance", "Updated"),
    "ci": ("🔧 CI/CD Improvements", "Updated"),
}

# Reverse mapping for quick lookup
SECTION_TITLE_TO_TYPE = {title: type_ for type_, (title, _) in TYPE_SECTION_MAP.items()}

# Default sections to always include (even if empty)
DEFAULT_SECTIONS = [
    "🚀 New Features",
    "🐞 Bug Fixes & Improvements", 
    "📚 Documentation",
    "🔧 Maintenance",
]

# --------------------------------------------------------------------------- #
# Git Helpers                                                                 #
# --------------------------------------------------------------------------- #

def run_git_command(cmd: List[str]) -> str:
    """Run git command and return stdout."""
    try:
        result = subprocess.run(
            ["git"] + cmd,
            capture_output=True,
            text=True,
            check=True,
        )
        return result.stdout.strip()
    except subprocess.CalledProcessError as e:
        print(f"Error running git {' '.join(cmd)}: {e.stderr}", file=sys.stderr)
        sys.exit(1)

def get_git_log(since: str, until: str = "HEAD") -> List[Dict[str, str]]:
    """Get git log between two points."""
    # Get commits with hash and subject
    log_format = "%h %s"
    git_log = run_git_command(["log", f"{since}..{until}", "--pretty=format:" + log_format])
    
    commits = []
    for line in git_log.split("\n"):
        if not line.strip():
            continue
        # Parse: hash subject
        parts = line.split(" ", 1)
        if len(parts) < 2:
            continue
        hash_val, subject = parts
        commits.append({"hash": hash_val, "subject": subject})
    
    return commits

# --------------------------------------------------------------------------- #
# Commit Parsing                                                              #
# --------------------------------------------------------------------------- #

def parse_conventional_commit(subject: str) -> Tuple[Optional[str], Optional[str], str]:
    """
    Parse conventional commit format.
    Returns: (type, scope, description) or (None, None, original) if not conventional.
    """
    # Match: type(scope)!: description OR type(scope): description OR type: description
    # The trailing "!" marks a breaking change (conventional commits spec); it is
    # moved onto the end of the description rather than dropped.
    match = re.match(r"^(\w+)(?:\(([^)]+)\))?(!)?:\s+(.+)$", subject)
    if not match:
        return None, None, subject

    commit_type, scope, breaking, description = match.groups()
    description = description.strip()
    if breaking:
        description += "!"
    return commit_type.lower(), scope if scope else None, description

def categorize_commits(commits: List[Dict[str, str]]) -> Dict[str, List[Dict[str, str]]]:
    """Group commits by type."""
    # Initialize all possible sections
    categorized = {title: [] for title, _ in TYPE_SECTION_MAP.values()}
    categorized["other"] = []  # For non-conventional commits

    for commit in commits:
        commit_type, scope, description = parse_conventional_commit(commit["subject"])

        if commit_type and commit_type in TYPE_SECTION_MAP:
            section_title, _ = TYPE_SECTION_MAP[commit_type]
            # Add scope to description if present
            if scope:
                desc_with_scope = f"{description} ({scope})"
            else:
                desc_with_scope = description
            categorized[section_title].append({
                "hash": commit["hash"],
                "description": desc_with_scope,
                "raw": commit["subject"]
            })
        else:
            categorized["other"].append({
                "hash": commit["hash"],
                "description": commit["subject"],
                "raw": commit["subject"]
            })

    return categorized

# --------------------------------------------------------------------------- #
# Changelog Generation                                                        #
# --------------------------------------------------------------------------- #

def generate_changelog_section(title: str, commits: List[Dict[str, str]]) -> str:
    """Generate a single changelog section."""
    if not commits:
        return f"## {title}\n\n*No changes in this category.*\n"
    
    lines = [f"## {title}\n"]
    for commit in commits:
        lines.append(f"- {commit['description']}")
    lines.append("")  # Blank line after section
    return "\n".join(lines)

def generate_changelog(
    since: str, 
    until: str = "HEAD",
    include_other: bool = False
) -> str:
    """Generate full changelog."""
    # Get commits
    commits = get_git_log(since, until)
    if not commits:
        return "# Changelog\n\nNo commits found between {since} and {until}.\n"
    
    # Categorize
    categorized = categorize_commits(commits)
    
    # Build changelog
    lines = ["# Changelog\n"]
    
    # Add sections in preferred order
    section_order = [title for title, _ in TYPE_SECTION_MAP.values()]
    if include_other:
        section_order.append("Other Changes")
    
    for title in section_order:
        # categorize_commits groups non-conventional commits under "other",
        # but the section heading reads "Other Changes" - translate the key.
        key = "other" if title == "Other Changes" else title
        if key in categorized:
            lines.append(generate_changelog_section(title, categorized[key]))
    
    # Add metadata
    lines.extend([
        "---\n",
        f"*Generated on {datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M UTC')}*\n",
        f"*Based on commits {since}..{until}*\n",
    ])
    
    return "\n".join(lines)

# --------------------------------------------------------------------------- #
# Self Test                                                                   #
# --------------------------------------------------------------------------- #

def run_self_test() -> bool:
    """Run automated self-test."""
    print("=" * 60)
    print("🧪 generate_changelog.py Self-Test")
    print("=" * 60)
    
    # Create a temporary git repo for testing
    import tempfile
    import shutil
    
    test_dir = Path(tempfile.mkdtemp(prefix="hb-changelog-test-"))
    try:
        os.chdir(test_dir)
        subprocess.run(["git", "init"], check=True, capture_output=True)
        subprocess.run(["git", "config", "user.name", "Test User"], check=True, capture_output=True)
        subprocess.run(["git", "config", "user.email", "test@example.com"], check=True, capture_output=True)
        
        # Create initial commit
        (test_dir / "README.md").write_text("# Test Repo\n", encoding="utf-8")
        subprocess.run(["git", "add", "README.md"], check=True, capture_output=True)
        subprocess.run(["git", "commit", "-m", "chore: initialize repo"], check=True, capture_output=True)
        
        # Create test commits
        test_commits = [
            "feat: add new feature",
            "fix: fix critical bug",
            "docs: update documentation",
            "chore: update dependencies",
            "refactor: cleanup utils module",
            "test: add unit tests",
            "ci: update github workflow",
            "style: fix indentation",
            "perf: optimize database query",
            "Just a regular commit",  # Non-conventional
        ]
        
        for i, msg in enumerate(test_commits):
            (test_dir / f"test{i}.txt").write_text(f"Test file {i}\n", encoding="utf-8")
            subprocess.run(["git", "add", f"test{i}.txt"], check=True, capture_output=True)
            subprocess.run(["git", "commit", "-m", msg], check=True, capture_output=True)
        
        # Test changelog generation
        changelog = generate_changelog("HEAD~10", "HEAD", include_other=True)
        
        # Verify sections exist
        assert "## 🚀 New Features" in changelog
        assert "## 🐞 Bug Fixes & Improvements" in changelog
        assert "## 📚 Documentation" in changelog
        assert "## 🔧 Maintenance" in changelog
        assert "## Other Changes" in changelog
        
        # Verify content
        assert "- add new feature" in changelog
        assert "- fix critical bug" in changelog
        assert "- update documentation" in changelog
        assert "- Just a regular commit" in changelog  # From other section
        
        print("✅ Self-test PASSED")
        print(f"Generated changelog preview:\n{changelog[:500]}...")
        return True
        
    except Exception as e:
        print(f"❌ Self-test FAILED: {e}")
        import traceback
        traceback.print_exc()
        return False
    finally:
        os.chdir("C:/")  # Reset to safe directory
        shutil.rmtree(test_dir, ignore_errors=True)

# --------------------------------------------------------------------------- #
# Main                                                                        #
# --------------------------------------------------------------------------- #

def main():
    import argparse
    
    parser = argparse.ArgumentParser(
        description="Generate changelog for Hermes Brain template releases"
    )
    parser.add_argument(
        "--since",
        required=True,
        help="Starting tag or commit (e.g. v1.22.21)"
    )
    parser.add_argument(
        "--until",
        default="HEAD",
        help="Ending tag or commit (default: HEAD)"
    )
    parser.add_argument(
        "--output",
        help="Output file path (if not provided, prints to stdout)"
    )
    parser.add_argument(
        "--preview",
        action="store_true",
        help="Print preview to stdout (same as --output to console)"
    )
    parser.add_argument(
        "--test",
        action="store_true",
        help="Run self-tests and exit"
    )
    parser.add_argument(
        "--include-other",
        action="store_true",
        help="Include non-conventional commits in 'Other Changes' section"
    )
    
    args = parser.parse_args()
    
    if args.test:
        if run_self_test():
            sys.exit(0)
        else:
            sys.exit(1)
    
    # Generate changelog
    changelog = generate_changelog(
        since=args.since,
        until=args.until,
        include_other=args.include_other,
    )
    
    # Output
    if args.output or args.preview:
        output_path = args.output if args.output else None
        if output_path:
            Path(output_path).write_text(changelog, encoding="utf-8")
            print(f"✅ Changelog written to: {output_path}")
        else:
            print(changelog)
    else:
        # Default: show preview
        print("📝 Changelog Preview (use --output to save to file):\n")
        print(changelog)

if __name__ == "__main__":
    main()