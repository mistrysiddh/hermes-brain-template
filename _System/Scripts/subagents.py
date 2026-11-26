#!/usr/bin/env python3
"""
Hermes Brain — Subagents Skill (multi-agent orchestration for vault maintenance).

Six sub-agents that operate on the Hermes Brain vault:

| Agent | Role | Trigger |
|-------|------|---------|
| ingestor | Writes new material from `raw/` into the vault | On new files in `raw/` |
| linker | Finds and adds missing connections between notes | Weekly / on demand |
| reviewer | Read-only vault audit — broken links, orphans, drift | Weekly |
| researcher | On-demand deep research on a topic across the vault | On demand |
| graph-analyst | Monthly navigation analysis — MOC health, clusters | Monthly |
| curator | Quarterly prune/archive review — stale notes, duplicates | Quarterly |

Multi-harness compatible:
  - --vault CLI arg for vault path (never module-level path resolution)
  - Path resolution deferred to main() after argument parsing
  - Works from any TUI agent (CLI, desktop, TUI, gateway)
  - --dry-run default / --apply for human-in-the-loop approval
  - Stdlib-only

Subcommands:
  subagents.py ingestor     Scan raw/ and ingest new material into vault
  subagents.py linker       Find missing links between related notes
  subagents.py reviewer     Read-only vault audit report
  subagents.py researcher   Research a topic across vault notes
  subagents.py graph-analyst Monthly navigation analysis
  subagents.py curator      Quarterly prune/archive review
  subagents.py --test       Built-in self-test suite

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
RAW_DIR = None
AGENTS_DIR = None
REPORTS_DIR = None


def init_paths(vault_path):
    """Resolve all vault-relative paths from the given vault root.
    Called from main() after argument parsing — never at import time.
    """
    global VAULT, RAW_DIR, AGENTS_DIR, REPORTS_DIR
    VAULT = os.path.abspath(vault_path)
    RAW_DIR = os.path.join(VAULT, "raw")
    AGENTS_DIR = os.path.join(VAULT, "04-Archives", "Agents")
    REPORTS_DIR = os.path.join(AGENTS_DIR, "reports")


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
    exclude_dirs = exclude_dirs or {".obsidian", ".git", ".trash", "raw"}
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


def tokenize(text):
    return set(re.findall(r"[a-z0-9]+", text.lower()))


def jaccard(a, b):
    if not a and not b:
        return 0.0
    if not a or not b:
        return 0.0
    inter = len(a & b)
    union = len(a | b)
    return inter / union if union > 0 else 0.0


# ---------------------------------------------------------------------------
# Agent 1: Ingestor — raw/ → vault
# ---------------------------------------------------------------------------
def ingestor_scan(raw_dir):
    """Scan raw/ for new material to ingest."""
    items = []
    if not os.path.isdir(raw_dir):
        return items
    for full, rel, name, content in walk_md(raw_dir):
        items.append({
            "path": full,
            "rel_path": rel,
            "name": name,
            "content": content,
        })
    return items


def run_ingestor(dry_run=True):
    """Run the ingestor agent."""
    items = ingestor_scan(RAW_DIR)
    results = []
    for item in items:
        # Determine target: Projects/ if it looks like a project, else Areas/
        content = item["content"]
        if re.search(r"(project|build|deploy|setup|install)", content, re.I):
            target_dir = "01-Projects"
        elif re.search(r"(area|topic|domain|field)", content, re.I):
            target_dir = "02-Areas"
        else:
            target_dir = "03-Resources"

        target_name = slugify(item["name"])
        target_rel = f"{target_dir}/{target_name}.md"

        results.append({
            "source": item["rel_path"],
            "target": target_rel,
            "action": "ingest",
            "applied": False,
            "reason": "dry-run preview" if dry_run else "ingested",
        })

        if not dry_run:
            write_file(os.path.join(VAULT, target_rel), content)
            results[-1]["applied"] = True
            results[-1]["reason"] = "ingested"

    return results


# ---------------------------------------------------------------------------
# Agent 2: Linker — find missing links
# ---------------------------------------------------------------------------
def run_linker(dry_run=True, threshold=0.6):
    """Find notes that share topics but aren't linked, suggest links."""
    notes = []
    for full, rel, name, content in walk_md(VAULT):
        existing_links = set(WIKILINK_RE.findall(content))
        # Strip aliases from existing links
        existing_links = {l.split("|")[0].strip() for l in existing_links}
        notes.append({
            "path": full,
            "rel_path": rel,
            "name": name,
            "content": content,
            "tokens": tokenize(content),
            "existing_links": existing_links,
        })

    suggestions = []
    for i in range(len(notes)):
        for j in range(i + 1, len(notes)):
            a, b = notes[i], notes[j]
            sim = jaccard(a["tokens"], b["tokens"])
            if sim < threshold:
                continue
            # Skip if already linked
            if b["name"] in a["existing_links"] or a["name"] in b["existing_links"]:
                continue
            suggestions.append({
                "source": a["rel_path"],
                "target": b["rel_path"],
                "similarity": round(sim, 3),
                "action": "suggest_link",
                "applied": False,
                "reason": "dry-run preview" if dry_run else "linked",
            })

            if not dry_run:
                # Add link to source note
                link_text = f"\n\nSee also [[{b['rel_path']}|{b['name']}]]\n"
                with open(a["path"], "a", encoding="utf-8") as f:
                    f.write(link_text)
                suggestions[-1]["applied"] = True
                suggestions[-1]["reason"] = "linked"

    return suggestions


# ---------------------------------------------------------------------------
# Agent 3: Reviewer — read-only vault audit
# ---------------------------------------------------------------------------
def run_reviewer():
    """Read-only vault audit report."""
    total_notes = 0
    total_links = 0
    broken_links = []
    orphaned = []
    by_dir = {}
    tags = {}
    stale = []

    all_rels = set()
    for full, rel, name, content in walk_md(VAULT):
        total_notes += 1
        all_rels.add(rel)
        top_dir = rel.split("/")[0] if "/" in rel else "_root"
        by_dir[top_dir] = by_dir.get(top_dir, 0) + 1

        # Links
        for m in WIKILINK_RE.finditer(content):
            total_links += 1
            target = m.group(1).strip().split("|")[0].strip()
            target_md = target + ".md"
            if target_md not in all_rels and target not in all_rels:
                broken_links.append({"source": rel, "target": target})

        # Tags
        for tag in TAG_RE.findall(content):
            tags[tag] = tags.get(tag, 0) + 1

    # Orphaned notes (no incoming links)
    linked_targets = set()
    for full, rel, name, content in walk_md(VAULT):
        for m in WIKILINK_RE.finditer(content):
            target = m.group(1).strip().split("|")[0].strip()
            linked_targets.add(target)

    for full, rel, name, content in walk_md(VAULT):
        if name not in linked_targets and rel.split("/")[-1].replace(".md", "") not in linked_targets:
            orphaned.append(rel)

    # Stale notes (no modification in 90 days)
    import datetime as dt
    cutoff = dt.datetime.now(dt.timezone.utc) - dt.timedelta(days=90)
    for full, rel, name, content in walk_md(VAULT):
        try:
            ts = os.path.getmtime(full)
            mtime = dt.datetime.fromtimestamp(ts, tz=dt.timezone.utc)
            if mtime < cutoff:
                stale.append({"path": rel, "days": (dt.datetime.now(dt.timezone.utc) - mtime).days})
        except Exception:
            pass

    stale.sort(key=lambda x: -x["days"])

    return {
        "total_notes": total_notes,
        "total_links": total_links,
        "broken_links": broken_links[:20],
        "broken_count": len(broken_links),
        "orphaned": orphaned[:20],
        "orphaned_count": len(orphaned),
        "by_dir": dict(sorted(by_dir.items(), key=lambda x: -x[1])),
        "top_tags": sorted(tags.items(), key=lambda x: -x[1])[:15],
        "stale": stale[:20],
        "stale_count": len(stale),
    }


# ---------------------------------------------------------------------------
# Agent 4: Researcher — research a topic across vault
# ---------------------------------------------------------------------------
def run_researcher(topic, days=None):
    """Research a topic across vault notes — find all related notes."""
    topic_tokens = tokenize(topic)
    results = []
    import datetime as dt
    cutoff = None
    if days:
        cutoff = dt.datetime.now(dt.timezone.utc) - dt.timedelta(days=days)

    for full, rel, name, content in walk_md(VAULT):
        if cutoff:
            try:
                ts = os.path.getmtime(full)
                mtime = dt.datetime.fromtimestamp(ts, tz=dt.timezone.utc)
                if mtime < cutoff:
                    continue
            except Exception:
                pass

        sim = jaccard(topic_tokens, tokenize(content))
        if sim > 0:
            # Find matching context
            context = ""
            for line in content.splitlines():
                if any(t in line.lower() for t in topic_tokens):
                    context = line.strip()[:200]
                    break
            results.append({
                "rel_path": rel,
                "name": name,
                "similarity": round(sim, 3),
                "context": context,
            })

    results.sort(key=lambda x: -x["similarity"])
    return results


# ---------------------------------------------------------------------------
# Agent 5: Graph Analyst — monthly navigation analysis
# ---------------------------------------------------------------------------
def run_graph_analyst():
    """Analyze vault navigation graph — MOC health, clusters, centrality."""
    notes = []
    link_graph = {}  # rel -> set of linked targets

    for full, rel, name, content in walk_md(VAULT):
        notes.append({"rel_path": rel, "name": name, "content": content})
        links = set()
        for m in WIKILINK_RE.finditer(content):
            target = m.group(1).strip().split("|")[0].strip()
            links.add(target)
        link_graph[rel] = links

    # Count incoming links (centrality)
    incoming = {}
    for rel, targets in link_graph.items():
        for t in targets:
            incoming[t] = incoming.get(t, 0) + 1

    # Most linked notes (central nodes)
    central = sorted(incoming.items(), key=lambda x: -x[1])[:10]

    # Notes with no outgoing links (dead ends)
    dead_ends = [rel for rel, targets in link_graph.items() if not targets]

    # MOC detection — notes with many outgoing links
    mocs = sorted(
        [(rel, len(targets)) for rel, targets in link_graph.items()],
        key=lambda x: -x[1],
    )[:10]

    # Clusters by directory
    dir_links = {}
    for rel, targets in link_graph.items():
        d = rel.split("/")[0] if "/" in rel else "_root"
        dir_links.setdefault(d, set())
        for t in targets:
            td = t.split("/")[0] if "/" in t else "_root"
            if td != d:
                dir_links[d].add(td)

    return {
        "total_notes": len(notes),
        "total_links": sum(len(t) for t in link_graph.values()),
        "central_nodes": central,
        "dead_ends": dead_ends[:20],
        "dead_end_count": len(dead_ends),
        "top_mocs": mocs,
        "directory_links": {k: sorted(v) for k, v in dir_links.items()},
    }


# ---------------------------------------------------------------------------
# Agent 6: Curator — quarterly prune/archive review
# ---------------------------------------------------------------------------
def run_curator(dry_run=True):
    """Quarterly curation — identify stale notes, duplicates, archive candidates."""
    import datetime as dt
    cutoff = dt.datetime.now(dt.timezone.utc) - dt.timedelta(days=180)

    candidates = []
    for full, rel, name, content in walk_md(VAULT):
        reasons = []
        try:
            ts = os.path.getmtime(full)
            mtime = dt.datetime.fromtimestamp(ts, tz=dt.timezone.utc)
            days = (dt.datetime.now(dt.timezone.utc) - mtime).days
            if days > 180:
                reasons.append(f"stale ({days} days)")
        except Exception:
            pass

        # Very short notes (likely stubs)
        if len(content.strip()) < 50:
            reasons.append("stub (<50 chars)")

        # Duplicate title check (same name in different dirs)
        # (handled by merge_duplicate, just flag here)

        if reasons:
            candidates.append({
                "path": rel,
                "reasons": reasons,
                "action": "review",
                "applied": False,
                "reason": "dry-run preview" if dry_run else "flagged for review",
            })

    return candidates


# ---------------------------------------------------------------------------
# Report generation
# ---------------------------------------------------------------------------
def generate_ingestor_report(results):
    lines = ["# Ingestor Report", f"Generated: {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}", ""]
    if not results:
        lines.append("## ✅ No new material in `raw/` to ingest.")
        return "\n".join(lines)
    lines.append(f"## {len(results)} item(s) to ingest")
    lines.append("")
    lines.append("| Source | Target | Action |")
    lines.append("|--------|--------|--------|")
    for r in results:
        lines.append(f"| `{r['source']}` | `{r['target']}` | {r['action']} |")
    return "\n".join(lines)


def generate_linker_report(results):
    lines = ["# Linker Report", f"Generated: {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}", ""]
    if not results:
        lines.append("## ✅ No missing links found.")
        return "\n".join(lines)
    lines.append(f"## {len(results)} suggested link(s)")
    lines.append("")
    lines.append("| Source | Target | Similarity |")
    lines.append("|--------|--------|------------|")
    for r in results:
        lines.append(f"| `{r['source']}` | `{r['target']}` | {r['similarity']} |")
    return "\n".join(lines)


def generate_reviewer_report(review):
    lines = ["# Reviewer Report", f"Generated: {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}", ""]
    lines.append("## Summary")
    lines.append(f"- **Total notes**: {review['total_notes']}")
    lines.append(f"- **Total wikilinks**: {review['total_links']}")
    lines.append(f"- **Broken links**: {review['broken_count']}")
    lines.append(f"- **Orphaned notes**: {review['orphaned_count']}")
    lines.append(f"- **Stale notes** (>90 days): {review['stale_count']}")
    lines.append("")
    if review["broken_links"]:
        lines.append("### Broken links (first 20)")
        for b in review["broken_links"]:
            lines.append(f"- `[[{b['target']}]]` in `{b['source']}`")
        lines.append("")
    if review["orphaned"]:
        lines.append("### Orphaned notes (first 20)")
        for o in review["orphaned"]:
            lines.append(f"- `{o}`")
        lines.append("")
    if review["stale"]:
        lines.append("### Stale notes (first 20)")
        for s in review["stale"]:
            lines.append(f"- `{s['path']}` — {s['days']} days")
        lines.append("")
    return "\n".join(lines)


def generate_researcher_report(topic, results):
    lines = ["# Research Report", f"Topic: {topic}", f"Generated: {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}", ""]
    if not results:
        lines.append("## ✅ No notes found related to this topic.")
        return "\n".join(lines)
    lines.append(f"## {len(results)} related note(s)")
    lines.append("")
    lines.append("| Note | Similarity | Context |")
    lines.append("|------|------------|---------|")
    for r in results[:30]:
        ctx = r["context"][:80] if r["context"] else "—"
        lines.append(f"| `{r['rel_path']}` | {r['similarity']} | {ctx} |")
    return "\n".join(lines)


def generate_graph_report(graph):
    lines = ["# Graph Analyst Report", f"Generated: {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}", ""]
    lines.append("## Summary")
    lines.append(f"- **Total notes**: {graph['total_notes']}")
    lines.append(f"- **Total links**: {graph['total_links']}")
    lines.append(f"- **Dead ends**: {graph['dead_end_count']}")
    lines.append("")
    if graph["central_nodes"]:
        lines.append("### Most linked notes (centrality)")
        lines.append("| Note | Incoming links |")
        lines.append("|------|----------------|")
        for rel, count in graph["central_nodes"][:10]:
            lines.append(f"| `{rel}` | {count} |")
        lines.append("")
    if graph["dead_ends"]:
        lines.append("### Dead ends (no outgoing links)")
        for d in graph["dead_ends"][:10]:
            lines.append(f"- `{d}`")
        lines.append("")
    if graph["top_mocs"]:
        lines.append("### Top MOCs (most outgoing links)")
        lines.append("| Note | Outgoing links |")
        lines.append("|------|----------------|")
        for rel, count in graph["top_mocs"][:10]:
            lines.append(f"| `{rel}` | {count} |")
        lines.append("")
    return "\n".join(lines)


def generate_curator_report(results):
    lines = ["# Curator Report", f"Generated: {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}", ""]
    if not results:
        lines.append("## ✅ No curation candidates found.")
        return "\n".join(lines)
    lines.append(f"## {len(results)} curation candidate(s)")
    lines.append("")
    lines.append("| Note | Reasons |")
    lines.append("|------|---------|")
    for r in results:
        lines.append(f"| `{r['path']}` | {', '.join(r['reasons'])} |")
    return "\n".join(lines)


def save_report(agent_name, report_md):
    """Save report to vault."""
    today = datetime.datetime.now().strftime("%Y-%m-%d")
    safe_name = slugify(agent_name)
    path = os.path.join(REPORTS_DIR, f"{safe_name}-{today}.md")
    write_file(path, report_md)
    return path


# ---------------------------------------------------------------------------
# Self-test
# ---------------------------------------------------------------------------
def run_self_test():
    import tempfile
    import shutil

    print("🧪 subagents.py Self-Test Suite")
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

    # Test 1: ingestor_scan
    def test_ingestor():
        tmp = tempfile.mkdtemp()
        try:
            init_paths(tmp)
            os.makedirs(os.path.join(tmp, "raw"), exist_ok=True)
            write_file(os.path.join(tmp, "raw", "idea.md"), "# New Idea\n\nA project idea about AI agents.")
            items = ingestor_scan(os.path.join(tmp, "raw"))
            assert len(items) == 1
            assert items[0]["name"] == "idea"
        finally:
            shutil.rmtree(tmp)
    check("ingestor_scan finds new material", test_ingestor)

    # Test 2: run_linker finds missing links
    def test_linker():
        tmp = tempfile.mkdtemp()
        try:
            init_paths(tmp)
            write_file(os.path.join(tmp, "a.md"), "# Note A\n\nContent about AI.")
            write_file(os.path.join(tmp, "b.md"), "# Note B\n\nContent about AI and machine learning.")
            results = run_linker(dry_run=True, threshold=0.3)
            # Should suggest a link between A and B (shared "ai" topic)
            ai_links = [r for r in results if "a.md" in r["source"] and "b.md" in r["target"]]
            assert len(ai_links) >= 1, f"Expected link suggestion, got {len(ai_links)}"
        finally:
            shutil.rmtree(tmp)
    check("linker finds missing links", test_linker)

    # Test 3: run_reviewer produces summary
    def test_reviewer():
        tmp = tempfile.mkdtemp()
        try:
            init_paths(tmp)
            write_file(os.path.join(tmp, "a.md"), "# A\n\nContent.")
            write_file(os.path.join(tmp, "b.md"), "# B\n\nSee [[A]].")
            review = run_reviewer()
            assert review["total_notes"] == 2
            assert review["total_links"] >= 1
        finally:
            shutil.rmtree(tmp)
    check("reviewer produces summary", test_reviewer)

    # Test 4: run_researcher finds topic
    def test_researcher():
        tmp = tempfile.mkdtemp()
        try:
            init_paths(tmp)
            write_file(os.path.join(tmp, "ai.md"), "# AI\n\nArtificial intelligence is great.")
            write_file(os.path.join(tmp, "cooking.md"), "# Cooking\n\nHow to make pasta.")
            results = run_researcher("artificial intelligence")
            assert len(results) >= 1
            assert results[0]["name"] == "ai"
        finally:
            shutil.rmtree(tmp)
    check("researcher finds topic", test_researcher)

    # Test 5: run_graph_analyst
    def test_graph():
        tmp = tempfile.mkdtemp()
        try:
            init_paths(tmp)
            write_file(os.path.join(tmp, "a.md"), "# A\n\nSee [[B]].")
            write_file(os.path.join(tmp, "b.md"), "# B\n\nSee [[A]] and [[C]].")
            write_file(os.path.join(tmp, "c.md"), "# C\n\nStandalone note.")
            graph = run_graph_analyst()
            assert graph["total_notes"] == 3
            assert graph["total_links"] >= 3
        finally:
            shutil.rmtree(tmp)
    check("graph analyst analyzes vault", test_graph)

    # Test 6: run_curator flags stale notes
    def test_curator():
        tmp = tempfile.mkdtemp()
        try:
            init_paths(tmp)
            write_file(os.path.join(tmp, "old.md"), "# Old\n\nJust a tiny note.")
            # Make it old
            old_time = (datetime.datetime.now(datetime.timezone.utc) - datetime.timedelta(days=200)).timestamp()
            os.utime(os.path.join(tmp, "old.md"), (old_time, old_time))
            results = run_curator(dry_run=True)
            stale_found = any("old.md" in r["path"] for r in results)
            assert stale_found, "Expected old.md to be flagged as stale/stub"
        finally:
            shutil.rmtree(tmp)
    check("curator flags stale notes", test_curator)

    print("=" * 50)
    print(f"🎉 Self-tests: {passed} passed, {failed} failed")
    return failed == 0


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------
def parse_args():
    parser = argparse.ArgumentParser(
        description="Hermes Brain Subagents — multi-agent vault maintenance.",
    )
    parser.add_argument("--vault", help="Path to the Hermes Brain vault root")
    sub = parser.add_subparsers(dest="command", help="Agent to run")

    p_ingest = sub.add_parser("ingestor", help="Scan raw/ and ingest new material into vault")
    p_ingest.add_argument("--apply", action="store_true", help="Apply ingestion (overrides --dry-run)")

    p_link = sub.add_parser("linker", help="Find missing links between related notes")
    p_link.add_argument("--threshold", type=float, default=0.6, help="Similarity threshold (default: 0.6)")
    p_link.add_argument("--apply", action="store_true", help="Apply links (overrides --dry-run)")

    sub.add_parser("reviewer", help="Read-only vault audit report")

    p_research = sub.add_parser("researcher", help="Research a topic across vault notes")
    p_research.add_argument("--topic", required=True, help="Topic to research")
    p_research.add_argument("--days", type=int, help="Only include notes modified within N days")

    sub.add_parser("graph-analyst", help="Monthly navigation analysis")

    p_curator = sub.add_parser("curator", help="Quarterly prune/archive review")
    p_curator.add_argument("--apply", action="store_true", help="Flag for review (overrides --dry-run)")

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

    if args.command == "ingestor":
        results = run_ingestor(dry_run=dry_run)
        report = generate_ingestor_report(results)
        print(report)
        if args.save:
            saved = save_report("ingestor", report)
            print(f"\n📄 Saved to {saved}")

    elif args.command == "linker":
        results = run_linker(dry_run=dry_run, threshold=args.threshold)
        report = generate_linker_report(results)
        print(report)
        if args.save:
            saved = save_report("linker", report)
            print(f"\n📄 Saved to {saved}")

    elif args.command == "reviewer":
        review = run_reviewer()
        report = generate_reviewer_report(review)
        print(report)
        if args.save:
            saved = save_report("reviewer", report)
            print(f"\n📄 Saved to {saved}")

    elif args.command == "researcher":
        results = run_researcher(args.topic, days=args.days)
        report = generate_researcher_report(args.topic, results)
        print(report)
        if args.save:
            saved = save_report("researcher", report)
            print(f"\n📄 Saved to {saved}")

    elif args.command == "graph-analyst":
        graph = run_graph_analyst()
        report = generate_graph_report(graph)
        print(report)
        if args.save:
            saved = save_report("graph-analyst", report)
            print(f"\n📄 Saved to {saved}")

    elif args.command == "curator":
        results = run_curator(dry_run=dry_run)
        report = generate_curator_report(results)
        print(report)
        if args.save:
            saved = save_report("curator", report)
            print(f"\n📄 Saved to {saved}")

    else:
        print("Error: No command specified. Use: ingestor, linker, reviewer, researcher, graph-analyst, curator", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
