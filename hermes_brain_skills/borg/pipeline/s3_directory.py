"""Borg — Phase 2: S3 Directory Agent.

Per mem-draft-spec.txt §4 (Pipeline S3):
S3 Directory — Roles × Skills ontology.

Maintains a bidirectional ontology mapping roles to skills and skills to roles,
with role/skill definitions, domain/category metadata, and lookup operations.

Sub-prompts are loaded from separate template files in prompts/ for modularity.

Multi-harness compliant: --vault, --dry-run default, --apply, stdlib-only, --test.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any
import json


# ── Sub-prompt loading ───────────────────────────────────────────────────
_cli_dir = Path(__file__).resolve().parent
_prompts_dir = _cli_dir / "prompts"


def _load_prompt_file(name: str) -> str:
    path = _prompts_dir / f"{name}.txt"
    if not path.exists():
        raise FileNotFoundError(f"Sub-prompt not found: {name}")
    return path.read_text(encoding="utf-8")


S3_ROLE_DEFINE_PROMPT = _load_prompt_file("s3_role_define_prompt")
S3_SKILL_DEFINE_PROMPT = _load_prompt_file("s3_skill_define_prompt")
S3_ROLE_SKILL_MAP_PROMPT = _load_prompt_file("s3_role_skill_map_prompt")
S3_DIRECTORY_LOOKUP_PROMPT = _load_prompt_file("s3_directory_lookup_prompt")


def load_prompt(name: str) -> str:
    """Load a sub-prompt template by filename (without .txt extension)."""
    return _load_prompt_file(name)


# ── Record types ─────────────────────────────────────────────────────────

LOOKUP_ROLE = "role"
LOOKUP_SKILL = "skill"
LOOKUP_ALL = "all"
LOOKUP_ORPHAN_ROLES = "orphan_roles"
LOOKUP_ORPHAN_SKILLS = "orphan_skills"

VALID_LOOKUP_TYPES = {
    LOOKUP_ROLE, LOOKUP_SKILL, LOOKUP_ALL,
    LOOKUP_ORPHAN_ROLES, LOOKUP_ORPHAN_SKILLS,
}

MAPPING_ADD = "add"
MAPPING_REPLACE = "replace"

VALID_MAPPING_TYPES = {MAPPING_ADD, MAPPING_REPLACE}


def _normalize_name(name: str) -> str:
    """Normalize a role/skill name: lowercase, hyphens instead of spaces."""
    return name.strip().lower().replace(" ", "-").replace("_", "-")


@dataclass
class RoleRecord:
    """A role in the directory ontology."""

    name: str
    description: str = ""
    domain: str = ""
    level: str = ""
    skills: list[str] = field(default_factory=list)
    created_at: str = field(
        default_factory=lambda: datetime.now(timezone.utc).isoformat()
    )

    def to_dict(self) -> dict[str, Any]:
        return {
            "name": self.name,
            "description": self.description,
            "domain": self.domain,
            "level": self.level,
            "skills": list(self.skills),
            "created_at": self.created_at,
        }


@dataclass
class SkillRecord:
    """A skill in the directory ontology."""

    name: str
    description: str = ""
    category: str = ""
    difficulty: str = ""
    roles: list[str] = field(default_factory=list)
    created_at: str = field(
        default_factory=lambda: datetime.now(timezone.utc).isoformat()
    )

    def to_dict(self) -> dict[str, Any]:
        return {
            "name": self.name,
            "description": self.description,
            "category": self.category,
            "difficulty": self.difficulty,
            "roles": list(self.roles),
            "created_at": self.created_at,
        }


@dataclass
class DirectoryStats:
    """Directory statistics."""

    total_roles: int = 0
    total_skills: int = 0
    total_mappings: int = 0
    orphan_roles: int = 0
    orphan_skills: int = 0

    def to_dict(self) -> dict[str, Any]:
        return {
            "total_roles": self.total_roles,
            "total_skills": self.total_skills,
            "total_mappings": self.total_mappings,
            "orphan_roles": self.orphan_roles,
            "orphan_skills": self.orphan_skills,
        }


# ── S3 Directory Agent ───────────────────────────────────────────────────

class S3Directory:
    """S3 Directory agent — Roles × Skills ontology.

    Maintains bidirectional mappings between roles and skills,
    with role/skill definitions and lookup operations.
    """

    def __init__(self, vault_path: str | None = None):
        self.vault_path = Path(vault_path) if vault_path else None
        self._roles: dict[str, RoleRecord] = {}
        self._skills: dict[str, SkillRecord] = {}

    # ── Role operations ──────────────────────────────────────────────

    def define_role(
        self,
        role_name: str,
        description: str = "",
        domain: str = "",
        level: str = "",
    ) -> dict[str, Any]:
        """Define a new role in the directory."""
        errors: list[str] = []
        normalized = _normalize_name(role_name)

        if not normalized:
            errors.append("Role name cannot be empty")
            return {
                "role": None,
                "ok": False,
                "errors": errors,
            }

        if normalized in self._roles:
            errors.append(f"Role already exists: {normalized}")
            return {
                "role": None,
                "ok": False,
                "errors": errors,
            }

        role = RoleRecord(
            name=normalized,
            description=description,
            domain=domain,
            level=level,
        )
        self._roles[normalized] = role

        return {
            "role": role.to_dict(),
            "ok": True,
            "errors": [],
        }

    def define_skill(
        self,
        skill_name: str,
        description: str = "",
        category: str = "",
        difficulty: str = "",
    ) -> dict[str, Any]:
        """Define a new skill in the directory."""
        errors: list[str] = []
        normalized = _normalize_name(skill_name)

        if not normalized:
            errors.append("Skill name cannot be empty")
            return {
                "skill": None,
                "ok": False,
                "errors": errors,
            }

        if normalized in self._skills:
            errors.append(f"Skill already exists: {normalized}")
            return {
                "skill": None,
                "ok": False,
                "errors": errors,
            }

        skill = SkillRecord(
            name=normalized,
            description=description,
            category=category,
            difficulty=difficulty,
        )
        self._skills[normalized] = skill

        return {
            "skill": skill.to_dict(),
            "ok": True,
            "errors": [],
        }

    # ── Mapping operations ───────────────────────────────────────────

    def map_role_to_skills(
        self,
        role_name: str,
        skill_names: list[str],
        mapping_type: str = MAPPING_ADD,
    ) -> dict[str, Any]:
        """Map a role to skills (bidirectional)."""
        errors: list[str] = []
        normalized_role = _normalize_name(role_name)

        if normalized_role not in self._roles:
            errors.append(f"Role not found: {normalized_role}")
            return {
                "role_name": normalized_role,
                "mapped_skills": [],
                "mapping_type": mapping_type,
                "total_role_skills": 0,
                "bidirectional_mapped": False,
                "ok": False,
                "errors": errors,
            }

        if mapping_type not in VALID_MAPPING_TYPES:
            errors.append(f"Invalid mapping type: {mapping_type}")
            return {
                "role_name": normalized_role,
                "mapped_skills": [],
                "mapping_type": mapping_type,
                "total_role_skills": 0,
                "bidirectional_mapped": False,
                "ok": False,
                "errors": errors,
            }

        if mapping_type == MAPPING_REPLACE:
            # Clear existing mappings for this role
            old_skills = list(self._roles[normalized_role].skills)
            for old_skill in old_skills:
                if old_skill in self._skills:
                    self._skills[old_skill].roles = [
                        r for r in self._skills[old_skill].roles if r != normalized_role
                    ]
            self._roles[normalized_role].skills = []

        mapped: list[str] = []
        for skill_name in skill_names:
            normalized_skill = _normalize_name(skill_name)
            if normalized_skill not in self._skills:
                errors.append(f"Skill not found: {normalized_skill}")
                continue
            if normalized_skill not in self._roles[normalized_role].skills:
                self._roles[normalized_role].skills.append(normalized_skill)
            if normalized_role not in self._skills[normalized_skill].roles:
                self._skills[normalized_skill].roles.append(normalized_role)
            mapped.append(normalized_skill)

        ok = len(errors) == 0

        return {
            "role_name": normalized_role,
            "mapped_skills": mapped,
            "mapping_type": mapping_type,
            "total_role_skills": len(self._roles[normalized_role].skills),
            "bidirectional_mapped": ok,
            "ok": ok,
            "errors": errors,
        }

    # ── Lookup operations ────────────────────────────────────────────

    def lookup_role(self, role_name: str) -> dict[str, Any]:
        """Look up a role record plus its mapped skills."""
        normalized = _normalize_name(role_name)
        if normalized not in self._roles:
            return {
                "lookup_type": LOOKUP_ROLE,
                "results": None,
                "total": 0,
                "ok": False,
                "errors": [f"Role not found: {normalized}"],
            }
        role = self._roles[normalized]
        return {
            "lookup_type": LOOKUP_ROLE,
            "results": role.to_dict(),
            "total": 1,
            "ok": True,
            "errors": [],
        }

    def lookup_skill(self, skill_name: str) -> dict[str, Any]:
        """Look up a skill record plus its mapped roles."""
        normalized = _normalize_name(skill_name)
        if normalized not in self._skills:
            return {
                "lookup_type": LOOKUP_SKILL,
                "results": None,
                "total": 0,
                "ok": False,
                "errors": [f"Skill not found: {normalized}"],
            }
        skill = self._skills[normalized]
        return {
            "lookup_type": LOOKUP_SKILL,
            "results": skill.to_dict(),
            "total": 1,
            "ok": True,
            "errors": [],
        }

    def lookup_all(
        self,
        domain: str | None = None,
        category: str | None = None,
    ) -> dict[str, Any]:
        """Return all roles and skills with full mapping data."""
        roles = [
            r.to_dict() for r in self._roles.values()
            if not domain or r.domain == domain
        ]
        skills = [
            s.to_dict() for s in self._skills.values()
            if not category or s.category == category
        ]
        return {
            "lookup_type": LOOKUP_ALL,
            "results": {
                "roles": roles,
                "skills": skills,
            },
            "total": len(roles) + len(skills),
            "ok": True,
            "errors": [],
        }

    def lookup_orphan_roles(self) -> dict[str, Any]:
        """Return roles with no skills mapped."""
        orphans = [
            r.to_dict() for r in self._roles.values() if not r.skills
        ]
        return {
            "lookup_type": LOOKUP_ORPHAN_ROLES,
            "results": orphans,
            "total": len(orphans),
            "ok": True,
            "errors": [],
        }

    def lookup_orphan_skills(self) -> dict[str, Any]:
        """Return skills with no roles mapped."""
        orphans = [
            s.to_dict() for s in self._skills.values() if not s.roles
        ]
        return {
            "lookup_type": LOOKUP_ORPHAN_SKILLS,
            "results": orphans,
            "total": len(orphans),
            "ok": True,
            "errors": [],
        }

    # ── Stats ────────────────────────────────────────────────────────

    def stats(self) -> DirectoryStats:
        """Directory statistics."""
        total_mappings = sum(len(r.skills) for r in self._roles.values())
        orphan_roles = sum(1 for r in self._roles.values() if not r.skills)
        orphan_skills = sum(1 for s in self._skills.values() if not s.roles)
        return DirectoryStats(
            total_roles=len(self._roles),
            total_skills=len(self._skills),
            total_mappings=total_mappings,
            orphan_roles=orphan_roles,
            orphan_skills=orphan_skills,
        )

    # ── Persistence ──────────────────────────────────────────────────

    def save_to_vault(self, apply: bool = False) -> str | None:
        """Save directory to vault as JSON (if --apply / vault configured)."""
        if not self.vault_path or not apply:
            return None

        dir_path = self.vault_path / "02-Areas" / "Skills"
        dir_path.mkdir(parents=True, exist_ok=True)

        data = {
            "roles": {name: r.to_dict() for name, r in self._roles.items()},
            "skills": {name: s.to_dict() for name, s in self._skills.items()},
            "stats": self.stats().to_dict(),
            "saved_at": datetime.now(timezone.utc).isoformat(),
        }

        path = dir_path / "directory-ontology.json"
        path.write_text(json.dumps(data, indent=2), encoding="utf-8")
        return str(path)

    def load_from_vault(self) -> bool:
        """Load directory from vault JSON file (if vault configured)."""
        if not self.vault_path:
            return False

        path = self.vault_path / "02-Areas" / "Skills" / "directory-ontology.json"
        if not path.exists():
            return False

        try:
            data = json.loads(path.read_text(encoding="utf-8"))
            for name, rdata in data.get("roles", {}).items():
                self._roles[name] = RoleRecord(**rdata)
            for name, sdata in data.get("skills", {}).items():
                self._skills[name] = SkillRecord(**sdata)
            return True
        except (json.JSONDecodeError, TypeError):
            return False


# ── CLI ──────────────────────────────────────────────────────────────────

import argparse  # noqa: E402
import sys  # noqa: E402


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Borg S3 Directory — Roles × Skills ontology",
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

    # define-role
    p_role = sub.add_parser("define-role", help="Define a new role")
    p_role.add_argument("--name", required=True, help="Role name")
    p_role.add_argument("--description", default="", help="Role description")
    p_role.add_argument("--domain", default="", help="Functional domain")
    p_role.add_argument("--level", default="", help="Seniority level")

    # define-skill
    p_skill = sub.add_parser("define-skill", help="Define a new skill")
    p_skill.add_argument("--name", required=True, help="Skill name")
    p_skill.add_argument("--description", default="", help="Skill description")
    p_skill.add_argument("--category", default="", help="Skill category")
    p_skill.add_argument("--difficulty", default="", help="Difficulty level")

    # map-role-skills
    p_map = sub.add_parser("map", help="Map role to skills")
    p_map.add_argument("--role", required=True, help="Role name")
    p_map.add_argument(
        "--skills", required=True, help="Comma-separated skill names"
    )
    p_map.add_argument(
        "--mapping-type",
        default=MAPPING_ADD,
        choices=[MAPPING_ADD, MAPPING_REPLACE],
        help="add (default) or replace",
    )

    # lookup
    p_lookup = sub.add_parser("lookup", help="Look up roles/skills/mappings")
    p_lookup.add_argument(
        "--type",
        choices=list(VALID_LOOKUP_TYPES),
        default=LOOKUP_ALL,
        help="Lookup type (default: all)",
    )
    p_lookup.add_argument("--name", help="Name to look up (for role/skill type)")
    p_lookup.add_argument("--domain", help="Domain filter (for all type)")
    p_lookup.add_argument("--category", help="Category filter (for all type)")

    # stats
    sub.add_parser("stats", help="Show directory statistics")

    return parser.parse_args()


def cmd_test() -> int:
    """Run self-test suite."""
    print("Borg S3 Directory — Self-Test Suite")
    print("=" * 50)

    passed = 0
    failed = 0

    # Test 1: Define role
    print("\n[1/8] Define role...")
    directory = S3Directory()
    result = directory.define_role(
        "data-engineer",
        description="Builds and maintains data pipelines",
        domain="data",
        level="mid",
    )
    assert result["ok"], f"Role define failed: {result['errors']}"
    assert result["role"]["name"] == "data-engineer"
    assert result["role"]["domain"] == "data"
    print(f"  ✅ Role defined: {result['role']['name']}")
    passed += 1

    # Test 2: Define skill
    print("\n[2/8] Define skill...")
    result = directory.define_skill(
        "python-scripting",
        description="Write and maintain Python scripts",
        category="programming",
        difficulty="intermediate",
    )
    assert result["ok"], f"Skill define failed: {result['errors']}"
    assert result["skill"]["name"] == "python-scripting"
    assert result["skill"]["category"] == "programming"
    print(f"  ✅ Skill defined: {result['skill']['name']}")
    passed += 1

    # Test 3: Map role to skills
    print("\n[3/8] Map role to skills...")
    # Define skills first
    directory.define_skill("python-scripting", description="Python scripting", category="programming", difficulty="intermediate")
    directory.define_skill("sql", description="SQL queries", category="data", difficulty="beginner")
    directory.define_skill("airflow", description="Workflow orchestration", category="data", difficulty="intermediate")
    result = directory.map_role_to_skills(
        "data-engineer",
        ["python-scripting", "sql", "airflow"],
    )
    assert result["ok"], f"Map failed: {result['errors']}"
    assert "python-scripting" in result["mapped_skills"]
    assert "sql" in result["mapped_skills"]
    assert result["total_role_skills"] == 3
    print(f"  ✅ Mapped {result['total_role_skills']} skills to role")
    passed += 1

    # Test 4: Lookup role
    print("\n[4/8] Lookup role...")
    result = directory.lookup_role("data-engineer")
    assert result["ok"], f"Role lookup failed: {result['errors']}"
    assert result["results"]["name"] == "data-engineer"
    assert len(result["results"]["skills"]) == 3
    print(f"  ✅ Role lookup: {len(result['results']['skills'])} skills")
    passed += 1

    # Test 5: Lookup skill (bidirectional)
    print("\n[5/8] Lookup skill (bidirectional)...")
    result = directory.lookup_skill("python-scripting")
    assert result["ok"], f"Skill lookup failed: {result['errors']}"
    assert "data-engineer" in result["results"]["roles"]
    print(f"  ✅ Skill lookup: {len(result['results']['roles'])} roles")
    passed += 1

    # Test 6: Lookup all
    print("\n[6/8] Lookup all...")
    result = directory.lookup_all()
    assert result["ok"], f"All lookup failed: {result['errors']}"
    assert result["results"]["roles"]  # non-empty
    assert result["results"]["skills"]  # non-empty
    print(f"  ✅ All lookup: {result['total']} entries")
    passed += 1

    # Test 7: Orphan roles/skills
    print("\n[7/8] Orphan roles/skills...")
    directory.define_role("junior-dev", domain="engineering", level="junior")
    directory.define_skill("git", category="tooling")
    orphans = directory.lookup_orphan_roles()
    assert orphans["ok"]
    assert any(r["name"] == "junior-dev" for r in orphans["results"])
    orphans = directory.lookup_orphan_skills()
    assert orphans["ok"]
    assert any(s["name"] == "git" for s in orphans["results"])
    print(f"  ✅ Orphans: {orphans['total']} roles, skills with no roles")
    passed += 1

    # Test 8: Stats
    print("\n[8/8] Stats...")
    stats = directory.stats()
    assert stats.total_roles >= 2
    assert stats.total_skills >= 2
    assert stats.total_mappings >= 3
    print(f"  ✅ Stats: {stats.total_roles} roles, {stats.total_skills} skills, {stats.total_mappings} mappings")
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

    directory = S3Directory(vault_path=args.vault)

    # Try to load existing directory from vault
    directory.load_from_vault()

    dry_run = args.dry_run and not args.apply

    if args.command == "define-role":
        result = directory.define_role(
            args.name,
            description=args.description,
            domain=args.domain,
            level=args.level,
        )
        print(json.dumps(result, indent=2))
        if result["ok"] and not dry_run:
            path = directory.save_to_vault(apply=True)
            if path:
                print(f"\nSaved to: {path}")
        return 0 if result["ok"] else 1

    if args.command == "define-skill":
        result = directory.define_skill(
            args.name,
            description=args.description,
            category=args.category,
            difficulty=args.difficulty,
        )
        print(json.dumps(result, indent=2))
        if result["ok"] and not dry_run:
            path = directory.save_to_vault(apply=True)
            if path:
                print(f"\nSaved to: {path}")
        return 0 if result["ok"] else 1

    if args.command == "map":
        skills = [s.strip() for s in args.skills.split(",") if s.strip()]
        result = directory.map_role_to_skills(
            args.role,
            skills,
            mapping_type=args.mapping_type,
        )
        print(json.dumps(result, indent=2))
        if result["ok"] and not dry_run:
            path = directory.save_to_vault(apply=True)
            if path:
                print(f"\nSaved to: {path}")
        return 0 if result["ok"] else 1

    if args.command == "lookup":
        if args.type == LOOKUP_ROLE:
            if not args.name:
                print("--name is required for role lookup")
                return 1
            result = directory.lookup_role(args.name)
        elif args.type == LOOKUP_SKILL:
            if not args.name:
                print("--name is required for skill lookup")
                return 1
            result = directory.lookup_skill(args.name)
        elif args.type == LOOKUP_ALL:
            result = directory.lookup_all(
                domain=args.domain,
                category=args.category,
            )
        elif args.type == LOOKUP_ORPHAN_ROLES:
            result = directory.lookup_orphan_roles()
        elif args.type == LOOKUP_ORPHAN_SKILLS:
            result = directory.lookup_orphan_skills()
        else:
            print(f"Unknown lookup type: {args.type}")
            return 1
        print(json.dumps(result, indent=2))
        return 0 if result["ok"] else 1

    if args.command == "stats":
        stats = directory.stats()
        print(json.dumps(stats.to_dict(), indent=2))
        return 0

    parser.print_help()
    return 1


if __name__ == "__main__":
    sys.exit(main())
