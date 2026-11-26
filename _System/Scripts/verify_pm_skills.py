#!/usr/bin/env python3
"""
Hermes Brain — verify_pm_skills.py

Pre-commit verification sweep for the pm_best_practices_*.py skill family
(and any other --test-capable script matching a glob). Discovers every
matching script under _System/Scripts/, runs its built-in `--test`
self-test suite, and reports pass/fail per script plus an overall summary.

Exists because an automated full-file rewrite pass (2026-11-26, see
AGENTS.md "Editing Rules") silently broke 55+ scripts without anyone
noticing until a manual repair pass. This gives a single command to
run before committing any change to the skill family, instead of
remembering to `--test` each file individually.

Usage:
    python _System/Scripts/verify_pm_skills.py --vault .
    python _System/Scripts/verify_pm_skills.py --vault . --glob "pm_best_practices_*.py"
    python _System/Scripts/verify_pm_skills.py --vault . --json

Exit code: 0 if all scripts pass --test, 1 if any fail.
"""

from __future__ import annotations

import argparse
import json
import subprocess
import sys
from pathlib import Path


DEFAULT_GLOB = "pm_best_practices_*.py"


def discover_scripts(scripts_dir: Path, glob: str) -> list[Path]:
    """Find all scripts matching the glob pattern, sorted by name."""
    return sorted(scripts_dir.glob(glob))


def run_self_test(script_path: Path, vault: Path, timeout: int = 60) -> dict:
    """Run `--vault <vault> --test` on a script and capture the result."""
    result = {
        "script": script_path.name,
        "path": str(script_path),
        "passed": False,
        "exit_code": None,
        "error": None,
        "output_tail": "",
    }
    try:
        proc = subprocess.run(
            [sys.executable, str(script_path), "--vault", str(vault), "--test"],
            capture_output=True,
            text=True,
            timeout=timeout,
        )
        result["exit_code"] = proc.returncode
        result["passed"] = proc.returncode == 0
        combined = (proc.stdout or "") + (proc.stderr or "")
        result["output_tail"] = "\n".join(combined.strip().splitlines()[-6:])
    except subprocess.TimeoutExpired:
        result["error"] = f"timed out after {timeout}s"
    except Exception as e:  # noqa: BLE001
        result["error"] = str(e)
    return result


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Verify sweep: run --test on every pm_best_practices_*.py skill"
    )
    parser.add_argument("--vault", required=True, help="Path to vault directory")
    parser.add_argument(
        "--glob",
        default=DEFAULT_GLOB,
        help=f"Glob pattern for scripts to verify (default: {DEFAULT_GLOB})",
    )
    parser.add_argument(
        "--scripts-dir",
        default=None,
        help="Override scripts directory (default: <vault>/_System/Scripts)",
    )
    parser.add_argument("--json", action="store_true", help="Output JSON instead of text")
    parser.add_argument(
        "--timeout", type=int, default=60, help="Per-script timeout in seconds (default: 60)"
    )
    args = parser.parse_args()

    vault = Path(args.vault).resolve()
    scripts_dir = Path(args.scripts_dir) if args.scripts_dir else vault / "_System" / "Scripts"

    if not scripts_dir.exists():
        print(f"Error: scripts directory not found: {scripts_dir}")
        return 1

    scripts = discover_scripts(scripts_dir, args.glob)
    if not scripts:
        print(f"No scripts matched glob '{args.glob}' in {scripts_dir}")
        return 1

    results = []
    for script in scripts:
        results.append(run_self_test(script, vault, timeout=args.timeout))

    passed = [r for r in results if r["passed"]]
    failed = [r for r in results if not r["passed"]]

    if args.json:
        print(json.dumps({
            "total": len(results),
            "passed": len(passed),
            "failed": len(failed),
            "results": results,
        }, indent=2))
    else:
        print(f"Verify sweep: {args.glob} ({len(results)} scripts)")
        print("=" * 60)
        for r in results:
            mark = "✅" if r["passed"] else "❌"
            print(f"{mark} {r['script']}")
            if not r["passed"]:
                if r["error"]:
                    print(f"    error: {r['error']}")
                if r["output_tail"]:
                    for line in r["output_tail"].splitlines():
                        print(f"    | {line}")
        print("=" * 60)
        print(f"Results: {len(passed)}/{len(results)} passed, {len(failed)} failed")
        if failed:
            print("❌ VERIFY SWEEP FAILED — fix before committing")
        else:
            print("✅ ALL SKILLS VERIFIED")

    return 0 if not failed else 1


if __name__ == "__main__":
    sys.exit(main())
