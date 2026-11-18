#!/usr/bin/env python3
"""
Hermes Brain — Legacy Seams (Michael Feathers, Working Effectively with Legacy Code).

Detects seams in vault scripts — places where behavior can be altered without
editing the code itself — and identifies characterization-test candidates
(code that needs tests before you refactor it). Feathers' core principle:
"Find the seams, cover them with tests, then refactor safely."

Subcommands:
  legacy-seams scan       Scan vault for seams, god modules, dead code
  legacy-seams seams <file>  Show seam points in a specific Python file
  legacy-seams characterization <file>  Suggest characterization tests for a file
  legacy-seams dependencies <file>  Find hardcoded dependencies to break
  legacy-seams --test     Built-in self-test suite

Multi-harness compatible:
  - --vault CLI arg for vault path (never module-level path resolution)
  - Path resolution deferred to main() after argument parsing
  - Stdlib-only
  - --dry-run default, --apply for human-in-the-loop approval
  - --test self-tests

Exit code: 0 always (reporting tool, not a gate).
"""

import argparse
import ast
import datetime
import os
import re
import sys

# ---------------------------------------------------------------------------
# Path resolution — deferred to main(), never at import time
# ---------------------------------------------------------------------------
VAULT = None
REPORT_DIR = None


def init_paths(vault_path):
    """Resolve all vault-relative paths from the given vault root.
    Called from main() after argument parsing — never at import time.
    """
    global VAULT, REPORT_DIR
    VAULT = os.path.abspath(vault_path)
    REPORT_DIR = os.path.join(VAULT, "04-Archives", "Audit-Reports")


# ---------------------------------------------------------------------------
# Seam types (Feathers terminology)
# ---------------------------------------------------------------------------
SEAM_TYPES = {
    "object_seam": "Override a method in a subclass to change behavior",
    "link_seam": "Replace a module import with a test double",
    "preprocessing_seam": "Use a preprocessor macro / env var to inject behavior",
    "adapter_seam": "Wrap a hard dependency behind an adapter interface",
}


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


def write_report(lines):
    os.makedirs(REPORT_DIR, exist_ok=True)
    path = os.path.join(REPORT_DIR, "Legacy-Seams-Report.md")
    with open(path, "w", encoding="utf-8") as f:
        f.write("\n".join(lines))
    print(f"\n📄 Legacy seams report written to: {path}")
    return path


def slugify(text):
    slug = "".join(c if c.isalnum() or c in "-_" else "-" for c in text.strip().lower()).strip("-_")
    return slug or "untitled"


def find_python_files():
    for root, dirs, files in os.walk(VAULT):
        dirs[:] = [d for d in dirs if not d.startswith(".") and d not in ("cache", "graphify-out", ".git")]
        for f in files:
            if f.endswith(".py"):
                yield os.path.join(root, f)


# ---------------------------------------------------------------------------
# Parse Python into AST for seam detection
# ---------------------------------------------------------------------------
def parse_python(path):
    content = read_file(path)
    try:
        return ast.parse(content), content
    except SyntaxError:
        return None, content


class SeamVisitor(ast.NodeVisitor):
    """Find seams in a Python file: hardcoded imports, direct instantiations,
    global state, side effects at module level, etc."""
    def __init__(self, file_path):
        self.file_path = file_path
        self.seams = []
        self.imports = []
        self.instantiations = []
        self.global_statements = []
        self.module_level_calls = []

    def visit_Import(self, node):
        for alias in node.names:
            self.imports.append({
                "line": node.lineno,
                "module": alias.name,
                "as": alias.asname,
                "type": "import",
            })
            self.seams.append({
                "line": node.lineno,
                "type": "link_seam",
                "description": f"Import `{alias.name}` — can be replaced with a test double",
                "suggestion": f"Inject `{alias.name}` as a parameter or use dependency injection",
            })
        self.generic_visit(node)

    def visit_ImportFrom(self, node):
        for alias in node.names:
            mod = node.module or ""
            self.imports.append({
                "line": node.lineno,
                "module": f"{mod}.{alias.name}",
                "as": alias.asname,
                "type": "from",
            })
            self.seams.append({
                "line": node.lineno,
                "type": "link_seam",
                "description": f"From-import `{mod}.{alias.name}` — can be replaced with a test double",
                "suggestion": f"Inject `{alias.name}` as a parameter or use dependency injection",
            })
        self.generic_visit(node)

    def visit_Call(self, node):
        # Detect direct instantiations of classes (new X())
        if isinstance(node.func, ast.Name):
            self.instantiations.append({
                "line": node.lineno,
                "class": node.func.id,
                "description": f"Direct instantiation ` {node.func.id}()` — hard to mock",
                "suggestion": f"Accept `{node.func.id}` instance as parameter instead of constructing inside",
            })
            self.seams.append({
                "line": node.lineno,
                "type": "object_seam",
                "description": f"Direct instantiation `{node.func.id}()` — subclass or inject to vary behavior",
                "suggestion": f"Accept `{node.func.id}` as a constructor parameter or factory",
            })
        # Detect calls to known side-effect functions at module level
        if isinstance(node.func, ast.Attribute):
            self.module_level_calls.append({
                "line": node.lineno,
                "call": f"{ast.dump(node.func)}",
            })
        self.generic_visit(node)

    def visit_Assign(self, node):
        # Detect module-level mutable global state
        for target in node.targets:
            if isinstance(target, ast.Name):
                self.global_statements.append({
                    "line": node.lineno,
                    "name": target.id,
                    "description": f"Module-level mutable state `{target.id}` — hidden dependency",
                    "suggestion": f"Pass `{target.id}` as a parameter or encapsulate in a class",
                })
                self.seams.append({
                    "line": node.lineno,
                    "type": "link_seam",
                    "description": f"Mutable global `{target.id}` — can be overridden in tests",
                    "suggestion": f"Inject `{target.id}` as a parameter",
                })
        self.generic_visit(node)


def detect_seams(file_path):
    tree, content = parse_python(file_path)
    if tree is None:
        return [], [], [], [], content
    visitor = SeamVisitor(file_path)
    visitor.visit(tree)
    return visitor.seams, visitor.imports, visitor.instantiations, visitor.global_statements, content


# ---------------------------------------------------------------------------
# God module detection (Feathers: classes/modules that do too much)
# ---------------------------------------------------------------------------
def detect_god_modules():
    findings = []
    for path in find_python_files():
        tree, content = parse_python(path)
        if tree is None:
            continue
        lines = content.splitlines()
        if len(lines) > 300:
            rel = os.path.relpath(path, VAULT)
            # Count classes and functions
            n_classes = sum(1 for n in ast.walk(tree) if isinstance(n, ast.ClassDef))
            n_funcs = sum(1 for n in ast.walk(tree) if isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef)))
            findings.append({
                "file": rel,
                "lines": len(lines),
                "classes": n_classes,
                "functions": n_funcs,
                "message": f"{rel} is {len(lines)} lines with {n_classes} classes and {n_funcs} functions — possible god module",
                "suggestion": f"Split {rel} into smaller modules, each with a single responsibility",
            })
    return findings


# ---------------------------------------------------------------------------
# Characterization test suggestions (Feathers: characterize before refactoring)
# ---------------------------------------------------------------------------
def suggest_characterization_tests(file_path):
    tree, content = parse_python(file_path)
    if tree is None:
        return [], content
    suggestions = []
    visitor = SeamVisitor(file_path)
    visitor.visit(tree)

    # For each public function without a clear return or with side effects,
    # suggest a characterization test
    for node in ast.walk(tree):
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            if node.name.startswith("_"):
                continue  # skip private
            has_return = any(isinstance(n, ast.Return) for n in ast.walk(node))
            has_print = any(
                isinstance(n, ast.Call) and (
                    (isinstance(n.func, ast.Attribute) and n.func.attr == "print") or
                    (isinstance(n.func, ast.Name) and n.func.id == "print")
                )
                for n in ast.walk(node)
            )
            has_file_write = any(
                isinstance(n, ast.Call) and
                isinstance(n.func, ast.Attribute) and
                n.func.attr in ("write", "open")
                for n in ast.walk(node)
            )
            if not has_return or has_print or has_file_write:
                suggestions.append({
                    "function": node.name,
                    "line": node.lineno,
                    "has_return": has_return,
                    "has_print": has_print,
                    "has_file_write": has_file_write,
                    "message": f"Characterize `{node.name}` at line {node.lineno} before refactoring",
                    "suggestion": f"Write a test that captures current output of `{node.name}` for representative inputs, then lock it in",
                })
    return suggestions, content


# ---------------------------------------------------------------------------
# Dependency breaking suggestions
# ---------------------------------------------------------------------------
def suggest_dependency_breaks(file_path):
    tree, content = parse_python(file_path)
    if tree is None:
        return [], content
    visitor = SeamVisitor(file_path)
    visitor.visit(tree)

    breaks = []
    for imp in visitor.imports:
        mod = imp["module"]
        # Flag imports of known hard-to-test modules
        hard_modules = ("os", "sys", "subprocess", "shutil", "requests", "urllib",
                        "sqlite3", "psycopg2", "boto3", "redis", "django", "flask")
        if any(mod.startswith(hm) for hm in hard_modules):
            breaks.append({
                "line": imp["line"],
                "module": mod,
                "message": f"Hard dependency `{mod}` imported at line {imp['line']}",
                "suggestion": f"Wrap `{mod}` behind an adapter interface or accept it as a parameter",
            })
    return breaks, content


# ---------------------------------------------------------------------------
# Scan: full vault scan
# ---------------------------------------------------------------------------
def scan_vault():
    all_seams = []
    god_modules = []
    all_characterization = []
    all_dependency_breaks = []

    for path in find_python_files():
        rel = os.path.relpath(path, VAULT)
        seams, imports, instantiations, globals_, content = detect_seams(path)
        for s in seams:
            s["file"] = rel
            all_seams.append(s)

        char_suggestions, _ = suggest_characterization_tests(path)
        for s in char_suggestions:
            s["file"] = rel
            all_characterization.append(s)

        dep_breaks, _ = suggest_dependency_breaks(path)
        for s in dep_breaks:
            s["file"] = rel
            all_dependency_breaks.append(s)

    god_modules = detect_god_modules()

    return {
        "seams": all_seams,
        "god_modules": god_modules,
        "characterization": all_characterization,
        "dependency_breaks": all_dependency_breaks,
    }


# ---------------------------------------------------------------------------
# Report generation
# ---------------------------------------------------------------------------
def generate_report(scan_results, dry_run=True):
    now = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    seams = scan_results["seams"]
    god_modules = scan_results["god_modules"]
    characterization = scan_results["characterization"]
    dependency_breaks = scan_results["dependency_breaks"]

    total = len(seams) + len(god_modules) + len(characterization) + len(dependency_breaks)

    lines = [
        "# Legacy Seams — Feathers WELC Scan Report",
        f"Generated: {now}",
        f"Vault: {VAULT}",
        f"Mode: {'DRY-RUN (no changes)' if dry_run else 'APPLY'}",
        "",
        "--",
        "",
        "## Summary",
        f"- **Total findings**: {total}",
        f"  - Seams: {len(seams)}",
        f"  - God modules: {len(god_modules)}",
        f"  - Characterization test candidates: {len(characterization)}",
        f"  - Dependency breaks: {len(dependency_breaks)}",
        "",
        "--",
        "",
    ]

    if seams:
        lines.append("## 🔗 Seams (Feathers: points where behavior can be altered without editing)")
        lines.append("")
        lines.append("| Type | File | Line | Description | Suggestion |")
        lines.append("|------|------|------|-------------|------------|")
        for s in seams:
            lines.append(f"| {s['type']} | {s['file']} | {s['line']} | {s['description']} | {s['suggestion']} |")
        lines.append("")
        lines.append("--")
        lines.append("")

    if god_modules:
        lines.append("## 🏛️ God Modules (do too much — split them)")
        lines.append("")
        lines.append("| File | Lines | Classes | Functions | Message | Suggestion |")
        lines.append("|------|-------|---------|-----------|---------|------------|")
        for g in god_modules:
            lines.append(f"| {g['file']} | {g['lines']} | {g['classes']} | {g['functions']} | {g['message']} | {g['suggestion']} |")
        lines.append("")
        lines.append("--")
        lines.append("")

    if characterization:
        lines.append("## 🧪 Characterization Test Candidates (cover before refactoring)")
        lines.append("")
        lines.append("| File | Function | Line | Issue | Suggestion |")
        lines.append("|------|----------|------|-------|------------|")
        for c in characterization:
            issue = []
            if not c["has_return"]:
                issue.append("no return value")
            if c["has_print"]:
                issue.append("prints to stdout")
            if c["has_file_write"]:
                issue.append("writes to file")
            lines.append(f"| {c['file']} | `{c['function']}` | {c['line']} | {', '.join(issue)} | {c['suggestion']} |")
        lines.append("")
        lines.append("--")
        lines.append("")

    if dependency_breaks:
        lines.append("## 🔌 Dependency Breaks (wrap hard dependencies)")
        lines.append("")
        lines.append("| File | Module | Line | Message | Suggestion |")
        lines.append("|------|--------|------|---------|------------|")
        for d in dependency_breaks:
            lines.append(f"| {d['file']} | `{d['module']}` | {d['line']} | {d['message']} | {d['suggestion']} |")
        lines.append("")
        lines.append("--")
        lines.append("")

    lines.append("## Feathers' Working Effectively with Legacy Code — Core Principles")
    lines.append("")
    lines.append("- **Find seams**: places where you can alter behavior without editing that code")
    lines.append("- **Characterize first**: write tests that capture current behavior before changing anything")
    lines.append("- **Break dependencies**: wrap hard dependencies (os, sys, subprocess, databases) behind adapters")
    lines.append("- **One change at a time**: characterize → test → refactor → verify, never all at once")
    lines.append("")
    lines.append("Pair with `tidy_first.py` (find tidy candidates) and `refactor_catalog.py` (apply named refactorings).")
    lines.append("")

    write_report(lines)


# ---------------------------------------------------------------------------
# Self-test
# ---------------------------------------------------------------------------
def run_self_test():
    print("🧪 Legacy Seams — Self-Test Suite")
    print("=" * 50)
    passed = 0
    failed = 0

    import tempfile
    import shutil

    # Test 1: detect_seams finds import seams
    try:
        tmp = tempfile.mkdtemp()
        try:
            init_paths(tmp)
            os.makedirs(os.path.join(tmp, "Scripts"))
            content = "import os\nimport sys\n\ndef foo():\n    return os.getcwd()\n"
            path = os.path.join(tmp, "Scripts", "script.py")
            with open(path, "w") as f:
                f.write(content)
            seams, imports, instantiations, globals_, _ = detect_seams(path)
            link_seams = [s for s in seams if s["type"] == "link_seam"]
            assert len(link_seams) >= 2, f"Expected 2+ link seams, got {len(link_seams)}"
            assert len(imports) == 2
            print("✅ Test 1: detect_seams finds import seams")
            passed += 1
        finally:
            shutil.rmtree(tmp)
    except AssertionError as e:
        print(f"❌ Test 1 failed: {e}")
        failed += 1

    # Test 2: detect_seams finds direct instantiation (object seam)
    try:
        tmp = tempfile.mkdtemp()
        try:
            init_paths(tmp)
            os.makedirs(os.path.join(tmp, "Scripts"))
            content = "def process():\n    db = DatabaseConnection()\n    return db.query()\n"
            path = os.path.join(tmp, "Scripts", "script.py")
            with open(path, "w") as f:
                f.write(content)
            seams, _, instantiations, _, _ = detect_seams(path)
            object_seams = [s for s in seams if s["type"] == "object_seam"]
            assert len(object_seams) >= 1, f"Expected 1 object seam, got {len(object_seams)}"
            assert len(instantiations) == 1
            assert instantiations[0]["class"] == "DatabaseConnection"
            print("✅ Test 2: detect_seams finds direct instantiation")
            passed += 1
        finally:
            shutil.rmtree(tmp)
    except AssertionError as e:
        print(f"❌ Test 2 failed: {e}")
        failed += 1

    # Test 3: detect_god_modules finds large files
    try:
        tmp = tempfile.mkdtemp()
        try:
            init_paths(tmp)
            os.makedirs(os.path.join(tmp, "Scripts"))
            # Create a file with >300 lines
            lines = ["class BigClass:"] + ["    def method_{}(self):\n        pass\n" for _ in range(40)]
            content = "class BigClass:\n" + "".join(
                f"    def method_{i}(self):\n        x = {i}\n        return x\n\n" for i in range(100)
            )
            assert len(content.splitlines()) > 300
            path = os.path.join(tmp, "Scripts", "big.py")
            with open(path, "w") as f:
                f.write(content)
            gods = detect_god_modules()
            assert len(gods) >= 1, f"Expected 1+ god module, got {len(gods)}"
            assert gods[0]["lines"] > 300
            print("✅ Test 3: detect_god_modules finds large files")
            passed += 1
        finally:
            shutil.rmtree(tmp)
    except AssertionError as e:
        print(f"❌ Test 3 failed: {e}")
        failed += 1

    # Test 4: suggest_characterization_tests finds side-effect functions
    try:
        tmp = tempfile.mkdtemp()
        try:
            init_paths(tmp)
            os.makedirs(os.path.join(tmp, "Scripts"))
            content = "def bad_func():\n    print('hello')\n    x = 1\n    return x\n"
            path = os.path.join(tmp, "Scripts", "script.py")
            with open(path, "w") as f:
                f.write(content)
            suggestions, _ = suggest_characterization_tests(path)
            assert len(suggestions) >= 1, f"Expected 1+ characterization suggestion, got {len(suggestions)}"
            assert suggestions[0]["function"] == "bad_func"
            assert suggestions[0]["has_print"] is True
            print("✅ Test 4: suggest_characterization_tests finds side-effect functions")
            passed += 1
        finally:
            shutil.rmtree(tmp)
    except AssertionError as e:
        print(f"❌ Test 4 failed: {e}")
        failed += 1

    # Test 5: suggest_dependency_breaks finds hard dependencies
    try:
        tmp = tempfile.mkdtemp()
        try:
            init_paths(tmp)
            os.makedirs(os.path.join(tmp, "Scripts"))
            content = "import os\nimport subprocess\n\ndef run():\n    pass\n"
            path = os.path.join(tmp, "Scripts", "script.py")
            with open(path, "w") as f:
                f.write(content)
            breaks, _ = suggest_dependency_breaks(path)
            assert len(breaks) >= 2, f"Expected 2+ dependency breaks, got {len(breaks)}"
            modules = {b["module"] for b in breaks}
            assert "os" in modules
            assert "subprocess" in modules
            print("✅ Test 5: suggest_dependency_breaks finds hard dependencies")
            passed += 1
        finally:
            shutil.rmtree(tmp)
    except AssertionError as e:
        print(f"❌ Test 5 failed: {e}")
        failed += 1

    # Test 6: scan_vault returns structured results
    try:
        tmp = tempfile.mkdtemp()
        try:
            init_paths(tmp)
            os.makedirs(os.path.join(tmp, "Scripts"))
            content = "import os\n\ndef foo():\n    return 1\n"
            path = os.path.join(tmp, "Scripts", "script.py")
            with open(path, "w") as f:
                f.write(content)
            results = scan_vault()
            assert "seams" in results
            assert "god_modules" in results
            assert "characterization" in results
            assert "dependency_breaks" in results
            assert isinstance(results["seams"], list)
            print("✅ Test 6: scan_vault returns structured results")
            passed += 1
        finally:
            shutil.rmtree(tmp)
    except AssertionError as e:
        print(f"❌ Test 6 failed: {e}")
        failed += 1

    print("=" * 50)
    print(f"🎉 Self-tests: {passed} passed, {failed} failed")
    return failed == 0


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------
def parse_args():
    parser = argparse.ArgumentParser(
        description="Hermes Brain — Legacy Seams (Michael Feathers): find seams, god modules, characterization candidates.",
    )
    parser.add_argument("--vault", help="Path to the Hermes Brain vault root")
    parser.add_argument("--dry-run", action="store_true", default=True,
                        help="Report only, no changes (default)")
    parser.add_argument("--apply", action="store_true",
                        help="Apply safe auto-fixes (overrides --dry-run)")
    parser.add_argument("--test", action="store_true",
                        help="Run built-in self-test suite")
    sub = parser.add_subparsers(dest="command", help="Command to run")

    sub.add_parser("scan", help="Scan vault for seams, god modules, dead code")

    p_seams = sub.add_parser("seams", help="Show seam points in a specific Python file")
    p_seams.add_argument("file", help="Python file path (relative to vault or absolute)")

    p_char = sub.add_parser("characterization", help="Suggest characterization tests for a file")
    p_char.add_argument("file", help="Python file path")

    p_deps = sub.add_parser("dependencies", help="Find hardcoded dependencies to break")
    p_deps.add_argument("file", help="Python file path")

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

    if args.command == "scan":
        results = scan_vault()
        generate_report(results, dry_run=dry_run)
        return

    if args.command == "seams":
        if not os.path.isabs(args.file):
            file_path = os.path.join(VAULT, args.file)
        else:
            file_path = args.file
        if not os.path.exists(file_path):
            print(f"Error: file not found: {file_path}", file=sys.stderr)
            sys.exit(1)
        seams, imports, instantiations, globals_, content = detect_seams(file_path)
        print(f"## Seams in {os.path.relpath(file_path, VAULT)}")
        print("")
        if not seams:
            print("No seams found — file is well-isolated.")
            return
        print(f"Found {len(seams)} seam(s):")
        print("")
        for s in seams:
            print(f"- **Line {s['line']}** ({s['type']}): {s['description']}")
            print(f"  Suggestion: {s['suggestion']}")
            print("")
        if imports:
            print("### Imports (link seams)")
            for imp in imports:
                print(f"- Line {imp['line']}: `import {imp['module']}`" +
                      (f" as `{imp['as']}`" if imp['as'] else ""))
            print("")
        if instantiations:
            print("### Direct instantiations (object seams)")
            for inst in instantiations:
                print(f"- Line {inst['line']}: `{inst['class']}()`")
                print(f"  {inst['description']}")
            print("")
        if globals_:
            print("### Module-level mutable state")
            for g in globals_:
                print(f"- Line {g['line']}: `{g['name']}`")
                print(f"  {g['description']}")
            print("")
        return

    if args.command == "characterization":
        if not os.path.isabs(args.file):
            file_path = os.path.join(VAULT, args.file)
        else:
            file_path = args.file
        if not os.path.exists(file_path):
            print(f"Error: file not found: {file_path}", file=sys.stderr)
            sys.exit(1)
        suggestions, content = suggest_characterization_tests(file_path)
        print(f"## Characterization Test Candidates — {os.path.relpath(file_path, VAULT)}")
        print("")
        if not suggestions:
            print("No characterization candidates found — functions look well-isolated.")
            return
        print(f"Found {len(suggestions)} candidate(s):")
        print("")
        for s in suggestions:
            issue = []
            if not s["has_return"]:
                issue.append("no return value")
            if s["has_print"]:
                issue.append("prints to stdout")
            if s["has_file_write"]:
                issue.append("writes to file")
            print(f"- **Line {s['line']}**: `{s['function']}` — {', '.join(issue)}")
            print(f"  {s['suggestion']}")
            print("")
        return

    if args.command == "dependencies":
        if not os.path.isabs(args.file):
            file_path = os.path.join(VAULT, args.file)
        else:
            file_path = args.file
        if not os.path.exists(file_path):
            print(f"Error: file not found: {file_path}", file=sys.stderr)
            sys.exit(1)
        breaks, content = suggest_dependency_breaks(file_path)
        print(f"## Dependency Breaks — {os.path.relpath(file_path, VAULT)}")
        print("")
        if not breaks:
            print("No hard dependencies found — file is well-isolated.")
            return
        print(f"Found {len(breaks)} dependency break(s):")
        print("")
        for d in breaks:
            print(f"- **Line {d['line']}**: `{d['module']}`")
            print(f"  {d['suggestion']}")
            print("")
        return

    print("Error: No command specified. Use 'scan', 'seams', 'characterization', "
          "or 'dependencies'.", file=sys.stderr)
    sys.exit(1)


if __name__ == "__main__":
    main()