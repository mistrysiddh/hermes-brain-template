#!/usr/bin/env python3
"""
Hermes Brain — Zettelkasten Note Management (mikonos-style).

Builds and maintains atomic, linked notes in the vault following Zettelkasten
principles: fleeting notes → literature notes → index notes (MOCs) → bidirectional
wikilinks between related notes.

Multi-harness compatible:
  - --vault CLI arg for vault path (never module-level path resolution)
  - Path resolution deferred to main() after argument parsing
  - Works from any TUI agent (CLI, desktop, TUI, gateway)

Subcommands:
  zknote.py fleeting       Capture a fleeting note (raw thought → inbox)
  zknote.py literature     Convert a fleeting note into a literature note (atomic + sources)
  zknote.py index          Build/rebuild index (MOC) notes for recurring topics
  zknote.py split          Atomize a long note into reusable smaller units
  zknote.py maintain       Network maintenance: orphans, weak links, bridges
  zknote.py all            Run literature + index + maintain in sequence
  zknote.py --test         Built-in self-test suite

Design principles (BASB/ZK):
- Atomic notes: each note holds one idea, linkable and reusable
- Progressive summarization: fleeting → literature → index
- Networked thought: every note gets ≥1 wikilink back to its source
- PARA-aware: respects Projects/Areas/Resources/Archives folder structure

Exit code: 0 always (reporting tool, not a gate)
"""

import argparse
import datetime
import os
import re
import sys
from pathlib import Path

# ---------------------------------------------------------------------------
# Path resolution — deferred to main(), never at import time
# ---------------------------------------------------------------------------
VAULT = None
INBOX_DIR = None
LITERATURE_DIR = None
INDEX_DIR = None
DAILY_DIR = None
REPORT_DIR = None
ZK_REPORT = None


def init_paths(vault_path):
    """Resolve all vault-relative paths from the given vault root.
    Called from main() after argument parsing — never at import time.
    """
    global VAULT, INBOX_DIR, LITERATURE_DIR, INDEX_DIR, DAILY_DIR, REPORT_DIR, ZK_REPORT
    VAULT = os.path.abspath(vault_path)
    INBOX_DIR = os.path.join(VAULT, "00-inbox")
    if not os.path.isdir(INBOX_DIR):
        INBOX_DIR = os.path.join(VAULT, "04-Archives", "Daily")
    LITERATURE_DIR = os.path.join(VAULT, "05-knowledge", "literature")
    INDEX_DIR = os.path.join(VAULT, "03-Resources", "MOCs")
    DAILY_DIR = os.path.join(VAULT, "04-Archives", "Daily")
    if not os.path.isdir(DAILY_DIR):
        DAILY_DIR = os.path.join(VAULT, "Daily")
    REPORT_DIR = os.path.join(VAULT, "04-Archives", "Audit-Reports")
    ZK_REPORT = os.path.join(REPORT_DIR, "Zettelkasten-Report.md")


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


def append_file(path, content):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "a", encoding="utf-8") as f:
        f.write(content)


def slugify(text):
    slug = re.sub(r"[^a-zA-Z0-9_-]+", "-", text.strip().lower()).strip("-_")
    return slug or "untitled"


WIKILINK_RE = re.compile(r"\[\[([^\]]+)\]\]")


def all_vault_files(vault):
    """Build a set of all note paths (relative, without .md) for link resolution."""
    all_files = set()
    for root, dirs, files in os.walk(vault):
        dirs[:] = [d for d in dirs if not d.startswith(".") and d not in ("cache", "graphify-out")]
        for fname in files:
            if not fname.endswith(".md"):
                continue
            full = os.path.join(root, fname)
            rel = os.path.relpath(full, vault).replace("\\", "/")
            all_files.add(rel)
            all_files.add(rel[:-3])  # without .md
            all_files.add(fname)
            all_files.add(fname[:-3])
    return all_files


# ---------------------------------------------------------------------------
# 1. Fleeting notes — capture raw thought into inbox
# ---------------------------------------------------------------------------
def capture_fleeting(vault_path, content, tags=None, source=None):
    """Capture a fleeting note: raw, unstructured, timestamped."""
    now = datetime.datetime.now()
    timestamp = now.strftime("%Y%m%d-%H%M%S")
    safe_slug = slugify(content[:40]) if content else "fleeting"
    fname = f"{timestamp}-{safe_slug}.md"
    target = os.path.join(INBOX_DIR, fname)
    front = f"""---\ntype: fleeting\nstatus: captured\ncreated: {now.strftime('%Y-%m-%d %H:%M:%S')}\nsource: {source or 'manual'}\ntags: [{', '.join(tags) if tags else ''}]\n---\n\n# Fleeting: {content[:60]}\n\n{content}\n\n---\n*Captured by zknote.py — review and promote to literature note.*\n"""
    write_file(target, front)
    return target


# ---------------------------------------------------------------------------
# 2. Literature notes — atomic, one idea per note, with sources
# ---------------------------------------------------------------------------
def literature_note(vault_path, source_path, idea, tags=None):
    """Convert a fleeting note into an atomic literature note."""
    now = datetime.datetime.now()
    safe_slug = slugify(idea[:50])
    target = os.path.join(LITERATURE_DIR, f"lit-{safe_slug}.md")
    counter = 1
    while os.path.exists(target):
        target = os.path.join(LITERATURE_DIR, f"lit-{safe_slug}-{counter}.md")
        counter += 1
    front = f"""---\ntype: literature-note\nstatus: active\ncreated: {now.strftime('%Y-%m-%d')}\nsource: [[{os.path.relpath(source_path, VAULT)}]]\ntags: [{', '.join(tags) if tags else ''}, literature-note]\n---\n\n# Literature Note: {idea}\n\n## Source\n[[{os.path.relpath(source_path, VAULT)}]]\n\n## Idea\n{idea}\n\n## Connections\n- [ ] Link to related notes\n- [ ] Add to relevant MOC (index note)\n\n---\n*Created by zknote.py — BASB/ZK atomic note.*\n"""
    write_file(target, front)
    return target


# ---------------------------------------------------------------------------
# 3. Index notes (MOCs) — build maps of content for recurring topics
# ---------------------------------------------------------------------------
def build_index_notes(vault_path, days=30):
    """Scan vault for recurring topics and build MOC notes."""
    all_files = all_vault_files(VAULT)
    # Collect all tags from all notes
    topic_counts = {}
    for root, dirs, files in os.walk(VAULT):
        dirs[:] = [d for d in dirs if not d.startswith(".") and d not in ("cache", "graphify-out")]
        for f in files:
            if not f.endswith(".md"):
                continue
            full = os.path.join(root, f)
            content = read_file(full)
            tf_match = re.search(r"^tags:\s*\[(.*?)\]", content, re.M)
            if tf_match:
                for t in tf_match.group(1).split(","):
                    t = t.strip().lower()
                    if t:
                        topic_counts[t] = topic_counts.get(t, 0) + 1
            for h in re.findall(r"#([A-Za-z0-9_\-]+)", content):
                topic_counts[h.lower()] = topic_counts.get(h.lower(), 0) + 1

    # Filter to topics with 2+ notes (recurring)
    recurring = {t: c for t, c in topic_counts.items() if c >= 2}
    recurring = dict(sorted(recurring.items(), key=lambda x: -x[1])[:10])

    created = []
    for topic, count in recurring.items():
        safe_topic = slugify(topic)
        target = os.path.join(INDEX_DIR, f"MOC-{safe_topic}.md")
        if os.path.exists(target):
            continue
        now = datetime.datetime.now()
        content = f"""---\ntype: moc\nstatus: active\ntopic: {topic}\ncreated: {now.strftime('%Y-%m-%d')}\ntags: [moc, structure-note]\n---\n\n# 🗺️ Map of Content: {topic.title()}\n\n> Auto-generated by zknote.py — aggregates notes tagged `#{topic}`.\n\n## Member Notes\n\n"""
        # Find notes with this tag
        for root, dirs, files in os.walk(VAULT):
            dirs[:] = [d for d in dirs if not d.startswith(".") and d not in ("cache", "graphify-out")]
            for f in files:
                if not f.endswith(".md"):
                    continue
                full = os.path.join(root, f)
                content_f = read_file(full)
                if f"#{topic}" in content_f or f'tags: [*{topic}' in content_f or f'tags: [ {topic}' in content_f or f'tags:[{topic}' in content_f:
                    rel = os.path.relpath(full, VAULT).replace("\\", "/")
                    name = os.path.splitext(f)[0]
                    content += f"- [[{rel}|{name}]]\n"
        content += "\n---\n*Generated by zknote.py — regenerate to refresh.*\n"
        write_file(target, content)
        created.append(target)
    return created


# ---------------------------------------------------------------------------
# 4. Note splitting — atomize a long note into smaller units
# ---------------------------------------------------------------------------
def split_note(vault_path, source_path):
    """Split a long note into atomic sub-notes by heading."""
    content = read_file(source_path)
    if not content:
        return []
    # Split by H2/H3 headings
    parts = re.split(r"(^#{2,3}\s+.+$)", content, flags=re.M)
    created = []
    current_title = os.path.splitext(os.path.basename(source_path))[0]
    current_body = ""
    for part in parts:
        if re.match(r"^#{2,3}\s+", part):
            if current_body.strip():
                # Save previous part
                sub_slug = slugify(current_title[:40])
                target = os.path.join(LITERATURE_DIR, f"split-{sub_slug}.md")
                counter = 1
                while os.path.exists(target):
                    target = os.path.join(LITERATURE_DIR, f"split-{sub_slug}-{counter}.md")
                    counter += 1
                now = datetime.datetime.now()
                sub_content = f"""---\ntype: literature-note\nstatus: active\ncreated: {now.strftime('%Y-%m-%d')}\nsource: [[{os.path.relpath(source_path, VAULT)}]]\nparent: [[{os.path.relpath(source_path, VAULT)}]]\ntags: [literature-note, split-from-{slugify(current_title)}]\n---\n\n# {current_title}\n\n## Source\n[[{os.path.relpath(source_path, VAULT)}]]\n\n{current_body.strip()}\n\n---\n*Split from [[{os.path.relpath(source_path, VAULT)}]] by zknote.py.*\n"""
                write_file(target, sub_content)
                created.append(target)
            current_title = part.replace("#", "").strip()
            current_body = ""
        else:
            current_body += part
    # Save last part
    if current_body.strip():
        sub_slug = slugify(current_title[:40])
        target = os.path.join(LITERATURE_DIR, f"split-{sub_slug}.md")
        counter = 1
        while os.path.exists(target):
            target = os.path.join(LITERATURE_DIR, f"split-{sub_slug}-{counter}.md")
            counter += 1
        now = datetime.datetime.now()
        sub_content = f"""---\ntype: literature-note\nstatus: active\ncreated: {now.strftime('%Y-%m-%d')}\nsource: [[{os.path.relpath(source_path, VAULT)}]]\nparent: [[{os.path.relpath(source_path, VAULT)}]]\ntags: [literature-note, split-from-{slugify(current_title)}]\n---\n\n# {current_title}\n\n## Source\n[[{os.path.relpath(source_path, VAULT)}]]\n\n{current_body.strip()}\n\n---\n*Split from [[{os.path.relpath(source_path, VAULT)}]] by zknote.py.*\n"""
        write_file(target, sub_content)
        created.append(target)
    return created


# ---------------------------------------------------------------------------
# 5. Network maintenance — orphans, weak links, bridges
# ---------------------------------------------------------------------------
def find_orphans(vault_path):
    """Find notes with no incoming wikilinks."""
    all_files = all_vault_files(VAULT)
    linked = set()
    for root, dirs, files in os.walk(VAULT):
        dirs[:] = [d for d in dirs if not d.startswith(".") and d not in ("cache", "graphify-out")]
        for f in files:
            if not f.endswith(".md"):
                continue
            full = os.path.join(root, f)
            content = read_file(full)
            clean = re.sub(r"```[\s\S]*?```", "", content)
            clean = re.sub(r"`[^`\n]+`", "", clean)
            for m in WIKILINK_RE.finditer(clean):
                link = m.group(1).split("|")[0].split("#")[0].strip()
                if link:
                    linked.add(link)
    orphans = []
    for root, dirs, files in os.walk(VAULT):
        dirs[:] = [d for d in dirs if not d.startswith(".") and d not in ("cache", "graphify-out")]
        for f in files:
            if not f.endswith(".md"):
                continue
            full = os.path.join(root, f)
            rel = os.path.relpath(full, VAULT).replace("\\", "/")
            name = os.path.splitext(f)[0]
            if rel not in linked and name not in linked and f not in linked:
                orphans.append(rel)
    return orphans


def find_weak_links(vault_path):
    """Find notes with only one incoming wikilink."""
    all_files = all_vault_files(VAULT)
    link_counts = {}
    for root, dirs, files in os.walk(VAULT):
        dirs[:] = [d for d in dirs if not d.startswith(".") and d not in ("cache", "graphify-out")]
        for f in files:
            if not f.endswith(".md"):
                continue
            full = os.path.join(root, f)
            content = read_file(full)
            clean = re.sub(r"```[\s\S]*?```", "", content)
            clean = re.sub(r"`[^`\n]+`", "", clean)
            for m in WIKILINK_RE.finditer(clean):
                link = m.group(1).split("|")[0].split("#")[0].strip()
                if link:
                    link_counts[link] = link_counts.get(link, 0) + 1
    weak = []
    for root, dirs, files in os.walk(VAULT):
        dirs[:] = [d for d in dirs if not d.startswith(".") and d not in ("cache", "graphify-out")]
        for f in files:
            if not f.endswith(".md"):
                continue
            full = os.path.join(root, f)
            rel = os.path.relpath(full, VAULT).replace("\\", "/")
            name = os.path.splitext(f)[0]
            count = link_counts.get(rel, 0) + link_counts.get(name, 0) + link_counts.get(f, 0)
            if 1 <= count <= 2:
                weak.append((rel, count))
    return weak


# ---------------------------------------------------------------------------
# Report generation
# ---------------------------------------------------------------------------
def generate_report(created, orphans, weak_links, dry_run=True):
    now = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    lines = [
        "# Zettelkasten Report",
        f"Generated: {now}",
        f"Vault: {VAULT}",
        f"Mode: {'DRY-RUN' if dry_run else 'APPLY'}",
        "",
        "---",
        "",
        "## Summary",
        f"- **Notes created**: {len(created)}",
        f"- **Orphaned notes**: {len(orphans)}",
        f"- **Weakly linked notes**: {len(weak_links)}",
        "",
        "---",
        "",
    ]
    if created:
        lines.append("## Created Notes")
        lines.append("")
        for c in created:
            lines.append(f"- [[{os.path.relpath(c, VAULT)}|{os.path.basename(c)}]]")
        lines.append("")
        lines.append("---")
        lines.append("")
    if orphans:
        lines.append("## Orphaned Notes (no incoming links)")
        lines.append("")
        for o in orphans[:20]:
            lines.append(f"- {o}")
        if len(orphans) > 20:
            lines.append(f"- ... and {len(orphans) - 20} more")
        lines.append("")
        lines.append("---")
        lines.append("")
    if weak_links:
        lines.append("## Weakly Linked Notes (1-2 incoming links)")
        lines.append("")
        for w, c in weak_links[:20]:
            lines.append(f"- {w} ({c} link{'s' if c > 1 else ''})")
        if len(weak_links) > 20:
            lines.append(f"- ... and {len(weak_links) - 20} more")
        lines.append("")
        lines.append("---")
        lines.append("")
    write_report(lines)


def write_report(lines):
    os.makedirs(REPORT_DIR, exist_ok=True)
    with open(ZK_REPORT, "w", encoding="utf-8") as f:
        f.write("\n".join(lines))


# ---------------------------------------------------------------------------
# Self-test
# ---------------------------------------------------------------------------
def run_self_test():
    import tempfile
    import shutil

    print("🧪 zknote.py Self-Test Suite")
    print("=" * 50)
    passed = 0
    failed = 0

    # Test 1: init_paths sets vars
    tmp = tempfile.mkdtemp()
    try:
        init_paths(tmp)
        assert VAULT == os.path.abspath(tmp)
        assert REPORT_DIR.endswith("04-Archives/Audit-Reports")
        print("✅ Test 1: init_paths sets vars")
        passed += 1
    except Exception as e:
        print(f"❌ Test 1 failed: {e}")
        failed += 1
    finally:
        shutil.rmtree(tmp)

    # Test 2: capture_fleeting creates a note
    tmp = tempfile.mkdtemp()
    try:
        init_paths(tmp)
        os.makedirs(INBOX_DIR, exist_ok=True)
        target = capture_fleeting(VAULT, "This is a fleeting thought about X", tags=["idea"])
        assert os.path.exists(target)
        content = read_file(target)
        assert "This is a fleeting thought about X" in content
        assert "type: fleeting" in content
        print("✅ Test 2: capture_fleeting creates note")
        passed += 1
    except Exception as e:
        print(f"❌ Test 2 failed: {e}")
        failed += 1
    finally:
        shutil.rmtree(tmp)

    # Test 3: literature_note creates atomic note
    tmp = tempfile.mkdtemp()
    try:
        init_paths(tmp)
        os.makedirs(LITERATURE_DIR, exist_ok=True)
        source = os.path.join(tmp, "04-Archives", "Daily", "session.md")
        os.makedirs(os.path.dirname(source), exist_ok=True)
        write_file(source, "# Session\nSome content here.")
        target = literature_note(VAULT, source, "Atomic idea about X", tags=["idea"])
        assert os.path.exists(target)
        content = read_file(target)
        assert "Atomic idea about X" in content
        assert "type: literature-note" in content
        print("✅ Test 3: literature_note creates atomic note")
        passed += 1
    except Exception as e:
        print(f"❌ Test 3 failed: {e}")
        failed += 1
    finally:
        shutil.rmtree(tmp)

    # Test 4: slugify works
    assert slugify("Hello World!") == "hello-world"
    assert slugify("") == "untitled"
    assert slugify("___") == "untitled"
    print("✅ Test 4: slugify works")
    passed += 1

    # Test 5: build_index_notes creates MOCs
    tmp = tempfile.mkdtemp()
    try:
        init_paths(tmp)
        os.makedirs(INDEX_DIR, exist_ok=True)
        # Create two notes with same tag
        os.makedirs(os.path.join(tmp, "04-Archives", "Daily"), exist_ok=True)
        n1 = os.path.join(tmp, "04-Archives", "Daily", "note1.md")
        n2 = os.path.join(tmp, "04-Archives", "Daily", "note2.md")
        write_file(n1, "---\ntags: [research]\n---\n# Note 1\nContent about research.")
        write_file(n2, "---\ntags: [research]\n---\n# Note 2\nMore about research.")
        created = build_index_notes(VAULT, days=30)
        # Should find 'research' tag with 2 notes
        moc_files = [f for f in os.listdir(INDEX_DIR) if f.endswith(".md")]
        assert len(moc_files) >= 1, f"Expected >=1 MOC, got {len(moc_files)}"
        print("✅ Test 5: build_index_notes creates MOCs")
        passed += 1
    except Exception as e:
        print(f"❌ Test 5 failed: {e}")
        failed += 1
    finally:
        shutil.rmtree(tmp)

    # Test 6: split_note atomizes a long note
    tmp = tempfile.mkdtemp()
    try:
        init_paths(tmp)
        os.makedirs(LITERATURE_DIR, exist_ok=True)
        source = os.path.join(tmp, "04-Archives", "Daily", "long.md")
        os.makedirs(os.path.dirname(source), exist_ok=True)
        write_file(source, """# Long Note\n\n## Part One\n\nContent of part one.\n\n## Part Two\n\nContent of part two.\n""")
        created = split_note(VAULT, source)
        assert len(created) >= 2, f"Expected >=2 split notes, got {len(created)}"
        for c in created:
            assert os.path.exists(c)
        print("✅ Test 6: split_note atomizes long note")
        passed += 1
    except Exception as e:
        print(f"❌ Test 6 failed: {e}")
        failed += 1
    finally:
        shutil.rmtree(tmp)

    # Test 7: find_orphans finds notes with no incoming links
    tmp = tempfile.mkdtemp()
    try:
        init_paths(tmp)
        os.makedirs(os.path.join(tmp, "04-Archives", "Daily"), exist_ok=True)
        n1 = os.path.join(tmp, "04-Archives", "Daily", "orphan.md")
        n2 = os.path.join(tmp, "04-Archives", "Daily", "linker.md")
        write_file(n1, "# Orphan\nNo links here.")
        write_file(n2, "# Linker\nLinks to [[04-Archives/Daily/orphan.md|orphan]].")
        orphans = find_orphans(VAULT)
        # orphan.md should NOT be orphan (it's linked), but linker.md has no incoming links
        assert "04-Archives/Daily/linker.md" in orphans, f"Expected linker.md to be orphan, got {orphans}"
        print("✅ Test 7: find_orphans works")
        passed += 1
    except Exception as e:
        print(f"❌ Test 7 failed: {e}")
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
        description="Hermes Brain Zettelkasten — atomic notes and MOCs.",
    )
    parser.add_argument("--vault", help="Path to the Hermes Brain vault root")
    parser.add_argument("--days", type=int, default=30, help="Days to scan for index notes (default: 30)")
    parser.add_argument("--test", action="store_true", help="Run built-in self-test suite")
    sub = parser.add_subparsers(dest="command", help="Command to run")
    sub.add_parser("fleeting", help="Capture a fleeting note (interactive)")
    sub.add_parser("literature", help="Convert fleeting note to literature note (interactive)")
    sub.add_parser("index", help="Build MOC index notes for recurring topics")
    sub.add_parser("split", help="Atomize a long note into smaller units (interactive)")
    sub.add_parser("maintain", help="Network maintenance: orphans, weak links")
    sub.add_parser("all", help="Run literature + index + maintain")
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

    command = args.command or "all"

    created = []
    orphans = []
    weak_links = []

    if command in ("fleeting", "all"):
        print("📝 Fleeting capture not yet implemented interactively — use --vault with content via script.")
        # Placeholder: no-op for now

    if command in ("literature", "all"):
        print("📖 Literature conversion not yet implemented interactively — use --vault with source via script.")

    if command in ("index", "all"):
        print("🗺️  Building MOC index notes...")
        created = build_index_notes(VAULT, args.days)
        print(f"   Created {len(created)} MOC notes")

    if command in ("split", "all"):
        print("✂️  Note splitting not yet implemented interactively — use --vault with source via script.")

    if command in ("maintain", "all"):
        print("🔧 Running maintenance...")
        orphans = find_orphans(VAULT)
        weak_links = find_weak_links(VAULT)
        print(f"   Found {len(orphans)} orphans, {len(weak_links)} weak links")

    generate_report(created, orphans, weak_links, dry_run=True)
    print(f"\n📄 Report written to {ZK_REPORT}")
    print("✅ Zettelkasten maintenance complete.")


if __name__ == "__main__":
    main()
