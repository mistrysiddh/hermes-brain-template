#!/usr/bin/env python3
"""
Hermes Brain — Metrics Skill (dated metrics snapshot command).

Computes vault-wide metrics: note counts, link density, session counts, tag
distribution, MOC health, and stale-content detection. Produces a dated
snapshot markdown file for trend tracking over time.

Multi-harness compatible:
  - --vault CLI arg for vault path (never module-level path resolution)
  - Path resolution deferred to main() after argument parsing
  - Works from any TUI agent (CLI, desktop, TUI, gateway)

Subcommands:
  metrics.py snapshot    Compute vault metrics and write snapshot (dry-run report)
  metrics.py --test      Built-in self-test suite

Metrics categories:
  - notes: total note count, notes per directory, recent activity
  - links: wikilink count, broken links, link density
  - sessions: session count, date range, sessions per week
  - tags: tag frequency distribution
  - moc: MOC note health, orphaned MOCs
  - stale: notes not modified in N days
  - all: every category

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
METRICS_DIR = None
SNAPSHOTS_DIR = None


def init_paths(vault_path):
    """Resolve all vault-relative paths from the given vault root.
    Called from main() after argument parsing — never at import time.
    """
    global VAULT, METRICS_DIR, SNAPSHOTS_DIR
    VAULT = os.path.abspath(vault_path)
    METRICS_DIR = os.path.join(VAULT, "04-Archives", "Metrics")
    SNAPSHOTS_DIR = os.path.join(METRICS_DIR, "snapshots")


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
    slug = re.sub(r"[^a-zA-Z0-9_-]+", "-", text.strip().lower()).strip("-_")
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


WIKILINK_RE = re.compile(r"\[\[([^\]]+)\]\]")
HEADING_RE = re.compile(r"^#{1,6}\s+(.+)$", re.M)
TAG_RE = re.compile(r"(?:^|\s)#([\w\-/]+)", re.M)
DATE_RE = re.compile(r"(\d{4})-(\d{2})-(\d{2})")


def get_mod_time(path):
    """Return datetime of last modification, or None."""
    try:
        ts = os.path.getmtime(path)
        return datetime.datetime.fromtimestamp(ts, tz=datetime.timezone.utc)
    except Exception:
        return None


# ---------------------------------------------------------------------------
# Metric collectors
# ---------------------------------------------------------------------------
def collect_notes(vault_dir, days=30):
    """Note-level metrics."""
    total = 0
    by_dir = {}
    recent = 0
    cutoff = datetime.datetime.now(datetime.timezone.utc) - datetime.timedelta(days=days)
    dir_sizes = {}

    for full, rel, name, content in walk_md(vault_dir):
        total += 1
        top_dir = rel.split("/")[0] if "/" in rel else "_root"
        by_dir[top_dir] = by_dir.get(top_dir, 0) + 1
        mtime = get_mod_time(full)
        if mtime and mtime >= cutoff:
            recent += 1
        dir_sizes[top_dir] = dir_sizes.get(top_dir, 0) + len(content.encode("utf-8"))

    return {
        "total": total,
        "by_dir": dict(sorted(by_dir.items(), key=lambda x: -x[1])),
        "recent_days": recent,
        "dir_sizes_bytes": dir_sizes,
    }


def collect_links(vault_dir):
    """Wikilink metrics: total links, unique targets, broken links."""
    total_links = 0
    unique_targets = set()
    broken = []
    all_notes = {rel: full for full, rel, _, _ in walk_md(vault_dir)}

    for full, rel, name, content in walk_md(vault_dir):
        for m in WIKILINK_RE.finditer(content):
            target = m.group(1).strip()
            # Strip alias if present: [[target|alias]]
            if "|" in target:
                target = target.split("|")[0].strip()
            total_links += 1
            unique_targets.add(target)
            # Check if target exists as a note
            target_md = target + ".md"
            target_rel = target_md
            # Try exact match first
            found = target_rel in all_notes
            if not found:
                # Try case-insensitive / path variants
                for existing_rel in all_notes:
                    if existing_rel.lower().endswith(target_md.lower()):
                        found = True
                        break
            if not found:
                broken.append({"source": rel, "target": target})

    return {
        "total_links": total_links,
        "unique_targets": len(unique_targets),
        "broken_links": len(broken),
        "broken_examples": broken[:5],
        "link_density": round(total_links / max(1, len(all_notes)), 2),
    }


def collect_sessions(vault_dir):
    """Session metrics from Daily/ archives."""
    daily_dirs = [
        os.path.join(vault_dir, "04-Archives", "Daily"),
        os.path.join(vault_dir, "Daily"),
    ]
    daily_dir = None
    for d in daily_dirs:
        if os.path.isdir(d):
            daily_dir = d
            break

    total = 0
    by_month = {}
    date_range = {"earliest": None, "latest": None}

    if daily_dir:
        for full, rel, name, content in walk_md(daily_dir):
            total += 1
            # Try to extract date from frontmatter created_at
            m = re.search(r'created_at:\s*"(\d{4})-(\d{2})-(\d{2})"', content)
            if m:
                date_str = f"{m.group(1)}-{m.group(2)}"
                by_month[date_str] = by_month.get(date_str, 0) + 1
                full_date = f"{m.group(1)}-{m.group(2)}-{m.group(3)}"
                if date_range["earliest"] is None or full_date < date_range["earliest"]:
                    date_range["earliest"] = full_date
                if date_range["latest"] is None or full_date > date_range["latest"]:
                    date_range["latest"] = full_date
            else:
                # Fall back to filename date pattern
                dm = re.search(r"(\d{4})[-/](\d{2})[-/](\d{2})", name)
                if dm:
                    date_str = f"{dm.group(1)}-{dm.group(2)}"
                    by_month[date_str] = by_month.get(date_str, 0) + 1

    return {
        "total_sessions": total,
        "by_month": dict(sorted(by_month.items())),
        "date_range": date_range,
    }


def collect_tags(vault_dir, top_n=20):
    """Tag frequency distribution."""
    tag_counts = {}
    for _, _, _, content in walk_md(vault_dir):
        for tag in TAG_RE.findall(content):
            tag_counts[tag] = tag_counts.get(tag, 0) + 1
    sorted_tags = sorted(tag_counts.items(), key=lambda x: -x[1])
    return {"total_unique_tags": len(tag_counts), "top_tags": sorted_tags[:top_n]}


def collect_mocs(vault_dir):
    """MOC (Map of Content) health metrics."""
    moc_dirs = [
        os.path.join(vault_dir, "03-Resources", "MOCs"),
        os.path.join(vault_dir, "MOCs"),
    ]
    moc_dir = None
    for d in moc_dirs:
        if os.path.isdir(d):
            moc_dir = d
            break

    total_mocs = 0
    orphaned = []
    healthy = 0

    if moc_dir:
        all_note_rels = {rel for _, rel, _, _ in walk_md(vault_dir)}
        for full, rel, name, content in walk_md(moc_dir):
            total_mocs += 1
            # A MOC is "healthy" if it contains at least one wikilink
            links = list(WIKILINK_RE.finditer(content))
            if links:
                healthy += 1
            else:
                orphaned.append(rel)

    return {
        "total_mocs": total_mocs,
        "healthy_mocs": healthy,
        "orphaned_mocs": orphaned[:10],
    }


def collect_stale(vault_dir, days=90):
    """Notes not modified in N days."""
    cutoff = datetime.datetime.now(datetime.timezone.utc) - datetime.timedelta(days=days)
    stale = []
    for full, rel, name, content in walk_md(vault_dir):
        mtime = get_mod_time(full)
        if mtime and mtime < cutoff:
            stale.append({
                "path": rel,
                "days_stale": (datetime.datetime.now(datetime.timezone.utc) - mtime).days,
            })
    stale.sort(key=lambda x: -x["days_stale"])
    return {"stale_count": len(stale), "stale_examples": stale[:10]}


# ---------------------------------------------------------------------------
# Snapshot generation
# ---------------------------------------------------------------------------
def generate_snapshot(vault_dir, days=30, stale_days=90, categories="all"):
    """Compute all metrics and return a snapshot dict."""
    now = datetime.datetime.now(datetime.timezone.utc)
    snapshot = {
        "generated_at": now.isoformat(),
        "vault": vault_dir,
        "categories": categories,
    }

    cat_list = categories.split(",") if categories != "all" else [
        "notes", "links", "sessions", "tags", "mocs", "stale",
    ]

    if "notes" in cat_list:
        snapshot["notes"] = collect_notes(vault_dir, days=days)
    if "links" in cat_list:
        snapshot["links"] = collect_links(vault_dir)
    if "sessions" in cat_list:
        snapshot["sessions"] = collect_sessions(vault_dir)
    if "tags" in cat_list:
        snapshot["tags"] = collect_tags(vault_dir)
    if "mocs" in cat_list:
        snapshot["mocs"] = collect_mocs(vault_dir)
    if "stale" in cat_list:
        snapshot["stale"] = collect_stale(vault_dir, days=stale_days)

    return snapshot


def snapshot_to_markdown(snapshot, days=30, stale_days=90):
    """Render snapshot dict to markdown."""
    lines = [
        "# Vault Metrics Snapshot",
        f"Generated: {snapshot['generated_at']}",
        f"Vault: {snapshot['vault']}",
        f"Window: last {days} days | Stale threshold: {stale_days} days",
        "",
        "---",
        "",
    ]

    # Notes
    if "notes" in snapshot:
        n = snapshot["notes"]
        lines.append("## Notes")
        lines.append(f"- **Total notes**: {n['total']}")
        lines.append(f"- **Notes modified (last {days} days)**: {n['recent_days']}")
        lines.append("")
        lines.append("### Notes by top directory")
        lines.append("| Directory | Count | Size (KB) |")
        lines.append("|-----------|-------|-----------|")
        for d in sorted(n["by_dir"].items(), key=lambda x: -x[1])[:10]:
            dir_name = d[0]
            count = d[1]
            size_kb = round(n.get("dir_sizes_bytes", {}).get(dir_name, 0) / 1024, 1)
            lines.append(f"| {dir_name} | {count} | {size_kb} |")
        lines.append("")

    # Links
    if "links" in snapshot:
        l = snapshot["links"]
        lines.append("## Links")
        lines.append(f"- **Total wikilinks**: {l['total_links']}")
        lines.append(f"- **Unique targets**: {l['unique_targets']}")
        lines.append(f"- **Broken links**: {l['broken_links']}")
        lines.append(f"- **Link density** (links per note): {l['link_density']}")
        if l["broken_examples"]:
            lines.append("")
            lines.append("### Broken link examples")
            for ex in l["broken_examples"]:
                lines.append(f"- `[[{ex['target']}]]` in `{ex['source']}`")
        lines.append("")

    # Sessions
    if "sessions" in snapshot:
        s = snapshot["sessions"]
        lines.append("## Sessions")
        lines.append(f"- **Total sessions**: {s['total_sessions']}")
        dr = s["date_range"]
        if dr["earliest"] and dr["latest"]:
            lines.append(f"- **Date range**: {dr['earliest']} → {dr['latest']}")
        if s["by_month"]:
            lines.append("")
            lines.append("### Sessions by month")
            lines.append("| Month | Sessions |")
            lines.append("|-------|----------|")
            for month, count in list(s["by_month"].items())[-12:]:
                lines.append(f"| {month} | {count} |")
        lines.append("")

    # Tags
    if "tags" in snapshot:
        t = snapshot["tags"]
        lines.append("## Tags")
        lines.append(f"- **Unique tags**: {t['total_unique_tags']}")
        if t["top_tags"]:
            lines.append("")
            lines.append("### Top tags")
            lines.append("| Tag | Count |")
            lines.append("|-----|-------|")
            for tag, count in t["top_tags"][:15]:
                lines.append(f"| #{tag} | {count} |")
        lines.append("")

    # MOCs
    if "mocs" in snapshot:
        m = snapshot["mocs"]
        lines.append("## MOCs (Maps of Content)")
        lines.append(f"- **Total MOCs**: {m['total_mocs']}")
        lines.append(f"- **Healthy MOCs** (contain wikilinks): {m['healthy_mocs']}")
        lines.append(f"- **Orphaned MOCs** (no links): {m['total_mocs'] - m['healthy_mocs']}")
        if m["orphaned_mocs"]:
            lines.append("")
            lines.append("### Orphaned MOC examples")
            for moc in m["orphaned_mocs"]:
                lines.append(f"- `{moc}`")
        lines.append("")

    # Stale
    if "stale" in snapshot:
        st = snapshot["stale"]
        lines.append("## Stale Notes")
        lines.append(f"- **Stale count** (> {stale_days} days): {st['stale_count']}")
        if st["stale_examples"]:
            lines.append("")
            lines.append("### Stale examples")
            for ex in st["stale_examples"]:
                lines.append(f"- `{ex['path']}` — {ex['days_stale']} days stale")
        lines.append("")

    lines.append("---")
    lines.append("")
    lines.append("## Next Steps")
    lines.append("")
    lines.append("Review metrics above. Compare against previous snapshots to track trends.")
    lines.append("Run again: `metrics.py --vault <path> snapshot --days 30 --apply`")

    return "\n".join(lines)


def write_snapshot_to_vault(snapshot, digest_type="daily"):
    """Write snapshot markdown to vault snapshots dir."""
    now = datetime.datetime.now(datetime.timezone.utc)
    date_str = now.strftime("%Y-%m-%d")
    filename = f"Metrics-{digest_type}-{date_str}.md"
    path = os.path.join(SNAPSHOTS_DIR, filename)
    content = snapshot_to_markdown(snapshot)
    write_file(path, content)
    return path


# ---------------------------------------------------------------------------
# Self-test
# ---------------------------------------------------------------------------
def run_self_test():
    import tempfile
    import shutil

    print("🧪 metrics.py Self-Test Suite")
    print("=" * 50)
    passed = 0
    failed = 0

    # Test 1: collect_notes counts notes correctly
    tmp = tempfile.mkdtemp()
    try:
        os.makedirs(os.path.join(tmp, "01-Projects"))
        os.makedirs(os.path.join(tmp, "03-Resources", "MOCs"))
        write_file(os.path.join(tmp, "01-Projects", "proj.md"), "# Project\n\nContent.")
        write_file(os.path.join(tmp, "03-Resources", "MOCs", "ai.md"), "# AI MOC\n\nSee [[Project]].")
        write_file(os.path.join(tmp, "README.md"), "# Root readme")
        init_paths(tmp)
        notes = collect_notes(tmp, days=30)
        assert notes["total"] == 2, f"Expected 2 notes (excl. README), got {notes['total']}"
        assert notes["by_dir"].get("01-Projects", 0) == 1
        assert notes["by_dir"].get("03-Resources", 0) == 1
        print("✅ Test 1: collect_notes counts notes correctly")
        passed += 1
    except Exception as e:
        print(f"❌ Test 1 failed: {e}")
        failed += 1
    finally:
        shutil.rmtree(tmp)

    # Test 2: collect_links finds links and detects broken ones
    tmp = tempfile.mkdtemp()
    try:
        write_file(os.path.join(tmp, "a.md"), "# A\n\nSee [[B]] and [[C|alias]].")
        write_file(os.path.join(tmp, "b.md"), "# B\n\nBack to [[A]].")
        init_paths(tmp)
        links = collect_links(tmp)
        assert links["total_links"] >= 3, f"Expected >=3 links, got {links['total_links']}"
        assert links["broken_links"] == 1, f"Expected 1 broken link (C), got {links['broken_links']}"
        assert links["link_density"] > 0
        print("✅ Test 2: collect_links finds links and detects broken ones")
        passed += 1
    except Exception as e:
        print(f"❌ Test 2 failed: {e}")
        failed += 1
    finally:
        shutil.rmtree(tmp)

    # Test 3: collect_tags extracts tags
    tmp = tempfile.mkdtemp()
    try:
        write_file(os.path.join(tmp, "t.md"), "# Tags\n\n#ai #ml #ai #research")
        init_paths(tmp)
        tags = collect_tags(tmp)
        assert tags["top_tags"][0][0] == "ai", f"Expected 'ai' as top tag, got {tags['top_tags'][0]}"
        assert tags["top_tags"][0][1] == 2, f"Expected count 2 for 'ai', got {tags['top_tags'][0][1]}"
        print("✅ Test 3: collect_tags extracts tags correctly")
        passed += 1
    except Exception as e:
        print(f"❌ Test 3 failed: {e}")
        failed += 1
    finally:
        shutil.rmtree(tmp)

    # Test 4: snapshot_to_markdown renders sections
    tmp = tempfile.mkdtemp()
    try:
        init_paths(tmp)
        snap = generate_snapshot(tmp, days=30, stale_days=90, categories="notes,links,tags")
        md = snapshot_to_markdown(snap, days=30, stale_days=90)
        assert "# Vault Metrics Snapshot" in md
        assert "## Notes" in md
        assert "## Links" in md
        assert "## Tags" in md
        assert "## Sessions" not in md  # not requested
        print("✅ Test 4: snapshot_to_markdown renders requested sections only")
        passed += 1
    except Exception as e:
        print(f"❌ Test 4 failed: {e}")
        failed += 1
    finally:
        shutil.rmtree(tmp)

    # Test 5: collect_stale identifies old notes
    tmp = tempfile.mkdtemp()
    try:
        write_file(os.path.join(tmp, "old.md"), "# Old note\n\nContent.")
        init_paths(tmp)
        # Make the file old by setting mtime to 200 days ago
        old_time = (datetime.datetime.now(datetime.timezone.utc) - datetime.timedelta(days=200)).timestamp()
        os.utime(os.path.join(tmp, "old.md"), (old_time, old_time))
        stale = collect_stale(tmp, days=90)
        assert stale["stale_count"] == 1, f"Expected 1 stale note, got {stale['stale_count']}"
        print("✅ Test 5: collect_stale identifies old notes")
        passed += 1
    except Exception as e:
        print(f"❌ Test 5 failed: {e}")
        failed += 1
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
        description="Hermes Brain Metrics — dated metrics snapshot command.",
    )
    parser.add_argument("--vault", help="Path to the Hermes Brain vault root")
    parser.add_argument("--days", type=int, default=30, help="Activity window in days (default: 30)")
    parser.add_argument("--stale-days", type=int, default=90, help="Stale threshold in days (default: 90)")
    parser.add_argument(
        "--categories",
        default="all",
        help="Comma-separated categories: notes,links,sessions,tags,mocs,stale,all (default: all)",
    )
    parser.add_argument("--digest-type", choices=["daily", "weekly", "monthly"], default="daily", help="Snapshot type (default: daily)")
    parser.add_argument("--dry-run", action="store_true", default=True, help="Report only, no snapshot written (default)")
    parser.add_argument("--apply", action="store_true", help="Write snapshot to vault (overrides --dry-run)")
    parser.add_argument("--test", action="store_true", help="Run built-in self-test suite")
    sub = parser.add_subparsers(dest="command", help="Command to run")
    sub.add_parser("snapshot", help="Compute vault metrics and write snapshot (dry-run report)")
    sub.add_parser("digest", help="Generate and write metrics digest to vault")
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

    print(f"📊 Computing vault metrics ({args.categories}) over last {args.days} days\n")

    snapshot = generate_snapshot(VAULT, days=args.days, stale_days=args.stale_days, categories=args.categories)
    md = snapshot_to_markdown(snapshot, days=args.days, stale_days=args.stale_days)

    if dry_run:
        print("📄 Snapshot preview (dry-run — not written to vault):")
        print(md[:2000])
        if len(md) > 2000:
            print(f"\n... ({len(md) - 2000} more chars)")
    else:
        snapshot_path = write_snapshot_to_vault(snapshot, digest_type=args.digest_type)
        print(f"📄 Snapshot written to {snapshot_path}")


if __name__ == "__main__":
    main()
