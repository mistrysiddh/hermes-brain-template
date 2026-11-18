#!/usr/bin/env python3
"""
Hermes Brain — Refactor Catalog (Martin Fowler's refactoring philosophy).

Named refactorings applied to vault content (Python scripts and markdown notes),
one refactoring at a time. Kent Beck's rule respected: tidy first, then behave —
never both in the same step. Use `tidy_first.py` scan to find candidates,
then apply a specific refactoring here.

Subcommands:
  refactor-catalog list        List all available refactorings
  refactor-catalog extract-method <file> <start_line> <end_line> <new_name>
                                Extract lines into a new function (Python only)
  refactor-catalog rename-function <file> <old_name> <new_name>
                                Rename a function across all .py files in vault
  refactor-catalog inline-method <file> <function_name>
                                Inline a simple method at its call sites (Python)
  refactor-catalog extract-variable <file> <line> <var_name>
                                Extract a literal into a named variable (Python)
  refactor-catalog rename-note <old_path> <new_path>
                                Rename a markdown note + update wikilinks
  refactor-catalog --test      Built-in self-test suite

Multi-harness compatible:
  - --vault CLI arg for vault path (never module-level path resolution)
  - Path resolution deferred to main() after argument parsing
  - Stdlib-only
  - --dry-run default, --apply for human-in-the-loop approval
  - --test self-tests

Exit code: 0 always (reporting tool, not a gate).
"""

import argparse
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
# Refactoring registry
# ---------------------------------------------------------------------------
REFACTORINGS = {
    "extract-method": {
        "label": "Extract Method",
        "thinker": "Martin Fowler — Refactoring (p. 110)",
        "description": "Turn a code fragment into a method whose name explains its purpose.",
        "applies_to": "Python (.py)",
    },
    "rename-function": {
        "label": "Rename Function",
        "thinker": "Martin Fowler — Refactoring (p. 264)",
        "description": "Change a function's name to better express its purpose; update all call sites.",
        "applies_to": "Python (.py)",
    },
    "inline-method": {
        "label": "Inline Method",
        "thinker": "Martin Fowler — Refactoring (p. 223)",
        "description": "Replace a method body with its contents at call sites, then remove the method.",
        "applies_to": "Python (.py)",
    },
    "extract-variable": {
        "label": "Extract Variable",
        "thinker": "Martin Fowler — Refactoring (p. 190)",
        "description": "Replace a magic literal with a named variable that explains its meaning.",
        "applies_to": "Python (.py)",
    },
    "rename-note": {
        "label": "Rename Note",
        "thinker": "Vault hygiene (Fowler spirit: names should reveal intent)",
        "description": "Rename a markdown note and update all wikilinks pointing to it.",
        "applies_to": "Markdown (.md)",
    },
}


def list_refactorings():
    """Return the refactoring registry."""
    return REFACTORINGS


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
    path = os.path.join(REPORT_DIR, "Refactor-Catalog-Report.md")
    with open(path, "w", encoding="utf-8") as f:
        f.write("\n".join(lines))
    print(f"\n📄 Refactor report written to: {path}")
    return path


def find_python_files():
    """Yield all .py files in vault."""
    for root, dirs, files in os.walk(VAULT):
        dirs[:] = [d for d in dirs if not d.startswith(".") and d not in ("cache", "graphify-out", ".git")]
        for f in files:
            if f.endswith(".py"):
                yield os.path.join(root, f)


def find_markdown_files():
    """Yield all .md files in vault."""
    for root, dirs, files in os.walk(VAULT):
        dirs[:] = [d for d in dirs if not d.startswith(".") and d not in ("cache", "graphify-out", ".git")]
        for f in files:
            if f.endswith(".md"):
                yield os.path.join(root, f)


def slugify(text):
    slug = "".join(c if c.isalnum() or c in "-_" else "-" for c in text.strip().lower()).strip("-_")
    return slug or "untitled"


# ---------------------------------------------------------------------------
# 1. Extract Method
# ---------------------------------------------------------------------------
def extract_method(file_path, start_line, end_line, new_name, dry_run=True):
    """Extract lines [start_line, end_line] into a new function named new_name.
    Replace the extracted lines with a call to the new function.
    """
    if not os.path.exists(file_path):
        return {"ok": False, "error": f"File not found: {file_path}"}

    content = read_file(file_path)
    lines = content.splitlines()

    if start_line < 1 or end_line > len(lines) or start_line > end_line:
        return {"ok": False, "error": f"Invalid line range: {start_line}-{end_line} (file has {len(lines)} lines)"}

    block = lines[start_line - 1:end_line]
    block_text = "\n".join(block)

    # Detect indentation of first line of block
    first_line = block[0]
    indent = len(first_line) - len(first_line.lstrip())

    # Build the new function
    func_indent = " " * indent
    func_def = f"{func_indent}def {new_name}():"
    func_body = []
    for line in block:
        stripped = line.strip()
        if stripped:
            # Remove the block's base indent, add function body indent (4 more)
            body_indent = " " * (indent + 4)
            func_body.append(body_indent + stripped)
        else:
            func_body.append("")
    func_text = "\n".join([func_def] + func_body)

    # Replace block lines with call
    call_indent = " " * indent
    call_line = f"{call_indent}{new_name}()"
    new_lines = lines[: start_line - 1] + [call_line] + lines[end_line:]
    new_content = "\n".join(new_lines)

    # Append the new function at end of file (or after last def)
    new_content = new_content.rstrip() + "\n\n" + func_text + "\n"

    result = {
        "ok": True,
        "refactoring": "extract-method",
        "file": file_path,
        "start_line": start_line,
        "end_line": end_line,
        "new_function": new_name,
        "lines_extracted": len(block),
        "before": content,
        "after": new_content,
    }

    if not dry_run:
        write_file(file_path, new_content)

    return result


# ---------------------------------------------------------------------------
# 2. Rename Function
# ---------------------------------------------------------------------------
def rename_function(old_name, new_name, dry_run=True):
    """Rename a function across all .py files in vault."""
    changed_files = []
    total_renames = 0

    # Pattern: def old_name( or async def old_name(
    def_pattern = re.compile(r"(^\s*)(async\s+)?def\s+" + re.escape(old_name) + r"\s*\(", re.M)
    # Call pattern: old_name( (word boundary)
    call_pattern = re.compile(r"\b" + re.escape(old_name) + r"\s*\(")

    for path in find_python_files():
        content = read_file(path)
        new_content, n_defs = def_pattern.subn(
            lambda m: m.group(1) + (m.group(2) or "") + "def " + new_name + "(",
            content,
        )
        new_content, n_calls = call_pattern.subn(
            lambda m: new_name + "(",
            new_content,
        )
        total = n_defs + n_calls
        if total > 0:
            changed_files.append({
                "file": path,
                "renames": total,
                "defs": n_defs,
                "calls": n_calls,
                "before": content,
                "after": new_content,
            })
            total_renames += total

    result = {
        "ok": True,
        "refactoring": "rename-function",
        "old_name": old_name,
        "new_name": new_name,
        "changed_files": changed_files,
        "total_renames": total_renames,
    }

    if not dry_run:
        for cf in changed_files:
            write_file(cf["file"], cf["after"])

    return result


# ---------------------------------------------------------------------------
# 3. Inline Method
# ---------------------------------------------------------------------------
def inline_method(file_path, function_name, dry_run=True):
    """Inline a simple method: replace its call sites with its body, then remove the method."""
    if not os.path.exists(file_path):
        return {"ok": False, "error": f"File not found: {file_path}"}

    content = read_file(file_path)
    lines = content.splitlines()

    # Find the function definition
    func_start = None
    func_end = None
    func_indent = None
    for i, line in enumerate(lines, 1):
        m = re.match(r"^(\s*)(?:async\s+)?def\s+" + re.escape(function_name) + r"\s*\(.*\):", line)
        if m:
            func_start = i - 1
            func_indent = len(m.group(1))
            break

    if func_start is None:
        return {"ok": False, "error": f"Function '{function_name}' not found in {file_path}"}

    # Find end of function (next def/class at same or lesser indent, or EOF)
    base_indent = " " * func_indent
    for i in range(func_start + 1, len(lines)):
        line = lines[i]
        stripped = line.strip()
        if stripped and not stripped.startswith("#") and not stripped.startswith('"""') and not stripped.startswith("'''"):
            line_indent = len(line) - len(line.lstrip())
            if line_indent <= func_indent:
                func_end = i
                break
    if func_end is None:
        func_end = len(lines)

    func_body_lines = lines[func_start + 1:func_end]
    # Remove one level of indent from body
    body_indent = " " * (func_indent + 4)
    func_body = []
    for line in func_body_lines:
        if line.startswith(body_indent):
            func_body.append(line[len(body_indent):])
        elif line.strip() == "":
            func_body.append("")
        else:
            func_body.append(line)

    # Find call sites: function_name()
    call_pattern = re.compile(r"\b" + re.escape(function_name) + r"\s*\(\s*\)")

    new_lines = []
    i = 0
    while i < len(lines):
        line = lines[i]
        # Skip the function definition itself
        if i == func_start:
            # skip until func_end
            i = func_end
            continue
        new_line, n = call_pattern.subn("\n".join(func_body), line)
        new_lines.append(new_line)
        i += 1

    new_content = "\n".join(new_lines)

    result = {
        "ok": True,
        "refactoring": "inline-method",
        "file": file_path,
        "function": function_name,
        "lines_removed": func_end - func_start,
        "before": content,
        "after": new_content,
    }

    if not dry_run:
        write_file(file_path, new_content)

    return result


# ---------------------------------------------------------------------------
# 4. Extract Variable
# ---------------------------------------------------------------------------
def extract_variable(file_path, line_no, var_name, dry_run=True):
    """Extract a literal on line_no into a named variable."""
    if not os.path.exists(file_path):
        return {"ok": False, "error": f"File not found: {file_path}"}

    content = read_file(file_path)
    lines = content.splitlines()

    if line_no < 1 or line_no > len(lines):
        return {"ok": False, "error": f"Invalid line: {line_no} (file has {len(lines)} lines)"}

    target_line = lines[line_no - 1]
    # Find string/number literals
    literal_pattern = re.compile(r'(["\'])(.*?)\1|(\b\d+(?:\.\d+)?\b)')
    matches = list(literal_pattern.finditer(target_line))

    if not matches:
        return {"ok": False, "error": f"No literal found on line {line_no}"}

    # Use the first literal
    m = matches[0]
    literal = m.group(0)
    # Determine quote style for replacement
    if literal.startswith(('"', "'")):
        quote = literal[0]
        literal_value = literal[1:-1]
    else:
        literal_value = literal

    indent = len(target_line) - len(target_line.lstrip())
    var_def_indent = " " * indent
    var_def = f"{var_def_indent}{var_name} = {literal}"

    # Replace the literal with the variable name in the target line
    new_line = target_line[: m.start()] + var_name + target_line[m.end():]

    new_lines = lines[: line_no - 1] + [var_def, new_line] + lines[line_no:]
    new_content = "\n".join(new_lines)

    result = {
        "ok": True,
        "refactoring": "extract-variable",
        "file": file_path,
        "line": line_no,
        "variable": var_name,
        "literal_extracted": literal,
        "before": content,
        "after": new_content,
    }

    if not dry_run:
        write_file(file_path, new_content)

    return result


# ---------------------------------------------------------------------------
# 5. Rename Note
# ---------------------------------------------------------------------------
def rename_note(old_path, new_path, dry_run=True):
    """Rename a markdown note and update all wikilinks pointing to it."""
    old_full = os.path.join(VAULT, old_path)
    new_full = os.path.join(VAULT, new_path)

    if not os.path.exists(old_full):
        return {"ok": False, "error": f"File not found: {old_path}"}

    # Build the wikilink references that reference this note
    # Extract the note name without extension
    old_name = os.path.splitext(os.path.basename(old_path))[0]
    new_name = os.path.splitext(os.path.basename(new_path))[0]

    # Simple string replacement for wikilinks:
    # [[old_name]] -> [[new_name]]  and  [[old_name| -> [[new_name|
    old_wikilink = "[[" + old_name + "]]"
    new_wikilink = "[[" + new_name + "]]"
    old_wikilink_pipe = "[[" + old_name + "|"
    new_wikilink_pipe = "[[" + new_name + "|"

    updated_files = []
    total_links = 0

    for path in find_markdown_files():
        content = read_file(path)
        new_content = content
        n = 0
        # Count and replace [[old_name]]
        count1 = content.count(old_wikilink)
        new_content = new_content.replace(old_wikilink, new_wikilink)
        n += count1
        # Count and replace [[old_name| (display variant)
        count2 = new_content.count(old_wikilink_pipe)
        new_content = new_content.replace(old_wikilink_pipe, new_wikilink_pipe)
        n += count2
        if n > 0:
            updated_files.append({
                "file": os.path.relpath(path, VAULT),
                "links_updated": n,
                "before": content,
                "after": new_content,
            })
            total_links += n

    result = {
        "ok": True,
        "refactoring": "rename-note",
        "old_path": old_path,
        "new_path": new_path,
        "updated_files": updated_files,
        "total_links_updated": total_links,
    }

    if not dry_run:
        # Rename the file
        os.makedirs(os.path.dirname(new_full), exist_ok=True)
        os.rename(old_full, new_full)
        # Update all referring files
        for uf in updated_files:
            write_file(os.path.join(VAULT, uf["file"]), uf["after"])

    return result


# ---------------------------------------------------------------------------
# Report generation
# ---------------------------------------------------------------------------
def generate_report(results, dry_run=True):
    now = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    lines = [
        "# Refactor Catalog — Report",
        f"Generated: {now}",
        f"Vault: {VAULT}",
        f"Mode: {'DRY-RUN (no changes)' if dry_run else 'APPLY'}",
        "",
        "--",
        "",
    ]

    if not results:
        lines.append("## No refactorings performed.")
        lines.append("")
        write_report(lines)
        return

    for r in results:
        label = REFACTORINGS.get(r["refactoring"], {}).get("label", r["refactoring"])
        thinker = REFACTORINGS.get(r["refactoring"], {}).get("thinker", "")
        lines.append(f"## {label}")
        lines.append("")
        lines.append(f"- **Refactoring**: {r['refactoring']}")
        if thinker:
            lines.append(f"- **Source**: {thinker}")
        lines.append("")

        if r["refactoring"] == "rename-function":
            lines.append(f"- **Old name**: {r['old_name']}")
            lines.append(f"- **New name**: {r['new_name']}")
            lines.append(f"- **Total renames**: {r['total_renames']}")
            lines.append(f"- **Files changed**: {len(r['changed_files'])}")
            lines.append("")
            for cf in r["changed_files"]:
                lines.append(f"  - {os.path.relpath(cf['file'], VAULT)}: {cf['renames']} renames ({cf['defs']} defs, {cf['calls']} calls)")
        elif r["refactoring"] == "extract-method":
            lines.append(f"- **File**: {os.path.relpath(r['file'], VAULT)}")
            lines.append(f"- **Lines extracted**: {r['start_line']}-{r['end_line']} ({r['lines_extracted']} lines)")
            lines.append(f"- **New function**: {r['new_function']}")
        elif r["refactoring"] == "inline-method":
            lines.append(f"- **File**: {os.path.relpath(r['file'], VAULT)}")
            lines.append(f"- **Function inlined**: {r['function']}")
            lines.append(f"- **Lines removed**: {r['lines_removed']}")
        elif r["refactoring"] == "extract-variable":
            lines.append(f"- **File**: {os.path.relpath(r['file'], VAULT)}")
            lines.append(f"- **Line**: {r['line']}")
            lines.append(f"- **Variable**: {r['variable']}")
            lines.append(f"- **Literal extracted**: {r['literal_extracted']}")
        elif r["refactoring"] == "rename-note":
            lines.append(f"- **Old path**: {r['old_path']}")
            lines.append(f"- **New path**: {r['new_path']}")
            lines.append(f"- **Links updated**: {r['total_links_updated']} across {len(r['updated_files'])} files")
            lines.append("")
            for uf in r["updated_files"]:
                lines.append(f"  - {uf['file']}: {uf['links_updated']} links")
        lines.append("")

    lines.append("--")
    lines.append("")
    lines.append("## Next Steps")
    lines.append("")
    lines.append("Review the changes above. Each refactoring is opt-in — run with `--apply` to execute.\nRemember: **one refactoring at a time**, then test, then commit. Never mix refactoring with behavioral change.")

    write_report(lines)


# ---------------------------------------------------------------------------
# Self-test
# ---------------------------------------------------------------------------
def run_self_test():
    print("🧪 Refactor Catalog — Self-Test Suite")
    print("=" * 50)
    passed = 0
    failed = 0

    import tempfile
    import shutil

    # Test 1: list_refactorings returns registry
    try:
        refs = list_refactorings()
        assert "extract-method" in refs
        assert "rename-function" in refs
        assert "rename-note" in refs
        assert len(refs) >= 5
        print("✅ Test 1: list_refactorings returns registry")
        passed += 1
    except AssertionError as e:
        print(f"❌ Test 1 failed: {e}")
        failed += 1

    # Test 2: extract-method dry run
    try:
        tmp = tempfile.mkdtemp()
        try:
            init_paths(tmp)
            os.makedirs(os.path.join(tmp, "Scripts"))
            content = "def process():\n    x = 1 + 2\n    y = x * 3\n    print(y)\n"
            path = os.path.join(tmp, "Scripts", "script.py")
            with open(path, "w") as f:
                f.write(content)
            result = extract_method(path, 2, 3, "compute_x", dry_run=True)
            assert result["ok"] is True
            assert result["new_function"] == "compute_x"
            assert "compute_x()" in result["after"]
            assert "def compute_x():" in result["after"]
            # File should NOT be modified in dry run
            with open(path) as f:
                assert f.read() == content
            print("✅ Test 2: extract-method dry run")
            passed += 1
        finally:
            shutil.rmtree(tmp)
    except AssertionError as e:
        print(f"❌ Test 2 failed: {e}")
        failed += 1

    # Test 3: extract-method apply modifies file
    try:
        tmp = tempfile.mkdtemp()
        try:
            init_paths(tmp)
            os.makedirs(os.path.join(tmp, "Scripts"))
            content = "def process():\n    x = 1 + 2\n    y = x * 3\n    print(y)\n"
            path = os.path.join(tmp, "Scripts", "script.py")
            with open(path, "w") as f:
                f.write(content)
            result = extract_method(path, 2, 3, "compute_x", dry_run=False)
            assert result["ok"] is True
            with open(path) as f:
                new_content = f.read()
            assert "compute_x()" in new_content
            assert "def compute_x():" in new_content
            assert "x = 1 + 2" not in new_content.split("def compute_x")[0] if "def compute_x" in new_content else True
            print("✅ Test 3: extract-method apply modifies file")
            passed += 1
        finally:
            shutil.rmtree(tmp)
    except AssertionError as e:
        print(f"❌ Test 3 failed: {e}")
        failed += 1

    # Test 4: rename-function dry run
    try:
        tmp = tempfile.mkdtemp()
        try:
            init_paths(tmp)
            os.makedirs(os.path.join(tmp, "Scripts"))
            content = "def old_name():\n    pass\nold_name()\n"
            path = os.path.join(tmp, "Scripts", "script.py")
            with open(path, "w") as f:
                f.write(content)
            result = rename_function("old_name", "new_name", dry_run=True)
            assert result["ok"] is True
            assert result["total_renames"] == 2
            # File unchanged
            with open(path) as f:
                assert f.read() == content
            print("✅ Test 4: rename-function dry run")
            passed += 1
        finally:
            shutil.rmtree(tmp)
    except AssertionError as e:
        print(f"❌ Test 4 failed: {e}")
        failed += 1

    # Test 5: rename-function apply
    try:
        tmp = tempfile.mkdtemp()
        try:
            init_paths(tmp)
            os.makedirs(os.path.join(tmp, "Scripts"))
            content = "def old_name():\n    pass\nold_name()\n"
            path = os.path.join(tmp, "Scripts", "script.py")
            with open(path, "w") as f:
                f.write(content)
            result = rename_function("old_name", "new_name", dry_run=False)
            assert result["ok"] is True
            with open(path) as f:
                new_content = f.read()
            assert "def new_name():" in new_content
            assert "new_name()" in new_content
            assert "old_name" not in new_content
            print("✅ Test 5: rename-function apply")
            passed += 1
        finally:
            shutil.rmtree(tmp)
    except AssertionError as e:
        print(f"❌ Test 5 failed: {e}")
        failed += 1

    # Test 6: rename-note dry run
    try:
        tmp = tempfile.mkdtemp()
        try:
            init_paths(tmp)
            os.makedirs(os.path.join(tmp, "Notes"))
            old_note = os.path.join(tmp, "Notes", "OldName.md")
            with open(old_note, "w") as f:
                f.write("# Old Note\n")
            referrer = os.path.join(tmp, "Notes", "Referrer.md")
            with open(referrer, "w") as f:
                f.write("See [[OldName]] for details.\n")
            result = rename_note("Notes/OldName.md", "Notes/NewName.md", dry_run=True)
            assert result["ok"] is True
            assert result["total_links_updated"] == 1
            # File not renamed in dry run
            assert os.path.exists(old_note)
            assert not os.path.exists(os.path.join(tmp, "Notes", "NewName.md"))
            print("✅ Test 6: rename-note dry run")
            passed += 1
        finally:
            shutil.rmtree(tmp)
    except AssertionError as e:
        print(f"❌ Test 6 failed: {e}")
        failed += 1

    # Test 7: rename-note apply
    try:
        tmp = tempfile.mkdtemp()
        try:
            init_paths(tmp)
            os.makedirs(os.path.join(tmp, "Notes"))
            old_note = os.path.join(tmp, "Notes", "OldName.md")
            with open(old_note, "w") as f:
                f.write("# Old Note\n")
            referrer = os.path.join(tmp, "Notes", "Referrer.md")
            with open(referrer, "w") as f:
                f.write("See [[OldName]] for details.\n")
            result = rename_note("Notes/OldName.md", "Notes/NewName.md", dry_run=False)
            assert result["ok"] is True
            assert os.path.exists(os.path.join(tmp, "Notes", "NewName.md"))
            assert not os.path.exists(old_note)
            with open(referrer) as f:
                assert "[[NewName]]" in f.read()
            print("✅ Test 7: rename-note apply")
            passed += 1
        finally:
            shutil.rmtree(tmp)
    except AssertionError as e:
        print(f"❌ Test 7 failed: {e}")
        failed += 1

    # Test 8: inline-method dry run
    try:
        tmp = tempfile.mkdtemp()
        try:
            init_paths(tmp)
            os.makedirs(os.path.join(tmp, "Scripts"))
            content = "def helper():\n    return 42\n\ndef main():\n    x = helper()\n    print(x)\n"
            path = os.path.join(tmp, "Scripts", "script.py")
            with open(path, "w") as f:
                f.write(content)
            result = inline_method(path, "helper", dry_run=True)
            assert result["ok"] is True
            assert "return 42" in result["after"]
            # helper() call replaced, def removed
            assert "def helper():" not in result["after"]
            # File unchanged
            with open(path) as f:
                assert f.read() == content
            print("✅ Test 8: inline-method dry run")
            passed += 1
        finally:
            shutil.rmtree(tmp)
    except AssertionError as e:
        print(f"❌ Test 8 failed: {e}")
        failed += 1

    # Test 9: extract-variable
    try:
        tmp = tempfile.mkdtemp()
        try:
            init_paths(tmp)
            os.makedirs(os.path.join(tmp, "Scripts"))
            content = "def process():\n    x = 100 + 200\n    print(x)\n"
            path = os.path.join(tmp, "Scripts", "script.py")
            with open(path, "w") as f:
                f.write(content)
            result = extract_variable(path, 2, "base_value", dry_run=True)
            assert result["ok"] is True
            assert result["variable"] == "base_value"
            assert "base_value = 100" in result["after"] or "base_value = 100 + 200" in result["after"]
            print("✅ Test 9: extract-variable")
            passed += 1
        finally:
            shutil.rmtree(tmp)
    except AssertionError as e:
        print(f"❌ Test 9 failed: {e}")
        failed += 1

    print("=" * 50)
    print(f"🎉 Self-tests: {passed} passed, {failed} failed")
    return failed == 0


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------
def parse_args():
    parser = argparse.ArgumentParser(
        description="Hermes Brain — Refactor Catalog (Martin Fowler): named refactorings for vault content.",
    )
    parser.add_argument("--vault", help="Path to the Hermes Brain vault root")
    parser.add_argument("--dry-run", action="store_true", default=True,
                        help="Report only, no changes (default)")
    parser.add_argument("--apply", action="store_true",
                        help="Apply refactorings (overrides --dry-run)")
    parser.add_argument("--test", action="store_true",
                        help="Run built-in self-test suite")
    sub = parser.add_subparsers(dest="command", help="Command to run")

    sub.add_parser("list", help="List all available refactorings")

    p_extract = sub.add_parser("extract-method", help="Extract lines into a new function (Python)")
    p_extract.add_argument("file", help="Python file path (relative to vault or absolute)")
    p_extract.add_argument("start_line", type=int, help="Start line (1-indexed)")
    p_extract.add_argument("end_line", type=int, help="End line (1-indexed, inclusive)")
    p_extract.add_argument("new_name", help="Name for the new function")

    p_rename = sub.add_parser("rename-function", help="Rename a function across all .py files")
    p_rename.add_argument("old_name", help="Current function name")
    p_rename.add_argument("new_name", help="New function name")

    p_inline = sub.add_parser("inline-method", help="Inline a simple method at call sites (Python)")
    p_inline.add_argument("file", help="Python file path")
    p_inline.add_argument("function_name", help="Function to inline")

    p_var = sub.add_parser("extract-variable", help="Extract a literal into a named variable (Python)")
    p_var.add_argument("file", help="Python file path")
    p_var.add_argument("line", type=int, help="Line containing the literal (1-indexed)")
    p_var.add_argument("var_name", help="Name for the new variable")

    p_note = sub.add_parser("rename-note", help="Rename a markdown note + update wikilinks")
    p_note.add_argument("old_path", help="Current note path (relative to vault)")
    p_note.add_argument("new_path", help="New note path (relative to vault)")

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

    if args.command == "list":
        print("## Refactor Catalog — Available Refactorings")
        print("")
        for key, info in REFACTORINGS.items():
            print(f"- **{key}** — {info['label']}")
            print(f"  - Thinker: {info['thinker']}")
            print(f"  - Applies to: {info['applies_to']}")
            print(f"  - {info['description']}")
            print("")
        return

    if args.command == "extract-method":
        # Resolve file path
        if not os.path.isabs(args.file):
            file_path = os.path.join(VAULT, args.file)
        else:
            file_path = args.file
        result = extract_method(file_path, args.start_line, args.end_line, args.new_name, dry_run=dry_run)
        if not result["ok"]:
            print(f"Error: {result['error']}", file=sys.stderr)
            sys.exit(1)
        print(f"## Extract Method — {result['new_function']}")
        print(f"")
        print(f"- **File**: {os.path.relpath(result['file'], VAULT)}")
        print(f"- **Lines**: {result['start_line']}-{result['end_line']} ({result['lines_extracted']} lines)")
        print(f"- **New function**: {result['new_function']}")
        print("")
        if not dry_run:
            print(f"✅ Applied: {result['new_function']}() extracted and block replaced with call.")
        else:
            print(f"🔍 Dry run — no changes made. Run with --apply to execute.")
        return

    if args.command == "rename-function":
        result = rename_function(args.old_name, args.new_name, dry_run=dry_run)
        print(f"## Rename Function — {args.old_name} → {args.new_name}")
        print(f"")
        print(f"- **Total renames**: {result['total_renames']}")
        print(f"- **Files changed**: {len(result['changed_files'])}")
        print("")
        for cf in result["changed_files"]:
            print(f"  - {os.path.relpath(cf['file'], VAULT)}: {cf['renames']} renames")
        print("")
        if not dry_run:
            print("✅ Applied: function renamed across vault.")
        else:
            print("🔍 Dry run — no changes made. Run with --apply to execute.")
        return

    if args.command == "inline-method":
        if not os.path.isabs(args.file):
            file_path = os.path.join(VAULT, args.file)
        else:
            file_path = args.file
        result = inline_method(file_path, args.function_name, dry_run=dry_run)
        if not result["ok"]:
            print(f"Error: {result['error']}", file=sys.stderr)
            sys.exit(1)
        print(f"## Inline Method — {result['function']}")
        print(f"")
        print(f"- **File**: {os.path.relpath(result['file'], VAULT)}")
        print(f"- **Lines removed**: {result['lines_removed']}")
        print("")
        if not dry_run:
            print("✅ Applied: method inlined and definition removed.")
        else:
            print("🔍 Dry run — no changes made. Run with --apply to execute.")
        return

    if args.command == "extract-variable":
        if not os.path.isabs(args.file):
            file_path = os.path.join(VAULT, args.file)
        else:
            file_path = args.file
        result = extract_variable(file_path, args.line, args.var_name, dry_run=dry_run)
        if not result["ok"]:
            print(f"Error: {result['error']}", file=sys.stderr)
            sys.exit(1)
        print(f"## Extract Variable — {result['variable']}")
        print(f"")
        print(f"- **File**: {os.path.relpath(result['file'], VAULT)}")
        print(f"- **Line**: {result['line']}")
        print(f"- **Literal extracted**: {result['literal_extracted']}")
        print("")
        if not dry_run:
            print("✅ Applied: literal replaced with named variable.")
        else:
            print("🔍 Dry run — no changes made. Run with --apply to execute.")
        return

    if args.command == "rename-note":
        result = rename_note(args.old_path, args.new_path, dry_run=dry_run)
        if not result["ok"]:
            print(f"Error: {result['error']}", file=sys.stderr)
            sys.exit(1)
        print(f"## Rename Note — {result['old_path']} → {result['new_path']}")
        print(f"")
        print(f"- **Links updated**: {result['total_links_updated']} across {len(result['updated_files'])} files")
        print("")
        for uf in result["updated_files"]:
            print(f"  - {uf['file']}: {uf['links_updated']} links")
        print("")
        if not dry_run:
            print("✅ Applied: note renamed and wikilinks updated.")
        else:
            print("🔍 Dry run — no changes made. Run with --apply to execute.")
        return

    print("Error: No command specified. Use 'list', 'extract-method', 'rename-function', "
          "'inline-method', 'extract-variable', or 'rename-note'.", file=sys.stderr)
    sys.exit(1)


if __name__ == "__main__":
    main()