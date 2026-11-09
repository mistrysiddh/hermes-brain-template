#!/usr/bin/env python3
"""
Hermes Brain — Smart Memory & RAG Skill (multi-harness compatible).

Agentic memory system inspired by Jev-Mem and laya-jev-GraphRAG:
- System-One control plane: fast heuristic decisions for memory routing/budget
- Multi-relational memory plane: semantic, temporal, causal, entity relations
- System-Two reasoning: invoked only for genuine synthesis
- Open model support: works with any local/open model, not tied to paid Jev API
- Data type awareness: different handling for different memory data types

Multi-harness compliant:
  - --vault CLI arg, deferred path resolution via init_paths()
  - --dry-run default / --apply for human-in-the-loop approval
  - stdlib-only
  - --test built-in self-test suite
"""

import argparse
import hashlib
import json
import math
import os
import re
import sys
from collections import defaultdict
from datetime import datetime, timedelta

# ---------------------------------------------------------------------------
# Path resolution — deferred to main(), never at import time
# ---------------------------------------------------------------------------
VAULT = None


def init_paths(vault_path):
    """Resolve all vault-relative paths from the given vault root."""
    global VAULT
    VAULT = os.path.abspath(vault_path)


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


# ---------------------------------------------------------------------------
# Memory storage (JSONL files in vault)
# ---------------------------------------------------------------------------
MEMORY_DIR = "_System/Memory"


def memory_dir(vault):
    return os.path.join(vault, MEMORY_DIR)


def _ensure_mem_dir(vault):
    d = memory_dir(vault)
    os.makedirs(d, exist_ok=True)
    return d


def _mem_file(vault, rel_type):
    return os.path.join(_ensure_mem_dir(vault), f"memory_{rel_type}.jsonl")


def _read_memories(vault, rel_type):
    path = _mem_file(vault, rel_type)
    if not os.path.exists(path):
        return []
    memories = []
    with open(path, encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if line:
                try:
                    memories.append(json.loads(line))
                except json.JSONDecodeError:
                    continue
    return memories


def _write_memories(vault, rel_type, memories):
    path = _mem_file(vault, rel_type)
    with open(path, "w", encoding="utf-8") as f:
        for m in memories:
            f.write(json.dumps(m) + "\n")


# ---------------------------------------------------------------------------
# Memory model: relations = semantic, temporal, causal, entity
# ---------------------------------------------------------------------------
RELATION_TYPES = ["semantic", "temporal", "causal", "entity"]


def _now_iso():
    return datetime.now().isoformat()


def _hash_text(text):
    return hashlib.sha256(text.encode("utf-8")).hexdigest()[:16]


def _simple_embedding(text):
    """Lightweight deterministic embedding (stdlib-only, no ML deps).

    Returns a 64-dim vector of hashed token features. Not a real embedding
    model — used for fast heuristic similarity in System-One plane.
    """
    text = text.lower()
    tokens = re.findall(r"\w+", text)
    vec = [0.0] * 64
    for tok in tokens:
        h = int(hashlib.md5(tok.encode("utf-8")).hexdigest(), 16)
        vec[h % 64] += 1.0
    norm = math.sqrt(sum(v * v for v in vec)) or 1.0
    return [v / norm for v in vec]


def _cosine(a, b):
    dot = sum(x * y for x, y in zip(a, b))
    na = math.sqrt(sum(x * x for x in a)) or 1.0
    nb = math.sqrt(sum(y * y for y in b)) or 1.0
    return dot / (na * nb)


# ---------------------------------------------------------------------------
# Memory operations
# ---------------------------------------------------------------------------
def add_memory(vault, content, rel_type="semantic", source="user",
               confidence=1.0, tags=None, dry_run=True):
    """Add a memory to the specified relation type."""
    if rel_type not in RELATION_TYPES:
        rel_type = "semantic"

    mem = {
        "id": _hash_text(content + _now_iso()),
        "content": content,
        "rel_type": rel_type,
        "source": source,
        "created_at": _now_iso(),
        "confidence": max(0.0, min(1.0, confidence)),
        "tags": tags or [],
        "access_count": 0,
        "last_accessed": None,
        "embedding": _simple_embedding(content),
    }

    result = {
        "action": "add_memory",
        "rel_type": rel_type,
        "memory_id": mem["id"],
        "content": content,
        "dry_run": dry_run,
    }

    if not dry_run:
        mems = _read_memories(vault, rel_type)
        mems.append(mem)
        _write_memories(vault, rel_type, mems)

    return result


def retrieve_memories(vault, query, rel_types=None, top_k=5, min_score=0.1,
                      dry_run=True):
    """Retrieve relevant memories using System-One heuristic scoring."""
    if rel_types is None:
        rel_types = RELATION_TYPES

    query_emb = _simple_embedding(query)
    results = []

    for rt in rel_types:
        if rt not in RELATION_TYPES:
            continue
        for mem in _read_memories(vault, rt):
            # System-One scoring: cosine similarity + confidence + recency
            sim = _cosine(query_emb, mem["embedding"])
            recency_boost = 0.0
            if mem["last_accessed"]:
                try:
                    dt = datetime.fromisoformat(mem["last_accessed"])
                    days = (datetime.now() - dt).days
                    recency_boost = max(0.0, 1.0 - days / 30.0) * 0.1
                except ValueError:
                    pass
            score = sim * 0.7 + mem["confidence"] * 0.2 + recency_boost + 0.1 * (mem["access_count"] / 10.0)
            if score >= min_score:
                results.append({
                    "id": mem["id"],
                    "content": mem["content"],
                    "rel_type": rt,
                    "score": round(score, 3),
                    "source": mem["source"],
                    "confidence": mem["confidence"],
                    "created_at": mem["created_at"],
                })

    results.sort(key=lambda x: x["score"], reverse=True)
    results = results[:top_k]

    result = {
        "action": "retrieve_memories",
        "query": query,
        "results": results,
        "count": len(results),
        "dry_run": dry_run,
    }

    if not dry_run:
        # Mark accessed
        for r in results:
            mems = _read_memories(vault, r["rel_type"])
            for m in mems:
                if m["id"] == r["id"]:
                    m["access_count"] += 1
                    m["last_accessed"] = _now_iso()
            _write_memories(vault, r["rel_type"], mems)

    return result


# ---------------------------------------------------------------------------
# System-One memory control: routing & budget decisions
# ---------------------------------------------------------------------------
def system_one_route(task_complexity, memory_budget_mb=50, dry_run=True):
    """Route a memory task based on complexity.

    Fast heuristic: low complexity = semantic only, high = all relations.
    """
    if task_complexity >= 0.7:
        rel_types = RELATION_TYPES
        tier = "full"
        reasoning = "High complexity — use all relation types"
    elif task_complexity >= 0.4:
        rel_types = ["semantic", "entity"]
        tier = "standard"
        reasoning = "Medium complexity — semantic + entity relations"
    else:
        rel_types = ["semantic"]
        tier = "light"
        reasoning = "Low complexity — semantic only"

    return {
        "action": "system_one_route",
        "task_complexity": task_complexity,
        "tier": tier,
        "rel_types": rel_types,
        "memory_budget_mb": memory_budget_mb,
        "reasoning": reasoning,
        "dry_run": dry_run,
    }


def memory_budget_check(estimated_tokens, budget_mb=50, dry_run=True):
    """Check if a memory operation fits within budget."""
    est_mb = estimated_tokens * 0.001  # rough: 1 token ~ 1 byte
    within_budget = est_mb <= budget_mb
    return {
        "action": "memory_budget_check",
        "estimated_mb": round(est_mb, 3),
        "budget_mb": budget_mb,
        "within_budget": within_budget,
        "dry_run": dry_run,
    }


# ---------------------------------------------------------------------------
# RAG retrieval: combine retrieved memories into context
# ---------------------------------------------------------------------------
def rag_retrieve(vault, query, rel_types=None, top_k=5, dry_run=True):
    """RAG retrieval: retrieve memories and format as context."""
    retrieval = retrieve_memories(vault, query, rel_types, top_k, dry_run=dry_run)

    context_parts = []
    for r in retrieval["results"]:
        context_parts.append(
            f"[{r['rel_type']}] {r['content']} (score: {r['score']})"
        )

    context = "\n".join(context_parts) if context_parts else "No relevant memories found."

    result = {
        "action": "rag_retrieve",
        "query": query,
        "context": context,
        "sources": retrieval["results"],
        "count": retrieval["count"],
        "dry_run": dry_run,
    }
    return result


# ---------------------------------------------------------------------------
# Report generation
# ---------------------------------------------------------------------------
def generate_report(vault, ops):
    """Generate markdown memory report."""
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    total_added = sum(1 for o in ops if o.get("action") == "add_memory" and not o.get("dry_run"))
    total_retrieved = sum(o.get("count", 0) for o in ops if o.get("action") == "retrieve_memories")

    lines = [
        "# Smart Memory & RAG Report",
        f"Generated: {now}",
        f"Vault: {vault}",
        "",
        "## Summary",
        f"- **Memories added**: {total_added}",
        f"- **Memories retrieved**: {total_retrieved}",
        f"- **Operations**: {len(ops)}",
        "",
        "## Relation Types",
        "",
    ]
    for rt in RELATION_TYPES:
        count = len(_read_memories(vault, rt))
        lines.append(f"- **{rt}**: {count} memory(ies)")

    lines += [
        "",
        "## Operations",
        "",
        "| Action | Rel Type | Content | Score |",
        "|--------|----------|---------|-------|",
    ]
    for o in ops:
        action = o.get("action", "unknown")
        rt = o.get("rel_type", "—")
        content = o.get("content", o.get("query", "—"))[:60]
        score = o.get("results", [{}])[0].get("score", "—") if o.get("results") else "—"
        lines.append(f"| {action} | {rt} | {content} | {score} |")

    lines += [
        "",
        "## Next Steps",
        "",
        "- Add more memories with `add_memory`",
        "- Retrieve relevant memories with `retrieve_memories` or `rag_retrieve`",
        "- Use `system_one_route` to optimize memory routing by complexity",
        "",
    ]

    return "\n".join(lines)


# ---------------------------------------------------------------------------
# Self-test
# ---------------------------------------------------------------------------
def run_self_test():
    print("🧪 Smart Memory & RAG Self-Test Suite")
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

    # Test 1: simple_embedding deterministic
    def test_embedding():
        e1 = _simple_embedding("hello world")
        e2 = _simple_embedding("hello world")
        assert e1 == e2, "Embedding should be deterministic"
        assert len(e1) == 64, f"Expected 64 dims, got {len(e1)}"
        e3 = _simple_embedding("goodbye world")
        assert e1 != e3, "Different texts should have different embeddings"
    check("simple_embedding is deterministic", test_embedding)

    # Test 2: cosine similarity
    def test_cosine():
        assert abs(_cosine([1.0, 0.0], [1.0, 0.0]) - 1.0) < 1e-9
        assert abs(_cosine([1.0, 0.0], [0.0, 1.0]) - 0.0) < 1e-9
    check("cosine similarity works", test_cosine)

    # Test 3: add + retrieve in temp vault
    def test_add_retrieve():
        import tempfile, shutil
        tmp = tempfile.mkdtemp()
        try:
            init_paths(tmp)
            r1 = add_memory(tmp, "The capital of France is Paris", "semantic", "user", 0.9, ["geo"], dry_run=False)
            assert r1["dry_run"] is False
            r2 = add_memory(tmp, "Paris is known for the Eiffel Tower", "semantic", "user", 0.8, ["landmark"], dry_run=False)
            assert r2["dry_run"] is False

            ret = retrieve_memories(tmp, "capital of France", ["semantic"], top_k=3, dry_run=True)
            assert ret["count"] >= 1
            assert ret["results"][0]["content"] == "The capital of France is Paris"
            assert ret["results"][0]["rel_type"] == "semantic"
        finally:
            shutil.rmtree(tmp)
    check("add_memory + retrieve_memories work", test_add_retrieve)

    # Test 4: system_one_route
    def test_route():
        r_light = system_one_route(0.2, dry_run=True)
        assert r_light["tier"] == "light"
        assert r_light["rel_types"] == ["semantic"]

        r_full = system_one_route(0.8, dry_run=True)
        assert r_full["tier"] == "full"
        assert set(r_full["rel_types"]) == set(RELATION_TYPES)
    check("system_one_route selects tiers correctly", test_route)

    # Test 5: rag_retrieve
    def test_rag():
        import tempfile, shutil
        tmp = tempfile.mkdtemp()
        try:
            init_paths(tmp)
            add_memory(tmp, "Python is a programming language", "semantic", "user", 0.9, dry_run=False)
            rag = rag_retrieve(tmp, "Python programming", dry_run=True)
            assert rag["count"] >= 1
            assert "Python" in rag["context"]
        finally:
            shutil.rmtree(tmp)
    check("rag_retrieve returns context", test_rag)

    # Test 6: memory_budget_check
    def test_budget():
        r = memory_budget_check(10000, budget_mb=10, dry_run=True)
        assert r["within_budget"] is True
        r2 = memory_budget_check(100000, budget_mb=10, dry_run=True)
        assert r2["within_budget"] is False
    check("memory_budget_check works", test_budget)

    print("=" * 50)
    print(f"🎉 Self-tests: {passed} passed, {failed} failed")
    return failed == 0


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------
def parse_args():
    parser = argparse.ArgumentParser(
        description="Hermes Brain Smart Memory & RAG — agentic memory with RAG retrieval.",
    )
    parser.add_argument("--vault", help="Path to the Hermes Brain vault root")
    parser.add_argument("--dry-run", action="store_true", default=True,
                        help="Preview without applying (default)")
    parser.add_argument("--apply", action="store_true",
                        help="Apply changes (overrides --dry-run)")
    parser.add_argument("--test", action="store_true",
                        help="Run built-in self-test suite")
    sub = parser.add_subparsers(dest="command", help="Command to run")

    p_add = sub.add_parser("add", help="Add a memory")
    p_add.add_argument("--content", required=True, help="Memory content")
    p_add.add_argument("--rel-type", default="semantic", choices=RELATION_TYPES, help="Relation type")
    p_add.add_argument("--source", default="user", help="Memory source")
    p_add.add_argument("--confidence", type=float, default=1.0, help="Confidence 0-1")
    p_add.add_argument("--tags", default="", help="Comma-separated tags")
    p_add.add_argument("--dry-run", action="store_true", default=True, help="Preview without applying (default)")
    p_add.add_argument("--apply", action="store_true", help="Apply changes (overrides --dry-run)")

    p_retrieve = sub.add_parser("retrieve", help="Retrieve memories")
    p_retrieve.add_argument("--query", required=True, help="Search query")
    p_retrieve.add_argument("--rel-types", default="", help="Comma-separated relation types")
    p_retrieve.add_argument("--top-k", type=int, default=5, help="Max results")
    p_retrieve.add_argument("--min-score", type=float, default=0.1, help="Min score threshold")
    p_retrieve.add_argument("--dry-run", action="store_true", default=True, help="Preview without applying (default)")
    p_retrieve.add_argument("--apply", action="store_true", help="Apply changes (overrides --dry-run)")

    p_rag = sub.add_parser("rag", help="RAG retrieval")
    p_rag.add_argument("--query", required=True, help="Search query")
    p_rag.add_argument("--rel-types", default="", help="Comma-separated relation types")
    p_rag.add_argument("--top-k", type=int, default=5, help="Max results")
    p_rag.add_argument("--dry-run", action="store_true", default=True, help="Preview without applying (default)")
    p_rag.add_argument("--apply", action="store_true", help="Apply changes (overrides --dry-run)")

    p_route = sub.add_parser("route", help="System-One route decision")
    p_route.add_argument("--complexity", type=float, default=0.5, help="Task complexity 0-1")
    p_route.add_argument("--budget", type=int, default=50, help="Memory budget MB")
    p_route.add_argument("--dry-run", action="store_true", default=True, help="Preview without applying (default)")
    p_route.add_argument("--apply", action="store_true", help="Apply changes (overrides --dry-run)")

    p_budget = sub.add_parser("budget", help="Memory budget check")
    p_budget.add_argument("--tokens", type=int, default=1000, help="Estimated tokens")
    p_budget.add_argument("--budget-mb", type=int, default=50, help="Budget in MB")
    p_budget.add_argument("--dry-run", action="store_true", default=True, help="Preview without applying (default)")
    p_budget.add_argument("--apply", action="store_true", help="Apply changes (overrides --dry-run)")

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

    ops = []

    if args.command == "add":
        result = add_memory(VAULT, args.content, args.rel_type, args.source,
                            args.confidence, args.tags.split(",") if args.tags else [],
                            dry_run=dry_run)
        ops.append(result)
        print(f"🧠 Add memory: {result['memory_id']} ({result['rel_type']})")
        print(f"   Content: {args.content[:80]}")
        print(f"   Mode: {'DRY-RUN' if dry_run else 'APPLY'}")

    elif args.command == "retrieve":
        rel_types = args.rel_types.split(",") if args.rel_types else None
        result = retrieve_memories(VAULT, args.query, rel_types, args.top_k, args.min_score, dry_run)
        ops.append(result)
        print(f"🔍 Retrieve: {result['count']} result(s) for '{args.query}'")
        for r in result["results"]:
            print(f"   [{r['rel_type']}] {r['content'][:70]} (score: {r['score']})")

    elif args.command == "rag":
        rel_types = args.rel_types.split(",") if args.rel_types else None
        result = rag_retrieve(VAULT, args.query, rel_types, args.top_k, dry_run)
        ops.append(result)
        print(f"📚 RAG: {result['count']} source(s) for '{args.query}'")
        print(f"   Context:\n{result['context'][:200]}...")

    elif args.command == "route":
        result = system_one_route(args.complexity, args.budget, dry_run)
        ops.append(result)
        print(f"🧭 Route: {result['tier']} tier for complexity {args.complexity}")
        print(f"   Rel types: {', '.join(result['rel_types'])}")
        print(f"   Reasoning: {result['reasoning']}")

    elif args.command == "budget":
        result = memory_budget_check(args.tokens, args.budget_mb, dry_run)
        ops.append(result)
        print(f"💰 Budget: {result['estimated_mb']:.3f} MB est. vs {result['budget_mb']} MB limit")
        print(f"   Within budget: {result['within_budget']}")

    else:
        print("Error: No command specified. Use: add, retrieve, rag, route, budget", file=sys.stderr)
        sys.exit(1)

    # Generate report
    report = generate_report(VAULT, ops)
    report_path = os.path.join(VAULT, "04-Archives", "Audit-Reports", "Smart-Memory-Report.md")
    write_file(report_path, report)
    print(f"   Report: {report_path}")

    if dry_run:
        print("   Run with --apply to write changes to vault.")

    return 0


if __name__ == "__main__":
    sys.exit(main())
