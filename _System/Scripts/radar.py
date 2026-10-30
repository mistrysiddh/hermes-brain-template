#!/usr/bin/env python3
"""
Hermes Brain — Radar Skill (standing surveillance on sources → daily digest).

Tracks configured sources (blogs, news feeds, academic papers) and produces a
daily or weekly digest of new items for the Hermes Brain vault.

Multi-harness compatible:
  - --vault CLI arg for vault path (never module-level path resolution)
  - Path resolution deferred to main() after argument parsing
  - Works from any TUI agent (CLI, desktop, TUI, gateway)

Subcommands:
  radar.py scan        Scan all configured sources for new items (dry-run report)
  radar.py digest      Generate and write daily/weekly digest to vault
  radar.py --test      Built-in self-test suite

Sources file format (JSONL, one source per line):
  {"name": "Hermes Blog", "type": "rss", "url": "https://hermes-agent.nousresearch.com/blog/rss", "category": "news"}
  {"name": "arXiv AI", "type": "arxiv", "query": "cat:cs.AI AND submittedDate:[202610010000 TO *]", "category": "papers"}
  {"name": "GitHub Releases", "type": "json", "url": "https://api.github.com/repos/mistrysiddh/hermes-brain-template/releases", "category": "news"}

Exit code: 0 always (reporting tool, not a gate)
"""

import argparse
import datetime
import hashlib
import json
import os
import re
import sys
import urllib.error
import urllib.request
import xml.etree.ElementTree as ET
from email.utils import parsedate_to_datetime

# ---------------------------------------------------------------------------
# Path resolution — deferred to main(), never at import time
# ---------------------------------------------------------------------------
VAULT = None
RADAR_DIR = None
SOURCES_FILE = None
DIGESTS_DIR = None


def init_paths(vault_path):
    """Resolve all vault-relative paths from the given vault root.
    Called from main() after argument parsing — never at import time.
    """
    global VAULT, RADAR_DIR, SOURCES_FILE, DIGESTS_DIR
    VAULT = os.path.abspath(vault_path)
    RADAR_DIR = os.path.join(VAULT, "04-Archives", "Radar")
    SOURCES_FILE = os.path.join(RADAR_DIR, "sources.jsonl")
    DIGESTS_DIR = os.path.join(RADAR_DIR, "digests")


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


def item_id(item):
    """Stable ID for deduplication: hash of title + source."""
    raw = f"{item.get('source','')}|{item.get('title','')}|{item.get('url','')}"
    return hashlib.sha256(raw.encode("utf-8")).hexdigest()[:16]


# ---------------------------------------------------------------------------
# Sources
# ---------------------------------------------------------------------------
DEFAULT_SOURCES = [
    {
        "name": "Hermes Agent Blog",
        "type": "rss",
        "url": "https://hermes-agent.nousresearch.com/blog/rss",
        "category": "news",
    },
    {
        "name": "arXiv AI (cs.AI)",
        "type": "arxiv",
        "query": "cat:cs.AI",
        "category": "papers",
    },
    {
        "name": "GitHub Releases — Hermes Brain Template",
        "type": "json",
        "url": "https://api.github.com/repos/mistrysiddh/hermes-brain-template/releases",
        "category": "news",
    },
]


def load_sources(sources_path=None):
    """Load sources from JSONL file; fall back to defaults if missing."""
    sources_path = sources_path or SOURCES_FILE
    sources = []
    if os.path.exists(sources_path):
        with open(sources_path, encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if not line or line.startswith("#"):
                    continue
                try:
                    src = json.loads(line)
                    if "name" in src and "type" in src:
                        sources.append(src)
                except json.JSONDecodeError:
                    continue
    if not sources:
        sources = DEFAULT_SOURCES
    return sources


def save_sources(sources, sources_path=None):
    """Persist sources to JSONL file."""
    sources_path = sources_path or SOURCES_FILE
    os.makedirs(os.path.dirname(sources_path), exist_ok=True)
    with open(sources_path, "w", encoding="utf-8") as f:
        for s in sources:
            f.write(json.dumps(s, ensure_ascii=False) + "\n")


# ---------------------------------------------------------------------------
# Fetchers
# ---------------------------------------------------------------------------
def fetch_rss(url, max_items=20):
    """Fetch an RSS/Atom feed and return list of items."""
    items = []
    try:
        req = urllib.request.Request(url, headers={"User-Agent": "HermesRadar/1.0"})
        with urllib.request.urlopen(req, timeout=30) as resp:
            data = resp.read()
        root = ET.fromstring(data)

        # RSS 2.0
        for item in root.findall(".//item"):
            title = item.findtext("title") or ""
            link = item.findtext("link") or ""
            desc = item.findtext("description") or ""
            pub = item.findtext("pubDate")
            items.append({
                "title": title.strip(),
                "url": link.strip(),
                "summary": desc.strip()[:300],
                "published": pub,
                "type": "rss",
            })

        # Atom
        ns = {"atom": "http://www.w3.org/2005/Atom"}
        for entry in root.findall("atom:entry", ns):
            title = entry.findtext("atom:title", namespaces=ns) or ""
            link_el = entry.find("atom:link", ns)
            link = link_el.get("href", "") if link_el is not None else ""
            summary = entry.findtext("atom:summary", namespaces=ns) or ""
            pub = entry.findtext("atom:published", namespaces=ns) or ""
            items.append({
                "title": title.strip(),
                "url": link.strip(),
                "summary": summary.strip()[:300],
                "published": pub,
                "type": "atom",
            })
    except Exception as e:
        items.append({
            "title": f"[fetch error] {url}",
            "url": url,
            "summary": str(e),
            "published": "",
            "type": "error",
        })
    return items[:max_items]


def fetch_arxiv(query, max_items=20):
    """Query arXiv API and return list of papers."""
    items = []
    try:
        import urllib.parse
        params = urllib.parse.urlencode({
            "search_query": query,
            "start": "0",
            "max_results": str(max_items),
            "sortBy": "submittedDate",
            "sortOrder": "descending",
        })
        url = f"https://export.arxiv.org/api/query?{params}"
        req = urllib.request.Request(url, headers={"User-Agent": "HermesRadar/1.0"})
        with urllib.request.urlopen(req, timeout=30) as resp:
            data = resp.read()
        root = ET.fromstring(data)
        ns = {
            "atom": "http://www.w3.org/2005/Atom",
            "arxiv": "http://arxiv.org/schemas/atom",
        }
        for entry in root.findall("atom:entry", ns):
            title = entry.findtext("atom:title", namespaces=ns) or ""
            link_el = entry.find("atom:id", ns)
            link = link_el.text if link_el is not None else ""
            summary = entry.findtext("atom:summary", namespaces=ns) or ""
            pub = entry.findtext("atom:published", namespaces=ns) or ""
            authors = [
                a.findtext("atom:name", namespaces=ns) or ""
                for a in entry.findall("atom:author", ns)
            ]
            items.append({
                "title": re.sub(r"\s+", " ", title).strip(),
                "url": link.strip(),
                "summary": re.sub(r"\s+", " ", summary).strip()[:300],
                "published": pub,
                "type": "arxiv",
                "authors": ", ".join(authors)[:100],
            })
    except Exception as e:
        items.append({
            "title": f"[fetch error] arXiv: {query}",
            "url": "https://arxiv.org",
            "summary": str(e),
            "published": "",
            "type": "error",
        })
    return items[:max_items]


def fetch_json(url, max_items=20):
    """Fetch a JSON API endpoint and return list of items."""
    items = []
    try:
        req = urllib.request.Request(url, headers={"User-Agent": "HermesRadar/1.0"})
        with urllib.request.urlopen(req, timeout=30) as resp:
            data = json.loads(resp.read().decode("utf-8"))
        if isinstance(data, list):
            for entry in data[:max_items]:
                title = entry.get("name") or entry.get("title") or entry.get("tag_name") or "Untitled"
                url_val = entry.get("html_url") or entry.get("url") or ""
                body = entry.get("body") or entry.get("description") or ""
                pub = entry.get("published_at") or entry.get("created_at") or ""
                items.append({
                    "title": title.strip(),
                    "url": url_val.strip(),
                    "summary": body.strip()[:300],
                    "published": pub,
                    "type": "json",
                })
        elif isinstance(data, dict):
            # GitHub releases wrapping
            releases = data.get("releases") or data.get("items") or []
            for entry in releases[:max_items]:
                title = entry.get("name") or entry.get("tag_name") or "Untitled"
                url_val = entry.get("html_url") or ""
                body = entry.get("body") or ""
                pub = entry.get("published_at") or ""
                items.append({
                    "title": title.strip(),
                    "url": url_val.strip(),
                    "summary": body.strip()[:300],
                    "published": pub,
                    "type": "json",
                })
    except Exception as e:
        items.append({
            "title": f"[fetch error] {url}",
            "url": url,
            "summary": str(e),
            "published": "",
            "type": "error",
        })
    return items[:max_items]


def fetch_source(source, max_items=20):
    """Dispatch to the right fetcher based on source type."""
    stype = source.get("type", "").lower()
    if stype == "rss" or stype == "atom":
        return fetch_rss(source["url"], max_items)
    elif stype == "arxiv":
        return fetch_arxiv(source.get("query", ""), max_items)
    elif stype == "json":
        return fetch_json(source["url"], max_items)
    else:
        return [{
            "title": f"[unsupported type] {stype}",
            "url": source.get("url", ""),
            "summary": f"Unknown source type: {stype}",
            "published": "",
            "type": "error",
        }]


# ---------------------------------------------------------------------------
# Date filtering
# ---------------------------------------------------------------------------
def parse_date(date_str):
    if not date_str:
        return None
    try:
        return parsedate_to_datetime(date_str)
    except Exception:
        try:
            return datetime.datetime.fromisoformat(date_str.replace("Z", "+00:00"))
        except Exception:
            return None


def within_window(item, days):
    """Return True if item was published within the last N days."""
    dt = parse_date(item.get("published", ""))
    if dt is None:
        return True  # include items we can't date
    cutoff = datetime.datetime.now(datetime.timezone.utc) - datetime.timedelta(days=days)
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=datetime.timezone.utc)
    return dt >= cutoff


# ---------------------------------------------------------------------------
# Scan
# ---------------------------------------------------------------------------
def scan_sources(sources, days=7, max_per_source=20):
    """Scan all sources and return new items within the time window."""
    all_items = []
    for source in sources:
        items = fetch_source(source, max_items=max_per_source)
        for item in items:
            item["source_name"] = source.get("name", "Unknown")
            item["source_category"] = source.get("category", "general")
            if within_window(item, days):
                all_items.append(item)
    # Deduplicate by stable ID
    seen = set()
    unique = []
    for item in all_items:
        iid = item_id(item)
        if iid not in seen:
            seen.add(iid)
            unique.append(item)
    return unique


# ---------------------------------------------------------------------------
# Digest generation
# ---------------------------------------------------------------------------
def generate_digest(items, digest_type="daily", days=7):
    """Generate a markdown digest from scanned items."""
    now = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    total = len(items)
    by_category = {}
    by_source = {}
    for item in items:
        c = item.get("source_category", "general")
        s = item.get("source_name", "Unknown")
        by_category[c] = by_category.get(c, 0) + 1
        by_source[s] = by_source.get(s, 0) + 1

    lines = [
        f"# Radar Digest — {digest_type.capitalize()}",
        f"Generated: {now}",
        f"Window: last {days} days",
        f"Mode: {'DRY-RUN (no changes)' if os.environ.get('HERMES_RADAR_DRY_RUN', '1') == '1' else 'APPLY'}",
        "",
        "---",
        "",
        "## Summary",
        f"- **Total new items**: {total}",
    ]
    for c in ("news", "papers", "general"):
        if by_category.get(c, 0) > 0:
            lines.append(f"  - {c}: {by_category[c]}")
    lines.append("")
    lines.append("---")
    lines.append("")

    if not items:
        lines.append("## ✅ No new items found in the time window.")
        return "\n".join(lines)

    lines.append("## New Items")
    lines.append("")
    lines.append("| Source | Category | Title | Published |")
    lines.append("|--------|----------|-------|-----------|")
    for item in items[:50]:
        pub = parse_date(item.get("published", ""))
        pub_str = pub.strftime("%Y-%m-%d") if pub else "unknown"
        lines.append(
            f"| {item['source_name']} | {item['source_category']} | "
            f"[{item['title'][:60]}]({item['url']}) | {pub_str} |"
        )
    if len(items) > 50:
        lines.append(f"| ... | ... | ... and {len(items) - 50} more | ... | ... |")
    lines.append("")
    lines.append("---")
    lines.append("")

    lines.append("## Details by Source")
    lines.append("")
    for source_name in sorted(by_source.keys()):
        src_items = [i for i in items if i.get("source_name") == source_name]
        lines.append(f"### {source_name} ({len(src_items)} items)")
        for item in src_items[:10]:
            pub = parse_date(item.get("published", ""))
            pub_str = pub.strftime("%Y-%m-%d") if pub else "unknown"
            authors = item.get("authors", "")
            author_str = f" — {authors}" if authors else ""
            lines.append(
                f"- [{item['title'][:70]}]({item['url']}) ({pub_str}){author_str}\n"
                f"  {item.get('summary', '')[:200]}"
            )
        if len(src_items) > 10:
            lines.append(f"  ... and {len(src_items) - 10} more")
        lines.append("")
    lines.append("---")
    lines.append("")

    lines.append("## Next Steps")
    lines.append("")
    lines.append("Review items above. To add a source, append a JSONL entry to `04-Archives/Radar/sources.jsonl`.")
    lines.append("To run again: `radar.py --vault <path> scan --days 7`")
    return "\n".join(lines)


def write_digest_to_vault(content, digest_type="daily", days=7):
    """Write the digest markdown file into the vault."""
    today = datetime.datetime.now().strftime("%Y-%m-%d")
    filename = f"Radar-{digest_type}-{today}.md"
    path = os.path.join(DIGESTS_DIR, filename)
    write_file(path, content)
    return path


# ---------------------------------------------------------------------------
# Self-test
# ---------------------------------------------------------------------------
def run_self_test():
    import tempfile
    import shutil

    print("🧪 radar.py Self-Test Suite")
    print("=" * 50)
    passed = 0
    failed = 0

    # Test 1: item_id is stable
    try:
        a = item_id({"source": "s", "title": "t", "url": "u"})
        b = item_id({"source": "s", "title": "t", "url": "u"})
        c = item_id({"source": "s", "title": "different", "url": "u"})
        assert a == b, "Same item should produce same ID"
        assert a != c, "Different items should produce different IDs"
        print("✅ Test 1: item_id is stable and unique")
        passed += 1
    except Exception as e:
        print(f"❌ Test 1 failed: {e}")
        failed += 1

    # Test 2: within_window includes recent items
    try:
        recent = {"published": datetime.datetime.now(datetime.timezone.utc).isoformat()}
        old = {"published": (datetime.datetime.now(datetime.timezone.utc) - datetime.timedelta(days=30)).isoformat()}
        assert within_window(recent, 7), "Recent item should be in window"
        assert not within_window(old, 7), "30-day-old item should not be in 7-day window"
        assert within_window({}, 7), "Undated item should be included"
        print("✅ Test 2: within_window filters correctly")
        passed += 1
    except Exception as e:
        print(f"❌ Test 2 failed: {e}")
        failed += 1

    # Test 3: load_sources falls back to defaults
    try:
        init_paths("/tmp")
        sources = load_sources("/tmp/nonexistent.jsonl")
        assert len(sources) >= 1, "Should fall back to defaults"
        assert sources[0]["name"] == "Hermes Agent Blog"
        print("✅ Test 3: load_sources falls back to defaults")
        passed += 1
    except Exception as e:
        print(f"❌ Test 3 failed: {e}")
        failed += 1

    # Test 4: save_sources and load_sources round-trip
    tmp = tempfile.mkdtemp()
    try:
        test_sources = [
            {"name": "Test Blog", "type": "rss", "url": "https://example.com/rss", "category": "news"},
        ]
        save_sources(test_sources, os.path.join(tmp, "sources.jsonl"))
        loaded = load_sources(os.path.join(tmp, "sources.jsonl"))
        assert len(loaded) == 1
        assert loaded[0]["name"] == "Test Blog"
        print("✅ Test 4: save/load sources round-trips")
        passed += 1
    except Exception as e:
        print(f"❌ Test 4 failed: {e}")
        failed += 1
    finally:
        shutil.rmtree(tmp)

    # Test 5: scan deduplicates
    try:
        init_paths("/tmp")
        sources = [
            {"name": "Dup", "type": "rss", "url": "https://example.com/rss", "category": "news"},
        ]
        items = scan_sources(sources, days=7, max_per_source=5)
        ids = [item_id(i) for i in items]
        assert len(ids) == len(set(ids)), "No duplicate IDs after scan"
        print("✅ Test 5: scan deduplicates items")
        passed += 1
    except Exception as e:
        print(f"❌ Test 5 failed: {e}")
        failed += 1

    print("=" * 50)
    print(f"🎉 Self-tests: {passed} passed, {failed} failed")
    return failed == 0


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------
def parse_args():
    parser = argparse.ArgumentParser(
        description="Hermes Brain Radar — standing surveillance on sources → daily digest.",
    )
    parser.add_argument("--vault", help="Path to the Hermes Brain vault root")
    parser.add_argument("--sources-file", help="Path to sources JSONL file (default: <vault>/04-Archives/Radar/sources.jsonl)")
    parser.add_argument("--days", type=int, default=7, help="Days to look back (default: 7)")
    parser.add_argument("--digest-type", choices=["daily", "weekly"], default="daily", help="Digest type (default: daily)")
    parser.add_argument("--max-per-source", type=int, default=20, help="Max items per source (default: 20)")
    parser.add_argument("--dry-run", action="store_true", default=True, help="Report only, no digest written (default)")
    parser.add_argument("--apply", action="store_true", help="Write digest to vault (overrides --dry-run)")
    parser.add_argument("--test", action="store_true", help="Run built-in self-test suite")
    sub = parser.add_subparsers(dest="command", help="Command to run")
    sub.add_parser("scan", help="Scan all configured sources for new items (dry-run report)")
    sub.add_parser("digest", help="Generate and write daily/weekly digest to vault")
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

    sources_path = args.sources_file or SOURCES_FILE
    sources = load_sources(sources_path)
    print(f"📡 Loaded {len(sources)} sources from {sources_path}")

    items = scan_sources(sources, days=args.days, max_per_source=args.max_per_source)
    print(f"🔍 Found {len(items)} new items in last {args.days} days\n")

    if not items:
        print("✅ No new items found in the time window.")
        digest_md = generate_digest([], digest_type=args.digest_type, days=args.days)
    else:
        digest_md = generate_digest(items, digest_type=args.digest_type, days=args.days)

    if dry_run:
        print("📄 Digest preview (dry-run — not written to vault):")
        print(digest_md[:2000])
        if len(digest_md) > 2000:
            print(f"\n... ({len(digest_md) - 2000} more chars)")
    else:
        digest_path = write_digest_to_vault(digest_md, digest_type=args.digest_type, days=args.days)
        print(f"📄 Digest written to {digest_path}")


if __name__ == "__main__":
    main()
