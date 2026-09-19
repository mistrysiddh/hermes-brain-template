---
type: dashboard
status: beta
created: 2026-09-14
tags: [dashboard, hub, beta]
cssclasses: [dashboard-wide]
---

# Dashboard (Beta — card layout)

> **To activate:** Enable the `dashboard-beta` CSS snippet in **Settings → Appearance → CSS snippets** (toggle "dashboard-beta"). Requires Dataview plugin.

Experimental redesign of [[Dashboard]] as a website-style card dashboard: a
KPI strip up top, styled cards below, badges instead of inline emoji-text.
Same underlying data AND same level of detail as the original — nothing
new to configure, nothing trimmed. Needs the **dashboard-beta.css**
snippet enabled (Settings → Appearance → CSS snippets → toggle
"dashboard-beta") plus Dataview.

If this doesn't render as cards, the snippet isn't enabled — you'll still
see the data, just unstyled.

## Welcome

```dataviewjs
// Header card — brand/mantra (editable, localStorage-only) + live clock +
// mood-based greeting, adapted from Komorebi
// (InlitX/Obsidian-Dashboard-Gallery, MIT). localStorage keeps this
// personalization local to this machine/vault only — never committed,
// never leaves this device.
const card = dv.el("div", "", { cls: "dashboard-card" });

const LS = { title: "hb-dash-title", mantra: "hb-dash-mantra" };

const brandRow = card.createEl("div", { attr: { style: "display: flex; justify-content: space-between; align-items: flex-start; flex-wrap: wrap; gap: 12px; margin-bottom: 10px;" } });

const brand = brandRow.createEl("div");
const titleEl = brand.createEl("div", {
  text: localStorage.getItem(LS.title) || "HERMES BRAIN",
  attr: { contenteditable: "true", spellcheck: "false", style: "font-size: 1.1em; font-weight: 700; letter-spacing: 0.04em; color: var(--text-accent); outline: none;" }
});
titleEl.addEventListener("blur", () => { const v = titleEl.textContent.trim(); if (v) localStorage.setItem(LS.title, v); });
const mantraEl = brand.createEl("div", {
  text: localStorage.getItem(LS.mantra) || "your agent's memory, one glance at a time",
  attr: { contenteditable: "true", spellcheck: "false", style: "font-size: 0.8em; color: var(--text-muted); margin-top: 2px; outline: none;" }
});
mantraEl.addEventListener("blur", () => { const v = mantraEl.textContent.trim(); if (v) localStorage.setItem(LS.mantra, v); });

const clockBlock = brandRow.createEl("div", { attr: { style: "text-align: right;" } });
const timeEl = clockBlock.createEl("div", { attr: { style: "font-size: 1.4em; font-weight: 700; font-family: var(--font-monospace, monospace); color: var(--text-normal);" } });
const dateEl = clockBlock.createEl("div", { attr: { style: "font-size: 0.8em; color: var(--text-muted);" } });

function tick() {
  const now = new Date();
  const pad = n => String(n).padStart(2, "0");
  timeEl.textContent = `${pad(now.getHours())}:${pad(now.getMinutes())}:${pad(now.getSeconds())}`;
  dateEl.textContent = now.toLocaleDateString(undefined, { weekday: "long", month: "long", day: "numeric" });
}
tick();
setInterval(tick, 1000);

// Mood-based greeting (time-band phrases), adapted from Komorebi.
const HOUR = new Date().getHours();
const GREETS = [
  { h: [0, 5],  label: "Still going?" },
  { h: [5, 9],  label: "New day, new flow." },
  { h: [9, 13], label: "Peak focus. Engage." },
  { h: [13, 18],label: "Stay in the flow." },
  { h: [18, 21],label: "Review your progress." },
  { h: [21, 24],label: "Wind down. Reflect." },
];
const G = GREETS.find(g => HOUR >= g.h[0] && HOUR < g.h[1]) || GREETS[5];
card.createEl("div", { text: G.label, attr: { style: "font-size: 1.05em; color: var(--text-normal); padding-top: 4px; border-top: 1px solid var(--background-modifier-border);" } });
```

```dataviewjs
// Today's focus — editable, localStorage-only (personal, this vault only).
const card = dv.el("div", "", { cls: "dashboard-card" });
card.createEl("div", { cls: "dashboard-card-title", text: "Today's focus" });
const LS_FOCUS = "hb-dash-focus";
const focusEl = card.createEl("div", {
  text: localStorage.getItem(LS_FOCUS) || "click to set today's focus…",
  attr: { contenteditable: "true", spellcheck: "false", style: "font-size: 1.05em; outline: none; min-height: 1.4em;" }
});
focusEl.addEventListener("blur", () => {
  const v = focusEl.textContent.trim();
  if (v) localStorage.setItem(LS_FOCUS, v);
});
```

```dataviewjs
// Quick actions — runs real Obsidian commands where available, falls
// back to a Notice if the target command/plugin isn't installed.
const card = dv.el("div", "", { cls: "dashboard-card" });
card.createEl("div", { cls: "dashboard-card-title", text: "Quick actions" });

const ACTIONS = [
  { lbl: "New Daily Review", action: async () => {
      const tpl = app.vault.getAbstractFileByPath("Templates/Daily-Review.md");
      if (!tpl) { new Notice("Templates/Daily-Review.md not found"); return; }
      try { app.commands.executeCommandById("templater-obsidian:create-new-note-from-template"); }
      catch (e) { app.workspace.openLinkText("Templates/Daily-Review.md", "", false); }
  }},
  { lbl: "Open Memory-Review", action: () => app.workspace.openLinkText("Memory-Review/TEMPLATE.md", "", false) },
  { lbl: "Open Vault Audit report", action: () => app.workspace.openLinkText("Skills-Notes/Vault-Audit-Report.md", "", false) },
  { lbl: "Open Daily Timeline", action: () => app.workspace.openLinkText("Daily/Timeline.md", "", false) },
];

const grid = card.createEl("div", { attr: { style: "display: grid; grid-template-columns: repeat(auto-fit, minmax(140px, 1fr)); gap: 8px;" } });
ACTIONS.forEach(a => {
  const btn = grid.createEl("div", {
    text: a.lbl,
    attr: { style: "cursor: pointer; text-align: center; padding: 10px 8px; border-radius: 6px; background: var(--background-primary); border: 1px solid var(--background-modifier-border); font-size: 0.85em; transition: background 0.15s;" }
  });
  btn.addEventListener("mouseenter", () => btn.style.background = "var(--background-modifier-hover)");
  btn.addEventListener("mouseleave", () => btn.style.background = "var(--background-primary)");
  btn.addEventListener("click", async () => {
    try { await a.action(); } catch (e) { new Notice(`Failed: ${a.lbl}`); console.error(e); }
  });
});
```

```dataviewjs
// Mini calendar — dots mark days with archived Daily/ sessions (not
// vault-wide daily notes, since this is a Hermes agent memory vault).
// Adapted from Komorebi's calendar concept.
const card = dv.el("div", "", { cls: "dashboard-card" });
card.createEl("div", { cls: "dashboard-card-title", text: "Session calendar" });

let calY = new Date().getFullYear();
let calM = new Date().getMonth();
const calContainer = card.createEl("div");

function getSessionsForDate(year, month, day) {
  const dateStr = `${year}-${String(month + 1).padStart(2, "0")}-${String(day).padStart(2, "0")}`;
  const dailyPages = dv.pages('"Daily"')
    .where(p => p.file.name !== "README" && p.file.name !== "manifest"
      && p.file.name !== "Timeline" && p.file.name !== "Chat-Correlation")
    .array();
  return dailyPages.filter(p => p.file.ctime && `${p.file.ctime.year}-${String(p.file.ctime.month).padStart(2, "0")}-${String(p.file.ctime.day).padStart(2, "0")}` === dateStr);
}

function renderCal() {
  calContainer.empty ? calContainer.empty() : (calContainer.innerHTML = "");

  const nav = calContainer.createEl("div", { attr: { style: "display: flex; justify-content: space-between; align-items: center; margin-bottom: 6px;" } });
  const prev = nav.createEl("span", { text: "‹", attr: { style: "cursor: pointer; padding: 0 8px; color: var(--text-muted);" } });
  nav.createEl("span", { text: new Date(calY, calM).toLocaleDateString(undefined, { year: "numeric", month: "long" }), attr: { style: "font-weight: 600;" } });
  const next = nav.createEl("span", { text: "›", attr: { style: "cursor: pointer; padding: 0 8px; color: var(--text-muted);" } });
  prev.addEventListener("click", () => { if (calM === 0) { calM = 11; calY--; } else calM--; renderCal(); });
  next.addEventListener("click", () => { if (calM === 11) { calM = 0; calY++; } else calM++; renderCal(); });

  const grid = calContainer.createEl("div", { attr: { style: "display: grid; grid-template-columns: repeat(7, 1fr); gap: 2px; text-align: center;" } });
  ["Su", "Mo", "Tu", "We", "Th", "Fr", "Sa"].forEach(d => grid.createEl("div", { text: d, attr: { style: "font-size: 0.7em; color: var(--text-faint); padding: 2px 0;" } }));

  const firstDay = new Date(calY, calM, 1).getDay();
  const dim = new Date(calY, calM + 1, 0).getDate();
  const now = new Date();

  for (let i = 0; i < firstDay; i++) grid.createEl("div");
  for (let d = 1; d <= dim; d++) {
    const isToday = d === now.getDate() && calM === now.getMonth() && calY === now.getFullYear();
    const sessions = getSessionsForDate(calY, calM, d);
    const cell = grid.createEl("div", {
      attr: { style: `padding: 4px 0; border-radius: 4px; cursor: pointer; font-size: 0.8em; ${isToday ? "border: 1px solid var(--text-accent);" : ""}` }
    });
    cell.createEl("div", { text: String(d) });
    if (sessions.length > 0) {
      const dot = cell.createEl("div", { attr: { style: "width: 4px; height: 4px; border-radius: 50%; background: var(--text-accent); margin: 2px auto 0;" } });
    }
    cell.addEventListener("click", () => {
      if (sessions.length > 0) app.workspace.openLinkText(sessions[0].file.path, "", false);
    });
  }
}
renderCal();
```

```dataviewjs
// Weather — OpenWeatherMap. Requires your OWN free API key, pasted once
// into the settings popup below; stored ONLY in this browser profile's
// localStorage, never written to any file, never committed to git.
// Adapted from Komorebi (InlitX/Obsidian-Dashboard-Gallery, MIT).
const card = dv.el("div", "", { cls: "dashboard-card" });
card.createEl("div", { cls: "dashboard-card-title", text: "Weather" });

const LS_KEY = "hb-dash-weather-api-key";
const LS_CITY = "hb-dash-weather-city";
const contentEl = card.createEl("div");

function showSettings() {
  contentEl.innerHTML = "";
  const keyInput = contentEl.createEl("input", { attr: { type: "password", placeholder: "OpenWeatherMap API key", style: "width: 100%; margin-bottom: 6px; padding: 4px; background: var(--background-primary); border: 1px solid var(--background-modifier-border); border-radius: 4px; color: var(--text-normal);" } });
  keyInput.value = localStorage.getItem(LS_KEY) || "";
  const cityInput = contentEl.createEl("input", { attr: { type: "text", placeholder: "City (e.g. mumbai)", style: "width: 100%; margin-bottom: 6px; padding: 4px; background: var(--background-primary); border: 1px solid var(--background-modifier-border); border-radius: 4px; color: var(--text-normal);" } });
  cityInput.value = localStorage.getItem(LS_CITY) || "";
  const saveBtn = contentEl.createEl("div", { text: "Save", attr: { style: "cursor: pointer; display: inline-block; padding: 4px 12px; background: var(--interactive-accent); color: var(--text-on-accent); border-radius: 4px; font-size: 0.85em;" } });
  saveBtn.addEventListener("click", () => {
    if (keyInput.value.trim()) localStorage.setItem(LS_KEY, keyInput.value.trim());
    if (cityInput.value.trim()) localStorage.setItem(LS_CITY, cityInput.value.trim());
    renderWeather();
  });
}

async function renderWeather() {
  const apiKey = localStorage.getItem(LS_KEY);
  const city = localStorage.getItem(LS_CITY);
  contentEl.innerHTML = "";
  if (!apiKey || !city) {
    const setup = contentEl.createEl("div", { text: "Click to configure weather", attr: { style: "cursor: pointer; color: var(--text-muted);" } });
    setup.addEventListener("click", showSettings);
    return;
  }
  try {
    const url = `https://api.openweathermap.org/data/2.5/weather?q=${encodeURIComponent(city)}&units=metric&appid=${apiKey}`;
    const res = await fetch(url);
    if (!res.ok) throw new Error(`HTTP ${res.status}`);
    const data = await res.json();
    const row = contentEl.createEl("div", { attr: { style: "display: flex; justify-content: space-between; align-items: center;" } });
    const left = row.createEl("div");
    left.createEl("div", { text: `${Math.round(data.main.temp)}°C`, attr: { style: "font-size: 1.6em; font-weight: 700;" } });
    left.createEl("div", { text: data.weather?.[0]?.description ?? "", attr: { style: "color: var(--text-muted); font-size: 0.85em; text-transform: capitalize;" } });
    left.createEl("div", { text: data.name ?? city, attr: { style: "color: var(--text-faint); font-size: 0.8em;" } });
    const gear = row.createEl("span", { text: "⚙", attr: { style: "cursor: pointer; color: var(--text-faint);" } });
    gear.addEventListener("click", showSettings);
  } catch (e) {
    contentEl.createEl("div", { text: `Couldn't load weather: ${e.message}`, attr: { style: "color: var(--text-muted); font-size: 0.85em;" } });
    const gear = contentEl.createEl("span", { text: "⚙ settings", attr: { style: "cursor: pointer; color: var(--text-faint); font-size: 0.8em;" } });
    gear.addEventListener("click", showSettings);
  }
}
renderWeather();
```

```dataviewjs
// On this day — Daily/ sessions from past years/months on today's date.
// Hidden entirely when there's nothing to show (same as Atlas's behavior).
const dailyPages = dv.pages('"Daily"')
  .where(p => p.file.name !== "README" && p.file.name !== "manifest"
    && p.file.name !== "Timeline" && p.file.name !== "Chat-Correlation");

const today = new Date();
const mm = today.getMonth() + 1, dd = today.getDate(), yy = today.getFullYear();

const flashback = dailyPages
  .where(p => p.file.ctime && p.file.ctime.month === mm && p.file.ctime.day === dd && p.file.ctime.year !== yy)
  .array();

if (flashback.length > 0) {
  const card = dv.el("div", "", { cls: "dashboard-card" });
  card.createEl("div", { cls: "dashboard-card-title", text: "On this day" });
  for (const p of flashback.slice(0, 5)) {
    const row = card.createEl("div", { attr: { style: "display: flex; justify-content: space-between; align-items: center; padding: 4px 0; border-bottom: 1px solid var(--background-modifier-border);" } });
    const left = row.createEl("div");
    left.createEl("a", { text: p.file.name, href: p.file.path, cls: "internal-link" });
    const yrsAgo = today.getFullYear() - p.file.ctime.year;
    row.createEl("span", { text: yrsAgo === 1 ? "1 year ago" : `${yrsAgo} years ago`, attr: { style: "color: var(--text-muted); font-size: 0.85em;" } });
  }
}
// Renders nothing at all if there's no matching session — by design.
```

## Overview

```dataviewjs
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

const openCandidates = dv.pages('"Memory-Review"').file.tasks.where(t => !t.completed).length;

const dailyPages = dv.pages('"Daily"')
  .where(p => p.file.name !== "README" && p.file.name !== "manifest"
    && p.file.name !== "Timeline" && p.file.name !== "Chat-Correlation");
let healthLabel = "No data", healthClass = "dashboard-badge-info";
if (dailyPages.length > 0) {
  const newest = dailyPages.sort(p => p.file.mtime, 'desc').array()[0];
  const hoursAgo = (Date.now() - newest.file.mtime.toMillis()) / 3600000;
  if (hoursAgo < 3) { healthLabel = "Healthy"; healthClass = "dashboard-badge-ok"; }
  else if (hoursAgo < 48) { healthLabel = "Idle"; healthClass = "dashboard-badge-info"; }
  else { healthLabel = "Stale"; healthClass = "dashboard-badge-warn"; }
}

const strip = dv.el("div", "", { cls: "dashboard-kpi-strip" });

function kpi(value, label) {
  const card = strip.createEl("div", { cls: "dashboard-kpi-card" });
  card.createEl("div", { cls: "dashboard-kpi-value", text: value });
  card.createEl("div", { cls: "dashboard-kpi-label", text: label });
}

kpi(totalTokens.toLocaleString(), "Total tokens");
kpi(todayTokens.toLocaleString(), "Tokens today");
kpi(String(activeDays), "Active days (log)");
kpi(String(weekSessions), "Sessions (7d)");
kpi(String(openCandidates), "Open candidates");

const healthCard = strip.createEl("div", { cls: "dashboard-kpi-card" });
healthCard.createEl("div", { cls: "dashboard-kpi-label", text: "Archiver status" });
const badge = healthCard.createEl("span", { cls: `dashboard-badge ${healthClass}`, text: healthLabel });
badge.style.marginTop = "4px";
```

## Template update check

```dataviewjs
const card = dv.el("div", "", { cls: "dashboard-card" });
card.createEl("div", { cls: "dashboard-card-title", text: "Template version" });

const versionFile = app.vault.getAbstractFileByPath("VERSION");
if (!versionFile) {
  card.createEl("div", { text: "⚠️ No VERSION file found — can't check for updates." });
} else {
  const local = (await app.vault.read(versionFile)).trim();
  try {
    const res = await fetch("https://api.github.com/repos/mistrysiddh/hermes-brain-template/releases/latest");
    if (!res.ok) throw new Error(`HTTP ${res.status}`);
    const data = await res.json();
    const latest = (data.tag_name || "").replace(/^v/, "");
    if (!latest) throw new Error("no tag_name in response");
    if (latest === local) {
      const row = card.createEl("div");
      row.createEl("span", { cls: "dashboard-badge dashboard-badge-ok", text: `Up to date — v${local}` });
    } else {
      const row = card.createEl("div");
      row.createEl("span", { cls: "dashboard-badge dashboard-badge-warn", text: `Update available: v${latest}` });
      const detail = card.createEl("div", { attr: { style: "margin-top: 6px; color: var(--text-muted); font-size: 0.9em;" } });
      detail.createEl("span", { text: `You have v${local}. ` });
      detail.createEl("a", { text: "Release notes", href: data.html_url, cls: "external-link" });
      card.createEl("div", { attr: { style: "margin-top: 4px; color: var(--text-muted); font-size: 0.85em;" }, text: "Run update.sh / update.ps1 to pull it in." });
    }
  } catch (e) {
    card.createEl("div", { text: `⚠️ Couldn't check for updates (offline, or GitHub API unreachable): ${e.message}. Running v${local}.` });
  }
}
```

_Checked live each time this note opens — needs internet access. Nothing is sent anywhere; this only reads GitHub's public releases API._

## Vault health

```dataviewjs
const card = dv.el("div", "", { cls: "dashboard-card" });
card.createEl("div", { cls: "dashboard-card-title", text: "Health checks" });

const dailyPages = dv.pages('"Daily"')
  .where(p => p.file.name !== "README" && p.file.name !== "manifest"
    && p.file.name !== "Timeline" && p.file.name !== "Chat-Correlation");

const archiverRow = card.createEl("div", { attr: { style: "display: flex; justify-content: space-between; align-items: center; padding: 4px 0;" } });
archiverRow.createEl("span", { text: "Session archiver" });
if (dailyPages.length === 0) {
  archiverRow.createEl("span", { cls: "dashboard-badge dashboard-badge-info", text: "No sessions yet" });
} else {
  const newest = dailyPages.sort(p => p.file.mtime, 'desc').array()[0];
  const hoursAgo = (Date.now() - newest.file.mtime.toMillis()) / 3600000;
  if (hoursAgo < 3) {
    archiverRow.createEl("span", { cls: "dashboard-badge dashboard-badge-ok", text: `Alive — ${Math.round(hoursAgo * 10) / 10}h ago` });
  } else if (hoursAgo < 48) {
    archiverRow.createEl("span", { cls: "dashboard-badge dashboard-badge-info", text: `Idle — ${Math.round(hoursAgo)}h ago` });
  } else {
    archiverRow.createEl("span", { cls: "dashboard-badge dashboard-badge-warn", text: `Stale — ${Math.round(hoursAgo / 24)}d ago` });
  }
}

const openTasks = dv.pages('"Memory-Review"').file.tasks.where(t => !t.completed).length;
const reviewRow = card.createEl("div", { attr: { style: "display: flex; justify-content: space-between; align-items: center; padding: 4px 0;" } });
reviewRow.createEl("span", { text: "Memory-Review backlog" });
if (openTasks === 0) {
  reviewRow.createEl("span", { cls: "dashboard-badge dashboard-badge-ok", text: "0 open" });
} else if (openTasks <= 20) {
  reviewRow.createEl("span", { cls: "dashboard-badge dashboard-badge-info", text: `${openTasks} open` });
} else {
  reviewRow.createEl("span", { cls: "dashboard-badge dashboard-badge-warn", text: `${openTasks} open — growing` });
}
```

_Read-only checks against files already in this vault — nothing leaves your machine._

## Token usage & activity

```dataviewjs
const card = dv.el("div", "", { cls: "dashboard-card" });
card.createEl("div", { cls: "dashboard-card-title", text: "Token usage" });

const tokenLog = app.vault.getAbstractFileByPath("Skills-Notes/Token-Usage.log");
if (!tokenLog) {
  card.createEl("div", { text: "No token usage recorded yet — will appear after first hourly archive run with token extraction." });
} else {
  const content = await app.vault.read(tokenLog);
  const lines = content.split("\n").map(l => l.trim())
    .filter(l => l && !l.startsWith("#") && !l.startsWith("---") && !l.startsWith("<!--"));
  let runningTotal = 0;
  const dailyData = [];
  for (const line of lines) {
    const match = line.match(/^(\d{4}-\d{2}-\d{2}):\s*(\d+)\s*tokens?\s*\((\d+)\s*session/);
    if (match) {
      const [, date, tokens, sessions] = match;
      const t = parseInt(tokens), s = parseInt(sessions);
      runningTotal += t;
      dailyData.push({ date, tokens: t, sessions: s });
    }
  }
  if (dailyData.length === 0) {
    card.createEl("div", { text: "Token log found but no valid entries parsed yet." });
  } else {
    const today = new Date().toISOString().split("T")[0];
    const todayEntry = dailyData.find(d => d.date === today);
    if (todayEntry) {
      card.createEl("div", { text: `⚡ Today: ${todayEntry.tokens.toLocaleString()} tokens (${todayEntry.sessions} session${todayEntry.sessions !== 1 ? "s" : ""})` });
    }
    card.createEl("div", { text: `🔢 All-time total: ${runningTotal.toLocaleString()} tokens` });
    const last7 = dailyData.slice(-7);
    if (last7.length > 1) {
      const weekTotal = last7.reduce((a, b) => a + b.tokens, 0);
      const avg = Math.round(weekTotal / last7.length);
      card.createEl("div", { text: `📊 Last ${last7.length} days: ${weekTotal.toLocaleString()} tokens (avg ${avg.toLocaleString()}/day)` });
    }
    if (dailyData.length >= 2) {
      const last = dailyData[dailyData.length - 1];
      const prev = dailyData[dailyData.length - 2];
      const diff = last.tokens - prev.tokens;
      const pct = prev.tokens > 0 ? Math.round((diff / prev.tokens) * 100) : 0;
      const trend = diff > 0 ? `📈 +${diff.toLocaleString()} (${pct}%)` : diff < 0 ? `📉 ${diff.toLocaleString()} (${pct}%)` : `➡️ No change`;
      card.createEl("div", { text: `Day-over-day: ${trend}` });
    }
  }
}
```

_Updates live each time this note opens — reads from Skills-Notes/Token-Usage.log which is maintained by hourly_archive.py._

```dataviewjs
const card = dv.el("div", "", { cls: "dashboard-card" });
card.createEl("div", { cls: "dashboard-card-title", text: "Activity heatmap (18 weeks)" });

const tokenLog = app.vault.getAbstractFileByPath("Skills-Notes/Token-Usage.log");
if (!tokenLog) {
  card.createEl("div", { text: "No activity data yet — will appear after your first hourly archive run." });
} else {
  const content = await app.vault.read(tokenLog);
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
  const dates = Object.keys(byDate);
  if (dates.length === 0) {
    card.createEl("div", { text: "No activity data yet." });
  } else {
    const WEEKS = 18;
    const today = new Date(); today.setHours(0, 0, 0, 0);
    const endOfWeek = new Date(today);
    endOfWeek.setDate(today.getDate() + (6 - today.getDay()));
    const start = new Date(endOfWeek);
    start.setDate(endOfWeek.getDate() - (WEEKS * 7 - 1));
    const maxTokens = Math.max(...dates.map(d => byDate[d].tokens), 1);

    function colorFor(tokens) {
      if (tokens === 0) return "var(--background-modifier-border)";
      const ratio = tokens / maxTokens;
      if (ratio > 0.75) return "var(--text-accent)";
      if (ratio > 0.45) return "color-mix(in srgb, var(--text-accent) 70%, var(--background-modifier-border))";
      if (ratio > 0.15) return "color-mix(in srgb, var(--text-accent) 40%, var(--background-modifier-border))";
      return "color-mix(in srgb, var(--text-accent) 18%, var(--background-modifier-border))";
    }

    const grid = card.createEl("div", { attr: { style: "display: flex; gap: 3px; overflow-x: auto; padding: 4px 0;" } });
    const dayLabels = grid.createEl("div", { attr: { style: "display: flex; flex-direction: column; gap: 3px; margin-right: 4px; font-size: 0.65em; color: var(--text-faint);" } });
    ["", "Mon", "", "Wed", "", "Fri", ""].forEach(label => {
      const cell = dayLabels.createEl("div", { text: label });
      cell.style.height = "11px"; cell.style.lineHeight = "11px";
    });

    let totalActiveDays = 0, cursor = new Date(start);
    for (let w = 0; w < WEEKS; w++) {
      const col = grid.createEl("div", { attr: { style: "display: flex; flex-direction: column; gap: 3px;" } });
      for (let d = 0; d < 7; d++) {
        const dateStr = cursor.toISOString().split("T")[0];
        const entry = byDate[dateStr] || { tokens: 0, sessions: 0 };
        if (entry.tokens > 0) totalActiveDays++;
        const isFuture = cursor > today;
        const cell = col.createEl("div");
        cell.style.width = "11px"; cell.style.height = "11px"; cell.style.borderRadius = "2px";
        cell.style.background = isFuture ? "transparent" : colorFor(entry.tokens);
        cell.title = isFuture ? "" : `${dateStr}: ${entry.tokens.toLocaleString()} tokens, ${entry.sessions} session${entry.sessions !== 1 ? "s" : ""}`;
        cursor.setDate(cursor.getDate() + 1);
      }
    }
    card.createEl("div", { attr: { style: "margin-top: 8px; font-size: 0.85em; color: var(--text-muted);" }, text: `${totalActiveDays} active day${totalActiveDays !== 1 ? "s" : ""} in the last ${WEEKS} weeks. Hover a cell for details.` });
  }
}
```

_Same data as Token usage above, shown as a calendar — darker green = more tokens that day._

## Vault audit & agent performance

```dataviewjs
const grid = dv.el("div", "", { attr: { style: "display: grid; grid-template-columns: repeat(auto-fit, minmax(280px, 1fr)); gap: 10px;" } });

const auditCard = grid.createEl("div", { cls: "dashboard-card" });
auditCard.createEl("div", { cls: "dashboard-card-title", text: "Vault audit" });
const auditReport = app.vault.getAbstractFileByPath("Skills-Notes/Vault-Audit-Report.md");
if (!auditReport) {
  auditCard.createEl("div", { text: "Vault audit report not found — will appear after first vault_audit.py run." });
} else {
  const content = await app.vault.read(auditReport);
  const summaryMatch = content.match(/## Summary\n\n([\s\S]*?)\n---/);
  if (summaryMatch) {
    const lines = summaryMatch[1].trim().split('\n').map(l => l.trim()).filter(l => l.startsWith('-'));
    for (const line of lines) {
      const m = line.match(/-\s+\*\*([^*]+)\*\*:\s*(\d+)/);
      if (m) {
        const [, label, count] = m;
        const row = auditCard.createEl("div", { attr: { style: "display: flex; justify-content: space-between; padding: 2px 0;" } });
        row.createEl("span", { text: label, attr: { style: "color: var(--text-muted);" } });
        const cls = parseInt(count) > 0 ? "dashboard-badge-warn" : "dashboard-badge-ok";
        row.createEl("span", { cls: `dashboard-badge ${cls}`, text: count });
      }
    }
  }
  const genMatch = content.match(/Generated:\s*([^\n]+)/);
  if (genMatch) {
    const footer = auditCard.createEl("div", { attr: { style: "margin-top: 8px; font-size: 0.85em; color: var(--text-faint);" } });
    footer.createEl("span", { text: `Last run: ${genMatch[1].trim()} — ` });
    footer.createEl("a", { text: "Open full report →", href: "Skills-Notes/Vault-Audit-Report.md", cls: "internal-link" });
  }
}

const perfCard = grid.createEl("div", { cls: "dashboard-card" });
perfCard.createEl("div", { cls: "dashboard-card-title", text: "Agent performance" });
const perfReport = app.vault.getAbstractFileByPath("Skills-Notes/Agent-Performance.md");
if (!perfReport) {
  perfCard.createEl("div", { text: "Agent performance report not found — run Scripts/agent_performance.py." });
} else {
  const content = await app.vault.read(perfReport);
  const overviewMatch = content.match(/## Overview\n\n([\s\S]*?)\n---/);
  if (overviewMatch) {
    const lines = overviewMatch[1].trim().split('\n').map(l => l.trim()).filter(l => l.startsWith('-'));
    for (const line of lines) {
      const m = line.match(/-\s+\*\*([^*]+)\*\*:\s*([\d,\.]+)/);
      if (m) {
        const [, label, value] = m;
        const row = perfCard.createEl("div", { attr: { style: "display: flex; justify-content: space-between; padding: 2px 0;" } });
        row.createEl("span", { text: label, attr: { style: "color: var(--text-muted);" } });
        row.createEl("span", { text: value, attr: { style: "font-family: var(--font-monospace, monospace);" } });
      }
    }
  }
  const footer = perfCard.createEl("div", { attr: { style: "margin-top: 8px; font-size: 0.85em; color: var(--text-faint);" } });
  footer.createEl("a", { text: "Open full report →", href: "Skills-Notes/Agent-Performance.md", cls: "internal-link" });
}
```

_Vault audit updated by `Scripts/vault_audit.py`, agent performance by `Scripts/agent_performance.py`, both on schedule via cron._

## Active projects

```dataviewjs
const card = dv.el("div", "", { cls: "dashboard-card" });
card.createEl("div", { cls: "dashboard-card-title", text: "Active projects" });

const activeProjects = dv.pages('"Projects"').where(p => p.type === "project" && p.status === "active").sort(p => p.created, 'desc');
if (activeProjects.length === 0) {
  card.createEl("div", { text: "No active projects." });
} else {
  const table = card.createEl("table", { attr: { style: "width: 100%; border-collapse: collapse;" } });
  const headRow = table.createEl("tr");
  ["Project", "Status", "Created"].forEach(h => {
    headRow.createEl("th", { text: h, attr: { style: "text-align: left; padding: 4px 8px 4px 0; border-bottom: 1px solid var(--background-modifier-border); color: var(--text-muted); font-size: 0.8em; text-transform: uppercase;" } });
  });
  for (const p of activeProjects.array()) {
    const row = table.createEl("tr");
    const nameCell = row.createEl("td", { attr: { style: "padding: 4px 8px 4px 0; border-bottom: 1px solid var(--background-modifier-border);" } });
    nameCell.createEl("a", { text: p.file.name, href: p.file.path, cls: "internal-link" });
    row.createEl("td", { text: p.status ?? "", attr: { style: "padding: 4px 8px 4px 0; border-bottom: 1px solid var(--background-modifier-border);" } });
    row.createEl("td", { text: p.created ? String(p.created) : "", attr: { style: "padding: 4px 0; border-bottom: 1px solid var(--background-modifier-border); color: var(--text-muted);" } });
  }
}
```

_All statuses, sortable/filterable: [[Projects/Projects.base|Projects.base]]._

## Open memory candidates

```dataviewjs
const card = dv.el("div", "", { cls: "dashboard-card" });
card.createEl("div", { cls: "dashboard-card-title", text: "Open memory candidates" });

const tasks = dv.pages('"Memory-Review"').file.tasks.where(t => !t.completed);
const list = tasks.array ? tasks.array() : Array.from(tasks);
if (list.length === 0) {
  card.createEl("div", { text: "Nothing pending." });
} else {
  const ul = card.createEl("ul", { attr: { style: "margin: 0; padding-left: 18px;" } });
  for (const t of list.slice(0, 15)) {
    ul.createEl("li", { text: t.text ?? String(t), attr: { style: "padding: 2px 0;" } });
  }
  if (list.length > 15) {
    card.createEl("div", { text: `…and ${list.length - 15} more.`, attr: { style: "color: var(--text-muted); font-size: 0.85em; margin-top: 4px;" } });
  }
}
```

_Full review flow: [[Memory-Review/TEMPLATE|Memory-Review/TEMPLATE.md]]. Regenerated by `Scripts/consolidate_memory.py`._

## Recent Daily sessions

```dataviewjs
const card = dv.el("div", "", { cls: "dashboard-card" });
card.createEl("div", { cls: "dashboard-card-title", text: "Recent Daily sessions" });

const dailyPages = dv.pages('"Daily"')
  .where(p => p.file.name !== "README" && p.file.name !== "manifest"
    && p.file.name !== "Timeline" && p.file.name !== "Chat-Correlation")
  .sort(p => p.file.mtime, 'desc');
const list = dailyPages.array ? dailyPages.array() : Array.from(dailyPages);
if (list.length === 0) {
  card.createEl("div", { text: "No archived sessions yet." });
} else {
  const table = card.createEl("table", { attr: { style: "width: 100%; border-collapse: collapse;" } });
  const headRow = table.createEl("tr");
  ["Session", "Modified", "Date folder"].forEach(h => {
    headRow.createEl("th", { text: h, attr: { style: "text-align: left; padding: 4px 8px 4px 0; border-bottom: 1px solid var(--background-modifier-border); color: var(--text-muted); font-size: 0.8em; text-transform: uppercase;" } });
  });
  for (const p of list.slice(0, 10)) {
    const row = table.createEl("tr");
    const nameCell = row.createEl("td", { attr: { style: "padding: 4px 8px 4px 0; border-bottom: 1px solid var(--background-modifier-border);" } });
    nameCell.createEl("a", { text: p.file.name, href: p.file.path, cls: "internal-link" });
    row.createEl("td", { text: p.file.mtime ? String(p.file.mtime) : "", attr: { style: "padding: 4px 8px 4px 0; border-bottom: 1px solid var(--background-modifier-border); color: var(--text-muted); font-size: 0.85em;" } });
    row.createEl("td", { text: p.file.folder ?? "", attr: { style: "padding: 4px 0; border-bottom: 1px solid var(--background-modifier-border); color: var(--text-muted); font-size: 0.85em;" } });
  }
}
```

_Full chronological view: [[Daily/Timeline]]._

## Installed skills

```dataviewjs
const card = dv.el("div", "", { cls: "dashboard-card" });
card.createEl("div", { cls: "dashboard-card-title", text: "Installed skills" });

const file = app.vault.getAbstractFileByPath("Skills-Notes/Installed-Skills-Index.md");
if (file) {
  const content = await app.vault.read(file);
  const rows = content.split("\n")
    .filter(l => l.trim().startsWith("|"))
    .filter(l => !l.includes("---") && !l.trim().startsWith("| Skill"));
  const populated = rows.filter(r => r.replace(/\|/g, "").trim().length > 0);
  const row = card.createEl("div");
  row.createEl("span", { cls: "dashboard-badge dashboard-badge-ok", text: `${populated.length} skill(s)` });
  const link = card.createEl("div", { attr: { style: "margin-top: 6px;" } });
  link.createEl("a", { text: "Installed Skills Index →", href: "Skills-Notes/Installed-Skills-Index.md", cls: "internal-link" });
} else {
  card.createEl("div", { text: "Skills-Notes/Installed-Skills-Index.md not found." });
}
```

---

_This is a beta layout note — the original [[Dashboard]] is untouched. Delete this file, or just stop opening it, if you don't like the card style. Uses the exact same data sources as the original ([[Skills-Notes/Token-Usage.log|Token-Usage.log]], [[Skills-Notes/Vault-Audit-Report|Vault-Audit-Report.md]], [[Skills-Notes/Agent-Performance|Agent-Performance.md]], [[Projects/Projects.base|Projects.base]], [[Memory-Review/TEMPLATE|Memory-Review]], [[Daily/Timeline|Daily]], [[Skills-Notes/Installed-Skills-Index|Installed-Skills-Index]]) — no new scripts or cron jobs, nothing trimmed._
