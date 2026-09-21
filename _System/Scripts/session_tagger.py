#!/usr/bin/env python3
"""
Hermes Brain — automated session tagging & topic tracking.

Extracts topics/themes from archived session markdown files and maintains:
- Per-session tags in manifest.jsonl
- Global tag cloud with counts in Skills-Notes/Tag-Cloud.log
- Daily tag trends in Skills-Notes/Tag-Trends.log

Designed to be called from hourly_archive.py after sessions are moved into
YYYY/MM/DD/ directories. Uses lightweight rule-based keyword extraction
(no external API, no heavy ML deps).
"""

import json
import os
import re
from collections import Counter
from datetime import datetime
from pathlib import Path

# ─── Configuration ──────────────────────────────────────────────────────────

VAULT = os.environ.get("HERMES_VAULT_PATH")
if not VAULT:
    print("HERMES_VAULT_PATH is not set — aborting.")
    exit(1)

# Normalize VAULT path (handle forward/backward slashes from shell,
# and convert /c/... style paths from git-bash to C:\...)
# git-bash /c/Users/... -> C:\Users\...
if VAULT.startswith("/") and len(VAULT) > 2 and VAULT[2] == "/":
    drive = VAULT[1].upper()
    VAULT = drive + ":" + VAULT[2:].replace("/", "\\")
else:
    VAULT = VAULT.replace("/", "\\")
VAULT = os.path.normpath(VAULT)

daily_cand = os.path.join(VAULT, "04-Archives", "Daily")
DAILY = daily_cand if os.path.exists(daily_cand) else os.path.join(VAULT, "Daily")
MANIFEST = os.path.join(DAILY, "manifest.jsonl")

tag_dir = os.path.join(VAULT, "04-Archives", "Audit-Reports") if os.path.exists(os.path.join(VAULT, "04-Archives", "Audit-Reports")) else os.path.join(VAULT, "Skills-Notes")
TAG_CLOUD_LOG = os.path.join(tag_dir, "Tag-Cloud.log")
TAG_TRENDS_LOG = os.path.join(tag_dir, "Tag-Trends.log")

# Ensure output directories exist
os.makedirs(os.path.dirname(TAG_CLOUD_LOG), exist_ok=True)
os.makedirs(os.path.dirname(TAG_TRENDS_LOG), exist_ok=True)

# ─── Topic extraction patterns ──────────────────────────────────────────────

# High-signal keywords grouped by semantic theme
TOPIC_PATTERNS = {
    "ai-agents": [
        r"\bagent\b", r"\bautonomous\b", r"\bagentic\b", r"\bmulti.?agent\b",
        r"\bcrewai\b", r"\bautogen\b", r"\blanggraph\b", r"\bhierarchical\b",
    ],
    "llm": [
        r"\bllm\b", r"\blarge language model\b", r"\btransformer\b", r"\bgpt\b",
        r"\bclaude\b", r"\bgemini\b", r"\bllama\b", r"\bmistral\b", r"\bphi\b",
        r"\bnemotron\b", r"\bfine.?tune\b", r"\bprompt\b", r"\bcompletion\b",
        r"\btokens?\b", r"\bcontext window\b", r"\binference\b",
    ],
    "hermes": [
        r"\bhermes\b", r"\bopencrawl?\b", r"\bnisha\b", r"\bmemory vault\b",
        r"\bbrain vault\b", r"\bdashboard\b", r"\bskill\b", r"\bplugin\b",
        r"\barchive\b", r"\bsession\b", r"\bcron\b",
    ],
    "linux": [
        r"\blinux\b", r"\bbash\b", r"\bshell\b", r"\bterminal\b", r"\bssh\b",
        r"\bdocker\b", r"\bcontainer\b", r"\bkubernetes\b", r"\bk8s\b",
        r"\bnginx\b", r"\bsystemd\b", r"\bcron\b", r"\bgrep\b", r"\bsed\b",
        r"\bawk\b", r"\btmux\b", r"\bzsh\b",
    ],
    "cybersecurity": [
        r"\bsecurity\b", r"\bpenetration\b", r"\bpentest\b", r"\bvulnerab\b",
        r"\bexploit\b", r"\bcve\b", r"\bmalware\b", r"\bforensic\b",
        r"\bsiem\b", r"\bids\b", r"\bips\b", r"\bfirewall\b", r"\bencryption\b",
        r"\bcert\b", r"\btls\b", r"\bssl\b", r"\bhash\b", r"\bpassword\b",
    ],
    "devops": [
        r"\bdevops\b", r"\bci/?cd\b", r"\bgithub actions?\b", r"\bgitlab\b",
        r"\bjenkins\b", r"\bpipeline\b", r"\bdeploy\b", r"\bterraform\b",
        r"\bansible\b", r"\bhelm\b", r"\bargocd\b", r"\bmonitoring\b",
        r"\bobservability\b", r"\blogging\b", r"\bmetrics\b",
    ],
    "python": [
        r"\bpython\b", r"\bpy\b", r"\bpip\b", r"\bvenv\b", r"\bconda\b",
        r"\bpythonic\b", r"\basync\b", r"\bawait\b", r"\bdecorator\b",
        r"\bdataclass\b", r"\btype.?hint\b", r"\bpydantic\b", r"\bfastapi\b",
        r"\bflask\b", r"\bdjango\b", r"\bnumpy\b", r"\bpandas\b",
    ],
    "javascript": [
        r"\bjavascript\b", r"\bjs\b", r"\bnode\b", r"\bnpm\b", r"\byarn\b",
        r"\btypescript\b", r"\bts\b", r"\breact\b", r"\bvue\b", r"\bsvelte\b",
        r"\bnext\.?js\b", r"\bwebpack\b", r"\bvite\b", r"\besbuild\b",
        r"\bdeno\b", r"\bbun\b",
    ],
    "database": [
        r"\bsql\b", r"\bpostgres\b", r"\bmysql\b", r"\bsqlite\b", r"\bmongo\b",
        r"\bredis\b", r"\bnosql\b", r"\bdatabase\b", r"\bquery\b", r"\bindex\b",
        r"\bmigration\b", r"\borm\b", r"\bprisma\b", r"\bsqlalchemy\b",
    ],
    "automation": [
        r"\bautomat\b", r"\bscript\b", r"\bworkflow\b", r"\bschedule\b",
        r"\bcron\b", r"\btrigger\b", r"\bwebhook\b", r"\bapi\b", r"\bhook\b",
        r"\bintegration\b", r"\bzapier\b", r"\bn8n\b",
    ],
    "networking": [
        r"\bnetwork\b", r"\bip\b", r"\bdns\b", r"\bvpn\b", r"\bproxy\b",
        r"\bload balanc\b", r"\brouter\b", r"\bswitch\b", r"\bsubnet\b",
        r"\bport\b", r"\bfirewall\b", r"\bwireguard\b", r"\btailscale\b",
    ],
    "self-hosting": [
        r"\bself.?host\b", r"\bhomelab\b", r"\bnas\b", r"\braid\b",
        r"\bzfs\b", r"\bproxmox\b", r"\besxi\b", r"\bhypervisor\b",
        r"\bvm\b", r"\bvirtualbox\b", r"\bvmware\b", r"\bunraid\b",
        r"\btruenas\b", r"\bportainer\b",
    ],
    "obsidian": [
        r"\bobsidian\b", r"\bvault\b", r"\bdataview\b", r"\bdataviewjs\b",
        r"\bcanvas\b", r"\bgraph\b", r"\bbacklink\b", r"\bfrontmatter\b",
        r"\btemplater\b", r"\bcalendar\b", r"\bdaily note\b", r"\bplugin\b",
    ],
    "video": [
        r"\byoutube\b", r"\bvideo\b", r"\bstream\b", r"\brecord\b",
        r"\bedit\b", r"\bffmpeg\b", r"\bobs\b", r"\bthumbnail\b",
        r"\btitle\b", r"\bdescription\b", r"\balgorithm\b", r"\bviews\b",
        r"\bsubscriber\b", r"\bmoneti\b",
    ],
    "productivity": [
        r"\bproductiv\b", r"\bnote.?tak\b", r"\bsecond brain\b", r"\bzettel\b",
        r"\btask\b", r"\bkanban\b", r"\btodo\b", r"\bproject\b",
        r"\bplan\b", r"\bgoal\b", r"\bhabit\b", r"\broutine\b", r"\bfocus\b",
    ],
}

# Compile all patterns
COMPILED_PATTERNS = {
    topic: [re.compile(p, re.IGNORECASE) for p in patterns]
    for topic, patterns in TOPIC_PATTERNS.items()
}

# ─── Core functions ─────────────────────────────────────────────────────────


def extract_topics_from_text(text: str, max_topics: int = 5) -> list[str]:
    """
    Extract topics from text using keyword pattern matching.
    Returns list of topic names sorted by match count (descending).
    """
    text_lower = text.lower()
    scores = {}

    for topic, patterns in COMPILED_PATTERNS.items():
        count = 0
        for pattern in patterns:
            count += len(pattern.findall(text_lower))
        if count > 0:
            scores[topic] = count

    # Sort by score descending, take top N
    sorted_topics = sorted(scores.items(), key=lambda x: x[1], reverse=True)
    return [topic for topic, _ in sorted_topics[:max_topics]]


def extract_topics_from_session_file(session_path: str) -> list[str]:
    """Extract topics from a session markdown file."""
    try:
        with open(session_path, encoding="utf-8") as f:
            content = f.read(5000)  # Read first 5KB (frontmatter + start of content)
    except Exception:
        return []

    # Extract frontmatter and first part of content
    # Frontmatter is between --- lines
    fm_match = re.match(r"^---\n(.*?)\n---", content, re.DOTALL)
    if fm_match:
        frontmatter = fm_match.group(1)
        # Also get some body content
        body = content[fm_match.end(): fm_match.end() + 2000]
        text = frontmatter + "\n" + body
    else:
        text = content[:3000]

    # Also extract title specifically
    title_match = re.search(r"title:\s*\"([^\"]*)\"", text)
    if title_match:
        text = title_match.group(1) + "\n" + text

    return extract_topics_from_text(text)


def load_existing_tag_cloud() -> Counter:
    """Load existing tag cloud from log file."""
    cloud = Counter()
    if os.path.exists(TAG_CLOUD_LOG):
        try:
            with open(TAG_CLOUD_LOG, encoding="utf-8") as f:
                for line in f:
                    line = line.strip()
                    if not line or line.startswith("#"):
                        continue
                    # Format: tag: count
                    parts = line.split(": ")
                    if len(parts) == 2:
                        try:
                            cloud[parts[0]] = int(parts[1])
                        except ValueError:
                            pass
        except Exception:
            pass
    return cloud


def save_tag_cloud(cloud: Counter):
    """Save tag cloud to log file, sorted by count descending."""
    with open(TAG_CLOUD_LOG, "w", encoding="utf-8") as f:
        f.write("# Tag Cloud — updated " + datetime.now().isoformat() + "\n")
        f.write("# Format: tag: count\n")
        for tag, count in cloud.most_common():
            f.write(f"{tag}: {count}\n")


def append_tag_trend(date_str: str, tags: list[str]):
    """Append daily tag trend entry."""
    if not tags:
        return
    tag_str = ", ".join(tags)
    with open(TAG_TRENDS_LOG, "a", encoding="utf-8") as f:
        f.write(f"{date_str}: {tag_str}\n")


def update_manifest_with_tags():
    """Read manifest, add tags to entries that don't have them, rewrite manifest."""
    if not os.path.exists(MANIFEST):
        return

    records = []
    with open(MANIFEST, encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            try:
                rec = json.loads(line)
            except json.JSONDecodeError:
                continue
            records.append(rec)

    updated = False
    today = datetime.now().strftime("%Y-%m-%d")

    for rec in records:
        if "tags" in rec and rec["tags"]:
            continue  # Already tagged

        path = rec.get("path")
        if not path:
            continue

        # Normalize path (handle both forward and back slashes)
        path = path.replace(chr(92), "/")
        if not os.path.exists(path):
            continue

        tags = extract_topics_from_session_file(path)
        if tags:
            rec["tags"] = tags
            updated = True
            # Update tag cloud
            cloud = load_existing_tag_cloud()
            for tag in tags:
                cloud[tag] += 1
            save_tag_cloud(cloud)
            # Record daily trend
            append_tag_trend(today, tags)

    if updated:
        # Rewrite manifest with tags
        with open(MANIFEST, "w", encoding="utf-8") as f:
            for rec in records:
                f.write(json.dumps(rec) + "\n")
        print(f"Tagged {sum(1 for r in records if 'tags' in r and r['tags'])} session(s) in manifest.")


def main():
    print("🏷️  Session tagging & topic tracking")
    update_manifest_with_tags()

    # Print current tag cloud summary
    cloud = load_existing_tag_cloud()
    if cloud:
        print(f"\n📊 Current tag cloud ({len(cloud)} unique tags):")
        for tag, count in cloud.most_common(15):
            print(f"  {tag}: {count}")
    else:
        print("\n📊 Tag cloud is empty — will populate as sessions are tagged.")


if __name__ == "__main__":
    main()