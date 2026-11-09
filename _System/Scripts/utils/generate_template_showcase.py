#!/usr/bin/env python3
"""
generate_template_showcase.py — Builds _System/Templates/Template-Showcase.md.

Reads every note template in _System/Templates/ and 04-Archives/Memory-Review/TEMPLATE.md,
and generates an Obsidian-native gallery note where each template is enclosed in
a collapsible callout with 4-backtick raw markdown syntax highlighting and 1-click copy support.
"""
import os
import sys

VAULT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
TEMPLATES_DIR = os.path.join(VAULT_ROOT, "_System", "Templates")
OUTPUT_FILE = os.path.join(TEMPLATES_DIR, "Template-Showcase.md")

TEMPLATES_META = [
    {
        "file": "Project.md",
        "path": os.path.join(TEMPLATES_DIR, "Project.md"),
        "title": "Project Dashboard",
        "badge": "🟢 Active Project",
        "target": "01-Projects/<Project-Name>.md",
        "desc": "Responsive 2-column project dashboard with KPI strip, executive goal, tech stack, multi-agent squad roles (Codex, Argus, Ledger, Vox), and action checklist.",
        "shortcut": "Ctrl+T → Select 'Project'",
    },
    {
        "file": "Architecture-Decision-Record.md",
        "path": os.path.join(TEMPLATES_DIR, "Architecture-Decision-Record.md"),
        "title": "Architecture Decision Record (ADR)",
        "badge": "📑 Architecture ADR",
        "target": "01-Projects/ADR/ADR-<Number>-<Title>.md",
        "desc": "Formal engineering decision record featuring 4-persona multi-agent review (Argus security, Codex technical, Ledger token efficiency, Vox alignment).",
        "shortcut": "Ctrl+T → Select 'Architecture-Decision-Record'",
    },
    {
        "file": "Lesson-Learned.md",
        "path": os.path.join(TEMPLATES_DIR, "Lesson-Learned.md"),
        "title": "Lesson Learned",
        "badge": "⚠️ Operational Post-Mortem",
        "target": "02-Areas/Skills/Lessons-Learned/<Topic>.md",
        "desc": "Self-correction template capturing triggers, root cause analysis, human corrections, and standing preventative directives to prevent recurring agent mistakes.",
        "shortcut": "Ctrl+T → Select 'Lesson-Learned'",
    },
    {
        "file": "Daily-Review.md",
        "path": os.path.join(TEMPLATES_DIR, "Daily-Review.md"),
        "title": "Daily Review",
        "badge": "📅 Evening Reflection",
        "target": "04-Archives/Daily/YYYY/MM/YYYY-MM-DD-Review.md",
        "desc": "Daily reflection schema configured with Obsidian Daily Notes plugin. Includes automated Dataview query auditing all chat sessions archived during that day.",
        "shortcut": "Alt+D (or ribbon Daily Note icon)",
    },
    {
        "file": "Research-Note.md",
        "path": os.path.join(TEMPLATES_DIR, "Research-Note.md"),
        "title": "Research Note",
        "badge": "🔬 Technical Spike",
        "target": "03-Resources/Research/<Topic>.md",
        "desc": "Structured research investigation brief with explicit sections for research question/goal, empirical findings, cited sources, and open inquiry threads.",
        "shortcut": "Ctrl+T → Select 'Research-Note'",
    },
    {
        "file": "Personality-Judgment-Analysis.md",
        "path": os.path.join(TEMPLATES_DIR, "Personality-Judgment-Analysis.md"),
        "title": "Personality Judgment Analysis",
        "badge": "🎭 Cognitive Matrix",
        "target": "02-Areas/ or 04-Archives/Daily/YYYY/MM/DD/",
        "desc": "Deep 7-dimension behavioral and communication evaluation analyzing baseline communication, cognitive style, collaboration, tone, and behavioral anomalies.",
        "shortcut": "Ctrl+T → Select 'Personality-Judgment-Analysis'",
    },
    {
        "file": "Personality-Judgment-Dashboard.md",
        "path": os.path.join(TEMPLATES_DIR, "Personality-Judgment-Dashboard.md"),
        "title": "Personality Judgment Dashboard",
        "badge": "📈 Live Telemetry",
        "target": "02-Areas/ or 04-Archives/Daily/YYYY/MM/DD/",
        "desc": "Dataview and DataviewJS telemetry dashboard aggregating cross-session analyses, confidence levels, anomalies, and active behavioral hypotheses.",
        "shortcut": "Ctrl+T → Select 'Personality-Judgment-Dashboard'",
    },
    {
        "file": "TEMPLATE.md",
        "path": os.path.join(VAULT_ROOT, "04-Archives", "Memory-Review", "TEMPLATE.md"),
        "title": "Memory Review Candidate",
        "badge": "🧠 Memory Staging",
        "target": "04-Archives/Memory-Review/<Candidate-Name>.md",
        "desc": "Memory promotion rubric enforcing durability, security, and verification gates before facts are promoted into long-term agent memory or user profile.",
        "shortcut": "Manual duplicate / Kanban card creation",
    },
]


def build_showcase():
    lines = [
        "---",
        "type: index",
        "status: active",
        "tags:",
        "  - system",
        "  - templates",
        "  - showcase",
        "cssclasses:",
        "  - dashboard-beta",
        "  - dashboard-wide",
        "---",
        "",
        "# 📋 Templates Content Showcase & Raw Source Gallery",
        "",
        "> [!TIP] How to View and Copy Templates",
        "> In Obsidian, templates with complex Dataview queries or HTML containers often execute or format automatically. ",
        "> This showcase displays the **verbatim raw markdown source code** for every template inside expandable code boxes. ",
        "> Click **`Click to view & copy raw template markdown`**, then use Obsidian's top-right **Copy** button to copy the exact code in one click!",
        "",
        "<div class=\"dashboard-kpi-strip\">",
        "  <div class=\"dashboard-kpi-card\">",
        "    <div class=\"dashboard-kpi-label\">Total Templates</div>",
        f"    <div class=\"dashboard-kpi-value\" style=\"font-size: 1.25em; color: var(--text-accent);\">{len(TEMPLATES_META)} SCHEMAS</div>",
        "  </div>",
        "  <div class=\"dashboard-kpi-card\">",
        "    <div class=\"dashboard-kpi-label\">View Mode</div>",
        "    <div class=\"dashboard-kpi-value\" style=\"font-size: 1.25em; color: #4facfe;\">RAW SOURCE</div>",
        "  </div>",
        "  <div class=\"dashboard-kpi-card\">",
        "    <div class=\"dashboard-kpi-label\">1-Click Copy</div>",
        "    <div class=\"dashboard-kpi-value\" style=\"font-size: 1.25em; color: #bb86fc;\">ENABLED</div>",
        "  </div>",
        "  <div class=\"dashboard-kpi-card\">",
        "    <div class=\"dashboard-kpi-label\">Standard</div>",
        "    <div class=\"dashboard-kpi-value\" style=\"font-size: 1.25em;\">PARA ALIGNED</div>",
        "  </div>",
        "</div>",
        "",
        "---",
        "",
        "## 🧭 Jump to Template",
        "",
    ]

    for idx, item in enumerate(TEMPLATES_META, 1):
        lines.append(f"- **[[#{idx}. {item['title']}|{idx}. {item['title']}]]** (`{item['file']}`) — *{item['desc'].split('.')[0]}*")

    lines.extend(["", "---", ""])

    for idx, item in enumerate(TEMPLATES_META, 1):
        if not os.path.exists(item["path"]):
            continue
        with open(item["path"], "r", encoding="utf-8") as f:
            raw_content = f.read().rstrip()

        lines.extend([
            f"### {idx}. {item['title']}",
            "",
            f"> **File:** [`{item['file']}`](file:///{item['path'].replace(os.sep, '/')}) | **Target:** `{item['target']}` | **Insert:** `{item['shortcut']}`",
            "",
            f"*{item['desc']}*",
            "",
            "> [!example]- 📋 Click to view & copy raw template markdown",
            "> ````markdown",
        ])

        # Indent raw content by "> " so it lives cleanly inside the callout
        for raw_line in raw_content.splitlines():
            lines.append(f"> {raw_line}" if raw_line else ">")

        lines.extend([
            "> ````",
            "",
            "---",
            "",
        ])

    lines.extend([
        "## 🛠️ How to Add or Modify Templates",
        "",
        "1. Create or edit any `.md` file inside [`_System/Templates/`](file:///_System/Templates/).",
        "2. Keep frontmatter clean with `type: <category>`, `created: {{date}}`, and relevant tags.",
        "3. Run `python _System/Scripts/generate_template_showcase.py` to re-sync this showcase file automatically.",
        "",
        "---",
        "*Reference documentation: [[_System/Templates/README|Templates Reference Catalog]] · [[Dashboard|Vault Dashboard]]*",
        "",
    ])

    with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
        f.write("\n".join(lines))

    print(f"✅ Generated {OUTPUT_FILE} with {len(TEMPLATES_META)} template schemas.")


if __name__ == "__main__":
    build_showcase()
