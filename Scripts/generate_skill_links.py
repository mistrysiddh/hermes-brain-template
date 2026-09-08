#!/usr/bin/env python3
"""
generate_skill_links.py — regenerates Skills-Notes/Skill-to-Chat-Links.md.

Skills-Notes/README.md documents this file as "which archived chat sessions
actually invoked which skill, auto-generated from Daily/" — this script is
that generator (mechanical only, stdlib-only, cross-platform, in the spirit
of consolidate_memory.py).

Two matching strategies, auto-selected per run:
  1. Tool-call mode (used when Skills-Notes/Installed-Skills-Index.md
     exists and parses): the accurate method. Scans Daily/**/*.md for
     genuine `skill_view`/`skill_manage` TOOL CALLS naming an installed
     skill (parses each session's "## Tool calls" JSON fence directly,
     rather than regexing the escaped text), not just catalog listings
     from `skills_list`, which would dump every skill name into every
     matching session and cause false positives. Categories come from
     Installed-Skills-Index.md's own "## category" grouping.
  2. Prose mode (fallback, e.g. a freshly-installed template vault with no
     populated skill catalog yet): treats each Skills-Notes/*.md file as a
     documented skill (per Skills-Notes/README.md's own convention of "one
     note per skill area actually used by the team") and text-matches its
     filename stem against session content.

Usage:
    python generate_skill_links.py <vault_root>

Exit code 0 always (reporting/staging tool, not a gate).
"""
import sys
import os
import re
import json
from datetime import datetime, timezone

DAILY_EXCLUDE = {"readme", "manifest", "timeline", "chat-correlation"}
SKILLS_NOTES_EXCLUDE = {
    "readme",
    "dataview-query-library",
    "installed-skills-index",
    "team-profiles-index",
    "skill-to-chat-links",
}

# A "## Tool calls" fence holds a JSON array of {"function": {"name": ...,
# "arguments": "<json-encoded string>"}} entries. Actually parsing this
# (rather than regexing the escaped text) survives whatever whitespace/key-
# order variation different Hermes/session-export versions produce - a
# regex over the raw escaped string silently under-matched real sessions
# whose arguments used "name": "x" (space after colon) instead of
# "name":"x". Deliberately excludes skills_list (a full-catalog dump, not a
# genuine per-skill invocation).
JSON_FENCE_RE = re.compile(r"```json\s*\n(.*?)\n```", re.S)
CATEGORY_HEADER_RE = re.compile(r"^##\s+(\S.*)$", re.M)
CATALOG_ENTRY_RE = re.compile(r"^-\s+\*\*([a-zA-Z0-9_-]+)\*\*")


def read(path):
    if not os.path.exists(path):
        return ""
    with open(path, "r", encoding="utf-8", errors="ignore") as f:
        return f.read()


def extract_invoked_skills(text):
    """Genuine skill_view/skill_manage invocations in one session's tool-call fences."""
    skills = set()
    for block in JSON_FENCE_RE.findall(text):
        try:
            calls = json.loads(block)
        except ValueError:
            continue
        if not isinstance(calls, list):
            continue
        for call in calls:
            if not isinstance(call, dict):
                continue
            fn = call.get("function")
            if not isinstance(fn, dict) or fn.get("name") not in ("skill_view", "skill_manage"):
                continue
            args_raw = fn.get("arguments")
            if not isinstance(args_raw, str):
                continue
            try:
                args = json.loads(args_raw)
            except ValueError:
                continue
            name = args.get("name") if isinstance(args, dict) else None
            if name:
                skills.add(name)
    return skills


def parse_skill_catalog(index_path):
    """Installed-Skills-Index.md's '## category' + '- **skill** — ...' -> {skill: category}."""
    text = read(index_path)
    if not text:
        return None
    catalog = {}
    current_category = "uncategorized"
    for line in text.splitlines():
        m = CATEGORY_HEADER_RE.match(line)
        if m and m.group(1).strip().lower() != "table of contents":
            current_category = m.group(1).strip()
            continue
        m = CATALOG_ENTRY_RE.match(line)
        if m:
            catalog[m.group(1)] = current_category
    return catalog or None


def find_skill_notes(skills_dir):
    """Prose-mode vocabulary: skill name -> display label, one per documented skill note."""
    skills = {}
    if not os.path.isdir(skills_dir):
        return skills
    for fname in sorted(os.listdir(skills_dir)):
        if not fname.lower().endswith(".md"):
            continue
        stem = fname[:-3]
        if stem.lower() in SKILLS_NOTES_EXCLUDE:
            continue
        text = read(os.path.join(skills_dir, fname))
        m = re.search(r"^#\s+(.+)$", text, re.M)
        label = m.group(1).strip() if m else stem
        skills[stem] = label
    return skills


def find_session_files(daily_dir):
    sessions = []
    if not os.path.isdir(daily_dir):
        return sessions
    for root, _, files in os.walk(daily_dir):
        for fname in files:
            if not fname.lower().endswith(".md"):
                continue
            stem = fname[:-3]
            if stem.lower() in DAILY_EXCLUDE:
                continue
            sessions.append(os.path.join(root, fname))
    return sessions


def skill_pattern(skill_name):
    # '-', '_', ' ' are interchangeable when matching a skill name in prose.
    flexible = re.sub(r"[-_ ]", "[-_ ]", re.escape(skill_name))
    return re.compile(rf"\b{flexible}\b", re.I)


def rel_wikilink(vault, path):
    rel = os.path.relpath(path, vault)[:-3]  # strip .md
    return rel.replace(os.sep, "/")


def render_header(vault, generated_note):
    return [
        "# Skill-to-Chat-Links",
        "",
        f"Regenerated {datetime.now(timezone.utc).isoformat()} by "
        f"`Scripts/generate_skill_links.py`. {generated_note}",
        "",
    ]


def render_tool_call_mode(vault, sessions, catalog, hits):
    by_category = {}
    for skill, paths in hits.items():
        category = catalog.get(skill, "uncategorized")
        by_category.setdefault(category, {})[skill] = paths

    total_skills = len(hits)
    total_links = sum(len(p) for p in hits.values())
    categories = sorted(by_category.keys(), key=str.lower)

    lines = render_header(
        vault,
        f"Scanned all {len(sessions)} archived files under `Daily/` for genuine "
        "`skill_view`/`skill_manage` TOOL CALLS naming an installed skill (not "
        "just catalog listings from `skills_list`, which dumps every skill name "
        "into every matching session and would give false positives). "
        "Categories come from [[Installed-Skills-Index]].",
    )

    if not hits:
        lines.append(
            "No genuine skill invocations found yet in `Daily/` — nothing to link."
        )
        return lines

    lines.append(
        f"**Skills genuinely invoked across archived chats: {total_skills}** "
        f"(grouped into {len(categories)} categories, {total_links} total links)"
    )
    lines.append("")
    lines.append("## Table of contents")
    lines.append("")
    for cat in categories:
        n = len(by_category[cat])
        lines.append(f"- [{cat}](#{re.sub(r'[^a-z0-9]+', '-', cat.lower()).strip('-')}) ({n} skill{'s' if n != 1 else ''})")
    lines.append("")
    lines.append("---")
    lines.append("")

    for cat in categories:
        lines.append(f"## {cat}")
        lines.append("")
        for skill in sorted(by_category[cat].keys()):
            lines.append(f"### {skill}")
            lines.append("")
            for session_path in sorted(by_category[cat][skill]):
                link = rel_wikilink(vault, session_path)
                fname = os.path.basename(session_path)
                lines.append(f"- [[{link}|{fname}]]")
            lines.append("")

    return lines


def render_prose_mode(vault, skills, sessions, matches):
    lines = render_header(
        vault,
        f"Correlates each documented skill note in [[README|Skills-Notes]] "
        f"against every archived session in [[../Daily/README|Daily/]] "
        "(scanned by filename mention) that mentions it by name. No "
        "Installed-Skills-Index.md was found, so this used prose matching "
        "instead of scanning for skill_view/skill_manage tool calls "
        "directly - see the script's own docstring for when each mode kicks in.",
    )

    if not skills:
        lines.append(
            "No skill notes found yet. Add one markdown file per skill area "
            "actually used by the team to `Skills-Notes/` (e.g. `arxiv.md`), "
            "then re-run this script — see [[README]] for the convention."
        )
    elif not sessions:
        lines.append(
            "No archived sessions found under `Daily/` yet — this vault "
            "starts empty on purpose. Once your Hermes agent's archiving "
            "cron job starts exporting sessions, re-run this script (or "
            "schedule it alongside `consolidate_memory.py`) to populate "
            "the links below."
        )
    else:
        any_matches = False
        for stem in sorted(skills, key=str.lower):
            hits = matches[stem]
            if not hits:
                continue
            any_matches = True
            lines.append(f"## {skills[stem]}")
            for session_path in sorted(hits):
                lines.append(f"- [[{rel_wikilink(vault, session_path)}]]")
            lines.append("")
        if not any_matches:
            lines.append(
                "No sessions matched any documented skill name yet — "
                "nothing to link."
            )

    return lines


def main():
    if len(sys.argv) < 2:
        print("usage: generate_skill_links.py <vault_root>")
        sys.exit(1)
    vault = sys.argv[1]
    skills_dir = os.path.join(vault, "Skills-Notes")
    daily_dir = os.path.join(vault, "Daily")
    out_path = os.path.join(skills_dir, "Skill-to-Chat-Links.md")

    sessions = find_session_files(daily_dir)
    catalog = parse_skill_catalog(os.path.join(skills_dir, "Installed-Skills-Index.md"))

    if catalog:
        hits = {}
        for session_path in sessions:
            text = read(session_path)
            for skill in extract_invoked_skills(text):
                hits.setdefault(skill, set()).add(session_path)
        lines = render_tool_call_mode(vault, sessions, catalog, hits)
        total_skills = len(hits)
        total_links = sum(len(p) for p in hits.values())
        mode = "tool-call"
    else:
        skills = find_skill_notes(skills_dir)
        matches = {stem: [] for stem in skills}
        for session_path in sessions:
            text = read(session_path)
            for stem in skills:
                if skill_pattern(stem).search(text):
                    matches[stem].append(session_path)
        lines = render_prose_mode(vault, skills, sessions, matches)
        total_skills = sum(1 for v in matches.values() if v)
        total_links = sum(len(v) for v in matches.values())
        mode = "prose"

    os.makedirs(skills_dir, exist_ok=True)
    with open(out_path, "w", encoding="utf-8") as f:
        f.write("\n".join(lines) + "\n")

    print(
        f"[generate_skill_links] mode={mode}, {len(sessions)} session(s) scanned, "
        f"{total_skills} skill(s) with hits, {total_links} link(s) written "
        "to Skills-Notes/Skill-to-Chat-Links.md"
    )


if __name__ == "__main__":
    main()
