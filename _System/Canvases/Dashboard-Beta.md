---
type: dashboard
status: beta
created: 2026-09-14
updated: 2026-11-26
tags: [dashboard, hub, beta, admin]
cssclasses: [dashboard-wide, hbd-app]
---

%%
Hermes Brain — Dashboard-Beta

Requires the Dataview plugin with JavaScript queries enabled, and the
`dashboard-beta` CSS snippet (all styling lives there). Best in Reading view.
%%

```dataviewjs
const vault = app.vault;

// ---------- config ----------
const REPORTS = "04-Archives/Audit-Reports";
const PATHS = {
  tokens: [`${REPORTS}/Token-Usage.log`, "Skills-Notes/Token-Usage.log"],
  audit: [`${REPORTS}/Vault-Audit-Report.md`, "Skills-Notes/Vault-Audit-Report.md"],
  skills: [`${REPORTS}/Skill-Quality-Report.md`, "Skills-Notes/Skill-Quality-Report.md"],
  critique: [`${REPORTS}/Self-Critique-Report.md`, "Skills-Notes/Self-Critique-Report.md"],
  board: ["04-Archives/Memory-Review/Memory-Board.md", "Memory-Review/Memory-Board.md"],
  preamble: ["04-Archives/Memory-Review/HERMES-PREAMBLE.md"],
  timeline: ["04-Archives/Daily/Timeline.md"],
  projects: ["01-Projects/Projects.base"],
  version: ["VERSION"],
};
const STALE_DAYS = 7;

// ---------- helpers ----------
const pad = n => String(n).padStart(2, "0");
const isoDay = d => `${d.getFullYear()}-${pad(d.getMonth() + 1)}-${pad(d.getDate())}`;
const arr = x => !x ? [] : (x.array ? x.array() : Array.from(x));
const find = key => PATHS[key].map(p => vault.getAbstractFileByPath(p)).find(Boolean);
const read = async key => { const f = find(key); return f ? { file: f, text: await vault.read(f) } : null; };
const msOf = t => !t ? 0 : (t.toMillis ? t.toMillis() : new Date(t).getTime());
const daysSince = ms => Math.floor((Date.now() - ms) / 86400000);
const shortDate = d => d.toLocaleDateString(undefined, { day: "numeric", month: "short" });
const compact = n => new Intl.NumberFormat(undefined, { notation: "compact", maximumFractionDigits: 1 }).format(n);
const plural = (n, word) => `${n.toLocaleString()} ${word}${n === 1 ? "" : "s"}`;
const notify = m => typeof Notice === "function" ? new Notice(m) : console.warn(m);
const timeAgo = t => {
  const min = Math.floor((Date.now() - msOf(t)) / 60000);
  if (min < 1) return "just now";
  if (min < 60) return `${min}m ago`;
  const hr = Math.floor(min / 60);
  return hr < 24 ? `${hr}h ago` : `${Math.floor(hr / 24)}d ago`;
};
const generatedAt = text => {
  const m = text.match(/Generated:\s*(\d{4}-\d{2}-\d{2})[ T](\d{2}:\d{2}:\d{2})/);
  return m ? new Date(`${m[1]}T${m[2]}`) : null;
};
const summaryCount = (text, label) => {
  const line = text.split(/\r?\n/).find(l => l.includes(`**${label}`));
  const m = line?.match(/\*\*:\s*(\d+)\s*$/);
  return m ? Number(m[1]) : null; // null = missing or unreadable
};

// ---------- actions ----------
const openPath = path => app.workspace.openLinkText(path, "", false);
const openKey = key => { const f = find(key); f ? openPath(f.path) : notify(`Not found: ${PATHS[key][0]}`); };
const runCommand = id => { if (!app.commands.executeCommandById(id)) notify(`Command unavailable: ${id}`); };
const search = query => {
  const plugin = app.internalPlugins.getPluginById("global-search");
  plugin?.enabled ? plugin.instance.openGlobalSearch(query) : notify("Enable the core Search plugin.");
};

// Creates a new note from a template, so the template itself is never edited.
async function newFromTemplate(templatePath, folder, prefix) {
  const template = vault.getAbstractFileByPath(templatePath);
  if (!template) return notify(`Template not found: ${templatePath}`);
  if (!vault.getAbstractFileByPath(folder)) await vault.createFolder(folder);
  const now = new Date();
  const title = `${prefix}-${isoDay(now)}-${pad(now.getHours())}${pad(now.getMinutes())}${pad(now.getSeconds())}`;
  const text = (await vault.read(template))
    .replaceAll("{{date}}", isoDay(now))
    .replaceAll("{{title}}", title);
  const file = await vault.create(`${folder}/${title}.md`, text);
  openPath(file.path);
}

// ---------- components ----------
function button(parent, label, onClick, cls = "hbd-btn") {
  const b = parent.createEl("button", { cls, text: label, attr: { type: "button" } });
  b.addEventListener("click", async () => {
    try { await onClick(); } catch (e) { console.error("[Dashboard-Beta]", e); notify(`Failed: ${label}`); }
  });
  return b;
}

function link(parent, path, cls) {
  const a = parent.createEl("a", { cls, attr: { href: "#" } });
  a.addEventListener("click", e => { e.preventDefault(); openPath(path); });
  return a;
}

const empty = (parent, text) => parent.createDiv({ cls: "hbd-empty", text });
const badge = (parent, text, tone = "neutral") => parent.createSpan({ cls: `hbd-badge hbd-${tone}`, text });

function card(parent, title, span, { action, onAction } = {}) {
  const root = parent.createEl("section", { cls: `hbd-card hbd-span-${span}` });
  const head = root.createDiv({ cls: "hbd-card-head" });
  head.createEl("h3", { text: title });
  const meta = head.createDiv({ cls: "hbd-card-meta" });
  if (action) button(meta, action, onAction, "hbd-text-btn");
  return { body: root.createDiv({ cls: "hbd-card-body" }), meta };
}

// Shows when a report was generated; amber once it is older than STALE_DAYS.
function freshness(meta, date) {
  if (!date) return;
  const old = daysSince(date.getTime()) > STALE_DAYS;
  badge(meta, `${old ? "Stale · " : ""}${shortDate(date)}`, old ? "warn" : "neutral");
}

function bars(parent, series, unit) {
  const max = Math.max(1, ...series.map(s => s.value));
  const chart = parent.createDiv({ cls: "hbd-chart", attr: { role: "img", "aria-label": `${unit} per day, last ${series.length} days` } });
  for (const s of series) {
    const col = chart.createDiv({ cls: "hbd-bar", attr: { title: `${shortDate(s.date)}: ${s.value.toLocaleString()} ${unit}` } });
    col.style.height = s.value ? `${Math.max(8, (s.value / max) * 100)}%` : "2px";
    if (!s.value) col.addClass("hbd-bar-zero");
  }
  const axis = parent.createDiv({ cls: "hbd-axis" });
  axis.createSpan({ text: shortDate(series[0].date) });
  axis.createSpan({ text: shortDate(series[series.length - 1].date) });
}

function kpi(parent, label, value, sub, tone) {
  const k = parent.createDiv({ cls: "hbd-card hbd-kpi hbd-span-3" });
  k.createDiv({ cls: "hbd-kpi-label", text: label });
  k.createDiv({ cls: `hbd-kpi-value${tone ? ` hbd-text-${tone}` : ""}`, text: value });
  k.createDiv({ cls: "hbd-kpi-sub", text: sub });
  return k;
}

function statRow(parent, label, value, tone, path) {
  const row = path ? link(parent, path, "hbd-row") : parent.createDiv({ cls: "hbd-row" });
  row.createSpan({ text: label });
  badge(row, value, tone);
}

// ---------- data ----------
async function loadData() {
  const [tokens, audit, skills, critique, board, version] = await Promise.all(
    ["tokens", "audit", "skills", "critique", "board", "version"].map(read));

  // Token log: "YYYY-MM-DD: N tokens (M session(s))"
  const byDate = {};
  for (const raw of (tokens?.text || "").split("\n")) {
    const m = raw.trim().match(/^(\d{4}-\d{2}-\d{2}):\s*(\d+)(?:\s*tokens?\s*\((\d+)\s*session)?/);
    if (!m) continue;
    const d = byDate[m[1]] ||= { tokens: 0, sessions: 0 };
    d.tokens += Number(m[2]);
    d.sessions += Number(m[3] || 0);
  }
  const days = Array.from({ length: 14 }, (_, i) => {
    const date = new Date();
    date.setDate(date.getDate() - (13 - i));
    return { date, ...(byDate[isoDay(date)] || { tokens: 0, sessions: 0 }) };
  });
  const lastLogged = Object.keys(byDate).sort().pop();

  // Memory board: checkbox counts per Kanban column
  let memory = null;
  if (board) {
    memory = { candidates: 0, review: 0, approved: 0, rejected: 0 };
    let column = null;
    for (const line of board.text.split("\n")) {
      if (line.startsWith("## ")) {
        column = /approved|promoted/i.test(line) ? "approved"
          : /rejected/i.test(line) ? "rejected"
          : /review/i.test(line) ? "review" : "candidates";
      } else if (column && /^\s*- \[.\]/.test(line)) memory[column]++;
    }
  }

  const health = audit && {
    path: audit.file.path,
    date: generatedAt(audit.text),
    broken: summaryCount(audit.text, "Broken wikilinks"),
    stale: summaryCount(audit.text, "Stale Memory-Review"),
    duplicates: summaryCount(audit.text, "Duplicate sessions"),
    manifest: summaryCount(audit.text, "Manifest issues"),
    orphans: summaryCount(audit.text, "Orphaned files"),
  };

  const review = critique && {
    path: critique.file.path,
    date: generatedAt(critique.text),
    total: summaryCount(critique.text, "Total findings"),
    serious: [...critique.text.matchAll(/^\|\s*(critical|high|medium)\s*\|/gim)].length,
    broken: (critique.text.match(/\|\s*Broken wikilink \[\[/g) || []).length,
  };

  let quality = null;
  if (skills) {
    const count = label => (skills.text.match(new RegExp(`^###.*— ${label}\\s*$`, "gm")) || []).length;
    quality = { path: skills.file.path, date: generatedAt(skills.text), ready: count("READY"), rework: count("NEEDS REWORK"), reject: count("REJECT") };
    quality.total = quality.ready + quality.rework + quality.reject;
  }

  const SKIP = new Set(["README", "manifest", "Timeline", "Chat-Correlation"]);
  const sessions = arr(dv.pages('"04-Archives/Daily" or "Daily"').where(p => !SKIP.has(p.file.name)))
    .sort((a, b) => msOf(b.file.mtime) - msOf(a.file.mtime));

  const projects = arr(dv.pages('"01-Projects" or "Projects"').where(p => p.type === "project" && p.status === "active"))
    .sort((a, b) => msOf(b.file.mtime) - msOf(a.file.mtime));

  const self = dv.current()?.file?.path;
  const allPages = arr(dv.pages());
  const recent = allPages
    .filter(p => p.file.path !== self && !/^(04-Archives\/)?Daily\//.test(p.file.path))
    .sort((a, b) => msOf(b.file.mtime) - msOf(a.file.mtime))
    .slice(0, 6);

  return {
    days, lastLogged, memory, health, review, quality, sessions, projects, recent,
    noteCount: allPages.length,
    version: version?.text.trim().split("|").pop(),
  };
}

// Only things that call for action.
function alerts(d) {
  const out = [];
  const add = (tone, text, path) => out.push({ tone, text, path });
  const h = d.health, r = d.review, q = d.quality;
  if (h?.broken) add("error", `${plural(h.broken, "broken link")} in the vault audit`, h.path);
  if (r?.broken) add("error", `${plural(r.broken, "broken link")} in the self-critique`, r.path);
  if (h?.duplicates) add("warn", plural(h.duplicates, "duplicate session"), h.path);
  if (h?.manifest) add("warn", plural(h.manifest, "manifest issue"), h.path);
  if (h?.stale) add("warn", plural(h.stale, "stale memory review"), h.path);
  if (h && h.stale === null) add("warn", "Stale-review count is unreadable. Re-run vault_audit.py", h.path);
  if (r?.serious) add("warn", plural(r.serious, "medium-or-higher self-critique finding"), r.path);
  if (q?.reject) add("warn", plural(q.reject, "rejected skill"), q.path);
  for (const [name, rep] of [["Vault audit", h], ["Skill quality", q], ["Self-critique", r]]) {
    if (!rep) add("warn", `${name} report is missing`);
    else if (rep.date && daysSince(rep.date.getTime()) > STALE_DAYS) add("warn", `${name} report is ${daysSince(rep.date.getTime())} days old`, rep.path);
  }
  if (!d.lastLogged) add("warn", "No token usage has been logged");
  else {
    const age = daysSince(new Date(`${d.lastLogged}T00:00:00`).getTime());
    if (age > STALE_DAYS) add("warn", `Token log has no entries for ${age} days`);
  }
  return out.sort((a, b) => (a.tone === "error" ? 0 : 1) - (b.tone === "error" ? 0 : 1));
}

// ---------- sections ----------
function header(parent) {
  const bar = parent.createEl("header", { cls: "hbd-header" });
  const title = bar.createDiv();
  const now = new Date(), hour = now.getHours();
  const greet = hour < 12 ? "Good morning" : hour < 18 ? "Good afternoon" : "Good evening";
  title.createEl("h2", { text: "Hermes Brain" });
  title.createDiv({ cls: "hbd-muted", text: `${greet} · ${now.toLocaleDateString(undefined, { weekday: "long", day: "numeric", month: "long" })}` });

  const tools = bar.createDiv({ cls: "hbd-tools" });
  const input = tools.createEl("input", { cls: "hbd-search", attr: { type: "search", placeholder: "Search vault, then press Enter", "aria-label": "Search vault" } });
  input.addEventListener("keydown", e => { if (e.key === "Enter" && input.value.trim()) search(input.value.trim()); });
  button(tools, "Refresh", render);

  const actions = parent.createEl("nav", { cls: "hbd-actions", attr: { "aria-label": "Quick actions" } });
  button(actions, "Today's note", () => runCommand("daily-notes"), "hbd-btn hbd-primary");
  button(actions, "Memory board", () => openKey("board"));
  button(actions, "Context preamble", () => openKey("preamble"));
  button(actions, "New lesson", () => newFromTemplate("_System/Templates/Lesson-Learned.md", "02-Areas/Skills/Lessons-Learned", "Lesson"));
  button(actions, "New ADR", () => newFromTemplate("_System/Templates/Architecture-Decision-Record.md", "01-Projects/ADR", "ADR"));
}

function attention(parent, items) {
  const box = parent.createEl("section", { cls: `hbd-attention hbd-span-12${items.length ? "" : " hbd-clear"}` });
  if (!items.length) { box.createEl("strong", { text: "✓ All clear. Nothing needs attention." }); return; }
  box.createEl("strong", { text: `⚠ Needs attention (${items.length})` });
  const list = box.createDiv({ cls: "hbd-alerts" });
  for (const i of items) {
    const cls = `hbd-alert hbd-${i.tone}`;
    const chip = i.path ? link(list, i.path, cls) : list.createSpan({ cls });
    chip.setText(i.path ? `${i.text} →` : i.text);
  }
}

function kpis(grid, d) {
  const sum = key => d.days.reduce((s, x) => s + x[key], 0);
  const series = key => d.days.map(x => ({ date: x.date, value: x[key] }));
  const none = d.lastLogged ? `Last entry ${shortDate(new Date(`${d.lastLogged}T00:00:00`))}` : "No log entries yet";
  const today = d.days[d.days.length - 1].tokens;

  const tokens = sum("tokens");
  const t = kpi(grid, "Tokens · 14 days", tokens ? compact(tokens) : "—", tokens ? `${compact(today)} today` : none);
  if (tokens) bars(t, series("tokens"), "tokens");

  const count = sum("sessions");
  const s = kpi(grid, "Sessions · 14 days", count ? String(count) : "—", count ? plural(d.days.filter(x => x.sessions).length, "active day") : none);
  if (count) bars(s, series("sessions"), "sessions");

  const m = d.memory;
  const pending = m ? m.candidates + m.review : 0;
  kpi(grid, "Facts awaiting review", m ? String(pending) : "—", m ? `${m.approved} promoted` : "Memory board not found", pending ? "warn" : undefined);

  const last = d.sessions[0]?.file.mtime;
  const hours = last ? (Date.now() - msOf(last)) / 3600000 : null;
  const [label, tone] = hours === null ? ["No data"] : hours < 3 ? ["Healthy", "ok"] : hours < 48 ? ["Idle"] : ["Stale", "warn"];
  kpi(grid, "Archiver", label, last ? `Last archive ${timeAgo(last)}` : "No archived sessions", tone);
}

function fileList(body, pages, emptyText) {
  if (!pages.length) return empty(body, emptyText);
  for (const p of pages) {
    const row = link(body, p.file.path, "hbd-row");
    const info = row.createDiv({ cls: "hbd-row-main" });
    info.createDiv({ cls: "hbd-row-title", text: p.file.name });
    info.createDiv({ cls: "hbd-row-sub", text: p.file.folder || "Vault root" });
    row.createSpan({ cls: "hbd-muted", text: timeAgo(p.file.mtime) });
  }
}

const sections = [
  ["Recent sessions", 8, { action: "Timeline", onAction: () => openKey("timeline") }, ({ body }, d) =>
    fileList(body, d.sessions.slice(0, 6), "No archived sessions yet. They appear here once saved to 04-Archives/Daily.")],

  ["Memory pipeline", 4, { action: "Open board", onAction: () => openKey("board") }, ({ body }, d) => {
    const m = d.memory;
    if (!m) return empty(body, "Memory board not found.");
    const total = m.candidates + m.review + m.approved + m.rejected;
    if (!total) return empty(body, "The memory board is empty.");
    const pct = Math.round(((m.approved + m.rejected) / total) * 100);
    body.createDiv({ cls: "hbd-big", text: `${pct}% reviewed` });
    const track = body.createDiv({ cls: "hbd-track", attr: { role: "progressbar", "aria-valuenow": String(pct), "aria-valuemin": "0", "aria-valuemax": "100" } });
    track.createDiv({ cls: "hbd-fill-ok" }).style.width = `${pct}%`;
    statRow(body, "Candidates", String(m.candidates), m.candidates ? "warn" : "neutral");
    statRow(body, "Under review", String(m.review), m.review ? "warn" : "neutral");
    statRow(body, "Promoted", String(m.approved), "ok");
    statRow(body, "Rejected", String(m.rejected), "neutral");
  }],

  ["Active projects", 6, { action: "All projects", onAction: () => openKey("projects") }, ({ body }, d) =>
    fileList(body, d.projects.slice(0, 6), "No notes with type: project and status: active.")],

  ["Recent activity", 6, {}, ({ body }, d) =>
    fileList(body, d.recent, "No recent edits.")],

  ["Vault health", 4, {}, ({ body, meta }, d) => {
    const h = d.health, r = d.review;
    if (!h && !r) return empty(body, "No reports. Run vault_audit.py and self_critique.py.");
    const row = (label, n, path, bad) =>
      statRow(body, label, n === null ? "Unreadable" : n.toLocaleString(), n === null ? "warn" : n ? bad : "ok", path);
    if (h) {
      freshness(meta, h.date);
      row("Broken links (audit)", h.broken, h.path, "error");
      row("Stale memory reviews", h.stale, h.path, "warn");
      row("Duplicate sessions", h.duplicates, h.path, "warn");
      row("Manifest issues", h.manifest, h.path, "warn");
      row("Orphaned files (info)", h.orphans, h.path, "neutral");
    }
    if (r) {
      row("Broken links (critique)", r.broken, r.path, "error");
      row("Self-critique findings", r.total, r.path, r.serious ? "warn" : "neutral");
    }
  }],

  ["Skill quality", 4, {}, ({ body, meta }, d) => {
    const q = d.quality;
    if (!q || !q.total) return empty(body, "No results. Run skill_quality_checker.py.");
    freshness(meta, q.date);
    body.createDiv({ cls: "hbd-big", text: `${Math.round((q.ready / q.total) * 100)}% ready` });
    const track = body.createDiv({ cls: "hbd-track" });
    [["ok", q.ready], ["warn", q.rework], ["error", q.reject]].forEach(([tone, n]) => {
      track.createDiv({ cls: `hbd-fill-${tone}` }).style.width = `${(n / q.total) * 100}%`;
    });
    statRow(body, "Ready", String(q.ready), "ok", q.path);
    statRow(body, "Needs rework", String(q.rework), q.rework ? "warn" : "neutral", q.path);
    statRow(body, "Rejected", String(q.reject), q.reject ? "error" : "neutral", q.path);
  }],

  ["System", 4, {}, ({ body }, d) => {
    statRow(body, "Vault version", d.version ? `v${d.version}` : "Unknown");
    statRow(body, "Markdown notes", d.noteCount.toLocaleString());
    statRow(body, "Archived sessions", d.sessions.length.toLocaleString());
    statRow(body, "Active projects", d.projects.length.toLocaleString());
  }],
];

// ---------- render ----------
const container = dv.el("div", "", { cls: "hbd" });

async function render() {
  try {
    const data = await loadData();
    container.empty();
    header(container);
    const grid = container.createDiv({ cls: "hbd-grid" });
    attention(grid, alerts(data));
    kpis(grid, data);
    for (const [title, span, opts, fill] of sections) {
      const c = card(grid, title, span, opts);
      try { fill(c, data); }
      catch (e) { console.error(`[Dashboard-Beta] ${title}`, e); empty(c.body, `Could not load: ${e.message}`); }
    }
    container.createDiv({ cls: "hbd-footer", text: `Updated ${new Date().toLocaleTimeString()}` });
  } catch (e) {
    console.error("[Dashboard-Beta]", e);
    container.empty();
    empty(container, `Dashboard failed to load: ${e.message}`);
  }
}

await render();
```
