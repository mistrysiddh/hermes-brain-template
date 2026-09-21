---
type: dashboard
status: beta
created: 2026-09-14
tags: [dashboard, hub, beta]
cssclasses: [dashboard-wide]
---

# 🧭 Hermes Brain Dashboard (Widescreen View)

> **Theme integration:** Styled via the `dashboard-beta` CSS snippet in **Settings → Appearance → CSS snippets** (toggle "dashboard-beta"). Frontmatter `cssclasses: [dashboard-wide]` activates responsive widescreen multi-column layouts. Requires Dataview plugin.

```dataviewjs
// === ROW 1: COMMAND CENTER & HUMAN-AGENT ALIGNMENT (2 COLUMNS) ===
if (window._hbDashClock) {
  clearInterval(window._hbDashClock);
  window._hbDashClock = null;
}

const grid = dv.el("div", "", { cls: "dashboard-2col" });

// --- LEFT: COMMAND CENTER ---
const leftCard = grid.createEl("div", { cls: "dashboard-card" });
const LS = { title: "hb-dash-title", mantra: "hb-dash-mantra", focus: "hb-dash-focus" };

const brandRow = leftCard.createEl("div", {
  attr: { style: "display: flex; justify-content: space-between; align-items: flex-start; flex-wrap: wrap; gap: 12px; margin-bottom: 8px;" }
});

const brand = brandRow.createEl("div");
const titleEl = brand.createEl("div", {
  text: localStorage.getItem(LS.title) || "HERMES BRAIN",
  attr: { contenteditable: "true", spellcheck: "false", style: "font-size: 1.25em; font-weight: 700; letter-spacing: 0.04em; color: var(--text-accent); outline: none;" }
});
titleEl.addEventListener("blur", () => {
  const v = titleEl.textContent.trim();
  if (v) localStorage.setItem(LS.title, v);
});

const mantraEl = brand.createEl("div", {
  text: localStorage.getItem(LS.mantra) || "agent memory & cognitive telemetry at a glance",
  attr: { contenteditable: "true", spellcheck: "false", style: "font-size: 0.8em; color: var(--text-muted); margin-top: 2px; outline: none;" }
});
mantraEl.addEventListener("blur", () => {
  const v = mantraEl.textContent.trim();
  if (v) localStorage.setItem(LS.mantra, v);
});

const clockBlock = brandRow.createEl("div", { attr: { style: "text-align: right;" } });
const timeEl = clockBlock.createEl("div", { attr: { style: "font-size: 1.45em; font-weight: 700; font-family: var(--font-monospace, monospace); color: var(--text-normal);" } });
const dateEl = clockBlock.createEl("div", { attr: { style: "font-size: 0.8em; color: var(--text-muted);" } });

function tick() {
  const now = new Date();
  const pad = n => String(n).padStart(2, "0");
  timeEl.textContent = `${pad(now.getHours())}:${pad(now.getMinutes())}:${pad(now.getSeconds())}`;
  dateEl.textContent = now.toLocaleDateString(undefined, { weekday: "short", month: "short", day: "numeric" });
}
tick();
window._hbDashClock = setInterval(tick, 1000);

const subRow = leftCard.createEl("div", {
  attr: { style: "display: flex; justify-content: space-between; align-items: center; flex-wrap: wrap; gap: 8px; padding-top: 8px; border-top: 1px solid var(--background-modifier-border);" }
});

const HOUR = new Date().getHours();
const GREETS = [
  { h: [0, 5],  label: "🌙 Late night session. Keep it steady." },
  { h: [5, 9],  label: "🌅 New day, new flow." },
  { h: [9, 13], label: "⚡ Peak focus hours. Engage." },
  { h: [13, 18],label: "☕ Afternoon momentum. Keep moving." },
  { h: [18, 21],label: "🌆 Evening wind-down & review." },
  { h: [21, 24],label: "🌌 Night review & memory consolidation." },
];
const G = GREETS.find(g => HOUR >= g.h[0] && HOUR < g.h[1]) || GREETS[5];
subRow.createEl("div", { text: G.label, attr: { style: "font-size: 0.9em; color: var(--text-normal);" } });

const today = new Date();
const todayFolderStr = `Daily/${today.getFullYear()}/${String(today.getMonth() + 1).padStart(2, "0")}/${String(today.getDate()).padStart(2, "0")}`;
const reviewNotes = dv.pages('"Daily"').where(p => p.file.path.startsWith(todayFolderStr) && (p.file.name.includes("Review") || p.file.name.includes("Daily-Review")));
const hasReview = reviewNotes.length > 0;

const reviewStatus = subRow.createEl("div", { attr: { style: "display: flex; align-items: center; gap: 6px;" } });
if (hasReview) {
  const badge = reviewStatus.createEl("span", { cls: "dashboard-badge dashboard-badge-ok", text: "✅ Daily Review Logged" });
  badge.style.cursor = "pointer";
  badge.addEventListener("click", () => app.workspace.openLinkText(reviewNotes[0].file.path, "", false));
} else {
  const badge = reviewStatus.createEl("span", { cls: "dashboard-badge dashboard-badge-warn", text: "⏳ Daily Review Pending" });
  badge.title = "Click to start today's Daily Review";
  badge.style.cursor = "pointer";
  badge.addEventListener("click", async () => {
    const tpl = app.vault.getAbstractFileByPath("Templates/Daily-Review.md");
    if (!tpl) { new Notice("Templates/Daily-Review.md not found"); return; }
    try { app.commands.executeCommandById("templater-obsidian:create-new-note-from-template"); }
    catch (e) { app.workspace.openLinkText("Templates/Daily-Review.md", "", false); }
  });
}

const focusContainer = leftCard.createEl("div", {
  attr: { style: "margin-top: 10px; padding: 10px 12px; background: var(--background-primary); border-radius: 6px; border: 1px solid var(--background-modifier-border);" }
});
focusContainer.createEl("div", {
  text: "🎯 TODAY'S FOCUS",
  attr: { style: "font-size: 0.7em; font-weight: 700; color: var(--text-accent); letter-spacing: 0.05em; margin-bottom: 4px;" }
});
const focusEl = focusContainer.createEl("div", {
  text: localStorage.getItem(LS.focus) || "Click here to set today's primary focus...",
  attr: { contenteditable: "true", spellcheck: "false", style: "font-size: 0.95em; outline: none; min-height: 1.3em; color: var(--text-normal);" }
});
focusEl.addEventListener("blur", () => {
  const v = focusEl.textContent.trim();
  if (v) localStorage.setItem(LS.focus, v);
});

// --- RIGHT: HUMAN-AGENT ALIGNMENT BRIEFING ---
const rightCard = grid.createEl("div", { cls: "dashboard-card" });
const header = rightCard.createEl("div", { cls: "dashboard-card-title" });
header.createEl("span", { text: "👤 Human & Agent Alignment Parameters" });
header.createEl("a", { text: "Edit Profile →", href: "User-Profile.md", cls: "internal-link", attr: { style: "font-size: 0.85em; text-transform: none; font-weight: normal;" } });

const userFile = app.vault.getAbstractFileByPath("User-Profile.md");
if (!userFile) {
  rightCard.createEl("div", { text: "User-Profile.md not found. Create it to document operational boundaries." });
} else {
  const userContent = await app.vault.read(userFile);
  const toneMatch = userContent.match(/-\s+\*\*Tone:\*\*\s*([^\n]+)/);
  const ruleMatch = userContent.match(/-\s+\*\*When in doubt:\*\*\s*([^\n]+)/);
  const formatMatch = userContent.match(/-\s+\*\*Output format:\*\*\s*([^\n]+)/);
  
  const clean = val => {
    if (!val) return "Not set";
    const v = val.trim();
    if (v.startsWith("_(") && v.endsWith(")_")) return "Default template — customize in User-Profile.md";
    return v.replace(/^_\(/, "").replace(/\)_$/, "");
  };

  const alignGrid = rightCard.createEl("div", { attr: { style: "display: grid; grid-template-columns: 1fr; gap: 8px; margin-top: 4px;" } });
  
  const toneBox = alignGrid.createEl("div", { attr: { style: "padding: 8px 10px; border-radius: 6px; background: var(--background-primary); border: 1px solid var(--background-modifier-border);" } });
  toneBox.createEl("div", { text: "PREFERRED TONE", attr: { style: "font-size: 0.7em; font-weight: 700; color: var(--text-accent); letter-spacing: 0.04em;" } });
  toneBox.createEl("div", { text: clean(toneMatch?.[1]), attr: { style: "font-size: 0.85em; color: var(--text-normal); margin-top: 2px;" } });

  const ruleBox = alignGrid.createEl("div", { attr: { style: "padding: 8px 10px; border-radius: 6px; background: var(--background-primary); border: 1px solid var(--background-modifier-border);" } });
  ruleBox.createEl("div", { text: "WHEN IN DOUBT RULE", attr: { style: "font-size: 0.7em; font-weight: 700; color: var(--text-accent); letter-spacing: 0.04em;" } });
  ruleBox.createEl("div", { text: clean(ruleMatch?.[1]), attr: { style: "font-size: 0.85em; color: var(--text-normal); margin-top: 2px;" } });

  const formatBox = alignGrid.createEl("div", { attr: { style: "padding: 8px 10px; border-radius: 6px; background: var(--background-primary); border: 1px solid var(--background-modifier-border);" } });
  formatBox.createEl("div", { text: "PREFERRED FORMAT", attr: { style: "font-size: 0.7em; font-weight: 700; color: var(--text-accent); letter-spacing: 0.04em;" } });
  formatBox.createEl("div", { text: clean(formatMatch?.[1]), attr: { style: "font-size: 0.85em; color: var(--text-normal); margin-top: 2px;" } });
}
```

```dataviewjs
// === ROW 2: QUICK ACTIONS & VISUAL CANVASES (2 COLUMNS) ===
const grid = dv.el("div", "", { cls: "dashboard-2col" });

// --- LEFT: QUICK ACTIONS & TOOLS ---
const leftCard = grid.createEl("div", { cls: "dashboard-card" });
leftCard.createEl("div", { cls: "dashboard-card-title", text: "⚡ Quick Actions & Tools" });

const ACTIONS = [
  { lbl: "📝 Daily Review", action: async () => {
      const tpl = app.vault.getAbstractFileByPath("Templates/Daily-Review.md");
      if (!tpl) { new Notice("Templates/Daily-Review.md not found"); return; }
      try { app.commands.executeCommandById("templater-obsidian:create-new-note-from-template"); }
      catch (e) { app.workspace.openLinkText("Templates/Daily-Review.md", "", false); }
  }},
  { lbl: "🧠 Memory Kanban", action: () => app.workspace.openLinkText("Memory-Review/Memory-Board.kanban", "", false) },
  { lbl: "⚡ Context Preamble", action: () => app.workspace.openLinkText("Memory-Review/HERMES-PREAMBLE.md", "", false) },
  { lbl: "⚠️ Log Lesson", action: () => app.workspace.openLinkText("Templates/Lesson-Learned.md", "", false) },
  { lbl: "📑 New ADR", action: () => app.workspace.openLinkText("Templates/Architecture-Decision-Record.md", "", false) },
  { lbl: "🔍 New Analysis", action: () => app.workspace.openLinkText("Templates/Personality-Judgment-Analysis.md", "", false) },
  { lbl: "✨ Smart Search", action: () => {
      try { app.commands.executeCommandById("smart-connections:Smart Connections: Open connections view"); }
      catch (e) { new Notice("Smart Connections view triggered"); }
  }},
  { lbl: "🛡️ Vault Audit", action: () => app.workspace.openLinkText("Skills-Notes/Vault-Audit-Report.md", "", false) },
];

const actionGrid = leftCard.createEl("div", { attr: { style: "display: grid; grid-template-columns: repeat(auto-fit, minmax(130px, 1fr)); gap: 8px;" } });
ACTIONS.forEach(a => {
  const btn = actionGrid.createEl("div", { cls: "dashboard-btn", text: a.lbl });
  btn.addEventListener("click", async () => {
    try { await a.action(); } catch (e) { new Notice(`Failed: ${a.lbl}`); console.error(e); }
  });
});

// --- RIGHT: VISUAL CANVASES (LAUNCHPAD) ---
const rightCard = grid.createEl("div", { cls: "dashboard-card" });
rightCard.createEl("div", { cls: "dashboard-card-title", text: "🗺️ Visual Architecture Canvases" });

const canvases = [
  { name: "Memory Pipeline", path: "Canvases/Memory-Pipeline.canvas", desc: "Cron export, staging & durable facts", color: "dashboard-badge-ok" },
  { name: "Personality Judgment", path: "Canvases/Personality-Judgment-Canvas.canvas", desc: "11-dimension behavioral analysis framework", color: "dashboard-badge-purple" }
];

const canvasGrid = rightCard.createEl("div", { attr: { style: "display: grid; grid-template-columns: 1fr; gap: 8px;" } });
canvases.forEach(c => {
  const row = canvasGrid.createEl("div", {
    attr: { style: "display: flex; justify-content: space-between; align-items: center; padding: 10px 12px; border-radius: 6px; background: var(--background-primary); border: 1px solid var(--background-modifier-border); cursor: pointer;" }
  });
  const left = row.createEl("div");
  left.createEl("div", { text: c.name, attr: { style: "font-weight: 600; font-size: 0.9em; color: var(--text-accent);" } });
  left.createEl("div", { text: c.desc, attr: { style: "font-size: 0.75em; color: var(--text-muted);" } });
  row.createEl("span", { cls: `dashboard-badge ${c.color}`, text: "Canvas" });
  row.addEventListener("click", () => app.workspace.openLinkText(c.path, "", false));
});
```

```dataviewjs
// === ROW 3: DOMAIN KNOWLEDGE HUBS (MOCS) & SESSION CALENDAR (2 COLUMNS) ===
const grid = dv.el("div", "", { cls: "dashboard-2col" });

// --- LEFT: DOMAIN KNOWLEDGE HUBS ---
const leftCard = grid.createEl("div", { cls: "dashboard-card" });
leftCard.createEl("div", { cls: "dashboard-card-title", text: "🌐 Domain Knowledge Hubs (MOCs)" });

const mocs = [
  { name: "Agentic Architecture", path: "Skills-Notes/Agentic-Architecture-MOC.md", desc: "Multi-agent systems, swarms & orchestration" },
  { name: "AI & Machine Learning", path: "Skills-Notes/AI-ML-MOC.md", desc: "Foundational models, embeddings & evaluation" },
  { name: "Cybersecurity", path: "Skills-Notes/Cybersecurity-MOC.md", desc: "Threat hunting, defenses & compliance" },
  { name: "Technology Stack", path: "Skills-Notes/Technology-Stack-MOC.md", desc: "Frameworks, databases, infrastructure" },
  { name: "Vault Master MOC", path: "README.md", desc: "Complete architectural index of the brain" }
];

const mocGrid = leftCard.createEl("div", { attr: { style: "display: grid; grid-template-columns: 1fr; gap: 7px;" } });
mocs.forEach(m => {
  const row = mocGrid.createEl("div", {
    attr: { style: "display: flex; justify-content: space-between; align-items: center; padding: 7px 10px; border-radius: 6px; background: var(--background-primary); border: 1px solid var(--background-modifier-border); cursor: pointer;" }
  });
  const l = row.createEl("div");
  l.createEl("div", { text: m.name, attr: { style: "font-weight: 600; font-size: 0.85em; color: var(--text-normal);" } });
  l.createEl("div", { text: m.desc, attr: { style: "font-size: 0.75em; color: var(--text-muted);" } });
  row.createEl("span", { cls: "dashboard-badge dashboard-badge-blue", text: "MOC" });
  row.addEventListener("click", () => app.workspace.openLinkText(m.path, "", false));
});

// --- RIGHT: SESSION CALENDAR ---
const rightCard = grid.createEl("div", { cls: "dashboard-card" });
rightCard.createEl("div", { cls: "dashboard-card-title", text: "📅 Session Calendar" });

let calY = new Date().getFullYear();
let calM = new Date().getMonth();
const calContainer = rightCard.createEl("div");

function buildSessionIndex() {
  const index = new Map();
  const dailyPages = dv.pages('"Daily"')
    .where(p => p.file.name !== "README" && p.file.name !== "manifest"
      && p.file.name !== "Timeline" && p.file.name !== "Chat-Correlation");

  const dailyArray = dailyPages.array ? dailyPages.array() : Array.from(dailyPages);
  for (const p of dailyArray) {
    let dateStr = null;
    const match = p.file.path.match(/Daily\/(\d{4})\/(\d{2})\/(\d{2})/);
    if (match) {
      dateStr = `${match[1]}-${match[2]}-${match[3]}`;
    } else if (p.file.cday) {
      dateStr = p.file.cday.toISODate();
    }
    if (dateStr) {
      if (!index.has(dateStr)) index.set(dateStr, []);
      index.get(dateStr).push(p);
    }
  }
  return index;
}

const sessionIndex = buildSessionIndex();

function renderCal() {
  calContainer.innerHTML = "";

  const nav = calContainer.createEl("div", {
    attr: { style: "display: flex; justify-content: space-between; align-items: center; margin-bottom: 6px;" }
  });
  const prev = nav.createEl("span", { text: "‹", attr: { style: "cursor: pointer; padding: 2px 10px; font-size: 1.2em; color: var(--text-muted);" } });
  nav.createEl("span", {
    text: new Date(calY, calM).toLocaleDateString(undefined, { year: "numeric", month: "long" }),
    attr: { style: "font-weight: 600; font-size: 0.9em;" }
  });
  const next = nav.createEl("span", { text: "›", attr: { style: "cursor: pointer; padding: 2px 10px; font-size: 1.2em; color: var(--text-muted);" } });

  prev.addEventListener("click", () => {
    calM--;
    if (calM < 0) { calM = 11; calY--; }
    renderCal();
  });
  next.addEventListener("click", () => {
    calM++;
    if (calM > 11) { calM = 0; calY++; }
    renderCal();
  });

  const tbl = calContainer.createEl("table", {
    attr: { style: "width: 100%; border-collapse: collapse; text-align: center; font-size: 0.8em;" }
  });
  const hRow = tbl.createEl("tr");
  ["Su", "Mo", "Tu", "We", "Th", "Fr", "Sa"].forEach(d => {
    hRow.createEl("th", { text: d, attr: { style: "padding: 2px; color: var(--text-muted); font-weight: normal;" } });
  });

  const firstDay = new Date(calY, calM, 1).getDay();
  const daysInMonth = new Date(calY, calM + 1, 0).getDate();
  const todayDate = new Date();
  const isCurrentMonth = todayDate.getFullYear() === calY && todayDate.getMonth() === calM;

  let cellRow = tbl.createEl("tr");
  for (let i = 0; i < firstDay; i++) {
    cellRow.createEl("td", { attr: { style: "padding: 3px;" } });
  }

  for (let d = 1; d <= daysInMonth; d++) {
    const colIdx = (firstDay + d - 1) % 7;
    if (colIdx === 0 && d > 1) cellRow = tbl.createEl("tr");

    const dateStr = `${calY}-${String(calM + 1).padStart(2, "0")}-${String(d).padStart(2, "0")}`;
    const sessions = sessionIndex.get(dateStr) || [];
    const isToday = isCurrentMonth && todayDate.getDate() === d;

    const cell = cellRow.createEl("td", {
      attr: { style: "padding: 3px; position: relative; cursor: pointer; border-radius: 4px;" }
    });
    if (isToday) {
      cell.style.background = "var(--background-modifier-hover)";
      cell.style.fontWeight = "700";
    }
    const numSpan = cell.createEl("div", { text: String(d) });
    if (sessions.length > 0) {
      const dot = cell.createEl("div", {
        attr: { style: "width: 5px; height: 5px; border-radius: 50%; background: var(--text-accent); margin: 1px auto 0 auto;" }
      });
      if (sessions.length > 3) dot.style.background = "#ff8a00";
    }
    cell.addEventListener("click", () => showDay(dateStr, sessions));
  }
}

const detailBox = rightCard.createEl("div", {
  attr: { style: "margin-top: 8px; padding-top: 6px; border-top: 1px solid var(--background-modifier-border); font-size: 0.85em;" }
});

function showDay(dateStr, sessions) {
  detailBox.innerHTML = "";
  detailBox.createEl("div", {
    text: `Sessions on ${dateStr} (${sessions.length}):`,
    attr: { style: "font-weight: 600; margin-bottom: 4px; color: var(--text-accent);" }
  });
  if (sessions.length === 0) {
    detailBox.createEl("div", { text: "No sessions recorded.", attr: { style: "color: var(--text-muted); font-size: 0.85em;" } });
  } else {
    const ul = detailBox.createEl("ul", { attr: { style: "margin: 0; padding-left: 16px;" } });
    for (const s of sessions) {
      const li = ul.createEl("li");
      li.createEl("a", { text: s.file.name, href: s.file.path, cls: "internal-link" });
    }
  }
}

renderCal();
```

## 📊 Telemetry & Overview

```dataviewjs
// === KPI STRIP (FULL WIDTH) ===
const vault = app.vault;

let totalTokens = 0, todayTokens = 0, activeDays = 0, weekSessions = 0;
const tokenLog = vault.getAbstractFileByPath("Skills-Notes/Token-Usage.log");
if (tokenLog) {
  const content = await vault.read(tokenLog);
  const lines = content.split("\n").map(l => l.trim())
    .filter(l => l && !l.startsWith("#") && !l.startsWith("---") && !l.startsWith("<!--"));
  const byDate = {};
  for (const line of lines) {
    const m = line.match(/^(\d{4}-\d{2}-\d{2}):\s*(\d+)\s*tokens?\s*\((\d+)\s*session/);
    if (m) {
      const [, date, tokens, sessions] = m;
      if (!byDate[date]) byDate[date] = { tokens: 0, sessions: 0 };
      byDate[date].tokens += parseInt(tokens);
      byDate[date].sessions += parseInt(sessions);
    }
  }
  const today = new Date().toISOString().split("T")[0];
  const sevenDaysAgo = new Date(Date.now() - 7 * 86400000).toISOString().split("T")[0];
  for (const [date, d] of Object.entries(byDate)) {
    totalTokens += d.tokens;
    if (d.tokens > 0) activeDays++;
    if (date === today) todayTokens = d.tokens;
    if (date >= sevenDaysAgo) weekSessions += d.sessions;
  }
}

const memPages = dv.pages('"Memory-Review"');
const memTasks = memPages?.file?.tasks;
const memTaskArray = memTasks ? (memTasks.array ? memTasks.array() : Array.from(memTasks)) : [];
const openCandidates = memTaskArray.filter(t => !t.completed).length;

const analysesCount = dv.pages('#personality-judgment or "Daily"')
  .where(p => p.subject && p.file.name !== "Personality-Judgment-Analysis.md" && p.file.name !== "Personality-Judgment-Dashboard.md").length;

const dailyPages = dv.pages('"Daily"')
  .where(p => p.file.name !== "README" && p.file.name !== "manifest"
    && p.file.name !== "Timeline" && p.file.name !== "Chat-Correlation");

let healthLabel = "No data", healthClass = "dashboard-badge-info";
if (dailyPages.length > 0) {
  const sortedDaily = dailyPages.sort(p => p.file.mtime, 'desc');
  const sortedArr = sortedDaily.array ? sortedDaily.array() : Array.from(sortedDaily);
  const newest = sortedArr[0];
  if (newest && newest.file && newest.file.mtime) {
    const mtimeMs = newest.file.mtime.toMillis ? newest.file.mtime.toMillis() : new Date(newest.file.mtime).getTime();
    const hoursAgo = (Date.now() - mtimeMs) / 3600000;
    if (hoursAgo < 3) { healthLabel = "Healthy"; healthClass = "dashboard-badge-ok"; }
    else if (hoursAgo < 48) { healthLabel = "Idle"; healthClass = "dashboard-badge-info"; }
    else { healthLabel = "Stale"; healthClass = "dashboard-badge-warn"; }
  }
}

const strip = dv.el("div", "", { cls: "dashboard-kpi-strip" });

function kpi(value, label, customColor) {
  const card = strip.createEl("div", { cls: "dashboard-kpi-card" });
  const val = card.createEl("div", { cls: "dashboard-kpi-value", text: value });
  if (customColor) val.style.color = customColor;
  card.createEl("div", { cls: "dashboard-kpi-label", text: label });
}

kpi(totalTokens.toLocaleString(), "Total Tokens");
kpi(todayTokens.toLocaleString(), "Tokens Today");
kpi(String(activeDays), "Active Days");
kpi(String(weekSessions), "Sessions (7d)");
kpi(String(openCandidates), "Open Facts");
kpi(String(analysesCount), "Analyses Run", "var(--text-accent)");

const healthCard = strip.createEl("div", { cls: "dashboard-kpi-card" });
healthCard.createEl("div", { cls: "dashboard-kpi-label", text: "Archiver Status" });
const badge = healthCard.createEl("span", { cls: `dashboard-badge ${healthClass}`, text: healthLabel });
badge.style.marginTop = "4px";
```

```dataviewjs
// === ROW 4: VERSION CHECK & LOCAL WEATHER (2 COLUMNS) ===
const grid = dv.el("div", "", { cls: "dashboard-2col" });

// --- LEFT: VERSION & UPSTREAM CHECK ---
const leftCard = grid.createEl("div", { cls: "dashboard-card" });
leftCard.createEl("div", { cls: "dashboard-card-title", text: "🏷️ Vault Version & Upstream Release" });

const versionFile = app.vault.getAbstractFileByPath("VERSION");
if (!versionFile) {
  leftCard.createEl("div", { text: "⚠️ No VERSION file found — unable to check upstream releases." });
} else {
  const local = (await app.vault.read(versionFile)).trim();
  try {
    const res = await fetch("https://api.github.com/repos/mistrysiddh/hermes-brain-template/releases/latest");
    if (!res.ok) throw new Error(`HTTP ${res.status}`);
    const data = await res.json();
    const latest = (data.tag_name || "").replace(/^v/, "");
    if (!latest) throw new Error("no tag_name in response");
    if (latest === local) {
      const row = leftCard.createEl("div");
      row.createEl("span", { cls: "dashboard-badge dashboard-badge-ok", text: `Up to date — v${local}` });
    } else {
      const row = leftCard.createEl("div");
      row.createEl("span", { cls: "dashboard-badge dashboard-badge-warn", text: `Update available: v${latest}` });
      const detail = leftCard.createEl("div", { attr: { style: "margin-top: 6px; color: var(--text-muted); font-size: 0.85em;" } });
      detail.createEl("span", { text: `Installed: v${local}. ` });
      detail.createEl("a", { text: "View Release Notes →", href: data.html_url, cls: "external-link" });
    }
  } catch (e) {
    const row = leftCard.createEl("div");
    row.createEl("span", { cls: "dashboard-badge dashboard-badge-info", text: `Installed: v${local}` });
    const note = leftCard.createEl("div", { attr: { style: "margin-top: 4px; font-size: 0.8em; color: var(--text-faint);" } });
    note.textContent = "Offline or rate-limited; displaying local version.";
  }
}

// --- RIGHT: LOCAL WEATHER ---
const rightCard = grid.createEl("div", { cls: "dashboard-card" });
rightCard.createEl("div", { cls: "dashboard-card-title", text: "⛅ Local Environment & Weather" });

const W_LS = { city: "hb-weather-city", key: "hb-weather-key" };
let savedCity = localStorage.getItem(W_LS.city) || "";
let savedKey = localStorage.getItem(W_LS.key) || "";

const wBody = rightCard.createEl("div");

function renderWeatherConfig() {
  wBody.innerHTML = "";
  const form = wBody.createEl("div", { attr: { style: "display: flex; flex-direction: column; gap: 8px;" } });
  form.createEl("div", { text: "Enter City & OpenWeatherMap API Key:", attr: { style: "font-size: 0.85em; color: var(--text-muted);" } });
  
  const cIn = form.createEl("input", { attr: { type: "text", placeholder: "e.g. London, UK", value: savedCity, style: "padding: 4px 8px; border-radius: 4px; border: 1px solid var(--background-modifier-border); background: var(--background-primary); font-size: 0.85em;" } });
  const kIn = form.createEl("input", { attr: { type: "password", placeholder: "OpenWeatherMap API Key", value: savedKey, style: "padding: 4px 8px; border-radius: 4px; border: 1px solid var(--background-modifier-border); background: var(--background-primary); font-size: 0.85em;" } });
  
  const saveBtn = form.createEl("button", { text: "Save & Fetch Weather", cls: "dashboard-btn", attr: { style: "width: fit-content; padding: 4px 12px; font-size: 0.85em;" } });
  saveBtn.addEventListener("click", () => {
    savedCity = cIn.value.trim();
    savedKey = kIn.value.trim();
    localStorage.setItem(W_LS.city, savedCity);
    localStorage.setItem(W_LS.key, savedKey);
    fetchWeather();
  });
}

async function fetchWeather() {
  if (!savedCity || !savedKey) {
    renderWeatherConfig();
    return;
  }
  wBody.innerHTML = "Fetching current weather...";
  try {
    const res = await fetch(`https://api.openweathermap.org/data/2.5/weather?q=${encodeURIComponent(savedCity)}&appid=${savedKey}&units=metric`);
    if (!res.ok) throw new Error(`HTTP ${res.status}`);
    const data = await res.json();
    
    wBody.innerHTML = "";
    const row = wBody.createEl("div", { attr: { style: "display: flex; justify-content: space-between; align-items: center;" } });
    const info = row.createEl("div");
    info.createEl("div", { text: `${data.name}, ${data.sys?.country || ""}`, attr: { style: "font-weight: 600; font-size: 1em; color: var(--text-normal);" } });
    info.createEl("div", { text: data.weather?.[0]?.description ? data.weather[0].description.toUpperCase() : "", attr: { style: "font-size: 0.75em; color: var(--text-muted); letter-spacing: 0.04em;" } });
    
    const tempBlock = row.createEl("div", { attr: { style: "text-align: right;" } });
    tempBlock.createEl("div", { text: `${Math.round(data.main?.temp)}°C`, attr: { style: "font-size: 1.5em; font-weight: 700; color: var(--text-accent); font-family: var(--font-monospace, monospace);" } });
    tempBlock.createEl("div", { text: `Humidity: ${data.main?.humidity}% · Wind: ${Math.round(data.wind?.speed || 0)} m/s`, attr: { style: "font-size: 0.75em; color: var(--text-muted);" } });
    
    const editBtn = wBody.createEl("div", { attr: { style: "margin-top: auto; padding-top: 8px; font-size: 0.75em; color: var(--text-faint); cursor: pointer;" }, text: "⚙️ Change location" });
    editBtn.addEventListener("click", renderWeatherConfig);
  } catch (err) {
    wBody.innerHTML = "";
    wBody.createEl("div", { text: `Weather unavailable: ${err.message}`, attr: { style: "color: var(--text-muted); font-size: 0.85em;" } });
    const retry = wBody.createEl("div", { attr: { style: "margin-top: 4px; font-size: 0.8em; color: var(--text-accent); cursor: pointer;" }, text: "Reconfigure settings" });
    retry.addEventListener("click", renderWeatherConfig);
  }
}

fetchWeather();
```

## 📈 Activity Heatmap & Token Trends

```dataviewjs
// === TOKEN TRENDS & 18-WEEK HEATMAP (FULL WIDTH) ===
const card = dv.el("div", "", { cls: "dashboard-card" });
card.createEl("div", { cls: "dashboard-card-title", text: "📈 Token Activity Heatmap (Last 18 Weeks)" });

const logFile = app.vault.getAbstractFileByPath("Skills-Notes/Token-Usage.log");
const dataByDay = {};

if (logFile) {
  const content = await app.vault.read(logFile);
  const lines = content.split("\n").map(l => l.trim())
    .filter(l => l && !l.startsWith("#") && !l.startsWith("---") && !l.startsWith("<!--"));
  for (const line of lines) {
    const m = line.match(/^(\d{4}-\d{2}-\d{2}):\s*(\d+)/);
    if (m) dataByDay[m[1]] = (dataByDay[m[1]] || 0) + parseInt(m[2]);
  }
}

const WEEKS = 18;
const today = new Date();
const cells = [];
for (let i = WEEKS * 7 - 1; i >= 0; i--) {
  const d = new Date(today);
  d.setDate(d.getDate() - i);
  const key = d.toISOString().split("T")[0];
  cells.push({ date: key, val: dataByDay[key] || 0, dayOfWeek: d.getDay() });
}

const maxTokens = Math.max(1, ...Object.values(dataByDay));

const container = card.createEl("div", {
  attr: { style: "display: flex; gap: 8px; align-items: flex-start; overflow-x: auto; padding: 6px 0;" }
});

const dayLabels = container.createEl("div", {
  attr: { style: "display: flex; flex-direction: column; gap: 3px; font-size: 9px; color: var(--text-muted); line-height: 12px; margin-top: 1px;" }
});
["", "M", "", "W", "", "F", ""].forEach(label => {
  dayLabels.createEl("div", { text: label, attr: { style: "height: 12px; width: 10px; text-align: center;" } });
});

const gridWrap = container.createEl("div", {
  attr: { style: "display: flex; gap: 3px;" }
});

for (let w = 0; w < WEEKS; w++) {
  const col = gridWrap.createEl("div", {
    attr: { style: "display: flex; flex-direction: column; gap: 3px;" }
  });
  for (let d = 0; d < 7; d++) {
    const idx = w * 7 + d;
    const c = cells[idx];
    const cell = col.createEl("div", {
      attr: {
        style: "width: 12px; height: 12px; border-radius: 2px; cursor: pointer; transition: transform 0.1s;",
        title: `${c.date}: ${c.val.toLocaleString()} tokens`
      }
    });
    if (c.val === 0) {
      cell.style.background = "var(--background-modifier-border)";
    } else {
      const ratio = c.val / maxTokens;
      const alpha = Math.max(0.25, Math.min(1.0, 0.2 + ratio * 0.8));
      cell.style.background = `rgba(187, 134, 252, ${alpha.toFixed(2)})`;
    }
    cell.addEventListener("mouseenter", () => cell.style.transform = "scale(1.25)");
    cell.addEventListener("mouseleave", () => cell.style.transform = "scale(1.0)");
  }
}

const legend = card.createEl("div", {
  attr: { style: "display: flex; justify-content: flex-end; align-items: center; gap: 6px; font-size: 0.75em; color: var(--text-muted); margin-top: 6px;" }
});
legend.createEl("span", { text: "Less" });
[0, 0.25, 0.5, 0.75, 1.0].forEach(a => {
  const b = legend.createEl("div", { attr: { style: "width: 10px; height: 10px; border-radius: 2px;" } });
  b.style.background = a === 0 ? "var(--background-modifier-border)" : `rgba(187, 134, 252, ${a})`;
});
legend.createEl("span", { text: "More" });
```

## 📂 Active Workspace & Operations

```dataviewjs
// === ROW 5: ACTIVE PROJECTS & CONSOLIDATED ACTION ITEMS (2 COLUMNS) ===
const grid = dv.el("div", "", { cls: "dashboard-2col" });

// --- LEFT: ACTIVE PROJECTS ---
const leftCard = grid.createEl("div", { cls: "dashboard-card" });
leftCard.createEl("div", { cls: "dashboard-card-title", text: "🚀 Active Projects" });

const activeProjects = dv.pages('"Projects"').where(p => p.type === "project" && p.status === "active").sort(p => p.created, 'desc');
const projList = activeProjects.array ? activeProjects.array() : Array.from(activeProjects);

if (projList.length === 0) {
  leftCard.createEl("div", { text: "No active projects currently listed." });
} else {
  const table = leftCard.createEl("table", { attr: { style: "width: 100%; border-collapse: collapse;" } });
  const headRow = table.createEl("tr");
  ["Project", "Status", "Date"].forEach(h => {
    headRow.createEl("th", { text: h, attr: { style: "text-align: left; padding: 4px 8px 4px 0; border-bottom: 1px solid var(--background-modifier-border); color: var(--text-muted); font-size: 0.8em; text-transform: uppercase;" } });
  });
  for (const p of projList) {
    const row = table.createEl("tr");
    const nameCell = row.createEl("td", { attr: { style: "padding: 5px 8px 5px 0; border-bottom: 1px solid var(--background-modifier-border);" } });
    nameCell.createEl("a", { text: p.file.name, href: p.file.path, cls: "internal-link" });
    row.createEl("td", { text: p.status ?? "active", attr: { style: "padding: 5px 8px 5px 0; border-bottom: 1px solid var(--background-modifier-border); font-size: 0.85em;" } });
    
    let createdDate = "Active";
    if (p.created && typeof p.created === "string" && !p.created.includes("{{")) {
      createdDate = p.created;
    } else if (p.created && typeof p.created !== "string") {
      createdDate = String(p.created);
    } else if (p.file.cday) {
      createdDate = p.file.cday.toISODate();
    }
    row.createEl("td", { text: createdDate, attr: { style: "padding: 5px 0; border-bottom: 1px solid var(--background-modifier-border); color: var(--text-muted); font-size: 0.85em;" } });
  }
}

// --- RIGHT: CONSOLIDATED PROJECT ACTION ITEMS ---
const rightCard = grid.createEl("div", { cls: "dashboard-card" });
rightCard.createEl("div", { cls: "dashboard-card-title", text: "✅ Project Action Items & Next Tasks" });

const projPages = dv.pages('"Projects"');
const projectTasks = projPages?.file?.tasks;
const allTasks = projectTasks ? (projectTasks.array ? projectTasks.array() : Array.from(projectTasks)) : [];
const taskList = allTasks.filter(t => !t.completed);

if (taskList.length === 0) {
  rightCard.createEl("div", { text: "No pending action items found across active projects." });
} else {
  const ul = rightCard.createEl("ul", { attr: { style: "margin: 0; padding-left: 18px;" } });
  for (const t of taskList.slice(0, 7)) {
    const li = ul.createEl("li", { attr: { style: "padding: 3px 0; font-size: 0.85em;" } });
    const taskText = (t.text || String(t)).trim() || "Action item pending definition";
    li.createEl("span", { text: taskText });
    if (t.link) {
      const pLink = li.createEl("span", { attr: { style: "margin-left: 8px; font-size: 0.8em;" } });
      pLink.createEl("a", { text: `[${t.link.fileName || 'Project'}]`, href: t.link.path || "", cls: "internal-link" });
    }
  }
  if (taskList.length > 7) {
    rightCard.createEl("div", { text: `…and ${taskList.length - 7} more project action items.`, attr: { style: "color: var(--text-muted); font-size: 0.85em; margin-top: 6px;" } });
  }
}
```

## 🤖 Intelligence & Agent Roster

```dataviewjs
// === ROW 6: PERSONALITY JUDGMENT & MULTI-AGENT TEAM (2 COLUMNS) ===
const grid = dv.el("div", "", { cls: "dashboard-2col" });

// --- LEFT: PERSONALITY JUDGMENT ---
const leftCard = grid.createEl("div", { cls: "dashboard-card" });
leftCard.createEl("div", { cls: "dashboard-card-title", text: "🎭 Personality & Behavioral Analyses" });

const analyses = dv.pages('#personality-judgment or "Daily"')
  .where(p => p.subject && p.file.name !== "Personality-Judgment-Analysis.md" && p.file.name !== "Personality-Judgment-Dashboard.md")
  .sort(p => p.file.mtime, 'desc');

const list = analyses.array ? analyses.array() : Array.from(analyses);
if (list.length === 0) {
  leftCard.createEl("div", { text: "No personality analyses recorded yet. Launch one via Quick Actions." });
} else {
  const table = leftCard.createEl("table", { attr: { style: "width: 100%; border-collapse: collapse;" } });
  const headRow = table.createEl("tr");
  ["Subject", "Primary Style", "Confidence"].forEach(h => {
    headRow.createEl("th", { text: h, attr: { style: "text-align: left; padding: 4px 8px 4px 0; border-bottom: 1px solid var(--background-modifier-border); color: var(--text-muted); font-size: 0.8em; text-transform: uppercase;" } });
  });
  for (const a of list.slice(0, 5)) {
    const row = table.createEl("tr");
    const nameCell = row.createEl("td", { attr: { style: "padding: 5px 8px 5px 0; border-bottom: 1px solid var(--background-modifier-border);" } });
    nameCell.createEl("a", { text: a.subject, href: a.file.path, cls: "internal-link" });
    row.createEl("td", { text: a.primary_style ?? "—", attr: { style: "padding: 5px 8px 5px 0; border-bottom: 1px solid var(--background-modifier-border); font-size: 0.85em;" } });
    
    const conf = a.confidence ? String(a.confidence).trim() : "Review";
    let confBadge = "dashboard-badge-info";
    if (conf.toLowerCase() === "high") confBadge = "dashboard-badge-ok";
    else if (conf.toLowerCase() === "medium") confBadge = "dashboard-badge-warn";
    
    const confCell = row.createEl("td", { attr: { style: "padding: 5px 0; border-bottom: 1px solid var(--background-modifier-border);" } });
    confCell.createEl("span", { cls: `dashboard-badge ${confBadge}`, text: conf });
  }
}
const footerP = leftCard.createEl("div", { attr: { style: "margin-top: auto; padding-top: 8px; font-size: 0.85em;" } });
footerP.createEl("a", { text: "Open Full Personality Dashboard →", href: "Templates/Personality-Judgment-Dashboard.md", cls: "internal-link" });

// --- RIGHT: MULTI-AGENT TEAM ROSTER ---
const rightCard = grid.createEl("div", { cls: "dashboard-card" });
rightCard.createEl("div", { cls: "dashboard-card-title", text: "🤖 Multi-Agent Team Roster" });

const teamFile = app.vault.getAbstractFileByPath("Skills-Notes/Team-Profiles-Index.md");
if (!teamFile) {
  rightCard.createEl("div", { text: "Skills-Notes/Team-Profiles-Index.md not found." });
} else {
  const content = await app.vault.read(teamFile);
  const rows = content.split("\n")
    .filter(l => l.trim().startsWith("|"))
    .filter(l => !l.includes("---") && !l.toLowerCase().includes("profile |"));
  
  if (rows.length === 0) {
    rightCard.createEl("div", { text: "No profiles configured in Team-Profiles-Index.md." });
  } else {
    const table = rightCard.createEl("table", { attr: { style: "width: 100%; border-collapse: collapse;" } });
    const headRow = table.createEl("tr");
    ["Profile", "Specialization"].forEach(h => {
      headRow.createEl("th", { text: h, attr: { style: "text-align: left; padding: 4px 8px 4px 0; border-bottom: 1px solid var(--background-modifier-border); color: var(--text-muted); font-size: 0.8em; text-transform: uppercase;" } });
    });
    for (const r of rows) {
      const cols = r.split("|").map(c => c.trim()).filter(c => c.length > 0);
      if (cols.length >= 2) {
        const row = table.createEl("tr");
        const nameCell = row.createEl("td", { attr: { style: "padding: 4px 8px 4px 0; border-bottom: 1px solid var(--background-modifier-border); font-weight: 600; font-size: 0.85em; color: var(--text-accent);" } });
        nameCell.textContent = cols[0];
        const specCell = row.createEl("td", { attr: { style: "padding: 4px 0; border-bottom: 1px solid var(--background-modifier-border); color: var(--text-muted); font-size: 0.85em;" } });
        specCell.textContent = cols[1];
      }
    }
  }
}
const footerT = rightCard.createEl("div", { attr: { style: "margin-top: auto; padding-top: 8px; font-size: 0.85em;" } });
footerT.createEl("a", { text: "Correlate Chats by Agent →", href: "Daily/Chat-Correlation.md", cls: "internal-link" });
```

## ⚡ Competency & Research

```dataviewjs
// === ROW 7: SKILL RADAR & ACTIVE RESEARCH (2 COLUMNS) ===
const grid = dv.el("div", "", { cls: "dashboard-2col" });

// --- LEFT: HERMES SKILL COMPETENCIES ---
const leftCard = grid.createEl("div", { cls: "dashboard-card" });
const headerS = leftCard.createEl("div", { cls: "dashboard-card-title" });
headerS.createEl("span", { text: "⚡ Hermes Skill Competencies" });
headerS.createEl("a", { text: "Full Catalog →", href: "Skills-Notes/Installed-Skills-Index.md", cls: "internal-link", attr: { style: "font-size: 0.85em; text-transform: none; font-weight: normal;" } });

const mapFile = app.vault.getAbstractFileByPath("Scripts/tag_skill_map.json");
if (mapFile) {
  try {
    const raw = await app.vault.read(mapFile);
    const map = JSON.parse(raw);
    const categories = Object.entries(map).filter(([_, skills]) => skills && skills.length > 0).slice(0, 6);
    
    const catGrid = leftCard.createEl("div", { attr: { style: "display: grid; grid-template-columns: repeat(auto-fit, minmax(180px, 1fr)); gap: 8px;" } });
    categories.forEach(([cat, skills]) => {
      const box = catGrid.createEl("div", { attr: { style: "padding: 8px 10px; border-radius: 6px; background: var(--background-primary); border: 1px solid var(--background-modifier-border);" } });
      box.createEl("div", { text: cat.toUpperCase(), attr: { style: "font-size: 0.7em; font-weight: 700; color: var(--text-accent); letter-spacing: 0.04em;" } });
      const listStr = skills.map(s => s.replace(/-/g, " ")).join(", ");
      box.createEl("div", { text: listStr, attr: { style: "font-size: 0.8em; color: var(--text-muted); margin-top: 3px; line-height: 1.3;" } });
    });
  } catch (e) {
    leftCard.createEl("div", { text: "Skill mapping indexed in Scripts/tag_skill_map.json" });
  }
} else {
  leftCard.createEl("div", { text: "Maintain skills in Skills-Notes/Installed-Skills-Index.md." });
}

// --- RIGHT: ACTIVE RESEARCH INVESTIGATIONS ---
const rightCard = grid.createEl("div", { cls: "dashboard-card" });
rightCard.createEl("div", { cls: "dashboard-card-title", text: "🔬 Active Research & Inquiries" });

const researchNotes = dv.pages('"Research"')
  .where(p => p.file.name !== "README")
  .sort(p => p.file.mtime, 'desc');

const resList = researchNotes.array ? researchNotes.array() : Array.from(researchNotes);
if (resList.length === 0) {
  rightCard.createEl("div", { text: "No research notes logged. Use Research/ to organize technical investigations." });
} else {
  const ul = rightCard.createEl("ul", { attr: { style: "margin: 0; padding-left: 18px;" } });
  for (const r of resList.slice(0, 6)) {
    const li = ul.createEl("li", { attr: { style: "padding: 3px 0; font-size: 0.85em;" } });
    li.createEl("a", { text: r.file.name, href: r.file.path, cls: "internal-link" });
    if (r.tags && r.tags.length > 0) {
      const tagSpan = li.createEl("span", { attr: { style: "color: var(--text-faint); font-size: 0.8em; margin-left: 6px;" } });
      tagSpan.textContent = `(${r.tags.join(", ")})`;
    }
  }
}
```

## 🧠 Memory Pipeline & Vault Pulse

```dataviewjs
// === ROW 8: MEMORY PIPELINE & GLOBAL VAULT PULSE (2 COLUMNS) ===
const grid = dv.el("div", "", { cls: "dashboard-2col" });

// --- LEFT: MEMORY PIPELINE & PROMOTION ---
const leftCard = grid.createEl("div", { cls: "dashboard-card" });
leftCard.createEl("div", { cls: "dashboard-card-title", text: "🧠 Memory Pipeline & Promotion" });

const memPages = dv.pages('"Memory-Review"');
const allTasks = memPages?.file?.tasks;
const taskArray = allTasks ? (allTasks.array ? allTasks.array() : Array.from(allTasks)) : [];
const completed = taskArray.filter(t => t.completed).length;
const pending = taskArray.filter(t => !t.completed).length;
const total = completed + pending;
const pct = total > 0 ? Math.round((completed / total) * 100) : 100;

const statsRow = leftCard.createEl("div", { attr: { style: "display: flex; justify-content: space-between; align-items: center; font-size: 0.85em; color: var(--text-muted); margin-bottom: 4px;" } });
statsRow.createEl("span", { text: `Durable Facts: ${completed} promoted` });
statsRow.createEl("span", { text: `${pending} pending review (${pct}% complete)` });

const track = leftCard.createEl("div", { cls: "dashboard-progress-track" });
const fill = track.createEl("div", { cls: "dashboard-progress-fill" });
fill.style.width = `${pct}%`;

const note = leftCard.createEl("div", { attr: { style: "display: flex; justify-content: space-between; align-items: center; margin-top: auto; padding-top: 8px; font-size: 0.8em; color: var(--text-faint);" } });
note.createEl("span", { text: "Nightly: consolidate_memory.py & sync_to_hermes.py" });
const boardLink = note.createEl("a", { text: "Open Kanban Board →", href: "Memory-Review/Memory-Board.kanban", cls: "internal-link" });

// --- RIGHT: GLOBAL VAULT PULSE ---
const rightCard = grid.createEl("div", { cls: "dashboard-card" });
const headerP = rightCard.createEl("div", { cls: "dashboard-card-title" });
headerP.createEl("span", { text: "🌐 Global Vault Pulse (Non-Daily Edits)" });

const allPages = dv.pages();
const allPagesArr = allPages.array ? allPages.array() : Array.from(allPages);
const allMd = allPagesArr.filter(p => p.file && p.file.extension === "md");
const totalCanvases = allPagesArr.filter(p => p.file && p.file.extension === "canvas").length;

headerP.createEl("span", {
  text: `${allMd.length} notes · ${totalCanvases} canvases`,
  attr: { style: "font-size: 0.85em; text-transform: none; color: var(--text-muted); font-weight: normal;" }
});

function timeAgo(mtime) {
  if (!mtime) return "";
  const ms = Date.now() - (mtime.toMillis ? mtime.toMillis() : new Date(mtime).getTime());
  const min = Math.floor(ms / 60000);
  if (min < 1) return "just now";
  if (min < 60) return `${min}m ago`;
  const hr = Math.floor(min / 60);
  if (hr < 24) return `${hr}h ago`;
  const d = Math.floor(hr / 24);
  return `${d}d ago`;
}

const recentQuery = dv.pages()
  .where(p => p.file && p.file.extension === "md" && !p.file.path.startsWith("Daily/") && p.file.name !== "Dashboard-Beta")
  .sort(p => p.file.mtime, 'desc');
const recentArray = recentQuery.array ? recentQuery.array() : Array.from(recentQuery);
const recentFiles = recentArray.slice(0, 6);

const table = rightCard.createEl("table", { attr: { style: "width: 100%; border-collapse: collapse; margin-top: 4px;" } });
const headRow = table.createEl("tr");
["Note", "Folder", "Edited"].forEach(h => {
  headRow.createEl("th", { text: h, attr: { style: "text-align: left; padding: 4px 8px 4px 0; border-bottom: 1px solid var(--background-modifier-border); color: var(--text-muted); font-size: 0.8em; text-transform: uppercase;" } });
});

for (const f of recentFiles) {
  const row = table.createEl("tr");
  const nameCell = row.createEl("td", { attr: { style: "padding: 4px 8px 4px 0; border-bottom: 1px solid var(--background-modifier-border);" } });
  nameCell.createEl("a", { text: f.file.name, href: f.file.path, cls: "internal-link" });
  row.createEl("td", { text: f.file.folder || "(root)", attr: { style: "padding: 4px 8px 4px 0; border-bottom: 1px solid var(--background-modifier-border); color: var(--text-muted); font-size: 0.85em;" } });
  row.createEl("td", { text: timeAgo(f.file.mtime), attr: { style: "padding: 4px 0; border-bottom: 1px solid var(--background-modifier-border); color: var(--text-faint); font-size: 0.85em;" } });
}
```

## 🛡️ Health & Topical Index

```dataviewjs
// === ROW 9: VAULT HEALTH & TOPICAL TAG CLOUD (2 COLUMNS) ===
const grid = dv.el("div", "", { cls: "dashboard-2col" });

// --- LEFT: VAULT HEALTH CHECKS ---
const leftCard = grid.createEl("div", { cls: "dashboard-card" });
leftCard.createEl("div", { cls: "dashboard-card-title", text: "🛡️ Vault Health & Integrity" });

const auditReport = app.vault.getAbstractFileByPath("Skills-Notes/Vault-Audit-Report.md");
if (!auditReport) {
  leftCard.createEl("div", { text: "Audit report not found — will generate on first vault_audit.py run." });
} else {
  const content = await app.vault.read(auditReport);
  const summaryMatch = content.match(/## Summary\n\n([\s\S]*?)\n---/);
  if (summaryMatch) {
    const lines = summaryMatch[1].trim().split('\n').map(l => l.trim()).filter(l => l.startsWith('-'));
    for (const line of lines) {
      const m = line.match(/-\s+\*\*([^*]+)\*\*:\s*(\d+)/);
      if (m) {
        const [, label, count] = m;
        const row = leftCard.createEl("div", { attr: { style: "display: flex; justify-content: space-between; align-items: center; padding: 3px 0;" } });
        row.createEl("span", { text: label, attr: { style: "color: var(--text-muted); font-size: 0.85em;" } });
        const cls = parseInt(count) > 0 ? "dashboard-badge-warn" : "dashboard-badge-ok";
        row.createEl("span", { cls: `dashboard-badge ${cls}`, text: count });
      }
    }
  }
  const genMatch = content.match(/Generated:\s*([^\n]+)/);
  if (genMatch) {
    const footer = leftCard.createEl("div", { attr: { style: "margin-top: auto; padding-top: 8px; font-size: 0.8em; color: var(--text-faint);" } });
    footer.createEl("span", { text: `Audit run: ${genMatch[1].trim()} · ` });
    footer.createEl("a", { text: "Full report →", href: "Skills-Notes/Vault-Audit-Report.md", cls: "internal-link" });
  }
}

// --- RIGHT: TOPICAL VAULT TAG CLOUD ---
const rightCard = grid.createEl("div", { cls: "dashboard-card" });
rightCard.createEl("div", { cls: "dashboard-card-title", text: "🏷️ Vault Topical Tags" });

const allPages = dv.pages();
const allPagesList = allPages.array ? allPages.array() : Array.from(allPages);
const tagCounts = {};
for (const p of allPagesList) {
  if (p.file && p.file.tags) {
    for (const t of p.file.tags) {
      const cleanTag = t.startsWith("#") ? t : "#" + t;
      tagCounts[cleanTag] = (tagCounts[cleanTag] || 0) + 1;
    }
  }
}
const sortedTags = Object.entries(tagCounts).sort((a, b) => b[1] - a[1]).slice(0, 16);

if (sortedTags.length === 0) {
  rightCard.createEl("div", { text: "No tags indexed in vault." });
} else {
  const container = rightCard.createEl("div", { attr: { style: "display: flex; flex-wrap: wrap; gap: 6px; padding: 4px 0;" } });
  sortedTags.forEach(([tag, count]) => {
    const pill = container.createEl("div", { cls: "dashboard-tag-pill" });
    pill.createEl("span", { text: tag });
    pill.createEl("span", { cls: "dashboard-tag-count", text: String(count) });
    pill.addEventListener("click", () => {
      try {
        const searchPlugin = app.internalPlugins.getPluginById("global-search");
        if (searchPlugin && searchPlugin.instance) {
          searchPlugin.instance.openGlobalSearch(`tag:${tag}`);
        }
      } catch (e) {
        console.error("Search failed:", e);
      }
    });
  });
}
```

## 📜 Recent Archived Sessions

```dataviewjs
// === ROW 10: RECENT DAILY SESSIONS (FULL WIDTH TABLE) ===
const card = dv.el("div", "", { cls: "dashboard-card" });
card.createEl("div", { cls: "dashboard-card-title", text: "📜 Recent Chat Sessions" });

const dailyPages = dv.pages('"Daily"')
  .where(p => p.file.name !== "README" && p.file.name !== "manifest"
    && p.file.name !== "Timeline" && p.file.name !== "Chat-Correlation")
  .sort(p => p.file.mtime, 'desc');

const list = dailyPages.array ? dailyPages.array() : Array.from(dailyPages);
if (list.length === 0) {
  card.createEl("div", { text: "No archived sessions found in Daily/." });
} else {
  const table = card.createEl("table", { attr: { style: "width: 100%; border-collapse: collapse;" } });
  const headRow = table.createEl("tr");
  ["Session", "Modified", "Folder"].forEach(h => {
    headRow.createEl("th", { text: h, attr: { style: "text-align: left; padding: 4px 8px 4px 0; border-bottom: 1px solid var(--background-modifier-border); color: var(--text-muted); font-size: 0.8em; text-transform: uppercase;" } });
  });
  for (const p of list.slice(0, 8)) {
    const row = table.createEl("tr");
    const nameCell = row.createEl("td", { attr: { style: "padding: 5px 8px 5px 0; border-bottom: 1px solid var(--background-modifier-border);" } });
    nameCell.createEl("a", { text: p.file.name, href: p.file.path, cls: "internal-link" });
    row.createEl("td", { text: p.file.mtime ? p.file.mtime.toISODate() : "", attr: { style: "padding: 5px 8px 5px 0; border-bottom: 1px solid var(--background-modifier-border); color: var(--text-muted); font-size: 0.85em;" } });
    row.createEl("td", { text: p.file.folder ?? "", attr: { style: "padding: 5px 0; border-bottom: 1px solid var(--background-modifier-border); color: var(--text-muted); font-size: 0.85em;" } });
  }
}
const footer = card.createEl("div", { attr: { style: "margin-top: 8px; font-size: 0.85em;" } });
footer.createEl("a", { text: "View Complete Timeline Archive →", href: "Daily/Timeline.md", cls: "internal-link" });
```

---

_Widescreen card dashboard for Hermes Brain Vault. Original linear view maintained at [[Dashboard]]._
