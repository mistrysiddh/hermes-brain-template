#!/usr/bin/env python3
"""
Hermes Brain — Future Skill Forecast widget (Enhanced).

Analyzes vault activity trends and installed skills to suggest
which skills to learn/install next for maximum relevance.

Features:
- Command-line configurability (--days, --top, --no-log, --debug, --no-color)
- External tag->skill mapping (JSON file with fallback)
- Recency-weighted tag trends
- Skill gap analysis and complementary skill suggestions
- Skill health checks (imbalance detection)
- Better error handling and guidance
- Optional colorized output

Outputs:
- Console report of suggested skills with reasoning
- Updates Skills-Notes/Skill-Forecast.log with timestamped suggestions (unless --no-log)
"""
import json
import os
import re
import sys
import argparse
from collections import Counter, defaultdict
from datetime import datetime, timedelta
from pathlib import Path

# Try to import colorama for cross-platform color support
try:
    from colorama import Fore, Style, init as colorama_init
    colorama_init()
    COLOR_AVAILABLE = True
except ImportError:
    COLOR_AVAILABLE = False

# Constants
VAULT = os.environ.get("HERMES_VAULT_PATH")
if not VAULT:
    print("HERMES_VAULT_PATH is not set — aborting.", file=sys.stderr)
    sys.exit(1)

SKILLS_NOTES = os.path.join(VAULT, "Skills-Notes")
TAG_TRENDS_LOG = os.path.join(SKILLS_NOTES, "Tag-Trends.log")
INSTALLED_INDEX = os.path.join(SKILLS_NOTES, "Installed-Skills-Index.md")
FORECAST_LOG = os.path.join(SKILLS_NOTES, "Skill-Forecast.log")
SKILL_TO_CHAT = os.path.join(SKILLS_NOTES, "Skill-to-Chat-Links.md")
TAG_SKILL_MAP_JSON = os.path.join(os.path.dirname(__file__), "tag_skill_map.json")

# ANSI color codes (fallback if colorama not available)
if COLOR_AVAILABLE:
    GREEN = Fore.GREEN
    YELLOW = Fore.YELLOW
    RED = Fore.RED
    BLUE = Fore.BLUE
    CYAN = Fore.CYAN
    RESET = Style.RESET_ALL
else:
    GREEN = YELLOW = RED = BLUE = CYAN = RESET = ""

def parse_args():
    parser = argparse.ArgumentParser(
        description="Hermes Brain Future Skill Forecast - Suggest skills to learn based on vault activity."
    )
    parser.add_argument(
        "--days", type=int, default=14,
        help="Number of days to look back for tag trends (default: 14)"
    )
    parser.add_argument(
        "--top", type=int, default=10,
        help="Number of top suggestions to show (default: 10)"
    )
    parser.add_argument(
        "--no-log", action="store_true",
        help="Show suggestions without writing to the log file"
    )
    parser.add_argument(
        "--debug", action="store_true",
        help="Enable debug output"
    )
    parser.add_argument(
        "--no-color", action="store_true",
        help="Disable colorized output (overrides NO_COLOR env)"
    )
    return parser.parse_args()

def supports_color():
    """Check if color output is supported."""
    # Check if --no-color was used (need to get from args)
    # For now, check env and --no-color will be handled in main
    if os.environ.get('NO_COLOR'):
        return False
    if not COLOR_AVAILABLE:
        return False
    return True

def color_text(text, color):
    """Apply color to text if supported."""
    # We'll check NO_COLOR and --no-color in the actual printing functions
    return f"{color}{text}{RESET}"

def debug_print(*args, **kwargs):
    """Print debug message if debug flag is set."""
    # This will be enabled in main based on args
    if getattr(debug_print, 'enabled', False):
        timestamp = datetime.now().strftime("%H:%M:%S")
        print(f"[DEBUG {timestamp}]", *args, **kwargs)

def parse_installed_skills():
    """Parse installed skills from the index file."""
    installed = set()
    if not os.path.exists(INSTALLED_INDEX):
        debug_print(f"Installed skills index not found: {INSTALLED_INDEX}")
        return installed

    try:
        with open(INSTALLED_INDEX, encoding="utf-8") as f:
            lines = f.readlines()
    except Exception as e:
        print(f"Warning: Could not read installed skills index: {e}", file=sys.stderr)
        return installed

    in_skills_table = False
    for line in lines:
        line = line.strip()
        if not line:
            continue

        # Detect section headers
        if line.startswith("## ") and not line.startswith("###"):
            in_skills_table = False
            continue

        # Detect skill table headers
        if line.startswith("| Skill |") or line.startswith("|---"):
            in_skills_table = True
            continue

        # Parse skill rows
        if in_skills_table and line.startswith("|") and "|" in line:
            parts = [part.strip() for part in line.split("|") if part.strip()]
            if len(parts) >= 2 and parts[0] and parts[0] != "Skill":
                skill_name = parts[0].strip()
                if skill_name:
                    installed.add(skill_name.lower())
        # Stop parsing when we hit a non-table line after starting
        elif in_skills_table and not line.startswith("|"):
            in_skills_table = False

    debug_print(f"Parsed {len(installed)} installed skills")
    return installed

def parse_recent_tag_trends(days=14):
    """Parse recent tag trends from the log file with recency weighting."""
    if not os.path.exists(TAG_TRENDS_LOG):
        debug_print(f"Tag trends log not found: {TAG_TRENDS_LOG}")
        return Counter()

    trends = Counter()
    cutoff_date = datetime.now() - timedelta(days=days)

    try:
        with open(TAG_TRENDS_LOG, encoding="utf-8") as f:
            for line_num, line in enumerate(f, 1):
                line = line.strip()
                if not line or line.startswith("#"):
                    continue

                # Format: YYYY-MM-DD: tag1, tag2, tag3
                if ": " not in line:
                    debug_print(f"Skipping malformed line {line_num}: {line[:50]}...")
                    continue

                date_str, tags_str = line.split(": ", 1)
                try:
                    log_date = datetime.strptime(date_str, "%Y-%m-%d")
                    if log_date < cutoff_date:
                        continue  # Skip old entries

                    # Calculate recency weight: more recent = higher weight
                    days_old = (datetime.now() - log_date).days
                    weight = max(1, (days - days_old) + 1)  # Linear decay, min weight 1
                    tags = [tag.strip() for tag in tags_str.split(",") if tag.strip()]
                    for tag in tags:
                        trends[tag] += weight
                except ValueError:
                    debug_print(f"Skipping line {line_num} with invalid date: {date_str}")
                    continue
    except Exception as e:
        print(f"Warning: Could not read tag trends log: {e}", file=sys.stderr)
        return Counter()

    debug_print(f"Parsed trends from {TAG_TRENDS_LOG} (last {days} days) with recency weighting")
    return trends

def parse_skill_to_chat_links():
    """Parse which skills were actually used in sessions."""
    used_skills = set()
    if not os.path.exists(SKILL_TO_CHAT):
        debug_print(f"Skill-to-chat links not found: {SKILL_TO_CHAT}")
        return used_skills

    try:
        with open(SKILL_TO_CHAT, encoding="utf-8") as f:
            lines = f.readlines()
    except Exception as e:
        print(f"Warning: Could not read skill-to-chat links: {e}", file=sys.stderr)
        return used_skills

    in_skills_table = False
    for line in lines:
        line = line.strip()
        if not line:
            continue

        if line.startswith("## ") and not line.startswith("###"):
            in_skills_table = False
            continue

        if line.startswith("| Skill |") or line.startswith("|---"):
            in_skills_table = True
            continue

        if in_skills_table and line.startswith("|") and "|" in line:
            parts = [part.strip() for part in line.split("|") if part.strip()]
            if len(parts) >= 2 and parts[0]:
                skill_name = parts[0].strip()
                if skill_name and skill_name.lower() not in ["skill", ""]:
                    used_skills.add(skill_name.lower())
        elif in_skills_table and not line.startswith("|"):
            in_skills_table = False

    debug_print(f"Parsed {len(used_skills)} used skills from sessions")
    return used_skills

def get_skill_categories():
    """Get skill categories from installed skills index."""
    categories = {}
    current_category = None

    if not os.path.exists(INSTALLED_INDEX):
        return categories

    try:
        with open(INSTALLED_INDEX, encoding="utf-8") as f:
            lines = f.readlines()
    except Exception as e:
        print(f"Warning: Could not read installed skills index for categories: {e}", file=sys.stderr)
        return categories

    for line in lines:
        line = line.strip()
        if not line:
            continue
        if line.startswith("## ") and not line.startswith("###"):
            current_category = line[3:].strip()
            categories[current_category] = []
        elif line.startswith("| Skill |") or line.startswith("|---"):
            continue
        elif line.startswith("|") and "|" in line and current_category:
            parts = [part.strip() for part in line.split("|") if part.strip()]
            if len(parts) >= 2 and parts[0] and parts[0] != "Skill":
                categories[current_category].append(parts[0].lower())

    debug_print(f"Found {len(categories)} skill categories")
    return categories

def load_tag_skill_mapping():
    """Load tag->skill mapping from JSON file with fallback to built-in."""
    built_in_mapping = {
        'hermes': ['hermes-brain-vault', 'hermes-plugin-discovery', 'hermes-desktop-plugin-dev', 'inspecting-hermes-desktop-dom'],
        'linux': ['virtualbox-vm-setup'],
        'llm': ['claude-code', 'codex', 'opencode'],
        'automation': ['automated-information-briefings', 'ai-ml-research-briefing', 'ntfy-notifications'],
        'obsidian': ['obsidian'],
        'video': [],
        'ai-agents': ['agentic-architecture', 'multi-agent-groupchat-collaboration'],
        'database': [],
        'devops': [],
        'javascript': [],
        'cybersecurity': [],
        'productivity': ['weekly-review-planning', 'meeting-action-items'],
        'python': [],
        'networking': [],
        'self-hosting': ['virtualbox-vm-setup']
    }

    if not os.path.exists(TAG_SKILL_MAP_JSON):
        debug_print(f"Tag skill map JSON not found: {TAG_SKILL_MAP_JSON}, using built-in mapping")
        return built_in_mapping

    try:
        with open(TAG_SKILL_MAP_JSON, encoding="utf-8") as f:
            mapping = json.load(f)
        debug_print(f"Loaded tag skill mapping from {TAG_SKILL_MAP_JSON}")
        # Validate structure
        if not isinstance(mapping, dict):
            print(f"Warning: Tag skill map is not a dictionary, using built-in", file=sys.stderr)
            return built_in_mapping
        return mapping
    except json.JSONDecodeError as e:
        print(f"Warning: Could not parse tag skill map JSON: {e}, using built-in", file=sys.stderr)
        return built_in_mapping
    except Exception as e:
        print(f"Warning: Could not read tag skill map: {e}, using built-in", file=sys.stderr)
        return built_in_mapping

def analyze_skill_gaps(categories):
    """Analyze skill distribution across categories to identify underrepresented areas."""
    if not categories:
        return {}

    # Count skills per category
    category_counts = {cat: len(skills) for cat, skills in categories.items()}
    total_skills = sum(category_counts.values())

    if total_skills == 0:
        return {}

    # Calculate expected distribution (equal for simplicity, could be weighted)
    expected_per_category = total_skills / len(categories) if categories else 0

    # Identify underrepresented categories (less than 50% of expected)
    gaps = {}
    for category, count in category_counts.items():
        if expected_per_category > 0 and count < (expected_per_category * 0.5):
            gaps[category] = {
                'current': count,
                'expected': expected_per_category,
                'deficit': expected_per_category - count
            }

    debug_print(f"Identified skill gaps in categories: {list(gaps.keys())}")
    return gaps

def get_complementary_skills(used_skills, categories):
    """Suggest complementary skills based on frequently used skills."""
    # Define known skill complements (could be externalized later)
    complements = {
        'hermes-brain-vault': ['hermes-plugin-discovery', 'hermes-desktop-plugin-dev'],
        'hermes-plugin-discovery': ['hermes-brain-vault', 'hermes-desktop-plugin-dev'],
        'hermes-desktop-plugin-dev': ['hermes-brain-vault', 'hermes-plugin-discovery'],
        'inspecting-hermes-desktop-dom': ['hermes-desktop-plugin-dev'],
        'virtualbox-vm-setup': ['vmware-vm-setup'],  # Alternative virtualization
        'claude-code': ['codex', 'opencode'],  # Other LLM coding assistants
        'codex': ['claude-code', 'opencode'],
        'opencode': ['claude-code', 'codex'],
        'automated-information-briefings': ['ai-ml-research-briefing', 'ntfy-notifications'],
        'ai-ml-research-briefing': ['automated-information-briefings', 'ntfy-notifications'],
        'ntfy-notifications': ['automated-information-briefings', 'ai-ml-research-briefing'],
        'obsidian': [],  # Standalone for now
        'agentic-architecture': ['multi-agent-groupchat-collaboration'],
        'multi-agent-groupchat-collaboration': ['agentic-architecture'],
        'weekly-review-planning': ['meeting-action-items'],
        'meeting-action-items': ['weekly-review-planning']
    }

    complementary = set()
    for skill in used_skills:
        if skill in complements:
            complementary.update(complements[skill])

    # Remove already used skills
    complementary -= used_skills
    debug_print(f"Found {len(complementary)} complementary skills based on usage")
    return list(complementary)

def suggest_skills(args):
    """Generate skill suggestions based on trends, installed skills, and smart algorithms."""
    installed = parse_installed_skills()
    recent_trends = parse_recent_tag_trends(days=args.days)
    used_skills = parse_skill_to_chat_links()
    categories = get_skill_categories()
    tag_mapping = load_tag_skill_mapping()

    debug_print(f"Installed skills: {len(installed)}")
    debug_print(f"Recent trends (weighted): {len(recent_trends)} unique tags")
    debug_print(f"Used skills: {len(used_skills)}")
    debug_print(f"Categories: {len(categories)}")

    # Analyze skill gaps and complementary skills
    skill_gaps = analyze_skill_gaps(categories)
    complementary_skills = get_complementary_skills(used_skills, categories)

    # For each trending tag, find related skills that are NOT installed
    suggested = []  # List of (skill, score, source_tag, reason)

    for tag, weighted_count in recent_trends.most_common(100):  # Check top 100 tags
        tag_lower = tag.lower().strip()
        if len(tag_lower) < 2:
            continue

        # Get potential skill names for this tag from mapping
        potential_skills = tag_mapping.get(tag_lower, [])

        # Also check for direct matches or partial matches in installed skills
        for skill in installed:
            skill_lower = skill.lower()
            # If the tag is contained in the skill name or vice versa (and tag is meaningful)
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
                # Handle variations (hyphens, underscores, spaces)
                if (installed_skill.replace('-', '_') == skill_lower.replace('-', '_') or
                    installed_skill.replace('_', '-') == skill_lower.replace('_', '-') or
                    installed_skill.replace(' ', '_') == skill_lower.replace(' ', '_') or
                    installed_skill.replace(' ', '-') == skill_lower.replace(' ', '-')):
                    is_installed = True
                    break

            if not is_installed:
                # Base score from weighted trend count
                score = float(weighted_count)
                reasons = [f"trending tag: {tag}"]

                # Boost score for complementary skills
                if skill in complementary_skills:
                    score *= 1.5
                    reasons.append("complementary to used skills")

                # Boost score for skills from gapped categories
                for category, skill_list in categories.items():
                    if skill in [s.lower() for s in skill_list]:
                        if category in skill_gaps:
                            score *= 1.3
                            reasons.append(f"addresses gap in {category}")
                        break

                suggested.append((skill, score, tag_lower, "; ".join(reasons)))

    # Remove duplicates (same skill suggested for multiple tags) - keep highest score
    seen_skills = {}
    for skill, score, tag, reason in suggested:
        if skill not in seen_skills or score > seen_skills[skill][0]:
            seen_skills[skill] = (score, tag, reason)

    # Convert back to list and sort by score descending
    unique_suggested = [(skill, score, tag, reason) for skill, (score, tag, reason) in seen_skills.items()]
    unique_suggested.sort(key=lambda x: x[1], reverse=True)

    return unique_suggested[:args.top], installed, recent_trends, used_skills, categories, skill_gaps, complementary_skills

def main():
    args = parse_args()
    debug_print.enabled = args.debug

    # Handle NO_COLOR env and --no-color flag
    no_color = args.no_color or bool(os.environ.get('NO_COLOR'))
    if no_color:
        # Disable colors by setting them to empty strings
        global GREEN, YELLOW, RED, BLUE, CYAN, RESET
        GREEN = YELLOW = RED = BLUE = CYAN = RESET = ""

    print("🔮 Hermes Brain — Future Skill Forecast (Enhanced)")
    print("=" * 60)

    try:
        suggested, installed, recent_trends, used_skills, categories, skill_gaps, complementary_skills = suggest_skills(args)
    except Exception as e:
        print(f"Error generating suggestions: {e}", file=sys.stderr)
        sys.exit(1)

    print(f"\n📊 Analysis based on:")
    print(f"   • {len(installed)} installed skills")
    print(f"   • {len(recent_trends)} unique trending tags (last {args.days} days, recency-weighted)")
    print(f"   • {len(used_skills)} skills actually used in sessions")
    print(f"   • {len(categories)} skill categories")
    if skill_gaps:
        print(f"   • {len(skill_gaps)} skill gap areas identified")
    if complementary_skills:
        print(f"   • {len(complementary_skills)} complementary skill opportunities")

    if not suggested:
        print(f"\n🎯 All trending topics already have corresponding skills installed!")
        print(f"   Consider exploring new skill categories or waiting for new trends.")
        if not args.no_log:
            # Still log that we ran and found nothing
            timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            log_entry = f"{timestamp}: [NO SUGGESTIONS - ALL COVERED]\n"
            try:
                os.makedirs(SKILLS_NOTES, exist_ok=True)
                with open(FORECAST_LOG, "a", encoding="utf-8") as f:
                    f.write(log_entry)
                print(f"📝 Forecast logged to: {FORECAST_LOG}")
            except Exception as e:
                print(f"Warning: Could not write to forecast log: {e}", file=sys.stderr)
        return

    print(f"\n💡 Top {len(suggested)} skill suggestions:")
    print("-" * 60)

    for i, (skill_tag, score, source_tag, reason) in enumerate(suggested, 1):
        # Determine if skill is installed (shouldn't be, but double-check)
        skill_lower = skill_tag.lower()
        installed_skills_lower = {s.lower() for s in installed}
        is_installed = skill_lower in installed_skills_lower

        # Find category
        suggested_category = "Unknown"
        for category, skills in categories.items():
            for skill in skills:
                if skill.lower() == skill_lower:
                    suggested_category = category
                    break
            if suggested_category != "Unknown":
                break

        # Apply colors if enabled
        skill_color = GREEN if not is_installed else RED
        status_text = "SUGGESTED" if not is_installed else "INSTALLED"
        status_color = GREEN if not is_installed else RED

        print(f"{i:2d}. {skill_color}{skill_tag:<25}{RESET} [{status_color}{status_text}{RESET}]")
        print(f"    📊 Score: {score:.1f}")
        print(f"    📂 Category: {suggested_category}")
        print(f"    🏷️  Based on: {source_tag}")
        print(f"    💭 Reason: {reason}")
        print()

    # Write to forecast log (unless --no-log)
    if not args.no_log:
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        suggested_skills = [skill for skill, _, _, _ in suggested]
        log_entry = f"{timestamp}: {', '.join(suggested_skills)}\n"

        try:
            os.makedirs(SKILLS_NOTES, exist_ok=True)
            with open(FORECAST_LOG, "a", encoding="utf-8") as f:
                f.write(log_entry)
            print(f"📝 Forecast logged to: {FORECAST_LOG}")
        except Exception as e:
            print(f"Warning: Could not write to forecast log: {e}", file=sys.stderr)

    print(f"\n💡 Next steps:")
    print(f"   1. Review suggested skills above")
    print(f"   2. Install via: hermes skills install <skill-name>")
    print(f"   3. Re-run this script after installing to update suggestions")
    if args.days != 14:
        print(f"   4. Adjust look-back period with --days <value> (current: {args.days})")
    if args.top != 10:
        print(f"   5. Adjust number of suggestions with --top <value> (current: {args.top})")

if __name__ == "__main__":
    main()