#!/usr/bin/env python3
"""
link_daily_archives.py

Smart knowledge-graph enricher for Hermes Brain vault.
Scans daily archive session notes and intelligently connects substantive user
conversations to relevant Domain MOCs, Projects, and Memory Review hubs.
Ignores background automated cron logs to keep the graph high-signal.
"""

import os
import re

VAULT_DIR = r"C:\Users\mistr\OneDrive - Mistry Siddh\27. Hermes Agent Vault\Brain\Hermes Brain"
DAILY_DIR = os.path.join(VAULT_DIR, "04-Archives", "Daily")

TOPIC_RULES = [
    {
        "name": "Cybersecurity",
        "link": "[[03-Resources/MOCs/Cybersecurity-MOC|Cybersecurity Framework MOC]]",
        "keywords": [r"\bcybersecurity\b", r"\bcve-\d+", r"\bpenetration test", r"\bvulnerability\b", r"\bcobalt strike\b", r"\bred-team", r"\bsecurity-auditor\b", r"\bphishing\b"]
    },
    {
        "name": "AI & Machine Learning",
        "link": "[[03-Resources/MOCs/AI-ML-MOC|AI/ML Workflows MOC]]",
        "keywords": [r"\bllm\b", r"\bmodels?\b", r"\bprompt\b", r"\btinysid\b", r"\btinyllama\b", r"\blora\b", r"\bollama\b", r"\bhugging ?face\b", r"\btransformer\b", r"\binference\b", r"\bembeddings?\b"]
    },
    {
        "name": "Agentic Architecture",
        "link": "[[03-Resources/MOCs/Agentic-Architecture-MOC|Agentic Architecture MOC]]",
        "keywords": [r"\bagentic\b", r"\bsubagent\b", r"\borchestrat", r"\bdelegat", r"\bmulti-agent\b", r"\bopenclaw\b", r"\bhermes agent\b", r"\bpersona\b"]
    },
    {
        "name": "Technology Stack & Infrastructure",
        "link": "[[03-Resources/MOCs/Technology-Stack-MOC|Technology Stack MOC]]",
        "keywords": [r"\bdocker\b", r"\bkubernetes\b", r"\blinux\b", r"\bdietpi\b", r"\braspberry pi\b", r"\bwaveshare\b", r"\bnginx\b", r"\bsystemd\b", r"\bsamba\b", r"\bhyper-v\b"]
    },
    {
        "name": "Memory Review & Staging",
        "link": "[[04-Archives/Memory-Review/TEMPLATE|Memory Review Criteria]]",
        "keywords": [r"\bsupermemory\b", r"\bconsolidat", r"\bcandidate fact\b", r"\bdurable fact\b", r"\bpreamble\b"]
    },
    {
        "name": "User Profile & Alignment",
        "link": "[[02-Areas/User-Profile|User Profile & Boundaries]]",
        "keywords": [r"\bnisha\b", r"\bpersonality judgment\b", r"\buser profile\b", r"\balignment\b"]
    },
    {
        "name": "Projects & Engineering Setup",
        "link": "[[01-Projects/Hermes-Agent-Vault-Setup|Hermes-Agent-Vault-Setup]]",
        "keywords": [r"\bqms\b", r"\bmace\b", r"\bmsil\b", r"\bmaruti\b"]
    }
]

def process_daily_archives(dry_run=False):
    processed = 0
    enriched = 0
    total_links_added = 0

    for root, _, files in os.walk(DAILY_DIR):
        for f in files:
            if not f.endswith(".md"):
                continue
            if f.startswith("cron_"):
                continue
            if f in ["README.md", "Timeline.md", "Chat-Correlation.md"]:
                continue
            if "hourly-weather" in f.lower() or "weather-updates" in f.lower():
                continue

            file_path = os.path.join(root, f)
            try:
                with open(file_path, "r", encoding="utf-8") as fp:
                    content = fp.read()
            except Exception:
                continue

            processed += 1
            if len(content) < 800:
                continue

            matched_links = []
            lower_content = content.lower()

            for rule in TOPIC_RULES:
                target_base = rule["link"].split("|")[0].strip("[ ]")
                if target_base.lower() in lower_content:
                    continue

                for kw in rule["keywords"]:
                    if re.search(kw, lower_content):
                        matched_links.append(rule["link"])
                        break

            if not matched_links:
                continue

            # Limit to top 3 most relevant domain links per session to prevent over-clustering
            matched_links = matched_links[:3]

            if "## 🔗 Knowledge Graph Connections" in content:
                insert_idx = content.find("## 🔗 Knowledge Graph Connections") + len("## 🔗 Knowledge Graph Connections\n")
                new_lines = "\n".join(f"- {lnk}" for lnk in matched_links) + "\n"
                new_content = content[:insert_idx] + new_lines + content[insert_idx:]
            else:
                footer = "\n\n---\n## 🔗 Knowledge Graph Connections\n" + "\n".join(f"- {lnk}" for lnk in matched_links) + "\n"
                new_content = content.rstrip() + footer

            if not dry_run:
                try:
                    with open(file_path, "w", encoding="utf-8") as fp:
                        fp.write(new_content)
                except Exception as e:
                    print(f"Error writing {f}: {e}")
                    continue

            enriched += 1
            total_links_added += len(matched_links)

    status = "DRY RUN COMPLETE" if dry_run else "ENRICHMENT COMPLETE"
    print(f"[{status}] Processed: {processed} user sessions | Enriched: {enriched} sessions | Total links added: {total_links_added}")
    return enriched, total_links_added

if __name__ == "__main__":
    import sys
    dry = "--dry-run" in sys.argv
    process_daily_archives(dry_run=dry)
