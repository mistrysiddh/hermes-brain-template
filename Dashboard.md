---
type: dashboard
status: active
created: 2026-09-10
tags:
  - dashboard
  - hub
dashboard_last_visit: 2026-09-17T16:15:12.982Z
dashboard_last_session_count: 0
dashboard_last_candidate_count: 3
---

# Dashboard

One glance at everything live in this vault. Requires the **Dataview**
plugin (already enabled) to render; without it these show as raw code
blocks instead of tables/lists.

> **Note:** An experimental card-style dashboard is available at `Canvases/Dashboard-Beta.md` (requires the `dashboard-beta` CSS snippet enabled in Settings → Appearance → CSS snippets).

## What's changed since your last visit

```dataviewjs
// Delta banner — compares this note's own frontmatter (last-visit
// snapshot) against current vault state. Updates the snapshot every time
// this note is opened, so the very next open shows what happened since.
const file = app.vault.getAbstractFileByPath("Dashboard.md");
const cache = app.metadataCache.getFileCache(file);
const fm = cache?.frontmatter ?? {};

const dailyPages = dv.pages('"Daily"')
  .where(p => p.file.name !== "README" && p.file.name !== "manifest"
    && p.file.name !== "Timeline" && p.file.name !== "Chat-Correlation");
const sessionCount = dailyPages.length;
const candidateCount = dv.pages('"Memory-Review"').file.tasks.where(t => !t.completed).length;

const prevSessionCount = fm.dashboard_last_session_count;
const prevCandidateCount = fm.dashboard_last_candidate_count;
const prevVisit = fm.dashboard_last_visit;

if (prevSessionCount === undefined) {
  dv.paragraph("👋 First time opening this Dashboard — nothing to compare yet. Come back later to see what changed.");
} else {
  const newSessions = Math.max(0, sessionCount - prevSessionCount);
  const candidateDelta = candidateCount - prevCandidateCount;
  const parts = [];
  if (newSessions > 0) parts.push(`**${newSessions}** new session${newSessions !== 1 ? "s" : ""} archived`);
  if (candidateDelta > 0) parts.push(`**${candidateDelta}** new Memory-Review candidate${candidateDelta !== 1 ? "s" : ""}`);
  else if (candidateDelta < 0) parts.push(`**${-candidateDelta}** candidate${-candidateDelta !== 1 ? "s" : ""} reviewed/cleared`);
  const when = prevVisit ? ` since you last opened this on ${new Date(prevVisit).toLocaleString()}` : "";
  dv.paragraph(parts.length > 0
    ? `🔔 ${parts.join(", ")}${when}.`
    : `😴 Nothing new${when} — quiet since your last visit.`);
}

// Write the new snapshot back into frontmatter for next time.
await app.fileManager.processFrontMatter(file, (f) => {
  f.dashboard_last_visit = new Date().toISOString();
  f.dashboard_last_session_count = sessionCount;
  f.dashboard_last_candidate_count = candidateCount;
});
```

_Compares this note's own frontmatter (written on every open) against
current counts — no separate log file needed. First open always shows the
"first time" message since there's nothing to compare against yet._

## Template update check

```dataviewjs
const versionFile = app.vault.getAbstractFileByPath("VERSION");
if (!versionFile) {
  dv.paragraph("⚠️ No `VERSION` file found — can't check for updates. (Vaults created before this feature was added: create one with the current version string, e.g. `1.2.0`.)");
} else {
  const local = (await app.vault.read(versionFile)).trim();
  try {
    const res = await fetch("https://api.github.com/repos/mistrysiddh/hermes-brain-template/releases/latest");
    if (!res.ok) throw new Error(`HTTP ${res.status}`);
    const data = await res.json();
    const latest = (data.tag_name || "").replace(/^v/, "");
    if (!latest) throw new Error("no tag_name in response");
    if (latest === local) {
      dv.paragraph(`✅ Up to date — running **v${local}**.`);
    } else {
      dv.paragraph(`🔔 **Update available: v${latest}** (you have v${local}). [Release notes](${data.html_url}) — run \`update.sh\` / \`update.ps1\` to pull it in.`);
    }
  } catch (e) {
    dv.paragraph(`⚠️ Couldn't check for updates (offline, or GitHub API unreachable): ${e.message}. Running v${local}.`);
  }
}
```

_Checked live each time this note opens — needs internet access. Nothing is sent anywhere; this only reads GitHub's public releases API._

## Vault health

```dataviewjs
// Last archived session — catches a dead/misconfigured hourly cron job.
const dailyPages = dv.pages('"Daily"')
  .where(p => p.file.name !== "README" && p.file.name !== "manifest"
    && p.file.name !== "Timeline" && p.file.name !== "Chat-Correlation");
if (dailyPages.length === 0) {
  dv.paragraph("⚪ No archived sessions yet. If you expected the hourly archiver to be running, check `cronjob_manage(action='list')` or your platform's task scheduler.");
} else {
  const newest = dailyPages.sort(p => p.file.mtime, 'desc').array()[0];
  const hoursAgo = (Date.now() - newest.file.mtime.toMillis()) / 3600000;
  if (hoursAgo < 3) {
    dv.paragraph(`✅ Last session archived ${Math.round(hoursAgo * 10) / 10}h ago — archiver looks alive.`);
  } else if (hoursAgo < 48) {
    dv.paragraph(`ℹ️ Last session archived ${Math.round(hoursAgo)}h ago. Fine if you simply haven't used Hermes since then.`);
  } else {
    dv.paragraph(`⚠️ Last session archived ${Math.round(hoursAgo / 24)} day(s) ago. If you expected hourly archiving, the cron job may have stopped — check \`cronjob_manage(action='list')\`.`);
  }
}

// Memory-Review backlog size — catches a review queue nobody's touching.
const openTasks = dv.pages('"Memory-Review"').file.tasks
  .where(t => !t.completed).length;
if (openTasks === 0) {
  dv.paragraph("✅ No open Memory-Review candidates.");
} else if (openTasks <= 20) {
  dv.paragraph(`ℹ️ **${openTasks}** open Memory-Review candidate(s) awaiting your review.`);
} else {
  dv.paragraph(`⚠️ **${openTasks}** open Memory-Review candidates — backlog is growing. Consider a review pass, or check whether \`Scripts/consolidate_memory.py\` is running on schedule.`);
}
```

_Read-only checks against files already in this vault — nothing leaves your machine._

## Storage & file counts

```dataviewjs
const files = app.vault.getFiles();
const totalBytes = files.reduce((sum, f) => sum + (f.stat?.size ?? 0), 0);
const totalMB = (totalBytes / (1024 * 1024)).toFixed(1);

const byExt = {};
for (const f of files) {
  const ext = f.extension || "(none)";
  byExt[ext] = (byExt[ext] ?? 0) + 1;
}
const topExts = Object.entries(byExt).sort((a, b) => b[1] - a[1]).slice(0, 5)
  .map(([ext, n]) => `${ext} (${n})`).join(", ");

dv.paragraph(`💾 **${files.length.toLocaleString()} files**, **${totalMB} MB** total. Top types: ${topExts}.`);
```

_Live count via Obsidian's own `app.vault.getFiles()` — no script or cron needed, purely a snapshot of what's on disk right now._

## Token usage

```dataviewjs
const tokenLog = app.vault.getAbstractFileByPath("Skills-Notes/Token-Usage.log");
if (!tokenLog) {
  dv.paragraph("ℹ️ Token usage log not found — will appear after first hourly archive run with token extraction.");
} else {
  const content = await app.vault.read(tokenLog);
  const lines = content.split("\n")
    .map(l => l.trim())
    .filter(l => l && !l.startsWith("#") && !l.startsWith("---") && !l.startsWith("<!--"));
  
  if (lines.length === 0) {
    dv.paragraph("ℹ️ No token usage recorded yet — will appear after first hourly archive run with token extraction.");
  } else {
    // Parse and sum
    let runningTotal = 0;
    const dailyData = [];
    for (const line of lines) {
      const match = line.match(/^(\d{4}-\d{2}-\d{2}):\s*(\d+)\s*tokens?\s*\((\d+)\s*session/);
      if (match) {
        const [, date, tokens, sessions] = match;
        const t = parseInt(tokens);
        const s = parseInt(sessions);
        runningTotal += t;
        dailyData.push({ date, tokens: t, sessions: s });
      }
    }
    
    if (dailyData.length === 0) {
      dv.paragraph("⚠️ Token log found but no valid entries parsed yet.");
    } else {
      // Today's entry (if any)
      const today = new Date().toISOString().split("T")[0];
      const todayEntry = dailyData.find(d => d.date === today);
      
      let output = "";
      if (todayEntry) {
        output += `⚡ **Today: ${todayEntry.tokens.toLocaleString()} tokens** (${todayEntry.sessions} session${todayEntry.sessions !== 1 ? "s" : ""})  \n`;
      }
      
      // Running total
      output += `🔢 **All-time total: ${runningTotal.toLocaleString()} tokens**  \n`;
      
      // Last 7 days
      const last7 = dailyData.slice(-7);
      if (last7.length > 1) {
        const weekTotal = last7.reduce((a, b) => a + b.tokens, 0);
        const avg = Math.round(weekTotal / last7.length);
        output += `📊 **Last ${last7.length} days: ${weekTotal.toLocaleString()} tokens** (avg ${avg.toLocaleString()}/day)  \n`;
      }
      
      // Trend indicator (compare last two days)
      if (dailyData.length >= 2) {
        const last = dailyData[dailyData.length - 1];
        const prev = dailyData[dailyData.length - 2];
        const diff = last.tokens - prev.tokens;
        const pct = prev.tokens > 0 ? Math.round((diff / prev.tokens) * 100) : 0;
        const trend = diff > 0 ? `📈 +${diff.toLocaleString()} (${pct}%)` : diff < 0 ? `📉 ${diff.toLocaleString()} (${pct}%)` : `➡️ No change`;
        output += `📈 **Day-over-day: ${trend}**`;
      }
      
      dv.paragraph(output);
    }
  }
}
```

_Updates live each time this note opens — reads from Skills-Notes/Token-Usage.log which is maintained by hourly_archive.py._

## Activity heatmap

```dataviewjs
const tokenLog = app.vault.getAbstractFileByPath("Skills-Notes/Token-Usage.log");
if (!tokenLog) {
  dv.paragraph("ℹ️ No activity data yet — will appear after your first hourly archive run.");
} else {
  const content = await app.vault.read(tokenLog);
  const lines = content.split("\n")
    .map(l => l.trim())
    .filter(l => l && !l.startsWith("#") && !l.startsWith("---") && !l.startsWith("<!--"));

  // Parse into a date -> {tokens, sessions} map, summing if a date appears
  // more than once (e.g. a [sample] line alongside a real one).
  const byDate = {};
  for (const line of lines) {
    const match = line.match(/^(\d{4}-\d{2}-\d{2}):\s*(\d+)\s*tokens?\s*\((\d+)\s*session/);
    if (match) {
      const [, date, tokens, sessions] = match;
      const t = parseInt(tokens);
      const s = parseInt(sessions);
      if (!byDate[date]) byDate[date] = { tokens: 0, sessions: 0 };
      byDate[date].tokens += t;
      byDate[date].sessions += s;
    }
  }

  const dates = Object.keys(byDate);
  if (dates.length === 0) {
    dv.paragraph("ℹ️ No activity data yet — will appear after your first hourly archive run.");
  } else {
    // Build a GitHub-style calendar grid: 18 weeks back from today,
    // columns = weeks (oldest to newest), rows = Sun..Sat.
    const WEEKS = 18;
    const today = new Date();
    today.setHours(0, 0, 0, 0);
    // Find the most recent Saturday (end of the last column) and walk back
    // WEEKS full weeks from there, starting each column on a Sunday.
    const endOfWeek = new Date(today);
    endOfWeek.setDate(today.getDate() + (6 - today.getDay()));
    const start = new Date(endOfWeek);
    start.setDate(endOfWeek.getDate() - (WEEKS * 7 - 1));

    const maxTokens = Math.max(...dates.map(d => byDate[d].tokens), 1);

    function colorFor(tokens) {
      if (tokens === 0) return "var(--background-modifier-border)";
      const ratio = tokens / maxTokens;
      // 4-step intensity toward the theme accent color.
      if (ratio > 0.75) return "var(--text-accent)";
      if (ratio > 0.45) return "color-mix(in srgb, var(--text-accent) 70%, var(--background-modifier-border))";
      if (ratio > 0.15) return "color-mix(in srgb, var(--text-accent) 40%, var(--background-modifier-border))";
      return "color-mix(in srgb, var(--text-accent) 18%, var(--background-modifier-border))";
    }

    const container = dv.el("div", "", { attr: { style: "display: flex; gap: 3px; overflow-x: auto; padding: 4px 0;" } });
    const dayLabels = dv.el("div", "", { attr: { style: "display: flex; flex-direction: column; gap: 3px; margin-right: 4px; font-size: 0.65em; color: var(--text-faint);" } });
    ["", "Mon", "", "Wed", "", "Fri", ""].forEach(label => {
      const cell = dayLabels.createEl("div", { text: label });
      cell.style.height = "11px";
      cell.style.lineHeight = "11px";
    });
    container.prepend(dayLabels);

    let totalActiveDays = 0;
    let cursor = new Date(start);
    for (let w = 0; w < WEEKS; w++) {
      const col = dv.el("div", "", { attr: { style: "display: flex; flex-direction: column; gap: 3px;" } });
      for (let d = 0; d < 7; d++) {
        const dateStr = cursor.toISOString().split("T")[0];
        const entry = byDate[dateStr] || { tokens: 0, sessions: 0 };
        if (entry.tokens > 0) totalActiveDays++;
        const isFuture = cursor > today;
        const cell = col.createEl("div");
        cell.style.width = "11px";
        cell.style.height = "11px";
        cell.style.borderRadius = "2px";
        cell.style.background = isFuture ? "transparent" : colorFor(entry.tokens);
        cell.title = isFuture ? "" : `${dateStr}: ${entry.tokens.toLocaleString()} tokens, ${entry.sessions} session${entry.sessions !== 1 ? "s" : ""}`;
        cursor.setDate(cursor.getDate() + 1);
      }
      container.appendChild(col);
    }

    dv.paragraph(`📅 **${totalActiveDays} active day${totalActiveDays !== 1 ? "s" : ""}** in the last ${WEEKS} weeks. Hover a cell for the exact date/tokens/sessions.`);
  }
}
```

_Same data as Token usage above, shown as a calendar — darker green = more tokens that day. `color-mix()` requires a recent Obsidian/Chromium version; if cells look uncolored, update Obsidian._

## Vault audit

```dataviewjs
const auditReport = app.vault.getAbstractFileByPath("Skills-Notes/Vault-Audit-Report.md");
if (!auditReport) {
  dv.paragraph("ℹ️ Vault audit report not found — will appear after first `vault_audit.py` run. Run manually or wait for scheduled cron.");
} else {
  const content = await app.vault.read(auditReport);
  // Extract summary lines
  const summaryMatch = content.match(/## Summary\n\n([\s\S]*?)\n---/);
  if (summaryMatch) {
    const summary = summaryMatch[1].trim();
    // Convert markdown list to simple display
    const lines = summary.split('\n').map(l => l.trim()).filter(l => l.startsWith('-'));
    if (lines.length > 0) {
      let output = "📋 **Latest Vault Audit Summary:**\n";
      for (const line of lines) {
        // Parse "- **Broken wikilinks**: 0"
        const match = line.match(/-\s+\*\*([^*]+)\*\*:\s*(\d+)/);
        if (match) {
          const [, label, count] = match;
          const icon = parseInt(count) > 0 ? "⚠️" : "✅";
          output += `  ${icon} **${label}**: ${count}\n`;
        }
      }
      dv.paragraph(output);
    }
  }
  // Show last generated time
  const genMatch = content.match(/Generated:\s*([^\n]+)/);
  if (genMatch) {
    dv.paragraph(`🕐 Last run: ${genMatch[1].trim()}  \n[Open full report →](Skills-Notes/Vault-Audit-Report.md)`);
  }
}
```

_Updated by `Scripts/vault_audit.py` on schedule (weekly/monthly via cron). Click the link above to see full details._

## Agent performance

```dataviewjs
const perfReport = app.vault.getAbstractFileByPath("Skills-Notes/Agent-Performance.md");
if (!perfReport) {
  dv.paragraph("ℹ️ Agent performance report not found — run `Scripts/agent_performance.py` or wait for scheduled cron.");
} else {
  const content = await app.vault.read(perfReport);
  // Extract Overview stats
  const overviewMatch = content.match(/## Overview\n\n([\s\S]*?)\n---/);
  if (overviewMatch) {
    const overview = overviewMatch[1].trim();
    const lines = overview.split('\n').map(l => l.trim()).filter(l => l.startsWith('-'));
    let output = "📊 **Agent Performance Snapshot:**\n";
    for (const line of lines) {
      const match = line.match(/-\s+\*\*([^*]+)\*\*:\s*([\d,\.]+)/);
      if (match) {
        const [, label, value] = match;
        output += `  🔹 **${label}**: ${value}\n`;
      }
    }
    dv.paragraph(output);
  }
  // Show top skills if present
  const skillsMatch = content.match(/## 🎯 Skill Usage.*?\n\| Skill \| Sessions Invoked \|\n([\s\S]*?)\n\|/);
  if (skillsMatch) {
    const skillLines = skillsMatch[1].trim().split('\n').slice(0, 5); // top 5
    if (skillLines.length > 0) {
      let output = "🎯 **Top Skills:**\n";
      for (const line of skillLines) {
        const parts = line.split('|').map(p => p.trim()).filter(p => p);
        if (parts.length >= 2) {
          output += `  • ${parts[0]} — ${parts[1]} session${parts[1] !== '1' ? 's' : ''}\n`;
        }
      }
      dv.paragraph(output);
    }
  }
  // Last generated
  const genMatch = content.match(/Generated:\s*([^\n]+)/);
  if (genMatch) {
    dv.paragraph(`🕐 Last run: ${genMatch[1].trim()}  \n[Open full report →](Skills-Notes/Agent-Performance.md)`);
  }
}
```

_Updated by `Scripts/agent_performance.py` on schedule (run alongside other scripts). Click the link above to see full details._

## Active projects

```dataview
TABLE status, created
FROM "Projects"
WHERE type = "project" AND status = "active"
SORT created DESC
```

_All statuses, sortable/filterable: [[Projects/Projects.base|Projects.base]]._

## Open memory candidates

```dataview
TASK
FROM "Memory-Review"
WHERE !completed
LIMIT 15
```

_Full review flow: [[Memory-Review/TEMPLATE|Memory-Review/TEMPLATE.md]]. Regenerated by `Scripts/consolidate_memory.py`._

## Recently promoted

```dataviewjs
// Recent Memory-Review promotions — parses Consolidation-Log.md, written
// by Scripts/consolidate_memory.py whenever a checked-off [x] candidate
// is archived. Shows the last few decided candidates so the review
// pipeline feels less like a black box.
const logFile = app.vault.getAbstractFileByPath("Memory-Review/Consolidation-Log.md");
if (!logFile) {
  dv.paragraph("ℹ️ No Consolidation-Log.md yet — will appear after your first `consolidate_memory.py` run that archives a decided candidate.");
} else {
  const content = await app.vault.read(logFile);
  // Lines look like: "- [x] some fact text `#abcd1234`"
  const entries = content.split("\n")
    .map(l => l.trim())
    .filter(l => l.match(/^-\s+\[(x|X)\]/));
  if (entries.length === 0) {
    dv.paragraph("ℹ️ Consolidation-Log.md exists but has no decided candidates yet.");
  } else {
    const recent = entries.slice(-5).reverse();
    let output = `📥 **${entries.length}** candidate(s) promoted/decided all-time. Most recent:\n`;
    for (const line of recent) {
      const text = line.replace(/^-\s+\[(x|X)\]\s+/, "").replace(/\s+`#[a-f0-9]{8}`\s*$/, "");
      output += `- ${text}\n`;
    }
    dv.paragraph(output);
  }
}
```

_Full audit trail: [[Memory-Review/Consolidation-Log|Consolidation-Log.md]] — append-only, written automatically, never edited by hand._

## Recent Daily sessions

```dataview
TABLE file.mtime AS "Modified", file.folder AS "Date folder"
FROM "Daily"
WHERE file.name != "README" AND file.name != "manifest" AND file.name != "Timeline" AND file.name != "Chat-Correlation"
SORT file.mtime DESC
LIMIT 10
```

_Full chronological view: [[Daily/Timeline]]._

## Installed skills

```dataviewjs
const file = app.vault.getAbstractFileByPath("Skills-Notes/Installed-Skills-Index.md");
if (file) {
  const content = await app.vault.read(file);
  const rows = content.split("\n")
    .filter(l => l.trim().startsWith("|"))
    .filter(l => !l.includes("---") && !l.trim().startsWith("| Skill"));
  const populated = rows.filter(r => r.replace(/\|/g, "").trim().length > 0);
  dv.paragraph(`**${populated.length}** skill(s) listed in [[Skills-Notes/Installed-Skills-Index|Installed Skills Index]].`);
} else {
  dv.paragraph("Skills-Notes/Installed-Skills-Index.md not found.");
}
```

## Top skills used

```dataviewjs
// Skill-usage breakdown — parses Skill-to-Chat-Links.md, auto-generated
// by Scripts/generate_skill_links.py. Counts how many archived sessions
// invoked each skill and shows the top 5.
const file = app.vault.getAbstractFileByPath("Skills-Notes/Skill-to-Chat-Links.md");
if (!file) {
  dv.paragraph("ℹ️ Skills-Notes/Skill-to-Chat-Links.md not found — run `Scripts/generate_skill_links.py` (or wait for scheduled cron) to generate it.");
} else {
  const content = await app.vault.read(file);
  // Tool-call mode: "### skill_name" heading followed by one "- [[link]]" per session.
  // Prose mode: "## Skill Display Name" heading followed by one "- [[link]]" per session.
  const lines = content.split("\n");
  const counts = {};
  let currentSkill = null;
  for (const line of lines) {
    const h3 = line.match(/^###\s+(.+)$/);
    const h2 = line.match(/^##\s+(.+)$/);
    if (h3) {
      currentSkill = h3[1].trim();
      counts[currentSkill] = counts[currentSkill] ?? 0;
      continue;
    }
    if (h2 && !line.startsWith("## Table of contents")) {
      currentSkill = h2[1].trim();
      counts[currentSkill] = counts[currentSkill] ?? 0;
      continue;
    }
    if (currentSkill && line.trim().startsWith("- [[")) {
      counts[currentSkill]++;
    }
  }
  const ranked = Object.entries(counts).filter(([, n]) => n > 0).sort((a, b) => b[1] - a[1]).slice(0, 5);
  if (ranked.length === 0) {
    dv.paragraph("ℹ️ No genuine skill invocations found yet in `Daily/` — nothing to rank.");
  } else {
    let output = "🎯 **Top skills by session count:**\n";
    for (const [skill, n] of ranked) {
      output += `- **${skill}** — ${n} session${n !== 1 ? "s" : ""}\n`;
    }
    dv.paragraph(output);
  }
}
```

_Full breakdown by category: [[Skills-Notes/Skill-to-Chat-Links|Skill-to-Chat-Links.md]]. Regenerated by `Scripts/generate_skill_links.py`._

## Semantic search

```dataviewjs
// Natural-language search over your vault — powered by the local
// sentence-transformers index (see Scripts/semantic_search.py).
// Requires: pip install sentence-transformers numpy, then run
// `python Scripts/semantic_search.py --build` once, and optionally
// `python Scripts/semantic_search.py --serve` to keep a local endpoint alive.
const input = dv.el("input", "", { attr: { type: "text", placeholder: "Search your vault… (e.g., \"prompt optimization last month\")", style: "width: 100%; padding: 6px 10px; font-size: 0.9em; border: 1px solid var(--background-modifier-border); border-radius: 4px; background: var(--input-background); color: var(--input-color);" } });
const resultsDiv = dv.el("div", "", { attr: { style: "margin-top: 8px; font-size: 0.85em;" } });

let debounceTimer = null;
input.addEventListener("input", () => {
  clearTimeout(debounceTimer);
  debounceTimer = setTimeout(async () => {
    const q = input.value.trim();
    if (!q) {
      resultsDiv.empty();
      return;
    }
    resultsDiv.empty();
    const loading = resultsDiv.createEl("div", { text: "🔍 Searching…", attr: { style: "color: var(--text-faint);" } });
    try {
      // Try local endpoint first (if --serve is running)
      const res = await fetch(`http://localhost:8765/search?q=${encodeURIComponent(q)}&k=5`);
      if (res.ok) {
        const data = await res.json();
        renderResults(data.results);
        return;
      }
    } catch (_) {
      // Fall through to direct fetch from index files (if CORS allows)
    }
    loading.remove();
    resultsDiv.createEl("div", { text: "⚠️ Could not reach local search server. Run `python Scripts/semantic_search.py --serve` in a terminal, or ensure the index is built and CORS allows file:// access.", attr: { style: "color: var(--text-error);" } });
  }, 250);
});

function renderResults(results) {
  resultsDiv.empty();
  if (!results || results.length === 0) {
    resultsDiv.createEl("div", { text: "😕 No matches found.", attr: { style: "color: var(--text-faint);" } });
    return;
  }
  const list = resultsDiv.createEl("ul", { attr: { style: "list-style: none; padding-left: 0;" } });
  for (const r of results) {
    const li = list.createEl("li", { attr: { style: "margin-bottom: 6px; padding: 6px 8px; background: var(--background-secondary); border-radius: 4px; border-left: 3px solid var(--text-accent);" } });
    const link = li.createEl("a", { text: `${r.file} (chunk ${r.chunk})`, href: `obsidian://open?vault=${encodeURIComponent(app.vault.getName())}&file=${encodeURIComponent(r.file)}`, attr: { style: "font-weight: 600; text-decoration: none; color: var(--text-normal);" } });
    link.addEventListener("click", (e) => {
      e.preventDefault();
      app.workspace.openLinkText(r.file, "", false);
    });
    const meta = li.createEl("div", { text: `score: ${r.score.toFixed(3)}`, attr: { style: "font-size: 0.75em; color: var(--text-faint); margin-top: 2px;" } });
    const snippet = li.createEl("div", { text: r.text, attr: { style: "font-size: 0.8em; color: var(--text-muted); margin-top: 4px; white-space: pre-wrap; max-height: 60px; overflow: hidden;" } });
  }
}
```

_Built with `sentence-transformers/all-MiniLM-L6-v2` (22 MB, runs entirely on your CPU). No data ever leaves your machine. Run `python Scripts/semantic_search.py --build` to create the index, then `python Scripts/semantic_search.py --serve` to power this widget. Re-run `--update` after new sessions are archived to keep it fresh._

## Tag cloud & trends

```dataviewjs
// Tag cloud & trends — reads from Skills-Notes/Tag-Cloud.log and
// Skills-Notes/Tag-Trends.log (maintained by session_tagger.py).
// Requires: run `python Scripts/session_tagger.py` after archiving,
// or let hourly_archive.py invoke it automatically.

const tagCloudLog = app.vault.getAbstractFileByPath("Skills-Notes/Tag-Cloud.log");
const tagTrendsLog = app.vault.getAbstractFileByPath("Skills-Notes/Tag-Trends.log");

if (!tagCloudLog) {
  dv.paragraph("ℹ️ Tag cloud not found — will appear after `session_tagger.py` runs (triggered automatically by hourly_archive.py). Run `python Scripts/session_tagger.py` manually to populate now.");
} else {
  const cloudContent = await app.vault.read(tagCloudLog);
  const cloudLines = cloudContent.split("\n")
    .map(l => l.trim())
    .filter(l => l && !l.startsWith("#"));

  if (cloudLines.length === 0) {
    dv.paragraph("ℹ️ Tag cloud log exists but is empty — will populate as sessions are tagged.");
  } else {
    // Parse tag: count
    const tags = [];
    for (const line of cloudLines) {
      const parts = line.split(": ");
      if (parts.length === 2) {
        const count = parseInt(parts[1]);
        if (!isNaN(count)) {
          tags.push({ tag: parts[0], count });
        }
      }
    }

    if (tags.length === 0) {
      dv.paragraph("⚠️ Tag cloud log found but no valid entries parsed yet.");
    } else {
      // Sort by count descending (should already be sorted)
      tags.sort((a, b) => b.count - a.count);

      // Render tag cloud as styled pills
      const container = dv.el("div", "", { attr: { style: "display: flex; flex-wrap: wrap; gap: 6px; margin-bottom: 12px;" } });
      const maxCount = tags[0].count;
      for (const { tag, count } of tags.slice(0, 30)) {
        const ratio = count / maxCount;
        // Size: 0.8em to 1.4em, Opacity: 0.5 to 1.0
        const size = 0.8 + ratio * 0.6;
        const opacity = 0.5 + ratio * 0.5;
        const pill = container.createEl("span", {
          text: `${tag} (${count})`,
          attr: {
            style: `font-size: ${size}em; opacity: ${opacity}; padding: 2px 8px; background: var(--background-secondary); border: 1px solid var(--background-modifier-border); border-radius: 999px; cursor: default; transition: opacity 0.15s, transform 0.15s;`
          }
        });
        pill.addEventListener("mouseenter", () => { pill.style.opacity = "1"; pill.style.transform = "scale(1.05)"; });
        pill.addEventListener("mouseleave", () => { pill.style.opacity = opacity; pill.style.transform = "scale(1)"; });
      }

      dv.paragraph(`🏷️ **${tags.length} unique tag${tags.length !== 1 ? "s" : ""}** tracked. Top tags shown above (click tags in notes to filter via Dataview).`);

      // Show recent trends if available
      if (tagTrendsLog) {
        const trendsContent = await app.vault.read(tagTrendsLog);
        const trendLines = trendsContent.split("\n")
          .map(l => l.trim())
          .filter(l => l && !l.startsWith("#"))
          .slice(-14); // last 14 days

        if (trendLines.length > 0) {
          let output = "\n📈 **Recent tag trends (last " + trendLines.length + " days):**\n";
          for (const line of trendLines) {
            const parts = line.split(": ");
            if (parts.length === 2) {
              output += `- **${parts[0]}**: ${parts[1]}\n`;
            }
          }
          dv.paragraph(output);
        }
      }
    }
  }
}
```

_Same data powers the tag cloud above — tags are extracted automatically from session content by `session_tagger.py` (keyword-based, no external API). Run `python Scripts/session_tagger.py` manually to backfill older sessions, or let `hourly_archive.py` handle it on each hourly run._

---

**Tip:** install the community plugin **Homepage** and point it at this
note to have Obsidian open here automatically on vault launch. Not bundled
by default — plugin settings live in `.obsidian/plugins/*/data.json`,
which this template deliberately git-ignores (see [[SETUP#What's NOT included (by design)|SETUP.md]]).

See also: [[MOC]] (topic index), [[Welcome]] (orientation).
