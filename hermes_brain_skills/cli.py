"""Hermes Brain — top-level CLI entry point.

Dispatches to sub-skill CLIs: borg, skill-pack, paper-mapping.

Usage:
    hermes-brain borg --vault <path> --layout-list
    hermes-brain skill-pack --vault <path> --topic "quantum mechanics"
    hermes-brain paper-mapping --vault <path> --query "Attention Is All You Need"

Multi-harness compliant:
  - --vault CLI arg, deferred path resolution
  - --dry-run default / --apply for human-in-the-loop approval
  - stdlib-only
  - --test built-in self-test suite
"""

import argparse
import sys


def main():
    parser = argparse.ArgumentParser(
        description="Hermes Brain Agent Skills — multi-harness agent skills for Obsidian vaults",
    )
    subparsers = parser.add_subparsers(dest="skill", help="Available skills")

    # borg subcommand
    borg_parser = subparsers.add_parser("borg", help="Borg skill-pack digestion")
    borg_parser.add_argument("--vault", help="Path to the Hermes Brain vault root")
    borg_parser.add_argument("--dry-run", action="store_true", default=True)
    borg_parser.add_argument("--apply", action="store_true", help="Apply changes")
    borg_parser.add_argument("--test", action="store_true", help="Run self-tests")
    borg_parser.add_argument("--layout-create", action="store_true")
    borg_parser.add_argument("--layout-list", action="store_true")
    borg_parser.add_argument("--model-validate", action="store_true")
    borg_parser.add_argument("--trust-scan", action="store_true")
    borg_parser.add_argument("--artifact", help="Path to artifact file")
    borg_parser.add_argument("--art-absorb", nargs="+", metavar="SOURCE")

    # skill-pack subcommand
    sp_parser = subparsers.add_parser("skill-pack", help="Skill pack for education")
    sp_parser.add_argument("--vault", help="Path to the Hermes Brain vault root")
    sp_parser.add_argument("--topic", help="Topic for question generation")
    sp_parser.add_argument("--difficulty", choices=["easy", "medium", "hard"], default="medium")
    sp_parser.add_argument("--self-eval", action="store_true")
    sp_parser.add_argument("--answer", help="Answer to evaluate")
    sp_parser.add_argument("--test", action="store_true", help="Run self-tests")

    # paper-mapping subcommand
    pm_parser = subparsers.add_parser("paper-mapping", help="Paper research via OpenAlex")
    pm_parser.add_argument("--vault", help="Path to the Hermes Brain vault root")
    pm_parser.add_argument("--query", help="Paper title or DOI to search")
    pm_parser.add_argument("--apply", action="store_true", help="Apply changes")
    pm_parser.add_argument("--test", action="store_true", help="Run self-tests")

    args = parser.parse_args()

    if args.skill is None:
        parser.print_help()
        sys.exit(1)

    if args.test:
        import subprocess
        import os

        skill_dir = os.path.join(
            os.path.dirname(__file__),
            args.skill.replace("-", "_"),
        )
        result = subprocess.run(
            [sys.executable, "-m", "pytest", skill_dir, "-v"],
            capture_output=True,
            text=True,
        )
        print(result.stdout)
        if result.stderr:
            print(result.stderr)
        sys.exit(result.returncode)

    if args.skill == "borg":
        from hermes_brain_skills.borg.cli import main as borg_main

        # Reconstruct sys.argv for the sub-CLI
        import sys as _sys
        _sys.argv = ["borg"] + [a for a in _sys.argv[1:] if a not in ("--test",)]
        borg_main()
    elif args.skill == "skill-pack":
        from hermes_brain_skills.skill_pack.cli import main as sp_main

        import sys as _sys
        _sys.argv = ["skill-pack"] + [a for a in _sys.argv[1:] if a not in ("--test",)]
        sp_main()
    elif args.skill == "paper-mapping":
        from hermes_brain_skills.paper_mapping.cli import main as pm_main

        import sys as _sys
        _sys.argv = ["paper-mapping"] + [a for a in _sys.argv[1:] if a not in ("--test",)]
        pm_main()


if __name__ == "__main__":
    main()
