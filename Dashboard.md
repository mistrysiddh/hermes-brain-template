---
type: dashboard
status: active
created: 2026-09-10
tags: [dashboard, hub]
---

# Dashboard

One glance at everything live in this vault. Requires the **Dataview**
plugin (already enabled) to render; without it these show as raw code
blocks instead of tables/lists.

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

---

**Tip:** install the community plugin **Homepage** and point it at this
note to have Obsidian open here automatically on vault launch. Not bundled
by default — plugin settings live in `.obsidian/plugins/*/data.json`,
which this template deliberately git-ignores (see [[SETUP#What's NOT included (by design)|SETUP.md]]).

See also: [[MOC]] (topic index), [[Welcome]] (orientation).
