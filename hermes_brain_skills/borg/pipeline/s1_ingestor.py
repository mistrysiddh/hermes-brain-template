"""Borg — Phase 2: S1 Ingestor Agent.

Per mem-draft-spec.txt §4 (Pipeline S1):
S1 Ingestor — Unpack, checksum, classify.

Each raw artifact passes through three sub-steps:
1. Unpack — extract readable content + metadata
2. Checksum — compute cryptographic hashes for integrity/dedup
3. Classify — determine record kind + suggested routing

Sub-prompts are loaded from separate template files in prompts/ for modularity.

Multi-harness compliant: --vault, --dry-run default, --apply, stdlib-only, --test.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from pathlib import Path
from typing import Any
import hashlib
import json
import sys

# ── Sub-prompt imports ───────────────────────────────────────────────────
import importlib.util

_cli_dir = Path(__file__).resolve().parent
_prompts_dir = _cli_dir / "prompts"


def _load_prompt_file(name: str) -> str:
    path = _prompts_dir / f"{name}.txt"
    if not path.exists():
        raise FileNotFoundError(f"Sub-prompt not found: {name}")
    return path.read_text(encoding="utf-8")


S1_UNPACK_PROMPT = _load_prompt_file("s1_unpack_prompt")
S1_CHECKSUM_PROMPT = _load_prompt_file("s1_checksum_prompt")
S1_CLASSIFY_PROMPT = _load_prompt_file("s1_classify_prompt")


def load_prompt(name: str) -> str:
    """Load a sub-prompt template by filename (without .txt extension)."""
    return _load_prompt_file(name)


# ── Record kind ──────────────────────────────────────────────────────────

class RecordKind(str, Enum):
    ROLE = "Role"
    SKILL = "Skill"
    ORCHESTRATION = "Orchestration"
    TRIGGER = "Trigger"
    POLICY = "Policy"
    RESOURCE = "Resource"
    TOOL_BINDING = "Tool-binding"


# ── Ingest result ────────────────────────────────────────────────────────

@dataclass
class IngestResult:
    """S1 Ingestor result for a single artifact."""

    artifact_path: str
    record_id: str
    record_kind: RecordKind = RecordKind.RESOURCE
    confidence: float = 0.0
    source_type: str = "unknown"
    content: str = ""
    metadata: dict[str, Any] = field(default_factory=dict)
    checksums: dict[str, str] = field(default_factory=dict)
    size_bytes: int = 0
    mtime: str = ""
    suggested_routing: list[str] = field(default_factory=list)
    unpack_ok: bool = False
    checksum_ok: bool = False
    classify_ok: bool = False
    errors: list[str] = field(default_factory=list)
    ingestion_notes: str = ""
    ingested_at: str = field(
        default_factory=lambda: datetime.now(timezone.utc).isoformat()
    )

    def to_dict(self) -> dict[str, Any]:
        return {
            "artifact_path": self.artifact_path,
            "record_id": self.record_id,
            "record_kind": self.record_kind.value,
            "confidence": self.confidence,
            "source_type": self.source_type,
            "content": self.content,
            "metadata": self.metadata,
            "checksums": self.checksums,
            "size_bytes": self.size_bytes,
            "mtime": self.mtime,
            "suggested_routing": self.suggested_routing,
            "unpack_ok": self.unpack_ok,
            "checksum_ok": self.checksum_ok,
            "classify_ok": self.classify_ok,
            "errors": self.errors,
            "ingestion_notes": self.ingestion_notes,
            "ingested_at": self.ingested_at,
        }

    @property
    def ok(self) -> bool:
        return self.unpack_ok and self.checksum_ok and self.classify_ok


# ── Step 1: Unpack ───────────────────────────────────────────────────────

def _detect_encoding(data: bytes) -> str:
    """Detect encoding of raw bytes."""
    for enc in ("utf-8", "utf-8-sig", "latin-1"):
        try:
            data.decode(enc)
            return enc
        except UnicodeDecodeError:
            continue
    return "latin-1"


def _detect_mime(filename: str, content: str) -> str:
    """Heuristic MIME type detection from filename and content."""
    lower = filename.lower()
    if lower.endswith((".md", ".markdown", ".txt")):
        return "text/markdown" if lower.endswith((".md", ".markdown")) else "text/plain"
    if lower.endswith(".py"):
        return "text/x-python"
    if lower.endswith(".json"):
        return "application/json"
    if lower.endswith((".yaml", ".yml")):
        return "application/x-yaml"
    if lower.endswith(".toml"):
        return "application/x-toml"
    if lower.endswith(".csv"):
        return "text/csv"
    if lower.endswith(".html"):
        return "text/html"
    if lower.endswith(".png"):
        return "image/png"
    if lower.endswith(".jpg") or lower.endswith(".jpeg"):
        return "image/jpeg"
    if lower.endswith(".pdf"):
        return "application/pdf"
    if content.strip().startswith("{") or content.strip().startswith("["):
        return "application/json"
    if content.strip().startswith("---"):
        return "text/markdown"
    return "application/octet-stream"


def step_unpack(
    artifact_path: Path,
) -> tuple[str, dict[str, Any], list[str], list[str]]:
    """Unpack a raw artifact into content + metadata.

    Returns (content, metadata, boundaries, embedded_structures, errors).
    """
    errors: list[str] = []
    boundaries: list[str] = []
    embedded: list[str] = []

    try:
        raw = artifact_path.read_bytes()
    except OSError as exc:
        errors.append(f"Cannot read artifact: {exc}")
        return "", {}, boundaries, embedded, errors

    encoding = _detect_encoding(raw)
    try:
        content = raw.decode(encoding)
    except UnicodeDecodeError:
        content = raw.decode("latin-1", errors="replace")
        errors.append("Encoding fallback to latin-1 with replacements")

    size_bytes = len(raw)
    mime = _detect_mime(artifact_path.name, content)

    # Detect boundaries (frontmatter, sections)
    if content.strip().startswith("---"):
        boundaries.append("frontmatter")
        embedded.append("frontmatter")

    # Detect code blocks
    if "```" in content:
        embedded.append("code_block")

    # Detect tables
    if "|" in content and "---" in content:
        embedded.append("table")

    # Detect links
    import re
    if re.search(r"\[.*\]\(.*\)", content):
        embedded.append("link")

    stat = artifact_path.stat()
    metadata = {
        "filename": artifact_path.name,
        "size_bytes": size_bytes,
        "encoding": encoding,
        "mime_type": mime,
        "boundaries": boundaries,
        "embedded_structures": embedded,
        "mtime": datetime.fromtimestamp(stat.st_mtime, timezone.utc).isoformat(),
    }

    return content, metadata, boundaries, embedded, errors


# ── Step 2: Checksum ─────────────────────────────────────────────────────

def step_checksum(
    artifact_path: Path,
    algorithm: str = "sha256",
) -> tuple[dict[str, str], int, str, list[str]]:
    """Compute cryptographic checksums for an artifact.

    Returns (checksums, size_bytes, mtime, errors).
    """
    errors: list[str] = []
    checksums: dict[str, str] = {}

    try:
        hasher = hashlib.new(algorithm)
    except ValueError:
        errors.append(f"Unsupported hash algorithm: {algorithm}")
        hasher = hashlib.sha256()

    sha256_hasher = hashlib.sha256()
    size = 0

    try:
        with open(artifact_path, "rb") as f:
            while True:
                chunk = f.read(65536)
                if not chunk:
                    break
                hasher.update(chunk)
                sha256_hasher.update(chunk)
                size += len(chunk)
    except OSError as exc:
        errors.append(f"Cannot read for checksum: {exc}")
        return {}, 0, "", errors

    checksums["sha256"] = sha256_hasher.hexdigest()
    if algorithm != "sha256":
        checksums[algorithm] = hasher.hexdigest()

    mtime = datetime.fromtimestamp(
        artifact_path.stat().st_mtime, timezone.utc
    ).isoformat()

    return checksums, size, mtime, errors


# ── Step 3: Classify ─────────────────────────────────────────────────────

_KIND_KEYWORDS: dict[RecordKind, list[str]] = {
    RecordKind.ROLE: ["role", "persona", "identity", "agent", "assistant"],
    RecordKind.SKILL: ["skill", "capability", "tool", "procedure", "how-to"],
    RecordKind.ORCHESTRATION: [
        "orchestration",
        "workflow",
        "dag",
        "pipeline",
        "scheduler",
    ],
    RecordKind.TRIGGER: ["trigger", "event", "hook", "webhook", "activation"],
    RecordKind.POLICY: ["policy", "rule", "constraint", "governance", "compliance"],
    RecordKind.RESOURCE: ["resource", "template", "reference", "data", "schema"],
    RecordKind.TOOL_BINDING: [
        "tool-binding",
        "adapter",
        "integration",
        "connector",
        "mcp",
    ],
}


def _detect_source_type(filename: str, mime: str) -> str:
    lower = filename.lower()
    if lower.endswith((".py", ".js", ".ts", ".go", ".rs", ".java", ".rb", ".sh")):
        return "code"
    if lower.endswith((".md", ".markdown", ".txt", ".rst")):
        return "markdown"
    if lower.endswith((".json", ".yaml", ".yml", ".toml", ".ini", ".cfg")):
        return "data"
    if lower.endswith((".png", ".jpg", ".jpeg", ".gif", ".svg", ".pdf")):
        return "binary"
    return "unknown"


def step_classify(
    content: str,
    metadata: dict[str, Any],
    checksums: dict[str, str],
) -> tuple[RecordKind, float, str, list[str], str]:
    """Classify an unpacked artifact into a record kind.

    Returns (kind, confidence, source_type, routing, notes).
    """
    errors: list[str] = []
    filename = metadata.get("filename", "")
    mime = metadata.get("mime_type", "unknown")
    source_type = _detect_source_type(filename, mime)

    content_lower = content.lower()
    filename_lower = filename.lower()

    # Score each kind
    scores: dict[RecordKind, float] = {}
    for kind, keywords in _KIND_KEYWORDS.items():
        score = 0.0
        for kw in keywords:
            if kw in content_lower:
                score += 0.2
            if kw in filename_lower:
                score += 0.3
        scores[kind] = min(score, 1.0)

    # Pick best kind
    best_kind = max(scores, key=scores.get)
    best_score = scores[best_kind]

    # If no strong signal, default to Resource
    if best_score < 0.1:
        best_kind = RecordKind.RESOURCE
        best_score = 0.1

    confidence = min(best_score, 1.0)

    # Suggested routing based on kind
    routing: list[str] = []
    if best_kind in (RecordKind.SKILL, RecordKind.TOOL_BINDING):
        routing.append("S2 Profiler")
        routing.append("S3 Directory")
    elif best_kind == RecordKind.POLICY:
        routing.append("S2 Profiler")
    elif best_kind == RecordKind.ORCHESTRATION:
        routing.append("S2 Profiler")
        routing.append("S5 Decompose")
    else:
        routing.append("S2 Profiler")

    notes = (
        f"Classified as {best_kind.value} with confidence {confidence:.2f} "
        f"based on content and filename signals."
    )

    return best_kind, confidence, source_type, routing, notes


# ── S1 Ingestor ──────────────────────────────────────────────────────────

class S1Ingestor:
    """S1 Ingestor agent — Unpack, checksum, classify.

    Processes raw artifacts through three sub-steps, each governed by a
    separately-loadable sub-prompt template.
    """

    def __init__(self, vault_path: str | None = None):
        self.vault_path = Path(vault_path) if vault_path else None
        self._results: dict[str, IngestResult] = {}

    def ingest_file(
        self,
        artifact_path: str | Path,
        record_id: str | None = None,
        algorithm: str = "sha256",
    ) -> IngestResult:
        """Ingest a single file through all three S1 sub-steps."""
        path = Path(artifact_path)
        if not path.exists():
            return IngestResult(
                artifact_path=str(path),
                record_id=record_id or path.name,
                errors=[f"File not found: {path}"],
            )

        if record_id is None:
            record_id = f"s1:{path.name}"

        # Step 1: Unpack
        content, metadata, boundaries, embedded, unpack_errors = step_unpack(path)
        unpack_ok = len(unpack_errors) == 0

        # Step 2: Checksum
        checksums, size_bytes, mtime, checksum_errors = step_checksum(path, algorithm)
        checksum_ok = len(checksum_errors) == 0

        # Merge metadata from unpack with checksum info
        metadata["size_bytes"] = size_bytes
        metadata["mtime"] = mtime

        # Step 3: Classify
        kind, confidence, source_type, routing, notes = step_classify(
            content, metadata, checksums
        )
        classify_ok = True

        all_errors = unpack_errors + checksum_errors

        result = IngestResult(
            artifact_path=str(path),
            record_id=record_id,
            record_kind=kind,
            confidence=confidence,
            source_type=source_type,
            content=content,
            metadata=metadata,
            checksums=checksums,
            size_bytes=size_bytes,
            mtime=mtime,
            suggested_routing=routing,
            unpack_ok=unpack_ok,
            checksum_ok=checksum_ok,
            classify_ok=classify_ok,
            errors=all_errors,
            ingestion_notes=notes,
        )

        self._results[record_id] = result
        return result

    def ingest_directory(
        self,
        directory: str | Path,
        glob_pattern: str = "**/*",
        algorithm: str = "sha256",
    ) -> list[IngestResult]:
        """Ingest all files in a directory matching glob_pattern."""
        dir_path = Path(directory)
        results: list[IngestResult] = []
        for file_path in sorted(dir_path.rglob(glob_pattern)):
            if file_path.is_file():
                result = self.ingest_file(file_path, algorithm=algorithm)
                results.append(result)
        return results

    def get_result(self, record_id: str) -> IngestResult | None:
        """Get a previously computed result."""
        return self._results.get(record_id)

    def list_results(self) -> list[IngestResult]:
        """List all results."""
        return list(self._results.values())

    def stats(self) -> dict[str, Any]:
        """Ingestor statistics."""
        if not self._results:
            return {"total": 0}
        kinds: dict[str, int] = {}
        ok_count = 0
        for r in self._results.values():
            kinds[r.record_kind.value] = kinds.get(r.record_kind.value, 0) + 1
            if r.ok:
                ok_count += 1
        return {
            "total": len(self._results),
            "ok": ok_count,
            "kinds": kinds,
        }


# ── CLI ──────────────────────────────────────────────────────────────────

import argparse  # noqa: E402


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Borg S1 Ingestor — Unpack, checksum, classify",
    )
    parser.add_argument("--vault", required=True, help="Path to vault directory")
    parser.add_argument(
        "--artifact", help="Single artifact file to ingest"
    )
    parser.add_argument("--record-id", help="Record ID (defaults to filename)")
    parser.add_argument(
        "--algorithm", default="sha256", help="Hash algorithm (default: sha256)"
    )
    parser.add_argument(
        "--directory", help="Directory to ingest (all files)"
    )
    parser.add_argument(
        "--glob", default="**/*", help="Glob pattern for directory ingestion"
    )
    parser.add_argument("--list", action="store_true", help="List all results")
    parser.add_argument("--stats", action="store_true", help="Show statistics")
    parser.add_argument("--test", action="store_true", help="Run self-test suite")
    parser.add_argument(
        "--dry-run", action="store_true", default=True, help="Dry run mode (default)"
    )
    parser.add_argument(
        "--apply", action="store_true", help="Apply changes (overrides dry-run)"
    )
    return parser.parse_args()


def cmd_test() -> int:
    """Run self-test suite."""
    print("Borg S1 Ingestor — Self-Test Suite")
    print("=" * 50)

    passed = 0
    failed = 0

    # Test 1: Sub-prompt loading
    print("\n[1/6] Sub-prompt loading...")
    try:
        unpack_prompt = S1_UNPACK_PROMPT
        checksum_prompt = S1_CHECKSUM_PROMPT
        classify_prompt = S1_CLASSIFY_PROMPT
        assert "TASK: Unpack" in unpack_prompt
        assert "TASK: Compute cryptographic" in checksum_prompt
        assert "TASK: Classify" in classify_prompt
        print("  ✅ All 3 sub-prompts loaded")
        passed += 1
    except Exception as exc:
        print(f"  ❌ Failed: {exc}")
        failed += 1

    # Test 2: Unpack step
    print("\n[2/6] Unpack step...")
    import tempfile
    import os

    with tempfile.NamedTemporaryFile(
        mode="w", suffix=".md", delete=False
    ) as f:
        f.write("---\ntitle: test\n---\n\n# Hello\n\nThis is **bold** text.\n")
        tmp_path = f.name

    try:
        content, metadata, boundaries, embedded, errors = step_unpack(Path(tmp_path))
        assert content, "Content should not be empty"
        assert metadata.get("filename"), "Filename should be set"
        assert "frontmatter" in boundaries, "Should detect frontmatter"
        assert "code_block" not in embedded, "No code blocks in this file"
        print(f"  ✅ Unpacked {len(content)} chars, {len(boundaries)} boundaries")
        passed += 1
    except Exception as exc:
        print(f"  ❌ Failed: {exc}")
        failed += 1
    finally:
        os.unlink(tmp_path)

    # Test 3: Checksum step
    print("\n[3/6] Checksum step...")
    with tempfile.NamedTemporaryFile(mode="w", delete=False) as f:
        f.write("deterministic content for hashing")
        tmp_path = f.name

    try:
        checksums, size, mtime, errors = step_checksum(Path(tmp_path))
        assert "sha256" in checksums, "SHA-256 should be computed"
        assert len(checksums["sha256"]) == 64, "SHA-256 hex digest is 64 chars"
        assert size > 0, "Size should be positive"
        print(f"  ✅ Checksum: {checksums['sha256'][:16]}... size={size}")
        passed += 1
    except Exception as exc:
        print(f"  ❌ Failed: {exc}")
        failed += 1
    finally:
        os.unlink(tmp_path)

    # Test 4: Classify step
    print("\n[4/6] Classify step...")
    content = "This is a skill definition for the borg pipeline agent system."
    metadata = {"filename": "borg_skill.py", "mime_type": "text/x-python"}
    checksums = {"sha256": "abc123"}

    try:
        kind, conf, src_type, routing, notes = step_classify(
            content, metadata, checksums
        )
        assert kind in RecordKind, "Kind should be a valid RecordKind"
        assert 0.0 <= conf <= 1.0, "Confidence should be 0-1"
        assert src_type == "code", f"Expected code, got {src_type}"
        print(f"  ✅ Classified as {kind.value} (confidence={conf:.2f}, type={src_type})")
        passed += 1
    except Exception as exc:
        print(f"  ❌ Failed: {exc}")
        failed += 1

    # Test 5: Full ingest_file
    print("\n[5/6] Full ingest_file...")
    with tempfile.NamedTemporaryFile(
        mode="w", suffix=".py", delete=False
    ) as f:
        f.write("# Borg skill adapter\n\ndef run():\n    pass\n")
        tmp_path = f.name

    try:
        ingestor = S1Ingestor()
        result = ingestor.ingest_file(tmp_path, record_id="test_rec_1")
        assert result.record_kind == RecordKind.SKILL, f"Expected SKILL, got {result.record_kind}"
        assert result.ok, "Result should be ok"
        assert result.checksums.get("sha256"), "Should have SHA-256"
        assert result.source_type == "code", f"Expected code, got {result.source_type}"
        print(f"  ✅ Ingested: {result.record_kind.value}, conf={result.confidence:.2f}, ok={result.ok}")
        passed += 1
    except Exception as exc:
        print(f"  ❌ Failed: {exc}")
        failed += 1
    finally:
        os.unlink(tmp_path)

    # Test 6: Stats
    print("\n[6/6] Stats...")
    try:
        ingestor = S1Ingestor()
        ingestor.ingest_file(__file__, record_id="stats_test")
        stats = ingestor.stats()
        assert stats["total"] >= 1, "Should have at least 1 result"
        assert "kinds" in stats, "Should have kinds breakdown"
        print(f"  ✅ Stats: {stats['total']} total, {stats.get('ok', 0)} ok")
        passed += 1
    except Exception as exc:
        print(f"  ❌ Failed: {exc}")
        failed += 1

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

    ingestor = S1Ingestor(vault_path=args.vault)

    if args.stats:
        stats = ingestor.stats()
        print("Ingestor Statistics:")
        for k, v in stats.items():
            print(f"  {k}: {v}")
        return 0

    if args.list:
        results = ingestor.list_results()
        print(f"Results ({len(results)}):")
        for r in results:
            print(
                f"  {r.record_id}: {r.record_kind.value} "
                f"(conf={r.confidence:.2f}, ok={r.ok}, "
                f"sha={r.checksums.get('sha256', 'n/a')[:12]}...)"
            )
        return 0

    if args.artifact:
        result = ingestor.ingest_file(args.artifact, record_id=args.record_id, algorithm=args.algorithm)
        print(f"Ingest result for {result.record_id}:")
        print(f"  Kind: {result.record_kind.value} (conf={result.confidence:.2f})")
        print(f"  Source type: {result.source_type}")
        print(f"  SHA-256: {result.checksums.get('sha256', 'n/a')}")
        print(f"  Size: {result.size_bytes} bytes")
        print(f"  OK: {result.ok}")
        print(f"  Routing: {', '.join(result.suggested_routing) or 'none'}")
        if result.errors:
            print(f"  Errors: {', '.join(result.errors)}")
        return 0 if result.ok else 1

    if args.directory:
        results = ingestor.ingest_directory(args.directory, glob_pattern=args.glob, algorithm=args.algorithm)
        print(f"Ingested {len(results)} files from {args.directory}")
        for r in results:
            status = "✅" if r.ok else "❌"
            print(
                f"  {status} {r.record_id}: {r.record_kind.value} "
                f"(conf={r.confidence:.2f})"
            )
        return 0

    print("No action given. Run with --help to see the options.")
    return 1


if __name__ == "__main__":
    sys.exit(main())
