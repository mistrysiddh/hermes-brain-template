#!/usr/bin/env python3
"""
Hermes Brain — session enrichment (optional).

Adds a simple summary frontmatter to archived session markdown files
that don't already have one. The summary is a heuristic: first non-empty
line of content (or first 200 characters) truncated to one line.

Intended to be run manually or via cron after archiving, to make sessions
more glanceable and to provide seed data for future memory pipeline steps.

Only standard library is used — no external dependencies.
"""
import os
import re
import sys
from datetime import datetime

def resolve_vault(explicit_vault=None):
    if explicit_vault and os.path.isdir(explicit_vault):
        return os.path.abspath(explicit_vault)
    script_dir = os.path.dirname(os.path.abspath(__file__))
    cand_para = os.path.abspath(os.path.join(script_dir, "..", ".."))
    if os.path.exists(os.path.join(cand_para, ".obsidian")) or os.path.exists(os.path.join(cand_para, "01-Projects")):
        return cand_para
    cand_flat = os.path.abspath(os.path.join(script_dir, ".."))
    if os.path.exists(os.path.join(cand_flat, ".obsidian")) or os.path.exists(os.path.join(cand_flat, "01-Projects")):
        return cand_flat
    env_vault = os.environ.get("HERMES_VAULT_PATH")
    if env_vault and os.path.exists(env_vault):
        return os.path.abspath(env_vault)
    return None


VAULT = resolve_vault()
daily_cand = os.path.join(VAULT, "04-Archives", "Daily") if VAULT else ""
DAILY = daily_cand if (daily_cand and os.path.exists(daily_cand)) else (os.path.join(VAULT, "Daily") if VAULT else "")
SUMMARY_FRONTMATTER_KEY = "summary"


def has_frontmatter(content):
    """Return True if content starts with a YAML frontmatter block."""
    return content.startswith('---\n')

def extract_frontmatter_and_body(content):
    """Split content into (frontmatter_dict, body_string)."""
    if not has_frontmatter(content):
        return {}, content
    # Find the end of the frontmatter (next '---' alone on a line)
    lines = content.split('\n')
    if len(lines) < 3 or not lines[0].strip() == '---':
        return {}, content
    fm_lines = []
    i = 1
    while i < len(lines):
        if lines[i].strip() == '---':
            i += 1
            break
        fm_lines.append(lines[i])
        i += 1
    frontmatter = '\n'.join(fm_lines)
    body = '\n'.join(lines[i:])
    # Parse very simple key:value frontmatter (we only care about summary)
    fm_dict = {}
    for line in frontmatter.split('\n'):
        if ':' in line:
            key, val = line.split(':', 1)
            fm_dict[key.strip()] = val.strip()
    return fm_dict, body

def set_frontmatter(fm_dict, body):
    """Return a string with YAML frontmatter and body."""
    lines = ['---']
    for key, val in fm_dict.items():
        lines.append(f'{key}: {val}')
    lines.append('---')
    lines.append(body)
    return '\n'.join(lines)

def generate_summary(body):
    """Heuristic: first non-empty line, trimmed to one line, max 200 chars."""
    for line in body.split('\n'):
        if line.strip():
            summary = line.strip()
            if len(summary) > 200:
                summary = summary[:200] + '...'
            return summary
    return "(no content)"

def process_file(filepath):
    """Read, enrich if needed, and write back."""
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            content = f.read()
    except Exception as e:
        print(f"  Failed to read {filepath}: {e}")
        return False

    fm_dict, body = extract_frontmatter_and_body(content)
    if SUMMARY_FRONTMATTER_KEY in fm_dict:
        # Already has a summary, skip
        return False

    summary = generate_summary(body)
    fm_dict[SUMMARY_FRONTMATTER_KEY] = summary
    new_content = set_frontmatter(fm_dict, body)

    if new_content == content:
        # No change
        return False

    try:
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(new_content)
        print(f"  Enriched {filepath}")
        return True
    except Exception as e:
        print(f"  Failed to write {filepath}: {e}")
        return False

def main():
    import argparse
    parser = argparse.ArgumentParser(description="Add summary frontmatter to session markdown files.")
    parser.add_argument('--path', default=DAILY, help='Root directory to search (default: Daily/)')
    parser.add_argument('--ext', default='.md', help='File extension to process (default: .md)')
    args = parser.parse_args()

    if not os.path.isdir(args.path):
        print(f"Error: {args.path} is not a directory.")
        sys.exit(1)

    enriched_count = 0
    total_count = 0
    for root, dirs, files in os.walk(args.path):
        for fname in files:
            if fname.endswith(args.ext):
                total_count += 1
                filepath = os.path.join(root, fname)
                if process_file(filepath):
                    enriched_count += 1

    print(f"\nProcessed {total_count} {args.ext} files, enriched {enriched_count}.")

if __name__ == "__main__":
    main()