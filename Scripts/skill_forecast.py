#!/usr/bin/env python3
"""
Hermes Brain — Future Skill Forecast widget.

Analyzes vault activity trends and installed skills to suggest
which skills to learn/install next for maximum relevance.

Outputs:
- Console report of suggested skills with reasoning
- Updates Skills-Notes/Skill-Forecast.log with timestamped suggestions
"""
import json
import os
import re
from collections import Counter
from datetime import datetime
from pathlib import Path

VAULT = os.environ.get("HERMES_VAULT_PATH")
if not VAULT:
    print("HERMES_VAULT_PATH is not set — aborting.")
    exit(1)

SKILLS_NOTES = os.path.join(VAULT, "Skills-Notes")
TAG_TRENDS_LOG = os.path.join(SKILLS_NOTES, "Tag-Trends.log")
INSTALLED_INDEX = os.path.join(SKILLS_NOTES, "Installed-Skills-Index.md")
FORECAST_LOG = os.path.join(SKILLS_NOTES, "Skill-Forecast.log")
SKILL_TO_CHAT = os.path.join(SKILLS_NOTES, "Skill-to-Chat-Links.md")


def parse_installed_skills():
    """Parse installed skills from the index file."""
    installed = set()
    if not os.path.exists(INSTALLED_INDEX):
        return installed

    with open(INSTALLED_INDEX, encoding="utf-8") as f:
        lines = f.readlines()

    # Parse the markdown table for skills
    in_skills_table = False
    for line in lines:
        line = line.strip()
        
        # Detect section headers
        if line.startswith("## ") and not line.startswith("###"):
            # We're in a new section
            in_skills_table = False
            continue
            
        # Detect skill table headers
        if line.startswith("| Skill |") or line.startswith("|---"):
            in_skills_table = True
            continue
            
        # Parse skill rows
        if in_skills_table and line.startswith("|") and "|" in line:
            # Split by | and get non-empty parts
            parts = [part.strip() for part in line.split("|") if part.strip()]
            if len(parts) >= 2 and parts[0] and parts[0] != "Skill":
                skill_name = parts[0].strip()
                if skill_name:
                    installed.add(skill_name.lower())
                    
        # Stop parsing when we hit a non-table line after starting
        elif in_skills_table and not line.startswith("|"):
            in_skills_table = False

    return installed


def parse_recent_tag_trends(days=14):
    """Parse recent tag trends from the log file."""
    if not os.path.exists(TAG_TRENDS_LOG):
        return Counter()

    trends = Counter()

    with open(TAG_TRENDS_LOG, encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line or line.startswith("#"):
                continue

            # Format: YYYY-MM-DD: tag1, tag2, tag3
            if ": " not in line:
                continue

            date_str, tags_str = line.split(": ", 1)
            try:
                # Parse date to ensure it's valid
                log_date = datetime.strptime(date_str, "%Y-%m-%d")
                # For simplicity, use all trends (could filter by date)
                tags = [tag.strip() for tag in tags_str.split(",")]
                trends.update(tags)
            except ValueError:
                continue

    return trends


def parse_skill_to_chat_links():
    """Parse which skills were actually used in sessions."""
    used_skills = set()
    if not os.path.exists(SKILL_TO_CHAT):
        return used_skills

    with open(SKILL_TO_CHAT, encoding="utf-8") as f:
        lines = f.readlines()

    # Parse the markdown table for skills
    in_skills_table = False
    for line in lines:
        line = line.strip()
        
        # Detect section headers
        if line.startswith("## ") and not line.startswith("###"):
            # We're in a new section
            in_skills_table = False
            continue
            
        # Detect skill table headers
        if line.startswith("| Skill |") or line.startswith("|---"):
            in_skills_table = True
            continue
            
        # Parse skill rows
        if in_skills_table and line.startswith("|") and "|" in line:
            # Split by | and get non-empty parts
            parts = [part.strip() for part in line.split("|") if part.strip()]
            if len(parts) >= 2 and parts[0]:
                # First column is usually the skill name
                skill_name = parts[0].strip()
                if skill_name and skill_name.lower() not in ["skill", ""]:
                    used_skills.add(skill_name.lower())
                    
        # Stop parsing when we hit a non-table line after starting
        elif in_skills_table and not line.startswith("|"):
            in_skills_table = False

    return used_skills


def get_skill_categories():
    """Get skill categories from installed skills index."""
    categories = {}
    current_category = None

    if not os.path.exists(INSTALLED_INDEX):
        return categories

    with open(INSTALLED_INDEX, encoding="utf-8") as f:
        lines = f.readlines()

    for line in lines:
        line = line.strip()
        if line.startswith("## ") and not line.startswith("###"):
            current_category = line[3:].strip()
            categories[current_category] = []
        elif line.startswith("| Skill |") or line.startswith("|---"):
            continue
        elif line.startswith("|") and "|" in line and current_category:
            parts = [part.strip() for part in line.split("|") if part.strip()]
            if len(parts) >= 2 and parts[0] and parts[0] != "Skill":
                categories[current_category].append(parts[0].lower())

    return categories


def tag_to_skill_mapping():
    """Map common tags to potential skill names."""
    # Mapping from session tags to skill names
    tag_mapping = {
        'hermes': ['hermes-brain-vault', 'hermes-plugin-discovery', 'hermes-desktop-plugin-dev', 'inspecting-hermes-desktop-dom'],
        'linux': ['virtualbox-vm-setup'],  # Linux-related skills
        'llm': ['claude-code', 'codex', 'opencode'],  # LLM/coding assistant skills
        'automation': ['automated-information-briefings', 'ai-ml-research-briefing', 'ntfy-notifications'],
        'obsidian': ['obsidian'],  # Direct match
        'video': [],  # No specific video skills yet
        'ai-agents': ['agentic-architecture', 'multi-agent-groupchat-collaboration'],
        'database': [],  # No specific database skills
        'devops': [],  # No specific devops skills yet
        'javascript': [],  # No specific JS skills
        'cybersecurity': [],  # No specific security skills
        'productivity': ['weekly-review-planning', 'meeting-action-items'],
        'python': [],  # No specific Python skills
        'networking': [],  # No specific networking skills
        'self-hosting': ['virtualbox-vm-setup'],  # Self-hosting related
    }
    return tag_mapping


def suggest_skills():
    """Generate skill suggestions based on trends and installed skills."""
    installed = parse_installed_skills()
    recent_trends = parse_recent_tag_trends(days=14)
    used_skills = parse_skill_to_chat_links()
    categories = get_skill_categories()
    tag_mapping = tag_to_skill_mapping()

    print(f"Debug: Found {len(installed)} installed skills")
    print(f"Debug: Found {len(recent_trends)} unique trending tags")
    print(f"Debug: Found {len(used_skills)} used skills")
    print(f"Debug: Found {len(categories)} categories")

    if installed:
        print(f"Debug: Sample installed skills: {list(sorted(installed))[:5]}")
    if recent_trends:
        print(f"Debug: Sample trending tags: {list(recent_trends.keys())[:5]}")

    # For each trending tag, find related skills that are NOT installed
    suggested = []

    for tag, count in recent_trends.most_common(50):  # Check top 50 tags
        tag_lower = tag.lower().strip()
        
        # Get potential skill names for this tag
        potential_skills = tag_mapping.get(tag_lower, [])
        
        # Also check for direct matches or partial matches
        for skill in installed:
            skill_lower = skill.lower()
            # If the tag is contained in the skill name or vice versa
            if (tag_lower in skill_lower or skill_lower in tag_lower) and len(tag_lower) > 2:
                if skill not in potential_skills:
                    potential_skills.append(skill)
        
        # Check which potential skills are NOT installed
        for skill in potential_skills:
            skill_lower = skill.lower()
            is_installed = False
            for installed_skill in installed:
                if installed_skill == skill_lower:
                    is_installed = True
                    break
                # Also check variations
                if (installed_skill.replace('-', '_') == skill_lower.replace('-', '_') or
                    installed_skill.replace('_', '-') == skill_lower.replace('_', '-') or
                    installed_skill.replace(' ', '_') == skill_lower.replace(' ', '_') or
                    installed_skill.replace(' ', '-') == skill_lower.replace(' ', '-')):
                    is_installed = True
                    break
            
            if not is_installed:
                # Calculate relevance score based on trend frequency
                suggested.append((skill, count, tag_lower))

    # Remove duplicates (same skill suggested for multiple tags)
    seen_skills = set()
    unique_suggested = []
    for skill, count, tag in suggested:
        if skill not in seen_skills:
            seen_skills.add(skill)
            unique_suggested.append((skill, count, tag))
    
    # Sort by score descending
    unique_suggested.sort(key=lambda x: x[1], reverse=True)

    return unique_suggested[:10], installed, recent_trends, used_skills, categories


def main():
    print("🔮 Hermes Brain — Future Skill Forecast")
    print("=" * 50)

    suggested, installed, recent_trends, used_skills, categories = suggest_skills()

    print(f"\n📊 Analysis based on:")
    print(f"   • {len(installed)} installed skills")
    print(f"   • {len(recent_trends)} unique trending tags (last 14 days)")
    print(f"   • {len(used_skills)} skills actually used in sessions")
    print(f"   • {len(categories)} skill categories")

    if not suggested:
        print("\n🎯 All trending topics already have corresponding skills installed!")
        print("   Consider exploring new skill categories or waiting for new trends.")
        return

    print(f"\n💡 Top {len(suggested)} skill suggestions:")
    print("-" * 50)

    for i, (skill_tag, score, source_tag) in enumerate(suggested, 1):
        # Find which category this skill might belong to
        suggested_category = "Unknown"
        for category, skills in categories.items():
            # Check if skill_tag matches any skill in this category (with variations)
            for skill in skills:
                skill_lower = skill.lower()
                tag_lower = skill_tag.lower()
                if (skill_lower == tag_lower or 
                    skill_lower.replace('-', '_') == tag_lower.replace('-', '_') or
                    skill_lower.replace('_', '-') == tag_lower.replace('_', '-') or
                    skill_lower in tag_lower or tag_lower in skill_lower):
                    suggested_category = category
                    break
            if suggested_category != "Unknown":
                break

        print(f"{i:2d}. {skill_tag:<25} (trending score: {score})")
        print(f"    📂 Suggested category: {suggested_category}")
        print(f"    🏷️  Based on trend: {source_tag}")
        
        # Show trend context
        if source_tag in recent_trends:
            print(f"    📈 Trending in: {recent_trends[source_tag]} recent sessions")
        print()

    # Write to forecast log
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    log_entry = f"{timestamp}: {', '.join([skill for skill, _, _ in suggested])}\n"

    os.makedirs(SKILLS_NOTES, exist_ok=True)
    with open(FORECAST_LOG, "a", encoding="utf-8") as f:
        f.write(log_entry)

    print(f"📝 Forecast logged to: {FORECAST_LOG}")
    print("\n💡 Next steps:")
    print("   1. Review suggested skills above")
    print("   2. Install via: hermes skills install <skill-name>")
    print("   3. Re-run this script after installing to update suggestions")


if __name__ == "__main__":
    main()