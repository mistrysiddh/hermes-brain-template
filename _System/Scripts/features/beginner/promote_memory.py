#!/usr/bin/env python3
"""
promote_memory.py — 1-Click Memory Promotion Backend for Hermes Brain.

Safely promotes human-reviewed memory candidates into:
  1. Hermes native MEMORY.md (~/.hermes/MEMORY.md)
  2. Vault User Profile (02-Areas/User-Profile.md)
  3. Dismissed / Rejected Archive

Maintains an immutable audit log in 04-Archives/Memory-Review/Consolidation-Log.md.

Usage:
  List pending candidates:
    python promote_memory.py --list [--vault <path>]

  Promote a candidate note to Hermes MEMORY.md:
    python promote_memory.py --file <path_to_candidate.md> --target hermes [--vault <path>]

  Promote a candidate note to User-Profile.md:
    python promote_memory.py --file <path_to_candidate.md> --target profile [--vault <path>]

  Dismiss a candidate note:
    python promote_memory.py --file <path_to_candidate.md> --target dismiss [--vault <path>]

  Run Self-Tests:
    python promote_memory.py --test
"""

import os
import sys
import re
import json
import argparse
from pathlib import Path
from datetime import datetime, timezone

# ---------------------------------------------------------------------------
# Vault Path Resolution
# ---------------------------------------------------------------------------

def get_vault_path(explicit_path=None):
    if explicit_path and os.path.isdir(explicit_path):
        return Path(explicit_path).resolve()

    env_vault = os.environ.get("HERMES_VAULT_PATH")
    if env_vault and os.path.isdir(env_vault):
        return Path(env_vault).resolve()

    script_dir = Path(__file__).resolve().parent
    for candidate in [
        Path.cwd().resolve(),
        script_dir.parent.parent,
        script_dir.parent,
    ]:
        if (candidate / ".obsidian").exists() or (candidate / "01-Projects").exists():
            return candidate.resolve()

    return Path.cwd().resolve()


def get_hermes_memory_path(explicit_path=None):
    if explicit_path:
        return Path(explicit_path).resolve()
    user_home = Path.home()
    return user_home / ".hermes" / "MEMORY.md"


# ---------------------------------------------------------------------------
# Memory Promotion Core
# ---------------------------------------------------------------------------

class MemoryPromoter:
    def __init__(self, vault_root: Path, hermes_memory_path: Path = None):
        self.vault = vault_root
        self.hermes_memory = hermes_memory_path or get_hermes_memory_path()

    def get_review_dir(self) -> Path:
        cand = [self.vault / "04-Archives" / "Memory-Review", self.vault / "Memory-Review"]
        review_dir = next((d for d in cand if d.exists()), self.vault / "04-Archives" / "Memory-Review")
        review_dir.mkdir(parents=True, exist_ok=True)
        return review_dir

    def list_candidates(self) -> list:
        """Find all pending memory candidates."""
        review_dir = self.get_review_dir()
        candidates = []

        # Find candidate notes (candidate_*.md)
        for f in sorted(review_dir.glob("*.md")):
            if f.name in ["README.md", "TEMPLATE.md", "HERMES-PREAMBLE.md", "Consolidation-Log.md", "Promotion-Candidates.md"]:
                continue
            try:
                content = f.read_text(encoding="utf-8", errors="replace")
            except Exception:
                continue

            # Check status
            status_match = re.search(r"^status:\s*([a-zA-Z0-9_\-]+)", content, re.M | re.I)
            status = status_match.group(1).lower() if status_match else "pending-review"

            if status in ["approved", "dismissed", "promoted", "archived"]:
                continue

            # Extract fact quote
            fact_match = re.search(r"### Candidate Fact\s*\n+>\s*(.+?)(?=\n\n|\n###|\Z)", content, re.S)
            fact = fact_match.group(1).strip() if fact_match else f.stem

            category_match = re.search(r"category:\s*([a-zA-Z0-9_\-]+)", content, re.I)
            category = category_match.group(1) if category_match else "general"

            source_match = re.search(r"source:\s*\"?([^\n\"]+)\"?", content, re.I)
            source = source_match.group(1) if source_match else "vault"

            candidates.append({
                "path": str(f.relative_to(self.vault)).replace("\\", "/"),
                "full_path": str(f),
                "filename": f.name,
                "fact": fact,
                "category": category,
                "source": source,
                "status": status,
            })

        return candidates

    def log_consolidation(self, fact: str, action: str, destination: str):
        """Append immutable record to Consolidation-Log.md."""
        review_dir = self.get_review_dir()
        log_file = review_dir / "Consolidation-Log.md"

        now_utc = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")
        mark = "x" if action in ["hermes", "profile"] else "-"
        entry = f"- [{mark}] {fact} ({action.upper()} → {destination} on {now_utc})\n"

        if not log_file.exists():
            header = "# Consolidation Log\n\nImmutable append-only audit trail of human-promoted memory items.\n\n"
            log_file.write_text(header + entry, encoding="utf-8")
        else:
            with open(log_file, "a", encoding="utf-8") as f:
                f.write(entry)

    def promote_to_hermes(self, fact: str, category: str = "general", candidate_path: Path = None) -> dict:
        """Promote a fact directly into ~/.hermes/MEMORY.md."""
        now_date = datetime.now(timezone.utc).strftime("%Y-%m-%d")
        entry_line = f"- [{now_date}] [{category}] {fact}\n"

        # Ensure directory exists
        self.hermes_memory.parent.mkdir(parents=True, exist_ok=True)

        if not self.hermes_memory.exists():
            content = f"# Hermes Memory\n\n## 🧠 Durable Facts & Architecture Rules\n{entry_line}"
            self.hermes_memory.write_text(content, encoding="utf-8")
        else:
            current = self.hermes_memory.read_text(encoding="utf-8", errors="replace")
            # If section exists, append to it, else append section
            if "## 🧠 Durable Facts" in current or "## Durable Facts" in current:
                target_header = "## 🧠 Durable Facts" if "## 🧠 Durable Facts" in current else "## Durable Facts"
                parts = current.split(target_header)
                updated = parts[0] + target_header + "\n" + entry_line + parts[1]
                self.hermes_memory.write_text(updated, encoding="utf-8")
            else:
                with open(self.hermes_memory, "a", encoding="utf-8") as f:
                    f.write(f"\n## 🧠 Durable Facts & Rules\n{entry_line}")

        # Mark candidate file as approved if provided
        if candidate_path and Path(candidate_path).exists():
            self._mark_file_status(Path(candidate_path), "approved", "Hermes MEMORY.md")

        self.log_consolidation(fact, "hermes", str(self.hermes_memory))
        return {
            "status": "success",
            "action": "promoted_to_hermes",
            "destination": str(self.hermes_memory),
            "fact": fact
        }

    def promote_to_profile(self, fact: str, candidate_path: Path = None) -> dict:
        """Promote a fact into 02-Areas/User-Profile.md."""
        profile_path = self.vault / "02-Areas" / "User-Profile.md"
        if not profile_path.exists():
            profile_path = self.vault / "User-Profile.md"

        now_date = datetime.now(timezone.utc).strftime("%Y-%m-%d")
        entry_line = f"- [{now_date}] {fact}\n"

        if profile_path.exists():
            content = profile_path.read_text(encoding="utf-8", errors="replace")
            target_heading = "## 📌 Learned Rules & Preferences"
            if target_heading in content:
                parts = content.split(target_heading)
                updated = parts[0] + target_heading + "\n" + entry_line + parts[1]
                profile_path.write_text(updated, encoding="utf-8")
            else:
                with open(profile_path, "a", encoding="utf-8") as f:
                    f.write(f"\n\n{target_heading}\n{entry_line}")
        else:
            profile_path.write_text(f"# User Profile\n\n## 📌 Learned Rules & Preferences\n{entry_line}", encoding="utf-8")

        if candidate_path and Path(candidate_path).exists():
            self._mark_file_status(Path(candidate_path), "approved", "User-Profile.md")

        self.log_consolidation(fact, "profile", str(profile_path))
        return {
            "status": "success",
            "action": "promoted_to_profile",
            "destination": str(profile_path),
            "fact": fact
        }

    def dismiss(self, fact: str, candidate_path: Path = None) -> dict:
        """Dismiss a candidate without promoting to memory."""
        if candidate_path and Path(candidate_path).exists():
            self._mark_file_status(Path(candidate_path), "dismissed", "None (Dismissed)")

        self.log_consolidation(fact, "dismiss", "Archived/Dismissed")
        return {
            "status": "success",
            "action": "dismissed",
            "destination": "Consolidation-Log.md",
            "fact": fact
        }

    def _mark_file_status(self, file_path: Path, new_status: str, target: str):
        try:
            content = file_path.read_text(encoding="utf-8", errors="replace")
            # Replace status in frontmatter
            if re.search(r"^status:\s*.*$", content, re.M):
                content = re.sub(r"^status:\s*.*$", f"status: {new_status}", content, flags=re.M)
            now_iso = datetime.now(timezone.utc).isoformat()
            append_banner = f"\n\n---\n> **Triage Decision:** `{new_status.upper()}` → {target} at {now_iso}\n"
            file_path.write_text(content + append_banner, encoding="utf-8")

            # Move to Reviewed subfolder to keep inbox clean
            reviewed_dir = file_path.parent / "Reviewed"
            reviewed_dir.mkdir(parents=True, exist_ok=True)
            dest = reviewed_dir / file_path.name
            file_path.rename(dest)
        except Exception as e:
            sys.stderr.write(f"Warning: could not update candidate file status: {e}\n")


# ---------------------------------------------------------------------------
# Self-Test / Diagnostics
# ---------------------------------------------------------------------------

def run_self_test():
    import tempfile, shutil
    print("=" * 60)
    print("🧪 promote_memory.py Self-Test Suite")
    print("=" * 60)

    test_dir = Path(tempfile.mkdtemp(prefix="hb-promote-test-"))
    try:
        vault = test_dir / "Vault"
        vault.mkdir()
        (vault / "02-Areas").mkdir(parents=True)
        (vault / "04-Archives" / "Memory-Review").mkdir(parents=True)
        (vault / "02-Areas" / "User-Profile.md").write_text("# User Profile\n", encoding="utf-8")

        fake_hermes = test_dir / "hermes_memory.md"
        promoter = MemoryPromoter(vault, fake_hermes)

        # 1. Create a dummy candidate note
        candidate_file = vault / "04-Archives" / "Memory-Review" / "candidate_test_fact.md"
        candidate_file.write_text("""---
type: memory-candidate
status: pending-review
category: architectural_rule
source: "test-session"
---

# 🧠 Memory Candidate: SQLite Wal Mode

### Candidate Fact
> Always enable WAL mode for SQLite concurrent access.
""", encoding="utf-8")

        # 2. Test list_candidates
        cands = promoter.list_candidates()
        assert len(cands) == 1
        assert "WAL mode" in cands[0]["fact"]
        print("✅ list_candidates -> OK (Found 1 candidate)")

        # 3. Test promote_to_hermes
        res_h = promoter.promote_to_hermes(cands[0]["fact"], cands[0]["category"], Path(cands[0]["full_path"]))
        assert res_h["status"] == "success"
        hermes_content = fake_hermes.read_text(encoding="utf-8")
        assert "Always enable WAL mode" in hermes_content
        print("✅ promote_to_hermes -> OK (Written to target memory)")

        # Verify candidate moved to Reviewed
        assert not candidate_file.exists()
        reviewed_file = vault / "04-Archives" / "Memory-Review" / "Reviewed" / "candidate_test_fact.md"
        assert reviewed_file.exists()
        print("✅ Candidate moved to Reviewed/ -> OK")

        # Verify Consolidation-Log.md updated
        log_file = vault / "04-Archives" / "Memory-Review" / "Consolidation-Log.md"
        assert log_file.exists()
        assert "WAL mode" in log_file.read_text(encoding="utf-8")
        print("✅ Consolidation-Log.md audit trail -> OK")

        # 4. Test promote_to_profile
        res_p = promoter.promote_to_profile("Prefer async/await over raw callbacks.")
        assert res_p["status"] == "success"
        prof_content = (vault / "02-Areas" / "User-Profile.md").read_text(encoding="utf-8")
        assert "Prefer async/await" in prof_content
        print("✅ promote_to_profile -> OK (Appended to User-Profile.md)")

        # 5. Test dismiss
        res_d = promoter.dismiss("One-time temporary fact.")
        assert res_d["status"] == "success"
        print("✅ dismiss -> OK")

        print("=" * 60)
        print("🎉 All promote_memory.py self-tests PASSED successfully!")
        print("=" * 60)

    finally:
        shutil.rmtree(test_dir, ignore_errors=True)


# ---------------------------------------------------------------------------
# Main Entry Point
# ---------------------------------------------------------------------------

def main():
    parser = argparse.ArgumentParser(description="Hermes Brain Memory Promotion Engine")
    parser.add_argument("--vault", type=str, default="", help="Path to vault root")
    parser.add_argument("--hermes-memory", type=str, default="", help="Path to ~/.hermes/MEMORY.md")
    parser.add_argument("--list", action="store_true", help="List pending memory candidates")
    parser.add_argument("--file", type=str, default="", help="Relative or absolute path to candidate markdown file")
    parser.add_argument("--fact", type=str, default="", help="Direct text of fact (if no file given)")
    parser.add_argument("--target", choices=["hermes", "profile", "dismiss"], help="Promotion target destination")
    parser.add_argument("--category", type=str, default="general", help="Category for fact")
    parser.add_argument("--test", action="store_true", help="Run automated self-tests")
    parser.add_argument("--review", action="store_true", help="Interactively review and promote/dismiss memory candidates")
    args = parser.parse_args()

    if args.test:
        run_self_test()
        sys.exit(0)

    if args.review:
        # Interactive review mode
        cands = promoter.list_candidates()
        if not cands:
            print("No pending memory candidates to review.")
            sys.exit(0)
        
        print("Found {} pending memory candidate(s):".format(len(cands)))
        print("-" * 60)
        for i, cand in enumerate(cands, 1):
            fact_display = cand['fact'][:80] + ('...' if len(cand['fact']) > 80 else '')
            print("{}. [{}] {}".format(i, cand['category'], fact_display))
            print("   File: {} | Source: {}".format(cand['filename'], cand['source']))
            print()
        
        while True:
            try:
                choice = input("Select candidate to review (1-{}, or 'q' to quit): ".format(len(cands))).strip()
                if choice.lower() == 'q':
                    print("Review cancelled.")
                    sys.exit(0)
                
                idx = int(choice) - 1
                if 0 <= idx < len(cands):
                    cand = cands[idx]
                    break
                else:
                    print("Please enter a number between 1 and {}".format(len(cands)))
            except ValueError:
                print("Please enter a valid number or 'q' to quit")
        
        print("\nReviewing candidate {}:".format(idx + 1))
        print("Fact: {}".format(cand['fact']))
        print("Category: {}".format(cand['category']))
        print("Source: {}".format(cand['source']))
        print("File: {}".format(cand['full_path']))
        print("-" * 60)
        
        # Show the full candidate note for context
        try:
            with open(cand['full_path'], 'r', encoding='utf-8') as f:
                note_content = f.read()
            print("Full note content:")
            print("=" * 40)
            print(note_content)
            print("=" * 40)
        except Exception as e:
            print("Could not read candidate file: {}".format(e))
        
        print("\nWhat would you like to do?")
        print("  [h] Promote to Hermes MEMORY.md")
        print("  [p] Promote to User-Profile.md")
        print("  [d] Dismiss / Reject")
        print("  [s] Skip (leave pending)")
        print("  [q] Quit review")
        
        while True:
            action = input("Choose action (h/p/s/d/q): ").strip().lower()
            if action in ['h', 'p', 's', 'd', 'q']:
                break
            print("Please choose h, p, s, d, or q")
        
        if action == 'q':
            print("Review cancelled.")
            sys.exit(0)
        elif action == 's':
            print("Candidate left pending for later review.")
            sys.exit(0)
        elif action == 'h':
            # Promote to Hermes MEMORY.md
            res = promoter.promote_to_hermes(cand['fact'], cand['category'], Path(cand['full_path']))
            fact_display = cand['fact'][:60] + ('...' if len(cand['fact']) > 60 else '')
            print("✅ Promoted to Hermes MEMORY.md: {}".format(fact_display))
        elif action == 'p':
            # Promote to User-Profile.md
            res = promoter.promote_to_profile(cand['fact'], Path(cand['full_path']))
            fact_display = cand['fact'][:60] + ('...' if len(cand['fact']) > 60 else '')
            print("✅ Promoted to User-Profile.md: {}".format(fact_display))
        elif action == 'd':
            # Dismiss
            res = promoter.dismiss(cand['fact'], Path(cand['full_path']))
            fact_display = cand['fact'][:60] + ('...' if len(cand['fact']) > 60 else '')
            print("🗑️ Dismissed candidate: {}".format(fact_display))

    vault_path = get_vault_path(args.vault)
    hermes_mem = get_hermes_memory_path(args.hermes_memory)
    promoter = MemoryPromoter(vault_path, hermes_mem)

    if args.list:
        cands = promoter.list_candidates()
        print(json.dumps(cands, indent=2))
        return

    if not args.target:
        parser.print_help()
        sys.exit(1)

    candidate_file = None
    fact_text = args.fact

    if args.file:
        candidate_file = (vault_path / args.file).resolve() if not os.path.isabs(args.file) else Path(args.file)
        if not candidate_file.exists():
            print(f"Error: Candidate file not found: {candidate_file}")
            sys.exit(1)
        if not fact_text:
            content = candidate_file.read_text(encoding="utf-8", errors="replace")
            fact_match = re.search(r"### Candidate Fact\s*\n+>\s*(.+?)(?=\n\n|\n###|\Z)", content, re.S)
            fact_text = fact_match.group(1).strip() if fact_match else candidate_file.stem
            cat_match = re.search(r"category:\s*([a-zA-Z0-9_\-]+)", content, re.I)
            if cat_match and args.category == "general":
                args.category = cat_match.group(1)

    if not fact_text:
        print("Error: No fact text provided via --fact or --file.")
        sys.exit(1)

    if args.target == "hermes":
        res = promoter.promote_to_hermes(fact_text, args.category, candidate_file)
        print(f"✅ Promoted to Hermes MEMORY.md: {fact_text}")
    elif args.target == "profile":
        res = promoter.promote_to_profile(fact_text, candidate_file)
        print(f"✅ Promoted to User-Profile.md: {fact_text}")
    elif args.target == "dismiss":
        res = promoter.dismiss(fact_text, candidate_file)
        print(f"🗑️ Dismissed candidate: {fact_text}")

if __name__ == "__main__":
    main()
