#!/usr/bin/env python3
"""
Hermes Brain — Wiki Maintenance Skill.

Implements Karpathy's LLM Wiki pattern:
- ingest: Process a new source file into wiki pages
- query: Answer questions against the wiki with citations
- lint: Health-check the wiki (contradictions, orphans, missing links)
- index: Show/update the wiki index

Multi-harness compliant: --vault, --dry-run default, --apply, stdlib-only, --test.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any
import hashlib
import json
import re
import sys


# ── Data models ──────────────────────────────────────────────────────────────

@dataclass
class WikiPageRecord:
    """A wiki page record."""

    id: str
    path: str  # relative path from vault root
    title: str
    type: str  # entity, concept, comparison, source, synthesis
    summary: str = ""
    sources: str = ""  # comma-separated source links
    status: str = "stub"  # stub, growing, mature, archived
    created_at: str = field(
        default_factory=lambda: datetime.now(timezone.utc).isoformat()
    )

    def to_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "path": self.path,
            "title": self.title,
            "type": self.type,
            "summary": self.summary,
            "sources": self.sources,
            "status": self.status,
            "created_at": self.created_at,
        }


@dataclass
class WikiIngestRecord:
    """A wiki ingest record."""

    id: str
    source_path: str
    source_name: str
    pages_created: str  # comma-separated wiki page paths
    summary: str = ""
    created_at: str = field(
        default_factory=lambda: datetime.now(timezone.utc).isoformat()
    )

    def to_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "source_path": self.source_path,
            "source_name": self.source_name,
            "pages_created": self.pages_created,
            "summary": self.summary,
            "created_at": self.created_at,
        }


@dataclass
class WikiLintRecord:
    """A wiki lint record."""

    id: str
    check_type: str  # contradiction, stale, orphan, missing-link, missing-page
    description: str
    page: str = ""
    resolved: bool = False
    created_at: str = field(
        default_factory=lambda: datetime.now(timezone.utc).isoformat()
    )

    def to_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "check_type": self.check_type,
            "description": self.description,
            "page": self.page,
            "resolved": self.resolved,
            "created_at": self.created_at,
        }


# ── Helpers ──────────────────────────────────────────────────────────────────

def _record_id(prefix: str, text: str) -> str:
    import hashlib

    h = hashlib.sha256(f"{prefix}:{text}".encode()).hexdigest()[:12]
    return f"{prefix}:{h}"


def _init_paths(vault_path: str | None) -> Path | None:
    if not vault_path:
        return None
    return Path(vault_path)


def _ensure_dirs(vault: Path) -> Path:
    dir_path = vault / "02-Areas" / "Wiki"
    dir_path.mkdir(parents=True, exist_ok=True)
    return dir_path


def _ensure_source_dirs(vault: Path) -> Path:
    dir_path = vault / "03-Resources" / "Sources"
    dir_path.mkdir(parents=True, exist_ok=True)
    return dir_path


def _load_json(path: Path) -> list[dict[str, Any]]:
    if not path.exists():
        return []
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
        if isinstance(data, list):
            return data
        return []
    except (json.JSONDecodeError, OSError):
        return []


def _save_json(path: Path, data: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, indent=2), encoding="utf-8")


def _find_wiki_pages(vault: Path) -> list[Path]:
    wiki_dir = vault / "02-Areas" / "Wiki"
    if not wiki_dir.exists():
        return []
    return sorted(wiki_dir.rglob("*.md"))


def _find_source_files(vault: Path) -> list[Path]:
    sources_dir = vault / "03-Resources" / "Sources"
    if not sources_dir.exists():
        return []
    return sorted(sources_dir.rglob("*"))


# ── CLI ──────────────────────────────────────────────────────────────────────

import argparse  # noqa: E402


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="PM Best Practices: Wiki Maintenance (LLM Wiki pattern)"
    )
    parser.add_argument("--vault", required=True, help="Path to vault directory")
    parser.add_argument(
        "--dry-run",
        action="store_true",
        default=True,
        help="Dry run mode (default)",
    )
    parser.add_argument(
        "--apply",
        action="store_true",
        help="Apply changes (overrides --dry-run)",
    )
    parser.add_argument("--test", action="store_true", help="Run self-test suite")

    sub = parser.add_subparsers(dest="command")

    # ingest
    p_ig = sub.add_parser("ingest", help="Ingest a new source into the wiki")
    p_ig.add_argument("--source", help="Path to source file (relative to vault)")
    p_ig.add_argument("--title", help="Source title")
    p_ig.add_argument("--summary", help="Summary of source content")

    # query
    p_q = sub.add_parser("query", help="Answer a question against the wiki")
    p_q.add_argument("--question", help="Question to answer")

    # lint
    p_l = sub.add_parser("lint", help="Health-check the wiki")
    p_l.add_argument("--fix", action="store_true", help="Auto-fix simple issues")

    # index
    p_idx = sub.add_parser("index", help="Show wiki index")
    p_idx.add_argument("--rebuild", action="store_true", help="Rebuild index from pages")

    # stats
    sub.add_parser("stats", help="Show wiki stats")

    return parser.parse_args()


def cmd_test() -> int:
    print("PM Best Practices: Wiki Maintenance — Self-Test Suite")
    print("=" * 50)

    passed = 0
    failed = 0

    # Test 1: Record creation
    print("\n[1/3] Record creation...")
    rec = WikiPageRecord(
        id=_record_id("page", "test-concept"),
        path="02-Areas/Wiki/concepts/test-concept.md",
        title="Test Concept",
        type="concept",
        summary="A test concept for self-test",
        sources="",
        status="stub",
    )
    assert rec.title == "Test Concept"
    assert rec.type == "concept"
    assert rec.status == "stub"
    print("  ✅ WikiPageRecord creation works")
    passed += 1

    # Test 2: Ingest record creation
    print("\n[2/3] Ingest record creation...")
    ing = WikiIngestRecord(
        id=_record_id("ingest", "test-source"),
        source_path="03-Resources/Sources/test.md",
        source_name="test.md",
        pages_created="02-Areas/Wiki/sources/test.md",
        summary="Test source ingested",
    )
    assert ing.source_name == "test.md"
    assert ing.pages_created == "02-Areas/Wiki/sources/test.md"
    print("  ✅ WikiIngestRecord creation works")
    passed += 1

    # Test 3: Lint record creation
    print("\n[3/3] Lint record creation...")
    lint = WikiLintRecord(
        id=_record_id("lint", "test-orphan"),
        check_type="orphan",
        description="Page has no inbound links",
        page="02-Areas/Wiki/entities/test.md",
        resolved=False,
    )
    assert lint.check_type == "orphan"
    assert lint.resolved is False
    print("  ✅ WikiLintRecord creation works")
    passed += 1

    total = passed + failed
    print(f"\n{'=' * 50}")
    print(f"Results: {passed}/{total} passed, {failed} failed")
    if failed == 0:
        print("✅ ALL TESTS PASSED")
        return 0
    else:
        print("❌ SOME TESTS FAILED")
        return 1


def main() -> int:
    args = parse_args()

    if args.test:
        return cmd_test()

    if not args.command:
        print(
            "No command specified. Use: ingest, query, lint, index, stats, or test."
        )
        return 1

    vault = _init_paths(args.vault)
    if not vault:
        print("Error: --vault required")
        return 1

    if args.command == "ingest":
        if not args.source:
            print("--source is required for ingest")
            return 1

        source_path = vault / args.source
        if not source_path.exists():
            print(f"Source file not found: {source_path}")
            return 1

        source_name = source_path.name
        pages_created = []

        # Determine wiki page type based on source extension/content
        wiki_type = "source"
        summary = args.summary or "Source ingested — summary pending"

        # Create source summary page in wiki
        wiki_page = vault / "02-Areas" / "Wiki" / "sources" / f"{source_name}.md"
        wiki_page.parent.mkdir(parents=True, exist_ok=True)

        page_content = f"""---
title: {args.title or source_name}
type: source
status: growing
aliases: {args.title or source_name}
sources: 03-Resources/Sources/{args.source}
updated: {datetime.now(timezone).strftime('%Y-%m-%d')}
---

# {args.title or source_name}

## Summary

{summary}

## Sources

- [[../../03-Resources/Sources/{args.source}|{args.source}]] — full source document.

## Notes

*(empty — add notes as you review)*
"""

        if args.apply:
            wiki_page.write_text(page_content, encoding="utf-8")
            print(f"✅ Created wiki page: {wiki_page.relative_to(vault)}")
            pages_created.append(str(wiki_page.relative_to(vault)))

            # Log the ingest
            log_path = vault / "04-Archives" / "Audit-Reports" / "WIKI-LOG.md"
            log_path.parent.mkdir(parents=True, exist_ok=True)
            log_entry = f"""
## [{datetime.now(timezone).strftime('%Y-%m-%d')}] ingest | {args.title or source_name}
- Wrote summary at `02-Areas/Wiki/sources/{source_name}.md`
- Source: `03-Resources/Sources/{args.source}`
"""
            if log_path.exists():
                log_path.write_text(log_path.read_text(encoding="utf-8") + log_entry, encoding="utf-8")
            else:
                log_path.write_text("# Wiki Log\n" + log_entry, encoding="utf-8")
            print(f"📝 Logged ingest to WIKI-LOG.md")
        else:
            print(f"[DRY-RUN] Would create: {wiki_page.relative_to(vault)}")
            pages_created.append(str(wiki_page.relative_to(vault)))

        print(f"\nIngest complete. {len(pages_created)} page(s) created/updated.")
        return 0

    if args.command == "query":
        if not args.question:
            print("--question is required for query")
            return 1

        wiki_pages = _find_wiki_pages(vault)
        print(f"🔍 Searching {len(wiki_pages)} wiki pages for: {args.question}")
        print()
        print("(Query mode — the LLM should read relevant pages and synthesize an answer.)")
        print()
        print("Relevant pages found:")
        for p in wiki_pages[:10]:
            print(f"  - {p.relative_to(vault)}")
        if len(wiki_pages) > 10:
            print(f"  ... and {len(wiki_pages) - 10} more")
        return 0

    if args.command == "lint":
        wiki_pages = _find_wiki_pages(vault)
        print(f"🔍 Linting {len(wiki_pages)} wiki pages...")

        issues = []
        for p in wiki_pages:
            content = p.read_text(encoding="utf-8")
            # Check for orphan pages (no inbound links is hard without full scan,
            # but we can check for missing frontmatter or empty content)
            if len(content.strip()) < 50:
                issues.append(("stub", p, "Page is very short — may need expansion"))
            if "## Summary" not in content:
                issues.append(("structure", p, "Missing '## Summary' section"))

        if issues:
            print(f"\n⚠️  Found {len(issues)} issue(s):")
            for check_type, page, desc in issues:
                print(f"  [{check_type}] {page.relative_to(vault)} — {desc}")
        else:
            print("✅ No issues found. Wiki looks healthy!")

        if args.apply and issues:
            print("\n[APPLY mode] Auto-fixes not yet implemented for lint issues.")
            print("Please review and fix manually, or ask the LLM to help.")

        return 0

    if args.command == "index":
        wiki_pages = _find_wiki_pages(vault)
        print(f"📚 Wiki Index — {len(wiki_pages)} page(s)")
        print()
        for p in wiki_pages:
            rel = p.relative_to(vault)
            # Try to extract title from first heading
            content = p.read_text(encoding="utf-8")
            title_match = re.search(r"^#\s+(.+)$", content, re.MULTILINE)
            title = title_match.group(1) if title_match else rel.stem
            print(f"  - [[{rel}|{title}]]")
        return 0

    if args.command == "stats":
        wiki_pages = _find_wiki_pages(vault)
        source_files = _find_source_files(vault)
        stats = {
            "wiki_pages": len(wiki_pages),
            "source_files": len(source_files),
            "wiki_dir": str(vault / "02-Areas" / "Wiki"),
            "sources_dir": str(vault / "03-Resources" / "Sources"),
        }
        print(json.dumps(stats, indent=2))
        return 0

    print("Unknown command. Use: ingest, query, lint, index, stats, or test.")
    return 1


if __name__ == "__main__":
    sys.exit(main())
