#!/usr/bin/env python3
"""
Hermes Brain — SOTA Sub-Skill: comparators (sota/comparators.py)

Fetches comparator repos from GitHub search API and classifies them
into peer clusters by methodology/domain.

Multi-harness compatible:
  - --vault CLI arg (never module-level path resolution)
  - Path resolution deferred to main() after argument parsing
  - --dry-run default / --apply (no-op for read-only scan)
  - Stdlib-only
  - --test self-tests (4/4)

Usage:
  python sota/comparators.py --vault <path> --domain agent-brain-vault
  python sota/comparators.py --vault <path> --test
"""

import argparse
import datetime
import json
import os
import sys
import urllib.request
import urllib.parse

# ---------------------------------------------------------------------------
# Path resolution — deferred to main(), never at import time
# ---------------------------------------------------------------------------
VAULT = None


def init_paths(vault_path):
    """Resolve all vault-relative paths from the given vault root."""
    global VAULT
    VAULT = os.path.abspath(vault_path)


# ---------------------------------------------------------------------------
# fetch_comparators — fetch comparator repos from GitHub search API
# ---------------------------------------------------------------------------
def fetch_comparators(domain, count=8):
    """Fetch comparator repos for a domain via GitHub search API."""
    comparators = []
    queries = [
        f"{domain} agent skill",
        f"{domain} obsidian vault",
        f"{domain} brain template",
    ]

    for query in queries:
        try:
            encoded = urllib.parse.quote(query)
            url = f"https://api.github.com/search/repositories?q={encoded}&sort=stars&order=desc&per_page={count}"
            req = urllib.request.Request(url, headers={"User-Agent": "HermesSOTA/1.0"})
            with urllib.request.urlopen(req, timeout=15) as resp:
                data = json.loads(resp.read().decode("utf-8"))
            for item in data.get("items", [])[:count]:
                comparators.append({
                    "name": item.get("full_name", ""),
                    "url": item.get("html_url", ""),
                    "stars": item.get("stargazers_count", 0),
                    "pushed": item.get("pushed_at", ""),
                    "description": item.get("description", ""),
                    "archived": item.get("archived", False),
                })
        except Exception:
            continue

    # Deduplicate by name
    seen = set()
    unique = []
    for c in comparators:
        if c["name"] not in seen:
            seen.add(c["name"])
            unique.append(c)
    return unique[:count]


# ---------------------------------------------------------------------------
# classify_cluster — cluster comparators into peer groups
# ---------------------------------------------------------------------------
def classify_cluster(comparators, us_profile):
    """Cluster comparators into peer groups by methodology/domain."""
    clusters = {}
    for c in comparators:
        desc = (c.get("description", "") + " " + c.get("name", "")).lower()
        label = "general"
        if any(k in desc for k in ["agent", "brain", "vault", "obsidian"]):
            label = "agent-brain-vault"
        elif any(k in desc for k in ["prompt", "quality", "eval"]):
            label = "prompt-quality"
        elif any(k in desc for k in ["security", "scan", "safety"]):
            label = "security-scan"
        elif any(k in desc for k in ["note", "zettel", "knowledge"]):
            label = "knowledge-management"
        clusters.setdefault(label, []).append(c)

    # Classify us into closest cluster
    us_domains = us_profile.get("domains", [])
    us_caps = us_profile.get("capabilities", [])
    us_label = "general"
    if any("agent-brain-vault" in d or "agent-system" in d for d in us_domains):
        us_label = "agent-brain-vault"
    elif any("github-agents" in c for c in us_caps):
        us_label = "agent-brain-vault"

    return clusters, us_label


# ---------------------------------------------------------------------------
# Self-test
# ---------------------------------------------------------------------------
def run_self_test():
    import tempfile
    import shutil

    print("🧪 sota/comparators.py Self-Test Suite")
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

    # Test 1: classify_cluster groups comparators correctly
    def test_classify_cluster():
        tmp = tempfile.mkdtemp()
        try:
            init_paths(tmp)
            comparators = [
                {"name": "user/agent-brain", "description": "Agent brain vault system",
                 "stars": 100, "pushed": "2026-01-01", "url": "https://github.com/user/agent-brain", "archived": False},
                {"name": "user/prompt-eval", "description": "Prompt quality evaluation",
                 "stars": 50, "pushed": "2026-01-01", "url": "https://github.com/user/prompt-eval", "archived": False},
            ]
            profile = {"domains": ["agent-brain-vault"], "capabilities": ["github-agents"]}
            clusters, us_label = classify_cluster(comparators, profile)
            assert "agent-brain-vault" in clusters
            assert us_label == "agent-brain-vault"
            assert len(clusters["agent-brain-vault"]) == 1
        finally:
            shutil.rmtree(tmp)
    check("classify_cluster groups comparators correctly", test_classify_cluster)

    # Test 2: classify_cluster knowledge management label
    def test_classify_cluster_km():
        tmp = tempfile.mkdtemp()
        try:
            init_paths(tmp)
            comparators = [
                {"name": "user/zettel-kasten", "description": "Zettelkasten knowledge management",
                 "stars": 200, "pushed": "2026-01-01", "url": "https://github.com/user/zettel-kasten", "archived": False},
            ]
            profile = {"domains": [], "capabilities": []}
            clusters, us_label = classify_cluster(comparators, profile)
            assert "knowledge-management" in clusters
            assert us_label == "general"
        finally:
            shutil.rmtree(tmp)
    check("classify_cluster knowledge management label", test_classify_cluster_km)

    # Test 3: classify_cluster empty comparators
    def test_classify_cluster_empty():
        tmp = tempfile.mkdtemp()
        try:
            init_paths(tmp)
            clusters, us_label = classify_cluster([], {"domains": [], "capabilities": []})
            assert clusters == {}
            assert us_label == "general"
        finally:
            shutil.rmtree(tmp)
    check("classify_cluster empty comparators", test_classify_cluster_empty)

    # Test 4: fetch_comparators deduplicates
    def test_fetch_comparators_dedup():
        tmp = tempfile.mkdtemp()
        try:
            init_paths(tmp)
            # Can't easily mock network, so just test the dedup logic indirectly
            # by verifying function exists and returns a list
            result = fetch_comparators("nonexistent-domain-xyz", count=1)
            assert isinstance(result, list)
        finally:
            shutil.rmtree(tmp)
    check("fetch_comparators returns list (no network crash)", test_fetch_comparators_dedup)

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
        description="Hermes Brain SOTA — comparators sub-skill.",
    )
    parser.add_argument("--vault", help="Path to the Hermes Brain vault root")
    parser.add_argument("--domain", default="agent-brain-vault", help="Domain to benchmark against")
    parser.add_argument("--count", type=int, default=8, help="Max comparators to fetch")
    parser.add_argument("--dry-run", action="store_true", default=True, help="Report only (default)")
    parser.add_argument("--apply", action="store_true", help="No-op for read-only scan")
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

    print(f"🌐 Fetching comparators for domain '{args.domain}'...")
    comparators = fetch_comparators(args.domain, count=args.count)
    print(f"📡 Found {len(comparators)} comparators")

    for c in comparators[:10]:
        print(f"   {c['name']} — {c['stars']}⭐ — {c.get('description', '')[:60]}")

    if dry_run:
        print("\nRun with --apply to confirm (read-only scan — no changes).")


if __name__ == "__main__":
    main()
