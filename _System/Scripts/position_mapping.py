#!/usr/bin/env python3
"""
Hermes Brain — Position Mapping Skill (multi-harness compatible).

Maps each note's position in the vault hierarchy:
- folder depth from vault root
- parent MOC (nearest Map of Contents)
- incoming/outgoing wikilink counts
- orphan detection (no links, no parent frontmatter)
- position score (connectivity + depth heuristic)

Every note gets a position record. With --apply, writes a position map
report and optionally injects `position:` frontmatter into notes.

Multi-harness compliant:
  - --vault CLI arg, deferred path resolution via init_paths()
  - --dry-run default / --apply for human-in-the-loop approval
  - stdlib-only
  - --test built-in self-test suite
"""

import argparse
import hashlib
import json
import os
import re
import sys
from collections import defaultdict
from datetime import datetime
from pathlib import Path

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


def write_file(path, content):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        f.write(content)


def iter_md_files(vault):
    """Yield all .md files under vault, skipping .git."""
    for root, dirs, files in os.walk(vault):
        dirs[:] = [d for d in dirs if d != ".git"]
        for f in files:
            if f.endswith(".md"):
                yield os.path.join(root, f)


WIKILINK_RE = re.compile(r"\[\[([^\]]+)\]\]")


def extract_wikilinks(content):
    """Return list of link targets (normalized, stripped of alias/anchor)."""
    targets = []
    for m in WIKILINK_RE.finditer(content):
        target = m.group(1)
        target = target.split("|")[0]
        target = target.split("#")[0]
        target = target.rstrip("/").rstrip("\\")
        targets.append(target)
    return targets


def parse_frontmatter(content):
    """Return (frontmatter_dict, body) or ({}, content) if no frontmatter."""
    if not content.startswith("---\n"):
        return {}, content
    end = content.find("\n---\n", 4)
    if end == -1:
        return {}, content
    fm_text = content[4:end]
    body = content[end + 5:]
    fm = {}
    for line in fm_text.splitlines():
        if ":" in line:
            key, _, val = line.partition(":")
            fm[key.strip()] = val.strip()
    return fm, body


def build_frontmatter(fm_dict):
    lines = ["---"]
    for k in sorted(fm_dict.keys()):
        lines.append(f"{k}: {fm_dict[k]}")
    lines.append("---")
    return "\n".join(lines) + "\n"


# ---------------------------------------------------------------------------
# Position mapping core
# ---------------------------------------------------------------------------
def scan_vault(vault):
    """Scan vault and build position map for every note."""
    md_files = list(iter_md_files(vault))

    # Index: normalized relative path -> file info
    notes = {}
    for path in md_files:
        rel = os.path.relpath(path, vault)
        notes[rel] = {
            "path": path,
            "rel": rel,
            "depth": rel.count(os.sep),
            "folder": os.path.dirname(rel),
            "name": os.path.basename(rel)[:-3],
            "content": read_file(path),
        }

    # Parse frontmatter + wikilinks for each note
    for rel, info in notes.items():
        fm, body = parse_frontmatter(info["content"])
        info["frontmatter"] = fm
        info["body"] = body
        info["links_out"] = extract_wikilinks(info["content"])
        info["parent"] = fm.get("parent", "")
        info["position"] = fm.get("position", "")

    # Build incoming link counts
    # Resolve each target relative to the source note's folder, then
    # normalize against the vault root so it matches notes keys.
    links_in = defaultdict(list)
    for rel, info in notes.items():
        source_dir = os.path.dirname(rel)
        for target in info["links_out"]:
            candidates = []
            # Resolve relative to source note's folder
            resolved = os.path.normpath(os.path.join(source_dir, target))
            candidates.append(resolved)
            candidates.append(resolved + ".md")
            # Also try vault-root resolution
            candidates.append(target)
            candidates.append(target + ".md")
            matched = False
            for nt in candidates:
                nt_norm = os.path.normpath(nt)
                if nt_norm in notes:
                    links_in[nt_norm].append(rel)
                    matched = True
                    break

    # Find nearest MOC for each note (search up folder tree)
    moc_files = {rel for rel in notes if os.path.basename(rel) == "_MOC.md"}

    def nearest_moc(folder):
        """Walk up folder tree to find nearest _MOC.md."""
        current = folder
        while True:
            moc_rel = os.path.join(current, "_MOC.md") if current else "_MOC.md"
            if moc_rel in notes:
                return moc_rel
            if not current or current == ".":
                break
            parent = os.path.dirname(current)
            if parent == current:
                break
            current = parent
        return None

    # Build position records
    positions = {}
    for rel, info in notes.items():
        links_out_count = len(info["links_out"])
        links_in_count = len(links_in.get(rel, []))
        total_links = links_out_count + links_in_count

        # Position score: connectivity weighted more than depth
        # Higher score = more central/important position
        depth = info["depth"]
        position_score = round(total_links * 1.0 - depth * 0.5, 2)

        moc = nearest_moc(info["folder"])

        # Determine position tier
        if depth == 0:
            tier = "root"
        elif total_links >= 10:
            tier = "hub"
        elif total_links >= 3:
            tier = "connector"
        elif total_links == 0:
            tier = "orphan"
        else:
            tier = "leaf"

        # Orphan check: no links in/out AND no parent frontmatter
        is_orphan = (total_links == 0 and not info["parent"])

        positions[rel] = {
            "rel": rel,
            "name": info["name"],
            "folder": info["folder"],
            "depth": depth,
            "tier": tier,
            "links_out": links_out_count,
            "links_in": links_in_count,
            "total_links": total_links,
            "position_score": position_score,
            "parent": info["parent"],
            "position": info["position"],
            "nearest_moc": moc or "",
            "is_orphan": is_orphan,
            "frontmatter": info["frontmatter"],
        }

    return positions


def generate_position_report(positions, vault):
    """Generate markdown position map report."""
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    total = len(positions)
    orphans = [p for p in positions.values() if p["is_orphan"]]
    hubs = [p for p in positions.values() if p["tier"] == "hub"]
    connectors = [p for p in positions.values() if p["tier"] == "connector"]
    leaves = [p for p in positions.values() if p["tier"] == "leaf"]
    roots = [p for p in positions.values() if p["tier"] == "root"]

    # Depth distribution
    depth_dist = defaultdict(int)
    for p in positions.values():
        depth_dist[p["depth"]] += 1

    # Tier distribution
    tier_dist = defaultdict(int)
    for p in positions.values():
        tier_dist[p["tier"]] += 1

    lines = [
        "# Position Map Report",
        f"Generated: {now}",
        f"Vault: {vault}",
        "",
        "## Summary",
        f"- **Total notes**: {total}",
        f"- **Root notes**: {len(roots)}",
        f"- **Hub notes** (10+ links): {len(hubs)}",
        f"- **Connector notes** (3-9 links): {len(connectors)}",
        f"- **Leaf notes** (1-2 links): {len(leaves)}",
        f"- **Orphaned notes** (no links, no parent): {len(orphans)}",
        "",
        "### Depth Distribution",
        "",
    ]
    for d in sorted(depth_dist.keys()):
        lines.append(f"- Depth {d}: {depth_dist[d]} note(s)")

    lines += [
        "",
        "### Tier Distribution",
        "",
    ]
    for tier in ["root", "hub", "connector", "leaf", "orphan"]:
        lines.append(f"- {tier}: {tier_dist[tier]} note(s)")

    lines += [
        "",
        "## Hub Notes (Most Connected)",
        "",
        "| Note | Folder | Depth | Links (in/out) | Score |",
        "|------|--------|-------|----------------|-------|",
    ]
    for p in sorted(hubs, key=lambda x: -x["position_score"])[:15]:
        lines.append(
            f"| {p['name']} | {p['folder']} | {p['depth']} | "
            f"{p['links_in']}/{p['links_out']} | {p['position_score']} |"
        )

    lines += [
        "",
        "## Orphaned Notes (No Links, No Parent)",
        "",
    ]
    if orphans:
        lines.append("| Note | Folder | Depth |")
        lines.append("|------|--------|-------|")
        for p in sorted(orphans, key=lambda x: x["name"]):
            lines.append(f"| {p['name']} | {p['folder']} | {p['depth']} |")
    else:
        lines.append("*None — every note has at least one connection or parent.*")

    lines += [
        "",
        "## Position Map (All Notes)",
        "",
        "| Note | Folder | Depth | Tier | Links | Score | MOC |",
        "|------|--------|-------|------|-------|-------|-----|",
    ]
    for p in sorted(positions.values(), key=lambda x: (x["depth"], x["name"])):
        lines.append(
            f"| {p['name']} | {p['folder']} | {p['depth']} | "
            f"{p['tier']} | {p['total_links']} | {p['position_score']} | "
            f"{p['nearest_moc'] or '—'} |"
        )

    return "\n".join(lines)


def inject_position_frontmatter(positions, vault, dry_run=True):
    """Inject position: frontmatter into notes missing it."""
    results = []
    for rel, p in positions.items():
        if p["position"]:
            continue  # already has position

        info = positions[rel]  # already have full info
        file_path = info.get("path") or os.path.join(vault, rel)

        # Read current content
        content = read_file(file_path)
        if not content:
            results.append({
                "rel": rel,
                "status": "skip",
                "reason": "could not read file",
            })
            continue

        fm, body = parse_frontmatter(content)

        new_fm = dict(fm)
        new_fm["position"] = p["tier"]
        new_fm["position_score"] = str(p["position_score"])

        new_content = build_frontmatter(new_fm) + body

        results.append({
            "rel": rel,
            "status": "would_inject" if dry_run else "injected",
            "position": p["tier"],
            "score": p["position_score"],
        })

        if not dry_run:
            write_file(file_path, new_content)

    return results


# ---------------------------------------------------------------------------
# Self-test
# ---------------------------------------------------------------------------
def run_self_test():
    import tempfile
    import shutil

    print("🧪 Position Mapping Self-Test Suite")
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

    # Test 1: extract_wikilinks
    def test_extract_wikilinks():
        result = extract_wikilinks("See [[Note A]] and [[Note B|alias]] and [[Note C#heading]]")
        assert result == ["Note A", "Note B", "Note C"], f"Got: {result}"
    check("extract_wikilinks parses targets correctly", test_extract_wikilinks)

    # Test 2: scan_vault builds position map
    def test_scan_vault():
        tmp = tempfile.mkdtemp()
        try:
            init_paths(tmp)
            # Create a simple vault structure
            os.makedirs(os.path.join(tmp, "01-Projects"))
            os.makedirs(os.path.join(tmp, "02-Areas"))
            write_file(os.path.join(tmp, "01-Projects", "Alpha.md"),
                       "---\nparent: 01-Projects\n---\n# Alpha\nSee [[../02-Areas/Beta]].")
            write_file(os.path.join(tmp, "02-Areas", "Beta.md"),
                       "---\nparent: 02-Areas\n---\n# Beta\nSee [[../01-Projects/Alpha]].")
            write_file(os.path.join(tmp, "01-Projects", "Orphan.md"),
                       "# Orphan\nNo links here.")

            positions = scan_vault(tmp)

            assert "01-Projects/Alpha.md" in positions
            assert "02-Areas/Beta.md" in positions
            assert "01-Projects/Orphan.md" in positions

            alpha = positions["01-Projects/Alpha.md"]
            assert alpha["depth"] == 1
            assert alpha["links_out"] == 1
            assert alpha["links_in"] == 1

            orphan = positions["01-Projects/Orphan.md"]
            assert orphan["is_orphan"] is True
            assert orphan["tier"] == "orphan"
        finally:
            shutil.rmtree(tmp)
    check("scan_vault builds correct position map", test_scan_vault)

    # Test 3: nearest_moc detection
    def test_nearest_moc():
        tmp = tempfile.mkdtemp()
        try:
            init_paths(tmp)
            os.makedirs(os.path.join(tmp, "03-Resources"))
            write_file(os.path.join(tmp, "03-Resources", "_MOC.md"), "# MOC")
            write_file(os.path.join(tmp, "03-Resources", "Note.md"), "# Note")
            positions = scan_vault(tmp)
            assert positions["03-Resources/Note.md"]["nearest_moc"] == "03-Resources/_MOC.md"
        finally:
            shutil.rmtree(tmp)
    check("nearest_moc finds folder MOC", test_nearest_moc)

    # Test 4: position report generation
    def test_report_generation():
        tmp = tempfile.mkdtemp()
        try:
            init_paths(tmp)
            write_file(os.path.join(tmp, "Solo.md"), "# Solo\nNo links.")
            positions = scan_vault(tmp)
            report = generate_position_report(positions, tmp)
            assert "Position Map Report" in report
            assert "Solo" in report
            assert "orphan" in report.lower()
        finally:
            shutil.rmtree(tmp)
    check("generate_position_report produces markdown", test_report_generation)

    # Test 5: inject_position_frontmatter dry-run
    def test_inject_dry_run():
        tmp = tempfile.mkdtemp()
        try:
            init_paths(tmp)
            write_file(os.path.join(tmp, "Note.md"), "# Note\nNo frontmatter.")
            positions = scan_vault(tmp)
            results = inject_position_frontmatter(positions, tmp, dry_run=True)
            assert len(results) == 1
            assert results[0]["status"] == "would_inject"
            # File unchanged in dry-run
            assert read_file(os.path.join(tmp, "Note.md")) == "# Note\nNo frontmatter."
        finally:
            shutil.rmtree(tmp)
    check("inject_position_frontmatter dry-run doesn't modify", test_inject_dry_run)

    print("=" * 50)
    print(f"🎉 Self-tests: {passed} passed, {failed} failed")
    return failed == 0


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------
def parse_args():
    parser = argparse.ArgumentParser(
        description="Hermes Brain Position Mapping — map note positions in vault hierarchy.",
    )
    parser.add_argument("--vault", help="Path to the Hermes Brain vault root")
    parser.add_argument("--dry-run", action="store_true", default=True,
                        help="Preview positions without applying (default)")
    parser.add_argument("--apply", action="store_true",
                        help="Apply position frontmatter (overrides --dry-run)")
    parser.add_argument("--test", action="store_true",
                        help="Run built-in self-test suite")
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

    positions = scan_vault(VAULT)

    # Generate report
    report = generate_position_report(positions, VAULT)
    report_path = os.path.join(VAULT, "04-Archives", "Audit-Reports", "Position-Map-Report.md")
    write_file(report_path, report)

    # Inject frontmatter if --apply
    injection_results = []
    if not dry_run:
        injection_results = inject_position_frontmatter(positions, VAULT, dry_run=False)

    # Print summary
    total = len(positions)
    orphans = sum(1 for p in positions.values() if p["is_orphan"])
    hubs = sum(1 for p in positions.values() if p["tier"] == "hub")

    print(f"📍 Position Map Complete")
    print(f"   Vault: {VAULT}")
    print(f"   Total notes: {total}")
    print(f"   Hubs: {hubs} | Orphans: {orphans}")
    print(f"   Mode: {'DRY-RUN' if dry_run else 'APPLY'}")
    print(f"   Report: {report_path}")

    if not dry_run and injection_results:
        injected = sum(1 for r in injection_results if r["status"] == "injected")
        print(f"   Frontmatter injected: {injected} note(s)")

    if dry_run:
        print("   Run with --apply to inject position frontmatter into notes.")

    return 0


if __name__ == "__main__":
    sys.exit(main())
