#!/usr/bin/env python3
"""
Hermes Brain — Knowledge Management Skill (multi-harness compatible).

Open Knowledge Management System concepts brought to the Hermes Brain vault:
- Decision systems: case → conclusion with explicit basis, computation, boundary
- Rules: explicit, versioned, changeable by business experts
- Knowledge base: articles, glossary, wiki, KB entries
- Ontology: objects, links, functions, actions
- Datasets: registers, columns, keys, AI context, relationships, quality
- Knowledge map: visualize and navigate knowledge structure

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
# Knowledge base directory structure
# ---------------------------------------------------------------------------
KB_DIR = "_System/KnowledgeBase"


def kb_dir(vault):
    return os.path.join(vault, KB_DIR)


def _ensure_kb_dir(vault):
    d = kb_dir(vault)
    os.makedirs(d, exist_ok=True)
    return d


def _kb_file(vault, name):
    return os.path.join(_ensure_kb_dir(vault), f"{name}.json")


def _read_kb(vault, name):
    path = _kb_file(vault, name)
    if not os.path.exists(path):
        return {}
    try:
        with open(path, encoding="utf-8") as f:
            return json.load(f)
    except json.JSONDecodeError:
        return {}


def _write_kb(vault, name, data):
    path = _kb_file(vault, name)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2)


# ---------------------------------------------------------------------------
# Knowledge helpers
# ---------------------------------------------------------------------------
def _now_iso():
    return datetime.now().isoformat()


def _hash_text(text):
    return hashlib.sha256(text.encode("utf-8")).hexdigest()[:16]


# ---------------------------------------------------------------------------
# Knowledge Base operations
# ---------------------------------------------------------------------------

def kb_add_article(vault, title, content, author="user", tags=None, dry_run=True):
    """Add a knowledge article."""
    kb = _read_kb(vault, "articles")
    article_id = _hash_text(title + _now_iso())
    article = {
        "id": article_id,
        "title": title,
        "content": content,
        "author": author,
        "tags": tags or [],
        "created_at": _now_iso(),
        "updated_at": _now_iso(),
        "version": 1,
    }

    result = {
        "action": "kb_add_article",
        "article_id": article_id,
        "title": title,
        "dry_run": dry_run,
    }

    if not dry_run:
        kb[article_id] = article
        _write_kb(vault, "articles", kb)

    return result


def kb_list_articles(vault, dry_run=True):
    """List all knowledge articles."""
    kb = _read_kb(vault, "articles")
    articles = []
    for aid, a in kb.items():
        articles.append({
            "id": aid,
            "title": a["title"],
            "author": a["author"],
            "created_at": a["created_at"],
            "version": a["version"],
            "tags": a["tags"],
        })
    articles.sort(key=lambda x: x["created_at"], reverse=True)

    result = {
        "action": "kb_list_articles",
        "count": len(articles),
        "articles": articles,
        "dry_run": dry_run,
    }
    return result


def kb_get_article(vault, article_id, dry_run=True):
    """Get a specific article by ID."""
    kb = _read_kb(vault, "articles")
    if article_id not in kb:
        return {"action": "kb_get_article", "error": f"Article {article_id} not found", "dry_run": dry_run}
    return {"action": "kb_get_article", "article": kb[article_id], "dry_run": dry_run}


# ---------------------------------------------------------------------------
# Decision System operations (openKMS core concept)
# ---------------------------------------------------------------------------

def ds_add_decision(vault, case, conclusion, basis, computation, boundary,
                    rule_id=None, author="user", dry_run=True):
    """Add a decision system record: case → conclusion with explicit basis,
    computation, and boundary (openKMS core concept)."""
    kb = _read_kb(vault, "decisions")
    decision_id = _hash_text(case + conclusion + _now_iso())
    decision = {
        "id": decision_id,
        "case": case,
        "conclusion": conclusion,
        "basis": basis,
        "computation": computation,
        "boundary": boundary,
        "rule_id": rule_id,
        "author": author,
        "created_at": _now_iso(),
        "version": 1,
    }

    result = {
        "action": "ds_add_decision",
        "decision_id": decision_id,
        "case": case,
        "conclusion": conclusion,
        "dry_run": dry_run,
    }

    if not dry_run:
        kb[decision_id] = decision
        _write_kb(vault, "decisions", kb)

    return result


def ds_list_decisions(vault, dry_run=True):
    """List all decision system records."""
    kb = _read_kb(vault, "decisions")
    decisions = []
    for did, d in kb.items():
        decisions.append({
            "id": did,
            "case": d["case"],
            "conclusion": d["conclusion"],
            "author": d["author"],
            "created_at": d["created_at"],
            "rule_id": d["rule_id"],
        })
    decisions.sort(key=lambda x: x["created_at"], reverse=True)

    result = {
        "action": "ds_list_decisions",
        "count": len(decisions),
        "decisions": decisions,
        "dry_run": dry_run,
    }
    return result


# ---------------------------------------------------------------------------
# Rules operations (explicit, versioned rules)
# ---------------------------------------------------------------------------

def rule_add(vault, name, condition, action, priority=1, author="user", dry_run=True):
    """Add an explicit, versioned rule (openKMS concept)."""
    kb = _read_kb(vault, "rules")
    rule_id = _hash_text(name + _now_iso())
    rule = {
        "id": rule_id,
        "name": name,
        "condition": condition,
        "action": action,
        "priority": priority,
        "author": author,
        "created_at": _now_iso(),
        "updated_at": _now_iso(),
        "version": 1,
        "active": True,
    }

    result = {
        "action": "rule_add",
        "rule_id": rule_id,
        "name": name,
        "dry_run": dry_run,
    }

    if not dry_run:
        kb[rule_id] = rule
        _write_kb(vault, "rules", kb)

    return result


def rule_list(vault, dry_run=True):
    """List all rules."""
    kb = _read_kb(vault, "rules")
    rules = []
    for rid, r in kb.items():
        rules.append({
            "id": rid,
            "name": r["name"],
            "condition": r["condition"],
            "action": r["action"],
            "priority": r["priority"],
            "active": r["active"],
            "version": r["version"],
        })
    rules.sort(key=lambda x: (-x["priority"], x["name"]))

    result = {
        "action": "rule_list",
        "count": len(rules),
        "rules": rules,
        "dry_run": dry_run,
    }
    return result


# ---------------------------------------------------------------------------
# Ontology operations (objects, links, functions, actions)
# ---------------------------------------------------------------------------

def ontology_add_object(vault, object_id, object_type, properties=None, dry_run=True):
    """Add an ontology object (openKMS concept)."""
    kb = _read_kb(vault, "ontology_objects")
    obj = {
        "id": object_id,
        "type": object_type,
        "properties": properties or {},
        "created_at": _now_iso(),
    }

    result = {
        "action": "ontology_add_object",
        "object_id": object_id,
        "object_type": object_type,
        "dry_run": dry_run,
    }

    if not dry_run:
        kb[object_id] = obj
        _write_kb(vault, "ontology_objects", kb)

    return result


def ontology_add_link(vault, source_id, target_id, link_type, properties=None, dry_run=True):
    """Add an ontology link between two objects."""
    kb = _read_kb(vault, "ontology_links")
    link_id = _hash_text(source_id + target_id + link_type + _now_iso())
    link = {
        "id": link_id,
        "source_id": source_id,
        "target_id": target_id,
        "link_type": link_type,
        "properties": properties or {},
        "created_at": _now_iso(),
    }

    result = {
        "action": "ontology_add_link",
        "link_id": link_id,
        "source_id": source_id,
        "target_id": target_id,
        "link_type": link_type,
        "dry_run": dry_run,
    }

    if not dry_run:
        kb[link_id] = link
        _write_kb(vault, "ontology_links", kb)

    return result


def ontology_list_objects(vault, dry_run=True):
    """List all ontology objects."""
    kb = _read_kb(vault, "ontology_objects")
    objects = []
    for oid, o in kb.items():
        objects.append({
            "id": oid,
            "type": o["type"],
            "created_at": o["created_at"],
        })
    result = {
        "action": "ontology_list_objects",
        "count": len(objects),
        "objects": objects,
        "dry_run": dry_run,
    }
    return result


def ontology_list_links(vault, dry_run=True):
    """List all ontology links."""
    kb = _read_kb(vault, "ontology_links")
    links = []
    for lid, l in kb.items():
        links.append({
            "id": lid,
            "source_id": l["source_id"],
            "target_id": l["target_id"],
            "link_type": l["link_type"],
        })
    result = {
        "action": "ontology_list_links",
        "count": len(links),
        "links": links,
        "dry_run": dry_run,
    }
    return result


# ---------------------------------------------------------------------------
# Dataset operations (registers, columns, keys, AI context, relationships, quality)
# ---------------------------------------------------------------------------

def dataset_register(vault, name, columns, keys=None, ai_context=None,
                     relationships=None, quality_notes=None, author="user", dry_run=True):
    """Register a dataset (openKMS concept)."""
    kb = _read_kb(vault, "datasets")
    ds_id = _hash_text(name + _now_iso())
    ds = {
        "id": ds_id,
        "name": name,
        "columns": columns,
        "keys": keys or [],
        "ai_context": ai_context or {},
        "relationships": relationships or [],
        "quality_notes": quality_notes or [],
        "author": author,
        "created_at": _now_iso(),
        "updated_at": _now_iso(),
        "version": 1,
    }

    result = {
        "action": "dataset_register",
        "dataset_id": ds_id,
        "name": name,
        "dry_run": dry_run,
    }

    if not dry_run:
        kb[ds_id] = ds
        _write_kb(vault, "datasets", kb)

    return result


def dataset_list(vault, dry_run=True):
    """List all datasets."""
    kb = _read_kb(vault, "datasets")
    datasets = []
    for did, d in kb.items():
        datasets.append({
            "id": did,
            "name": d["name"],
            "columns": d["columns"],
            "author": d["author"],
            "created_at": d["created_at"],
            "version": d["version"],
        })
    result = {
        "action": "dataset_list",
        "count": len(datasets),
        "datasets": datasets,
        "dry_run": dry_run,
    }
    return result


# ---------------------------------------------------------------------------
# Knowledge Map generation
# ---------------------------------------------------------------------------

def knowledge_map(vault, dry_run=True):
    """Generate a knowledge map: overview of all knowledge artifacts."""
    articles = _read_kb(vault, "articles")
    decisions = _read_kb(vault, "decisions")
    rules = _read_kb(vault, "rules")
    objects = _read_kb(vault, "ontology_objects")
    links = _read_kb(vault, "ontology_links")
    datasets = _read_kb(vault, "datasets")

    result = {
        "action": "knowledge_map",
        "counts": {
            "articles": len(articles),
            "decisions": len(decisions),
            "rules": len(rules),
            "objects": len(objects),
            "links": len(links),
            "datasets": len(datasets),
        },
        "total": sum([
            len(articles), len(decisions), len(rules),
            len(objects), len(links), len(datasets),
        ]),
        "dry_run": dry_run,
    }
    return result


# ---------------------------------------------------------------------------
# Report generation
# ---------------------------------------------------------------------------

def generate_report(vault, ops):
    """Generate markdown knowledge management report."""
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    total_ops = len(ops)

    lines = [
        "# Knowledge Management Report",
        f"Generated: {now}",
        f"Vault: {vault}",
        "",
        "## Summary",
        f"- **Operations**: {total_ops}",
        "",
    ]

    # Knowledge map
    km = knowledge_map(vault, dry_run=True)
    lines += [
        "## Knowledge Map",
        "",
        "| Artifact Type | Count |",
        "|---------------|-------|",
    ]
    for k, v in km["counts"].items():
        lines.append(f"| {k} | {v} |")
    lines.append(f"| **Total** | **{km['total']}** |")
    lines += ["", ""]

    # Operations
    lines += [
        "## Operations",
        "",
        "| Action | Details |",
        "|--------|---------|",
    ]
    for o in ops:
        action = o.get("action", "unknown")
        details = o.get("title", o.get("name", o.get("case", o.get("query", "—"))))
        lines.append(f"| {action} | {details} |")

    lines += [
        "",
        "## Next Steps",
        "",
        "- Add articles with `kb-add-article`",
        "- Record decisions with `ds-add-decision`",
        "- Define explicit rules with `rule-add`",
        "- Build ontology with `ontology-add-object` / `ontology-add-link`",
        "- Register datasets with `dataset-register`",
        "- View knowledge map with `knowledge-map`",
        "",
    ]

    return "\n".join(lines)


# ---------------------------------------------------------------------------
# Self-test
# ---------------------------------------------------------------------------
def run_self_test():
    print("🧪 Knowledge Management Self-Test Suite")
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

    # Test 1: kb add + list
    def test_kb_article():
        import tempfile, shutil
        tmp = tempfile.mkdtemp()
        try:
            init_paths(tmp)
            r = kb_add_article(tmp, "Test Article", "Test content", "tester", ["tag1"], dry_run=False)
            assert r["dry_run"] is False
            assert r["article_id"]
            lst = kb_list_articles(tmp, dry_run=True)
            assert lst["count"] == 1
            assert lst["articles"][0]["title"] == "Test Article"
        finally:
            shutil.rmtree(tmp)
    check("kb add + list articles", test_kb_article)

    # Test 2: ds add + list
    def test_ds_decision():
        import tempfile, shutil
        tmp = tempfile.mkdtemp()
        try:
            init_paths(tmp)
            r = ds_add_decision(tmp, "Case: underwrite policy", "Conclusion: approve",
                                "Basis: risk score < 0.3", "Computation: rule_engine_v2",
                                "Boundary: policies < $1M", "rule_1", "underwriter", dry_run=False)
            assert r["dry_run"] is False
            lst = ds_list_decisions(tmp, dry_run=True)
            assert lst["count"] == 1
            assert lst["decisions"][0]["case"] == "Case: underwrite policy"
        finally:
            shutil.rmtree(tmp)
    check("ds add + list decisions", test_ds_decision)

    # Test 3: rule add + list
    def test_rule():
        import tempfile, shutil
        tmp = tempfile.mkdtemp()
        try:
            init_paths(tmp)
            r = rule_add(tmp, "high_risk_rule", "risk_score > 0.8", "reject", 5, "compliance", dry_run=False)
            assert r["dry_run"] is False
            lst = rule_list(tmp, dry_run=True)
            assert lst["count"] == 1
            assert lst["rules"][0]["name"] == "high_risk_rule"
            assert lst["rules"][0]["priority"] == 5
        finally:
            shutil.rmtree(tmp)
    check("rule add + list rules", test_rule)

    # Test 4: ontology add object + link
    def test_ontology():
        import tempfile, shutil
        tmp = tempfile.mkdtemp()
        try:
            init_paths(tmp)
            r1 = ontology_add_object(tmp, "obj_1", "Person", {"name": "Alice"}, dry_run=False)
            r2 = ontology_add_object(tmp, "obj_2", "Organization", {"name": "Acme"}, dry_run=False)
            r3 = ontology_add_link(tmp, "obj_1", "obj_2", "works_at", dry_run=False)
            assert r1["dry_run"] is False
            assert r2["dry_run"] is False
            assert r3["dry_run"] is False

            objs = ontology_list_objects(tmp, dry_run=True)
            assert objs["count"] == 2
            links = ontology_list_links(tmp, dry_run=True)
            assert links["count"] == 1
            assert links["links"][0]["link_type"] == "works_at"
        finally:
            shutil.rmtree(tmp)
    check("ontology add object + link", test_ontology)

    # Test 5: dataset register + list
    def test_dataset():
        import tempfile, shutil
        tmp = tempfile.mkdtemp()
        try:
            init_paths(tmp)
            r = dataset_register(tmp, "customer_data", ["id", "name", "email"],
                                 ["id"], {"pii": True}, [], ["column_validation"], "data_eng", dry_run=False)
            assert r["dry_run"] is False
            lst = dataset_list(tmp, dry_run=True)
            assert lst["count"] == 1
            assert lst["datasets"][0]["name"] == "customer_data"
        finally:
            shutil.rmtree(tmp)
    check("dataset register + list datasets", test_dataset)

    # Test 6: knowledge map
    def test_knowledge_map():
        import tempfile, shutil
        tmp = tempfile.mkdtemp()
        try:
            init_paths(tmp)
            km = knowledge_map(tmp, dry_run=True)
            assert km["counts"]["articles"] == 0
            assert km["counts"]["decisions"] == 0
            assert km["total"] == 0
        finally:
            shutil.rmtree(tmp)
    check("knowledge_map generates summary", test_knowledge_map)

    print("=" * 50)
    print(f"🎉 Self-tests: {passed} passed, {failed} failed")
    return failed == 0


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------
def parse_args():
    parser = argparse.ArgumentParser(
        description="Hermes Brain Knowledge Management — openKMS-style decision systems, rules, ontology, datasets.",
    )
    parser.add_argument("--vault", help="Path to the Hermes Brain vault root")
    parser.add_argument("--dry-run", action="store_true", default=True,
                        help="Preview without applying (default)")
    parser.add_argument("--apply", action="store_true",
                        help="Apply changes (overrides --dry-run)")
    parser.add_argument("--test", action="store_true",
                        help="Run built-in self-test suite")
    sub = parser.add_subparsers(dest="command", help="Command to run")

    # kb-add-article
    p = sub.add_parser("kb-add-article", help="Add a knowledge article")
    p.add_argument("--title", required=True)
    p.add_argument("--content", required=True)
    p.add_argument("--author", default="user")
    p.add_argument("--tags", default="")
    p.add_argument("--dry-run", action="store_true", default=True)
    p.add_argument("--apply", action="store_true")

    # kb-list-articles
    p = sub.add_parser("kb-list-articles", help="List knowledge articles")
    p.add_argument("--dry-run", action="store_true", default=True)
    p.add_argument("--apply", action="store_true")

    # kb-get-article
    p = sub.add_parser("kb-get-article", help="Get a knowledge article")
    p.add_argument("--id", required=True, help="Article ID")
    p.add_argument("--dry-run", action="store_true", default=True)
    p.add_argument("--apply", action="store_true")

    # ds-add-decision
    p = sub.add_parser("ds-add-decision", help="Add a decision system record")
    p.add_argument("--case", required=True)
    p.add_argument("--conclusion", required=True)
    p.add_argument("--basis", required=True)
    p.add_argument("--computation", required=True)
    p.add_argument("--boundary", required=True)
    p.add_argument("--rule-id", default=None)
    p.add_argument("--author", default="user")
    p.add_argument("--dry-run", action="store_true", default=True)
    p.add_argument("--apply", action="store_true")

    # ds-list-decisions
    p = sub.add_parser("ds-list-decisions", help="List decision system records")
    p.add_argument("--dry-run", action="store_true", default=True)
    p.add_argument("--apply", action="store_true")

    # rule-add
    p = sub.add_parser("rule-add", help="Add an explicit rule")
    p.add_argument("--name", required=True)
    p.add_argument("--condition", required=True)
    p.add_argument("--action", required=True)
    p.add_argument("--priority", type=int, default=1)
    p.add_argument("--author", default="user")
    p.add_argument("--dry-run", action="store_true", default=True)
    p.add_argument("--apply", action="store_true")

    # rule-list
    p = sub.add_parser("rule-list", help="List all rules")
    p.add_argument("--dry-run", action="store_true", default=True)
    p.add_argument("--apply", action="store_true")

    # ontology-add-object
    p = sub.add_parser("ontology-add-object", help="Add an ontology object")
    p.add_argument("--id", required=True)
    p.add_argument("--type", required=True)
    p.add_argument("--properties", default="{}", help="JSON properties")
    p.add_argument("--dry-run", action="store_true", default=True)
    p.add_argument("--apply", action="store_true")

    # ontology-add-link
    p = sub.add_parser("ontology-add-link", help="Add an ontology link")
    p.add_argument("--source-id", required=True)
    p.add_argument("--target-id", required=True)
    p.add_argument("--link-type", required=True)
    p.add_argument("--properties", default="{}", help="JSON properties")
    p.add_argument("--dry-run", action="store_true", default=True)
    p.add_argument("--apply", action="store_true")

    # ontology-list-objects
    p = sub.add_parser("ontology-list-objects", help="List ontology objects")
    p.add_argument("--dry-run", action="store_true", default=True)
    p.add_argument("--apply", action="store_true")

    # ontology-list-links
    p = sub.add_parser("ontology-list-links", help="List ontology links")
    p.add_argument("--dry-run", action="store_true", default=True)
    p.add_argument("--apply", action="store_true")

    # dataset-register
    p = sub.add_parser("dataset-register", help="Register a dataset")
    p.add_argument("--name", required=True)
    p.add_argument("--columns", required=True, help="JSON list of column names")
    p.add_argument("--keys", default="[]", help="JSON list of key column names")
    p.add_argument("--ai-context", default="{}", help="JSON AI context")
    p.add_argument("--relationships", default="[]", help="JSON list of relationships")
    p.add_argument("--quality-notes", default="[]", help="JSON list of quality notes")
    p.add_argument("--author", default="user")
    p.add_argument("--dry-run", action="store_true", default=True)
    p.add_argument("--apply", action="store_true")

    # dataset-list
    p = sub.add_parser("dataset-list", help="List all datasets")
    p.add_argument("--dry-run", action="store_true", default=True)
    p.add_argument("--apply", action="store_true")

    # knowledge-map
    p = sub.add_parser("knowledge-map", help="Generate knowledge map")
    p.add_argument("--dry-run", action="store_true", default=True)
    p.add_argument("--apply", action="store_true")

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

    if args.command == "kb-add-article":
        result = kb_add_article(VAULT, args.title, args.content, args.author,
                                args.tags.split(",") if args.tags else [], dry_run)
        ops.append(result)
        print(f"📄 Add article: {result['article_id']}")
        print(f"   Title: {args.title}")
        print(f"   Mode: {'DRY-RUN' if dry_run else 'APPLY'}")

    elif args.command == "kb-list-articles":
        result = kb_list_articles(VAULT, dry_run)
        ops.append(result)
        print(f"📚 Articles: {result['count']}")
        for a in result["articles"]:
            print(f"   [{a['id']}] {a['title']} (v{a['version']}) by {a['author']}")

    elif args.command == "kb-get-article":
        result = kb_get_article(VAULT, args.id, dry_run)
        ops.append(result)
        if "error" in result:
            print(f"❌ {result['error']}")
        else:
            a = result["article"]
            print(f"📄 Article: {a['title']}")
            print(f"   ID: {a['id']}")
            print(f"   Author: {a['author']} | Version: {a['version']}")
            print(f"   Content: {a['content'][:100]}...")

    elif args.command == "ds-add-decision":
        result = ds_add_decision(VAULT, args.case, args.conclusion, args.basis,
                                 args.computation, args.boundary, args.rule_id,
                                 args.author, dry_run)
        ops.append(result)
        print(f"⚖️  Add decision: {result['decision_id']}")
        print(f"   Case: {args.case}")
        print(f"   Conclusion: {args.conclusion}")
        print(f"   Mode: {'DRY-RUN' if dry_run else 'APPLY'}")

    elif args.command == "ds-list-decisions":
        result = ds_list_decisions(VAULT, dry_run)
        ops.append(result)
        print(f"⚖️  Decisions: {result['count']}")
        for d in result["decisions"]:
            print(f"   [{d['id']}] {d['case']} → {d['conclusion']}")

    elif args.command == "rule-add":
        result = rule_add(VAULT, args.name, args.condition, args.action,
                          args.priority, args.author, dry_run)
        ops.append(result)
        print(f"📜 Add rule: {result['rule_id']}")
        print(f"   Name: {args.name}")
        print(f"   Condition: {args.condition} → Action: {args.action}")
        print(f"   Mode: {'DRY-RUN' if dry_run else 'APPLY'}")

    elif args.command == "rule-list":
        result = rule_list(VAULT, dry_run)
        ops.append(result)
        print(f"📜 Rules: {result['count']}")
        for r in result["rules"]:
            print(f"   [{r['id']}] {r['name']}: {r['condition']} → {r['action']} (priority {r['priority']}, active: {r['active']})")

    elif args.command == "ontology-add-object":
        try:
            props = json.loads(args.properties)
        except json.JSONDecodeError:
            props = {}
        result = ontology_add_object(VAULT, args.id, args.type, props, dry_run)
        ops.append(result)
        print(f"🔗 Add object: {result['object_id']} ({result['object_type']})")
        print(f"   Mode: {'DRY-RUN' if dry_run else 'APPLY'}")

    elif args.command == "ontology-add-link":
        try:
            props = json.loads(args.properties)
        except json.JSONDecodeError:
            props = {}
        result = ontology_add_link(VAULT, args.source_id, args.target_id,
                                   args.link_type, props, dry_run)
        ops.append(result)
        lid = result['link_type']
        print(f"🔗 Add link: {result['source_id']} →[{lid}]→ {result['target_id']}")
        print(f"   Mode: {'DRY-RUN' if dry_run else 'APPLY'}")

    elif args.command == "ontology-list-objects":
        result = ontology_list_objects(VAULT, dry_run)
        ops.append(result)
        print(f"🔗 Objects: {result['count']}")
        for o in result["objects"]:
            print(f"   [{o['id']}] {o['type']}")

    elif args.command == "ontology-list-links":
        result = ontology_list_links(VAULT, dry_run)
        ops.append(result)
        print(f"🔗 Links: {result['count']}")
        for l in result["links"]:
            lid = l['id']
            ltype = l['link_type']
            print(f"   [{lid}] {l['source_id']} →[{ltype}]→ {l['target_id']}")

    elif args.command == "dataset-register":
        try:
            columns = json.loads(args.columns)
            keys = json.loads(args.keys)
            ai_context = json.loads(args.ai_context)
            relationships = json.loads(args.relationships)
            quality_notes = json.loads(args.quality_notes)
        except json.JSONDecodeError as e:
            print(f"Error: Invalid JSON: {e}", file=sys.stderr)
            sys.exit(1)
        result = dataset_register(VAULT, args.name, columns, keys, ai_context,
                                  relationships, quality_notes, args.author, dry_run)
        ops.append(result)
        print(f"🗄️  Register dataset: {result['dataset_id']}")
        print(f"   Name: {args.name}")
        print(f"   Columns: {', '.join(columns)}")
        print(f"   Mode: {'DRY-RUN' if dry_run else 'APPLY'}")

    elif args.command == "dataset-list":
        result = dataset_list(VAULT, dry_run)
        ops.append(result)
        print(f"🗄️  Datasets: {result['count']}")
        for d in result["datasets"]:
            print(f"   [{d['id']}] {d['name']} ({len(d['columns'])} columns)")

    elif args.command == "knowledge-map":
        result = knowledge_map(VAULT, dry_run)
        ops.append(result)
        print(f"🗺️  Knowledge Map:")
        for k, v in result["counts"].items():
            print(f"   {k}: {v}")
        print(f"   Total: {result['total']}")

    else:
        print("Error: No command specified. Use: kb-add-article, kb-list-articles, kb-get-article, ds-add-decision, ds-list-decisions, rule-add, rule-list, ontology-add-object, ontology-add-link, ontology-list-objects, ontology-list-links, dataset-register, dataset-list, knowledge-map", file=sys.stderr)
        sys.exit(1)

    # Generate report
    report = generate_report(VAULT, ops)
    report_path = os.path.join(VAULT, "04-Archives", "Audit-Reports", "Knowledge-Management-Report.md")
    write_file(report_path, report)
    print(f"   Report: {report_path}")

    if dry_run:
        print("   Run with --apply to write changes to vault.")

    return 0


if __name__ == "__main__":
    sys.exit(main())
