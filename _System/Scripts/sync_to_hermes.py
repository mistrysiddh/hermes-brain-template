#!/usr/bin/env python3
"""
sync_to_hermes.py — Bidirectional Memory Sync & Context Preamble Generator.

Connects the Obsidian Hermes Brain Vault to the active Hermes / OpenClaw runtime:
1. Gathers approved facts (- [x]) from Memory-Review/Promotion-Candidates.md and
   Memory-Review/Memory-Board.kanban.
2. Synchronizes approved facts directly into Hermes's native MEMORY.md file.
3. Generates a calibrated Context Preamble (HERMES-PREAMBLE.md) with active
   projects, standing boundaries from User-Profile.md, and durable facts.

Usage:
    python Scripts/sync_to_hermes.py [vault_path] [--dry-run] [--preamble-only]
"""

import os
import sys
import re
import argparse
from datetime import datetime, timezone
from pathlib import Path

def find_vault_root(start_dir=None):
    """Locate the vault root directory containing User-Profile.md or Dashboard.md."""
    current = Path(start_dir or os.getcwd()).resolve()
    for p in [current, current.parent, current.parent.parent]:
        if (p / "User-Profile.md").exists() or (p / "Dashboard.md").exists():
            return p
    return current

def detect_hermes_memory_target(vault_root):
    """Detect the destination path for Hermes native MEMORY.md."""
    # 1. Check explicit environment variables
    env_path = os.environ.get("HERMES_MEMORY_PATH") or os.environ.get("OPENCLAW_MEMORY_PATH")
    if env_path and Path(env_path).parent.exists():
        return Path(env_path)

    # 2. Check standard home directory locations
    home = Path.home()
    candidates = [
        home / ".hermes" / "MEMORY.md",
        home / ".openclaw" / "MEMORY.md",
        home / ".openclaw" / "workspace" / "MEMORY.md",
        home / ".claude" / "MEMORY.md",
    ]
    for c in candidates:
        if c.parent.exists():
            return c

    # 3. Fallback to vault-local replica in Memory-Review/
    mr_dir = find_dir(vault_root, ("04-Archives", "Memory-Review"), "Memory-Review")
    return mr_dir / "ACTIVE-HERMES-MEMORY.md"

def find_dir(vault_root, *candidates):
    for c in candidates:
        p = vault_root.joinpath(*c) if isinstance(c, (list, tuple)) else vault_root / c
        if p.exists():
            return p
    first = candidates[0]
    return vault_root.joinpath(*first) if isinstance(first, (list, tuple)) else vault_root / first

def extract_approved_facts(vault_root):
    """Extract all approved facts from Promotion-Candidates.md and Memory-Board.kanban."""
    facts = []
    seen = set()

    mr_dir = find_dir(vault_root, ("04-Archives", "Memory-Review"), "Memory-Review")

    # 1. Read from Promotion-Candidates.md
    cand_file = mr_dir / "Promotion-Candidates.md"
    if cand_file.exists():
        content = cand_file.read_text(encoding="utf-8")
        for line in content.splitlines():
            m = re.match(r"^\s*-\s+\[x\]\s+(.*?)(?:\s*<!--.*-->)?$", line, re.I)
            if m:
                clean = m.group(1).strip()
                if clean and clean.lower() not in seen:
                    seen.add(clean.lower())
                    facts.append({"text": clean, "source": "Promotion-Candidates.md"})

    # 2. Read from Memory-Board.kanban
    kanban_file = mr_dir / "Memory-Board.kanban"
    if kanban_file.exists():
        content = kanban_file.read_text(encoding="utf-8")
        in_approved = False
        for line in content.splitlines():
            if line.startswith("## ") and ("approved" in line.lower() or "durable" in line.lower()):
                in_approved = True
                continue
            elif line.startswith("## "):
                in_approved = False

            if in_approved:
                m = re.match(r"^\s*-\s+\[[ x]\]\s+(.*?)$", line, re.I)
                if m:
                    clean = m.group(1).strip()
                    if clean and clean.lower() not in seen:
                        seen.add(clean.lower())
                        facts.append({"text": clean, "source": "Memory-Board.kanban"})

    return facts

def sync_facts_to_memory(target_file, facts, dry_run=False):
    """Sync approved facts into the destination MEMORY.md file without duplicating."""
    target_file.parent.mkdir(parents=True, exist_ok=True)
    existing_content = target_file.read_text(encoding="utf-8") if target_file.exists() else ""
    
    existing_lines = [l.strip().lower() for l in existing_content.splitlines() if l.strip()]
    
    new_facts = []
    for f in facts:
        norm = f["text"].lower()
        if not any(norm in l or l in norm for l in existing_lines):
            new_facts.append(f)

    if not new_facts:
        print("  [Memory Sync] No new facts to sync (already up to date).")
        return 0

    header = "\n\n## 🧠 Promoted Facts from Hermes Brain (Verified)\n"
    new_block = header + f"<!-- Synced at: {datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M UTC')} -->\n"
    for nf in new_facts:
        new_block += f"- {nf['text']}\n"

    if dry_run:
        print(f"  [DRY RUN] Would append {len(new_facts)} new facts to {target_file}:")
        for nf in new_facts:
            print(f"    + {nf['text']}")
    else:
        with open(target_file, "a", encoding="utf-8") as f:
            f.write(new_block)
        print(f"  [Memory Sync] Successfully synced {len(new_facts)} facts to {target_file}")

    return len(new_facts)

def generate_context_preamble(vault_root, facts, dry_run=False):
    """Build an executive system prompt preamble string from vault state."""
    # 1. Read User Profile operational boundaries
    user_file = find_dir(vault_root, ("02-Areas", "User-Profile.md"), "User-Profile.md")
    tone = "Direct, code first, zero fluff"
    rule = "Proceed unless destructive; verify before irreversible changes"
    out_format = "Concise markdown with actionable code snippets"
    
    if user_file.exists():
        u_content = user_file.read_text(encoding="utf-8")
        t_m = re.search(r"-\s+\*\*Tone:\*\*\s*([^\n]+)", u_content)
        r_m = re.search(r"-\s+\*\*When in doubt:\*\*\s*([^\n]+)", u_content)
        f_m = re.search(r"-\s+\*\*Output format:\*\*\s*([^\n]+)", u_content)
        if t_m and not t_m.group(1).startswith("_("): tone = t_m.group(1).strip()
        if r_m and not r_m.group(1).startswith("_("): rule = r_m.group(1).strip()
        if f_m and not f_m.group(1).startswith("_("): out_format = f_m.group(1).strip()

    # 2. Get active projects
    projects_dir = find_dir(vault_root, "01-Projects", "Projects")
    active_projects = []
    if projects_dir.exists():
        for pf in projects_dir.glob("*.md"):
            if pf.name not in ["README.md", "TEMPLATE.md", "Projects.base"]:
                p_text = pf.read_text(encoding="utf-8", errors="ignore")
                if "status: active" in p_text or "status: in-progress" in p_text:
                    active_projects.append(pf.stem)

    # 3. Assemble preamble block
    now_str = datetime.now().strftime("%Y-%m-%d %H:%M")
    lines = [
        "<!-- HERMES BRAIN ACTIVE CONTEXT PREAMBLE -->",
        f"# System Context: Hermes Brain ({now_str})",
        "",
        "## Standing Operational Parameters",
        f"- Preferred Tone: {tone}",
        f"- When In Doubt Rule: {rule}",
        f"- Preferred Output Format: {out_format}",
        "",
        "## Active Projects in Workspace",
    ]
    if active_projects:
        for ap in active_projects[:5]:
            proj_link = f"01-Projects/{ap}" if (vault_root / "01-Projects").exists() else f"Projects/{ap}"
            lines.append(f"- [[{proj_link}|{ap}]]")
    else:
        lines.append("- (No active projects tagged in 01-Projects/)")

    lines.extend([
        "",
        "## Core Durable Facts (Brain Substrate)",
    ])
    if facts:
        for f in facts[-8:]:
            lines.append(f"- {f['text']}")
    else:
        lines.append("- (No durable facts approved yet)")

    preamble_text = "\n".join(lines) + "\n"

    # Write preamble to 04-Archives/Memory-Review/HERMES-PREAMBLE.md
    mr_dir = find_dir(vault_root, ("04-Archives", "Memory-Review"), "Memory-Review")
    out_file = mr_dir / "HERMES-PREAMBLE.md"
    if not dry_run:
        out_file.write_text(preamble_text, encoding="utf-8")
        print(f"  [Preamble Generator] Generated calibrated context preamble: {out_file}")

    # Also mirror to ~/.hermes/PREAMBLE.md if directory exists
    home_preamble = Path.home() / ".hermes" / "PREAMBLE.md"
    if home_preamble.parent.exists() and not dry_run:
        home_preamble.write_text(preamble_text, encoding="utf-8")
        print(f"  [Preamble Generator] Mirrored to active Hermes directory: {home_preamble}")

    return preamble_text

def main():
    parser = argparse.ArgumentParser(description="Bidirectional memory sync for Hermes Brain")
    parser.add_argument("vault", nargs="?", default=None, help="Vault root directory path")
    parser.add_argument("--dry-run", action="store_true", help="Preview sync actions without modifying files")
    parser.add_argument("--preamble-only", action="store_true", help="Only regenerate context preamble")
    args = parser.parse_args()

    vault_root = find_vault_root(args.vault)
    print(f"🧠 Hermes Brain Bidirectional Sync — Target Vault: {vault_root}")

    # 1. Extract approved facts
    facts = extract_approved_facts(vault_root)
    print(f"  Found {len(facts)} approved durable facts in Memory-Review.")

    # 2. Sync to native memory target
    if not args.preamble_only:
        target_mem = detect_hermes_memory_target(vault_root)
        print(f"  Target Hermes Memory File: {target_mem}")
        sync_facts_to_memory(target_mem, facts, dry_run=args.dry_run)

    # 3. Generate context preamble
    generate_context_preamble(vault_root, facts, dry_run=args.dry_run)
    print("✅ Sync and context generation complete.")

if __name__ == "__main__":
    main()
