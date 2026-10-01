#!/usr/bin/env python3
"""
test_generate_changelog.py — Self-test suite for generate_changelog.py
"""

import os
import subprocess
import sys
import tempfile
import shutil
from pathlib import Path

# Add the script directory to path so we can import the module
script_dir = Path(__file__).parent.parent
sys.path.insert(0, str(script_dir))

from generate_changelog import (
    run_git_command,
    get_git_log,
    parse_conventional_commit,
    categorize_commits,
    generate_changelog_section,
    generate_changelog,
    run_self_test
)

def test_git_helpers():
    """Test git helper functions."""
    print("Testing git helpers...")
    
    # We'll test these in a temporary repo
    test_dir = Path(tempfile.mkdtemp(prefix="hb-test-git-"))
    original_cwd = os.getcwd()
    
    try:
        os.chdir(test_dir)
        subprocess.run(["git", "init"], check=True, capture_output=True)
        subprocess.run(["git", "config", "user.name", "Test User"], check=True, capture_output=True)
        subprocess.run(["git", "config", "user.email", "test@example.com"], check=True, capture_output=True)
        
        # Create initial commit
        (test_dir / "README.md").write_text("# Test\n", encoding="utf-8")
        subprocess.run(["git", "add", "README.md"], check=True, capture_output=True)
        subprocess.run(["git", "commit", "-m", "initial commit"], check=True, capture_output=True)
        
        # Test run_git_command
        result = run_git_command(["rev-parse", "HEAD"])
        assert len(result) == 40  # SHA-1 hash
        print("  ✅ run_git_command works")
        
        # Test get_git_log
        (test_dir / "test.txt").write_text("test\n", encoding="utf-8")
        subprocess.run(["git", "add", "test.txt"], check=True, capture_output=True)
        subprocess.run(["git", "commit", "-m", "feat: add test"], check=True, capture_output=True)
        
        logs = get_git_log("HEAD~1", "HEAD")
        assert len(logs) == 1
        assert logs[0]["subject"] == "feat: add test"
        print("  ✅ get_git_log works")
        
    finally:
        os.chdir(original_cwd)
        shutil.rmtree(test_dir, ignore_errors=True)

def test_commit_parsing():
    """Test commit parsing functions."""
    print("Testing commit parsing...")
    
    # Test conventional commits
    assert parse_conventional_commit("feat: add new feature") == ("feat", None, "add new feature")
    assert parse_conventional_commit("fix(core): fix bug") == ("fix", "core", "fix bug")
    assert parse_conventional_commit("docs: update README") == ("docs", None, "update README")
    assert parse_conventional_commit("refactor!: drop support") == ("refactor", None, "drop support!")  # Note: ! stays in description
    
    # Test non-conventional
    assert parse_conventional_commit("Just a regular commit") == (None, None, "Just a regular commit")
    assert parse_conventional_commit("Merge branch 'main'") == (None, None, "Merge branch 'main'")
    
    print("  ✅ Commit parsing works")

def test_categorization():
    """Test commit categorization."""
    print("Testing commit categorization...")
    
    commits = [
        {"hash": "abc123", "subject": "feat: add new feature"},
        {"hash": "def456", "subject": "fix: fix critical bug"},
        {"hash": "ghi789", "subject": "docs: update documentation"},
        {"hash": "jkl012", "subject": "Just a regular commit"},
        {"hash": "mno345", "subject": "feat(ui): add button"},
        {"hash": "pqr678", "subject": "perf: optimize query"},
    ]
    
    categorized = categorize_commits(commits)
    
    # Check sections exist
    assert "🚀 New Features" in categorized
    assert "🐞 Bug Fixes & Improvements" in categorized
    assert "📚 Documentation" in categorized
    assert "💡 Performance Improvements" in categorized
    assert "other" in categorized
    
    # Check counts
    assert len(categorized["🚀 New Features"]) == 2  # feat and feat(ui)
    assert len(categorized["🐞 Bug Fixes & Improvements"]) == 1
    assert len(categorized["📚 Documentation"]) == 1
    assert len(categorized["💡 Performance Improvements"]) == 1
    assert len(categorized["other"]) == 1
    
    print("  ✅ Commit categorization works")

def test_section_generation():
    """Test changelog section generation."""
    print("Testing section generation...")
    
    # Empty section
    empty = generate_changelog_section("Test Section", [])
    assert "## Test Section" in empty
    assert "*No changes in this category.*" in empty
    
    # Section with commits
    commits = [
        {"hash": "abc123", "description": "add feature A"},
        {"hash": "def456", "description": "fix bug B"},
    ]
    section = generate_changelog_section("Test Section", commits)
    assert "## Test Section" in section
    assert "- add feature A" in section
    assert "- fix bug B" in section
    assert section.count("\n") == 4  # Title + 2 items + blank line
    
    print("  ✅ Section generation works")

def test_full_changelog():
    """Test full changelog generation."""
    print("Testing full changelog generation...")
    
    test_dir = Path(tempfile.mkdtemp(prefix="hb-test-full-"))
    original_cwd = os.getcwd()
    
    try:
        os.chdir(test_dir)
        subprocess.run(["git", "init"], check=True, capture_output=True)
        subprocess.run(["git", "config", "user.name", "Test User"], check=True, capture_output=True)
        subprocess.run(["git", "config", "user.email", "test@example.com"], check=True, capture_output=True)
        
        # Initial commit
        (test_dir / "README.md").write_text("# Test\n", encoding="utf-8")
        subprocess.run(["git", "add", "README.md"], check=True, capture_output=True)
        subprocess.run(["git", "commit", "-m", "chore: initialize"], check=True, capture_output=True)
        
        # Create some commits
        test_commits = [
            "feat: add authentication system",
            "fix: fix login bug",
            "docs: update API docs",
            "perf: optimize database query",
            "Just a regular commit",
        ]
        
        for i, msg in enumerate(test_commits):
            (test_dir / f"commit{i}.txt").write_text(f"Content {i}\n", encoding="utf-8")
            subprocess.run(["git", "add", f"commit{i}.txt"], check=True, capture_output=True)
            subprocess.run(["git", "commit", "-m", msg], check=True, capture_output=True)
        
        # Generate changelog
        changelog = generate_changelog("HEAD~5", "HEAD", include_other=True)
        
        # Verify structure
        assert "# Changelog" in changelog
        assert "## 🚀 New Features" in changelog
        assert "## 🐞 Bug Fixes & Improvements" in changelog
        assert "## 📚 Documentation" in changelog
        assert "## 💡 Performance Improvements" in changelog
        assert "## Other Changes" in changelog
        
        # Verify content
        assert "add authentication system" in changelog
        assert "fix login bug" in changelog
        assert "update API docs" in changelog
        assert "optimize database query" in changelog
        assert "Just a regular commit" in changelog
        
        print("  ✅ Full changelog generation works")
        
    finally:
        os.chdir(original_cwd)
        shutil.rmtree(test_dir, ignore_errors=True)

def main():
    """Run all tests."""
    print("=" * 60)
    print("🧪 test_generate_changelog.py Test Suite")
    print("=" * 60)
    
    try:
        test_git_helpers()
        test_commit_parsing()
        test_categorization()
        test_section_generation()
        test_full_changelog()
        
        print("\n" + "=" * 60)
        print("🎉 ALL TESTS PASSED")
        print("=" * 60)
        return True
        
    except Exception as e:
        print(f"\n❌ TEST FAILED: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)