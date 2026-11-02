#!/usr/bin/env python3
"""
Hermes Brain — Metrics Sub-Skill: snapshot (metrics/snapshot.py)

Orchestrates all metric collectors (notes, links, sessions, tags, mocs)
and produces a dated snapshot markdown file for trend tracking over time.

Multi-harness compatible:
  - --vault CLI arg (never module-level path resolution)
  - Path resolution deferred to main() after argument parsing
  - --dry-run default / --apply for human-in-the-loop approval
  - Stdlib-only
  - --test self-tests (4/4)

Usage:
  python metrics/snapshot.py --vault <path> snapshot --days 30
  python metrics/snapshot.py --vault <path> snapshot --days 30 --apply
  python metrics/snapshot.py --vault <path> --test
"""

import argparse
import datetime
import os
import sys

# ---------------------------------------------------------------------------
# Path resolution — deferred to main(), never at import time
# ---------------------------------------------------------------------------
VAULT = None
METRICS_DIR = None
SNAPSHOTS_DIR = None


def init_paths(vault_path):
    """Resolve all vault-relative paths from the given vault root."""
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
    import re
    slug = re.sub(r"[^a-zA-Z0-9_-]+", "-", text.strip().lower()).strip("-_")
    return slug or "untitled"


# Ensure sibling sub-skill modules are importable when run standalone
_SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
_PARENT_DIR = os.path.dirname(_SCRIPT_DIR)
if _PARENT_DIR not in sys.path:
    sys.path.insert(0, _PARENT_DIR)

# ---------------------------------------------------------------------------
# Metric collectors (imported from sibling sub-skills)
# ---------------------------------------------------------------------------
from metrics.notes import collect_notes as _collect_notes   # noqa: E402
from metrics.links import collect_links as _collect_links   # noqa: E402
from metrics.sessions import collect_sessions as _collect_sessions  # noqa: E402
from metrics.tags import collect_tags as _collect_tags      # noqa: E402
from metrics.mocs import collect_mocs as _collect_mocs      # noqa: E402


# ---------------------------------------------------------------------------
# generate_snapshot — compute all metrics into a snapshot dict
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
        snapshot["notes"] = _collect_notes(vault_dir, days=days)
    if "links" in cat_list:
        snapshot["links"] = _collect_links(vault_dir)
    if "sessions" in cat_list:
        snapshot["sessions"] = _collect_sessions(vault_dir)
    if "tags" in cat_list:
        snapshot["tags"] = _collect_tags(vault_dir)
    if "mocs" in cat_list:
        snapshot["mocs"] = _collect_mocs(vault_dir)
    if "stale" in cat_list:
        snapshot["stale"] = _collect_stale(vault_dir, days=stale_days)

    return snapshot


def _collect_stale(vault_dir, days=90):
    """Collect stale notes — notes not modified in N days."""
    import datetime as dt
    cutoff = datetime.datetime.now(datetime.timezone.utc) - datetime.timedelta(days=days)
    stale = []
    for full, rel, name, content in _walk_md(vault_dir):
        mtime = _get_mod_time(full)
        if mtime and mtime < cutoff:
            stale.append({
                "path": rel,
                "days_stale": (datetime.datetime.now(datetime.timezone.utc) - mtime).days,
            })
    stale.sort(key=lambda x: -x["days_stale"])
    return {"stale_count": len(stale), "stale_examples": stale[:10]}


def _walk_md(vault_dir, exclude_dirs=None, exclude_files=None):
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


def _get_mod_time(path):
    try:
        ts = os.path.getmtime(path)
        return datetime.datetime.fromtimestamp(ts, tz=datetime.timezone.utc)
    except Exception:
        return None


# ---------------------------------------------------------------------------
# snapshot_to_markdown — render snapshot dict to markdown
# ---------------------------------------------------------------------------
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


# ---------------------------------------------------------------------------
# write_snapshot_to_vault
# ---------------------------------------------------------------------------
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

    print("🧪 metrics/snapshot.py Self-Test Suite")
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

    # Test 1: generate_snapshot computes all categories
    def test_generate_snapshot_all():
        tmp = tempfile.mkdtemp()
        try:
            os.makedirs(os.path.join(tmp, "01-Projects"))
            os.makedirs(os.path.join(tmp, "03-Resources", "MOCs"))
            write_file(os.path.join(tmp, "01-Projects", "proj.md"), "# Project\n\nContent.")
            write_file(os.path.join(tmp, "03-Resources", "MOCs", "ai.md"), "# AI MOC\n\nSee [[Project]].")
            init_paths(tmp)
            snap = generate_snapshot(tmp, days=30, stale_days=90, categories="notes,links,tags")
            assert "notes" in snap
            assert "links" in snap
            assert "tags" in snap
            assert "sessions" not in snap
            assert snap["notes"]["total"] == 2
            assert snap["links"]["total_links"] == 1  # [[Project]]
            assert snap["tags"]["total_unique_tags"] == 0
        finally:
            shutil.rmtree(tmp)
    check("generate_snapshot computes all categories", test_generate_snapshot_all)

    # Test 2: snapshot_to_markdown renders sections
    def test_snapshot_to_markdown():
        tmp = tempfile.mkdtemp()
        try:
            init_paths(tmp)
            snap = {
                "generated_at": "2026-01-01T00:00:00+00:00",
                "vault": tmp,
                "categories": "notes,links",
                "notes": {"total": 5, "recent_days": 3, "by_dir": {"_root": 5}, "dir_sizes_bytes": {"_root": 1024}},
                "links": {"total_links": 10, "unique_targets": 5, "broken_links": 1,
                          "broken_examples": [{"source": "a.md", "target": "Missing"}],
                          "link_density": 2.0},
            }
            md = snapshot_to_markdown(snap, days=30, stale_days=90)
            assert "# Vault Metrics Snapshot" in md
            assert "## Notes" in md
            assert "## Links" in md
            assert "## Sessions" not in md
        finally:
            shutil.rmtree(tmp)
    check("snapshot_to_markdown renders requested sections only", test_snapshot_to_markdown)

    # Test 3: write_snapshot_to_vault writes file
    def test_write_snapshot_to_vault():
        tmp = tempfile.mkdtemp()
        try:
            init_paths(tmp)
            snap = {"generated_at": "2026-01-01T00:00:00+00:00", "vault": tmp, "categories": "all"}
            path = write_snapshot_to_vault(snap, digest_type="daily")
            assert os.path.exists(path), f"Snapshot file not written at {path}"
            assert "Metrics-daily-" in os.path.basename(path)
        finally:
            shutil.rmtree(tmp)
    check("write_snapshot_to_vault writes snapshot file", test_write_snapshot_to_vault)

    # Test 4: generate_snapshot stale category
    def test_generate_snapshot_stale():
        tmp = tempfile.mkdtemp()
        try:
            write_file(os.path.join(tmp, "old.md"), "# Old note\n\nContent.")
            old_time = (datetime.datetime.now(datetime.timezone.utc) - datetime.timedelta(days=200)).timestamp()
            import os as _os
            _os.utime(os.path.join(tmp, "old.md"), (old_time, old_time))
            init_paths(tmp)
            snap = generate_snapshot(tmp, days=30, stale_days=90, categories="stale")
            assert "stale" in snap
            assert snap["stale"]["stale_count"] == 1
        finally:
            shutil.rmtree(tmp)
    check("generate_snapshot stale category", test_generate_snapshot_stale)

    print("=" * 50)
    print(f"🎉 Self-tests: {passed} passed, {failed} failed")
    return failed == 0


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------
def parse_args():
    parser = argparse.ArgumentParser(
        description="Hermes Brain Metrics — snapshot orchestrator sub-skill.",
    )
    parser.add_argument("--vault", help="Path to the Hermes Brain vault root")
    parser.add_argument("--days", type=int, default=30, help="Activity window in days (default: 30)")
    parser.add_argument("--stale-days", type=int, default=90, help="Stale threshold in days (default: 90)")
    parser.add_argument(
        "--categories",
        default="all",
        help="Comma-separated categories: notes,links,sessions,tags,mocs,stale,all (default: all)",
    )
    parser.add_argument(
        "--digest-type",
        choices=["daily", "weekly", "monthly"],
        default="daily",
        help="Snapshot type (default: daily)",
    )
    parser.add_argument("--dry-run", action="store_true", default=True, help="Report only (default)")
    parser.add_argument("--apply", action="store_true", help="Write snapshot to vault (overrides --dry-run)")
    parser.add_argument("--test", action="store_true", help="Run built-in self-test suite")
    sub = parser.add_subparsers(dest="command", help="Command to run")
    sub.add_parser("snapshot", help="Compute vault metrics and write snapshot (dry-run report)")
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

    if args.command and args.command != "snapshot":
        print(f"Error: Unknown command '{args.command}'. Use 'snapshot'.", file=sys.stderr)
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
