---
type: dashboard
status: beta
created: 2026-09-14
updated: 2026-10-11
tags: [dashboard, hub, beta]
cssclasses: [dashboard-wide, hb-app]
---

%%
Theme integration: styled by the `dashboard-beta` CSS snippet (Settings → Appearance → CSS snippets).
Requires the Dataview plugin with JavaScript queries enabled. Best viewed in Reading view.
Everything renders from the single dataviewjs block below; each widget is isolated, so one
failing widget shows an inline error instead of breaking the whole dashboard.
Original linear view: [[Dashboard]]
%%

```dataviewjs
// ============================================================
//  HERMES BRAIN — APP-STYLE DASHBOARD (single 12-column grid)
// ============================================================
const vault = app.vault;
const root = dv.el("div", "", { cls: "hb-dash" });

// ---------- helpers ----------
const pad = n => String(n).padStart(2, "0");
const localISO = d => `${d.getFullYear()}-${pad(d.getMonth() + 1)}-${pad(d.getDate())}`;
const arr = x => !x ? [] : (x.array ? x.array() : Array.from(x));
const getFile = (...paths) => paths.map(p => vault.getAbstractFileByPath(p)).find(Boolean);
const open = path => app.workspace.openLinkText(path, "", false);
const msOf = t => !t ? 0 : (t.toMillis ? t.toMillis() : new Date(t).getTime());
const compact = n => new Intl.NumberFormat(undefined, { notation: "compact", maximumFractionDigits: 1 }).format(n);
const store = {
  get: k => { try { return localStorage.getItem(k); } catch { return null; } },
  set: (k, v) => { try { localStorage.setItem(k, v); } catch {} },
};

function link(parent, text, path, cls = "") {
  const a = parent.createEl("a", { text, cls: `internal-link ${cls}`.trim(), href: path });
  a.addEventListener("click", e => { e.preventDefault(); open(path); });
  return a;
}

function timeAgo(t) {
  const min = Math.floor((Date.now() - msOf(t)) / 60000);
  if (min < 1) return "just now";
  if (min < 60) return `${min}m ago`;
  const hr = Math.floor(min / 60);
  return hr < 24 ? `${hr}h ago` : `${Math.floor(hr / 24)}d ago`;
}

function row(parent, { title, sub, badge, badgeCls = "hb-badge-info", path }) {
  const r = parent.createEl("div", { cls: "hb-row" });
  const main = r.createEl("div", { cls: "hb-row-main" });
  main.createEl("div", { cls: "hb-row-title", text: title });
  if (sub) main.createEl("div", { cls: "hb-row-sub", text: sub });
  if (badge) r.createEl("span", { cls: `hb-badge ${badgeCls}`, text: badge });
  if (path) { r.addClass("is-clickable"); r.addEventListener("click", () => open(path)); }
  return r;
}

// cells: string, or (td) => void for custom content
function table(parent, headers, rows) {
  const t = parent.createEl("table", { cls: "hb-table" });
  const hr = t.createEl("thead").createEl("tr");
  headers.forEach(h => hr.createEl("th", { text: h }));
  const tb = t.createEl("tbody");
  for (const cells of rows) {
    const tr = tb.createEl("tr");
    cells.forEach(c => {
      const td = tr.createEl("td");
      typeof c === "function" ? c(td) : td.setText(c ?? "");
    });
  }
  return t;
}

const empty = (parent, text) => parent.createEl("div", { cls: "hb-empty", text });

function card(span, title, { action, actionPath, cls } = {}) {
  const c = root.createEl("section", { cls: `hb-card hb-span-${span} ${cls || ""}`.trim() });
  if (title) {
    const h = c.createEl("header", { cls: "hb-card-head" });
    h.createEl("span", { cls: "hb-card-title", text: title });
    if (action) link(h, action, actionPath, "hb-card-action");
  }
  return c.createEl("div", { cls: "hb-card-body" });
}

const jobs = [];
function widget(span, title, opts, fill) {
  const body = card(span, title, opts);
  jobs.push(Promise.resolve().then(() => fill(body)).catch(err => {
    body.empty();
    empty(body, `⚠️ Couldn't load: ${err.message}`);
    console.error(`[Dashboard-Beta] ${title}`, err);
  }));
}

async function openDailyReview() {
  const tpl = getFile("_System/Templates/Daily-Review.md", "Templates/Daily-Review.md");
  if (!tpl) { new Notice("Daily-Review template not found"); return; }
  try { app.commands.executeCommandById("templater-obsidian:create-new-note-from-template"); }
  catch { open(tpl.path); }
}

// ---------- shared data ----------
const now = new Date();
const todayISO = localISO(now);

const byDate = {};
const tokenLog = getFile("04-Archives/Audit-Reports/Token-Usage.log", "Skills-Notes/Token-Usage.log");
if (tokenLog) {
  for (const raw of (await vault.read(tokenLog)).split("\n")) {
    const m = raw.trim().match(/^(\d{4}-\d{2}-\d{2}):\s*(\d+)(?:\s*tokens?\s*\((\d+)\s*session)?/);
    if (!m) continue;
    const d = byDate[m[1]] ||= { tokens: 0, sessions: 0 };
    d.tokens += parseInt(m[2]);
    d.sessions += parseInt(m[3] || "0");
  }
}
const lastDays = n => Array.from({ length: n }, (_, i) => {
  const d = new Date(now);
  d.setDate(d.getDate() - (n - 1 - i));
  return byDate[localISO(d)] || { tokens: 0, sessions: 0 };
});

const SKIP_DAILY = new Set(["README", "manifest", "Timeline", "Chat-Correlation"]);
const dailyPages = arr(dv.pages('"04-Archives/Daily" or "Daily"').where(p => !SKIP_DAILY.has(p.file.name)))
  .sort((a, b) => msOf(b.file.mtime) - msOf(a.file.mtime));

const memTasks = arr(dv.pages('"04-Archives/Memory-Review" or "Memory-Review"').file.tasks);
const memDone = memTasks.filter(t => t.completed).length;
const memOpen = memTasks.length - memDone;

const SKIP_ANALYSIS = new Set(["Personality-Judgment-Analysis", "Personality-Judgment-Dashboard"]);
const analyses = arr(dv.pages('#personality-judgment or "04-Archives/Daily" or "Daily"')
  .where(p => p.subject && !SKIP_ANALYSIS.has(p.file.name)))
  .sort((a, b) => msOf(b.file.mtime) - msOf(a.file.mtime));

let health = { label: "No data", cls: "hb-badge-info", sub: "no archived sessions" };
if (dailyPages.length) {
  const hrs = (Date.now() - msOf(dailyPages[0].file.mtime)) / 3600000;
  const sub = `last archive ${timeAgo(dailyPages[0].file.mtime)}`;
  health = hrs < 3 ? { label: "Healthy", cls: "hb-badge-ok", sub }
    : hrs < 48 ? { label: "Idle", cls: "hb-badge-info", sub }
    : { label: "Stale", cls: "hb-badge-warn", sub };
}

// ============================================================
//  TOP BAR
// ============================================================
{
  const bar = root.createEl("header", { cls: "hb-topbar hb-span-12" });

  const brand = bar.createEl("div", { cls: "hb-brand" });
  const editable = (key, fallback, cls) => {
    const el = brand.createEl("div", { cls, text: store.get(key) || fallback, attr: { contenteditable: "true", spellcheck: "false" } });
    el.addEventListener("blur", () => { const v = el.textContent.trim(); if (v) store.set(key, v); });
    el.addEventListener("keydown", e => { if (e.key === "Enter") { e.preventDefault(); el.blur(); } });
  };
  editable("hb-dash-title", "HERMES BRAIN", "hb-brand-title");
  editable("hb-dash-mantra", "agent memory & cognitive telemetry at a glance", "hb-brand-sub");

  const mid = bar.createEl("div", { cls: "hb-topbar-mid" });
  const H = now.getHours();
  const greet = H < 5 ? "🌙 Late night session. Keep it steady."
    : H < 9 ? "🌅 New day, new flow."
    : H < 13 ? "⚡ Peak focus hours. Engage."
    : H < 18 ? "☕ Afternoon momentum. Keep moving."
    : H < 21 ? "🌆 Evening wind-down & review."
    : "🌌 Night review & memory consolidation.";
  mid.createEl("div", { cls: "hb-greet", text: greet });

  const datePart = todayISO.replace(/-/g, "/");
  const review = arr(dv.pages('"04-Archives/Daily" or "Daily"')
    .where(p => p.file.path.includes(datePart) && p.file.name.includes("Review")))[0];
  const badge = mid.createEl("span", {
    cls: `hb-badge is-clickable ${review ? "hb-badge-ok" : "hb-badge-warn"}`,
    text: review ? "✅ Daily Review logged" : "⏳ Daily Review pending",
  });
  badge.addEventListener("click", () => review ? open(review.file.path) : openDailyReview());

  const clock = bar.createEl("div", { cls: "hb-clock" });
  const timeEl = clock.createEl("div", { cls: "hb-clock-time" });
  const dateEl = clock.createEl("div", { cls: "hb-clock-date" });
  if (window._hbDashClock) clearInterval(window._hbDashClock);
  let started = false;
  const tick = () => {
    if (started && !timeEl.isConnected) { clearInterval(window._hbDashClock); return; }
    started = true;
    const d = new Date();
    timeEl.textContent = `${pad(d.getHours())}:${pad(d.getMinutes())}:${pad(d.getSeconds())}`;
    dateEl.textContent = d.toLocaleDateString(undefined, { weekday: "long", month: "long", day: "numeric" });
  };
  tick();
  window._hbDashClock = setInterval(tick, 1000);
}

// ============================================================
//  KPI STRIP
// ============================================================
{
  const strip = root.createEl("section", { cls: "hb-kpis hb-span-12" });

  function spark(parent, vals) {
    const max = Math.max(1, ...vals), w = 100, h = 28, bw = w / vals.length;
    const bars = vals.map((v, i) => {
      const bh = v ? Math.max(2, (v / max) * h) : 1;
      return `<rect x="${(i * bw + bw * 0.15).toFixed(2)}" y="${(h - bh).toFixed(2)}" width="${(bw * 0.7).toFixed(2)}" height="${bh.toFixed(2)}" rx="0.8"/>`;
    }).join("");
    parent.createEl("div", { cls: "hb-spark" }).innerHTML =
      `<svg viewBox="0 0 ${w} ${h}" preserveAspectRatio="none" aria-hidden="true">${bars}</svg>`;
  }

  function kpi(label, value, sub, { sparkVals, accent, badge } = {}) {
    const k = strip.createEl("div", { cls: "hb-kpi" });
    k.createEl("div", { cls: "hb-kpi-label", text: label });
    if (badge) k.createEl("span", { cls: `hb-badge ${badge}`, text: value });
    else k.createEl("div", { cls: `hb-kpi-value ${accent ? "is-accent" : ""}`.trim(), text: value });
    if (sub) k.createEl("div", { cls: "hb-kpi-sub", text: sub });
    if (sparkVals) spark(k, sparkVals);
  }

  const days = Object.values(byDate);
  const totalTokens = days.reduce((s, d) => s + d.tokens, 0);
  const activeDays = days.filter(d => d.tokens > 0).length;
  const last14 = lastDays(14).map(d => d.tokens);
  const avg7 = last14.slice(7).reduce((a, b) => a + b, 0) / 7;
  const todayTokens = byDate[todayISO]?.tokens || 0;
  const weekSessions = lastDays(7).reduce((s, d) => s + d.sessions, 0);
  const sessions14 = lastDays(14).map(d => d.sessions);

  kpi("Total tokens", compact(totalTokens), "last 14 days", { sparkVals: last14 });
  kpi("Tokens today", compact(todayTokens), `7-day avg ${compact(Math.round(avg7))}`);
  kpi("Sessions · 7d", String(weekSessions), "last 14 days", { sparkVals: sessions14 });
  kpi("Active days", String(activeDays), "with token activity");
  kpi("Open facts", String(memOpen), `${memDone} promoted`, { accent: memOpen > 0 });
  kpi("Analyses", String(analyses.length), "personality judgments", { accent: true });
  kpi("Archiver", health.label, health.sub, { badge: health.cls });
}

// ============================================================
//  ROW: TODAY · QUICK ACTIONS · CALENDAR
// ============================================================
widget(4, "🎯 Today", { action: "Edit profile →", actionPath: "02-Areas/User-Profile.md" }, async body => {
  const focus = body.createEl("div", { cls: "hb-field" });
  focus.createEl("div", { cls: "hb-field-label", text: "Primary focus" });
  const fEl = focus.createEl("div", {
    cls: "hb-field-value",
    text: store.get("hb-dash-focus") || "Click to set today's primary focus…",
    attr: { contenteditable: "true", spellcheck: "false" },
  });
  fEl.addEventListener("blur", () => { const v = fEl.textContent.trim(); if (v) store.set("hb-dash-focus", v); });
  fEl.addEventListener("keydown", e => { if (e.key === "Enter") { e.preventDefault(); fEl.blur(); } });

  const userFile = getFile("02-Areas/User-Profile.md", "User-Profile.md");
  if (!userFile) { empty(body, "02-Areas/User-Profile.md not found — create it to set alignment parameters."); return; }
  const txt = await vault.read(userFile);
  const pick = re => {
    const v = txt.match(re)?.[1]?.trim();
    if (!v) return "Not set";
    if (v.startsWith("_(") && v.endsWith(")_")) return "Default — customize in User-Profile.md";
    return v;
  };
  [["Tone", /-\s+\*\*Tone:\*\*\s*([^\n]+)/],
   ["When in doubt", /-\s+\*\*When in doubt:\*\*\s*([^\n]+)/],
   ["Output format", /-\s+\*\*Output format:\*\*\s*([^\n]+)/]].forEach(([label, re]) => {
    const f = body.createEl("div", { cls: "hb-field" });
    f.createEl("div", { cls: "hb-field-label", text: label });
    f.createEl("div", { cls: "hb-field-value is-static", text: pick(re) });
  });
});

widget(4, "⚡ Quick actions", {}, body => {
  const ACTIONS = [
    ["📝", "Daily Review", openDailyReview],
    ["🧠", "Memory Kanban", () => open("04-Archives/Memory-Review/Memory-Board.kanban")],
    ["⚡", "Context Preamble", () => open("04-Archives/Memory-Review/HERMES-PREAMBLE.md")],
    ["⚠️", "Log Lesson", () => open("_System/Templates/Lesson-Learned.md")],
    ["📑", "New ADR", () => open("_System/Templates/Architecture-Decision-Record.md")],
    ["🔍", "New Analysis", () => open("_System/Templates/Personality-Judgment-Analysis.md")],
    ["✨", "Smart Search", () => app.commands.executeCommandById("smart-connections:Smart Connections: Open connections view")],
    ["🛡️", "Vault Audit", () => open("04-Archives/Audit-Reports/Vault-Audit-Report.md")],
  ];
  const grid = body.createEl("div", { cls: "hb-actions" });
  for (const [icon, label, fn] of ACTIONS) {
    const b = grid.createEl("button", { cls: "hb-action" });
    b.createEl("span", { cls: "hb-action-icon", text: icon });
    b.createEl("span", { text: label });
    b.addEventListener("click", async () => {
      try { await fn(); } catch (e) { new Notice(`Failed: ${label}`); console.error(e); }
    });
  }
});

widget(4, "📅 Session calendar", {}, body => {
  const index = new Map();
  for (const p of dailyPages) {
    const m = p.file.path.match(/Daily\/(\d{4})\/(\d{2})\/(\d{2})/);
    const key = m ? `${m[1]}-${m[2]}-${m[3]}` : p.file.cday?.toISODate?.();
    if (!key) continue;
    if (!index.has(key)) index.set(key, []);
    index.get(key).push(p);
  }

  let y = now.getFullYear(), mo = now.getMonth();
  const cal = body.createEl("div", { cls: "hb-cal" });
  const detail = body.createEl("div", { cls: "hb-cal-detail" });

  function showDay(key, sessions) {
    detail.empty();
    detail.createEl("div", { cls: "hb-cal-detail-head", text: `${key} · ${sessions.length} session${sessions.length === 1 ? "" : "s"}` });
    if (!sessions.length) return;
    const ul = detail.createEl("ul");
    sessions.slice(0, 6).forEach(s => link(ul.createEl("li"), s.file.name, s.file.path));
  }

  function render() {
    cal.empty();
    const nav = cal.createEl("div", { cls: "hb-cal-nav" });
    const prev = nav.createEl("button", { cls: "hb-icon-btn", text: "‹", attr: { "aria-label": "Previous month" } });
    nav.createEl("span", { cls: "hb-cal-month", text: new Date(y, mo).toLocaleDateString(undefined, { year: "numeric", month: "long" }) });
    const next = nav.createEl("button", { cls: "hb-icon-btn", text: "›", attr: { "aria-label": "Next month" } });
    prev.addEventListener("click", () => { if (--mo < 0) { mo = 11; y--; } render(); });
    next.addEventListener("click", () => { if (++mo > 11) { mo = 0; y++; } render(); });

    const grid = cal.createEl("div", { cls: "hb-cal-grid" });
    ["Su", "Mo", "Tu", "We", "Th", "Fr", "Sa"].forEach(d => grid.createEl("div", { cls: "hb-cal-dow", text: d }));
    const first = new Date(y, mo, 1).getDay();
    const days = new Date(y, mo + 1, 0).getDate();
    for (let i = 0; i < first; i++) grid.createEl("div");
    for (let d = 1; d <= days; d++) {
      const key = `${y}-${pad(mo + 1)}-${pad(d)}`;
      const sessions = index.get(key) || [];
      const cell = grid.createEl("div", { cls: "hb-cal-day", text: String(d) });
      if (key === todayISO) cell.addClass("is-today");
      if (sessions.length) cell.addClass(sessions.length > 3 ? "is-busy" : "has-sessions");
      cell.addEventListener("click", () => showDay(key, sessions));
    }
  }
  render();
  showDay(todayISO, index.get(todayISO) || []);
});

// ============================================================
//  ROW: HEATMAP · SYSTEM
// ============================================================
widget(8, "📈 Token activity · last 26 weeks", {}, body => {
  const WEEKS = 26;
  const start = new Date(now);
  start.setDate(start.getDate() - (WEEKS * 7 - 1));
  start.setDate(start.getDate() - start.getDay()); // align to Sunday
  const maxT = Math.max(1, ...Object.values(byDate).map(d => d.tokens));

  let periodTokens = 0, periodActive = 0;
  const heat = body.createEl("div", { cls: "hb-heat" });
  ["", "Mon", "", "Wed", "", "Fri", ""].forEach(l => heat.createEl("div", { cls: "hb-heat-label", text: l }));
  const cursor = new Date(start);
  while (cursor <= now) {
    for (let i = 0; i < 7; i++) {
      const iso = localISO(cursor);
      const v = byDate[iso]?.tokens || 0;
      const cell = heat.createEl("div", { cls: "hb-heat-cell" });
      if (cursor > now) cell.addClass("is-future");
      else {
        periodTokens += v;
        if (v) periodActive++;
        cell.title = `${iso}: ${v.toLocaleString()} tokens`;
        if (v) cell.style.background = `color-mix(in srgb, var(--interactive-accent) ${Math.round(25 + (v / maxT) * 75)}%, transparent)`;
      }
      cursor.setDate(cursor.getDate() + 1);
    }
  }

  const foot = body.createEl("div", { cls: "hb-heat-foot" });
  foot.createEl("span", { cls: "hb-muted", text: `${periodTokens.toLocaleString()} tokens · ${periodActive} active days` });
  const legend = foot.createEl("span", { cls: "hb-heat-legend" });
  legend.createEl("span", { text: "Less" });
  [0, 25, 50, 75, 100].forEach(p => {
    const sw = legend.createEl("span", { cls: "hb-heat-cell" });
    if (p) sw.style.background = `color-mix(in srgb, var(--interactive-accent) ${p}%, transparent)`;
  });
  legend.createEl("span", { text: "More" });
});

widget(4, "🖥️ System", {}, async body => {
  // Version
  const vSec = body.createEl("div", { cls: "hb-field" });
  vSec.createEl("div", { cls: "hb-field-label", text: "Vault version" });
  const vVal = vSec.createEl("div", { cls: "hb-field-value is-static" });
  const versionFile = getFile("VERSION");
  if (!versionFile) vVal.setText("⚠️ No VERSION file found");
  else {
    // VERSION file format is "<schema>|<semver>", e.g. "1|1.24.1"
    const local = (await vault.read(versionFile)).trim().split("|").pop();
    vVal.createEl("span", { cls: "hb-badge hb-badge-info", text: `Checking… v${local}` });
    fetch("https://api.github.com/repos/mistrysiddh/hermes-brain-template/releases/latest")
      .then(r => { if (!r.ok) throw new Error(`HTTP ${r.status}`); return r.json(); })
      .then(data => {
        const latest = (data.tag_name || "").replace(/^v/, "");
        if (!latest) throw new Error("no tag");
        vVal.empty();
        if (latest === local) vVal.createEl("span", { cls: "hb-badge hb-badge-ok", text: `Up to date · v${local}` });
        else {
          vVal.createEl("span", { cls: "hb-badge hb-badge-warn", text: `Update: v${latest}` });
          vVal.createEl("span", { cls: "hb-muted", text: ` installed v${local} · ` });
          vVal.createEl("a", { text: "release notes", href: data.html_url, cls: "external-link" });
        }
      })
      .catch(() => {
        vVal.empty();
        vVal.createEl("span", { cls: "hb-badge hb-badge-info", text: `v${local}` });
        vVal.createEl("span", { cls: "hb-faint", text: " offline — local version" });
      });
  }

  // Weather
  const wSec = body.createEl("div", { cls: "hb-field" });
  wSec.createEl("div", { cls: "hb-field-label", text: "Weather" });
  const wBody = wSec.createEl("div");
  const W = { city: "hb-weather-city", key: "hb-weather-key" };

  function config() {
    wBody.empty();
    const form = wBody.createEl("div", { cls: "hb-form" });
    const c = form.createEl("input", { cls: "hb-input", attr: { type: "text", placeholder: "City, e.g. London, UK" } });
    const k = form.createEl("input", { cls: "hb-input", attr: { type: "password", placeholder: "OpenWeatherMap API key" } });
    c.value = store.get(W.city) || "";
    k.value = store.get(W.key) || "";
    const save = form.createEl("button", { cls: "hb-action", text: "Save & fetch" });
    save.addEventListener("click", () => { store.set(W.city, c.value.trim()); store.set(W.key, k.value.trim()); load(); });
  }

  async function load() {
    const city = store.get(W.city), key = store.get(W.key);
    if (!city || !key) { config(); return; }
    wBody.setText("Fetching…");
    try {
      const res = await fetch(`https://api.openweathermap.org/data/2.5/weather?q=${encodeURIComponent(city)}&appid=${encodeURIComponent(key)}&units=metric`);
      if (!res.ok) throw new Error(`HTTP ${res.status}`);
      const d = await res.json();
      wBody.empty();
      const w = wBody.createEl("div", { cls: "hb-weather" });
      const info = w.createEl("div");
      info.createEl("div", { cls: "hb-row-title", text: `${d.name}${d.sys?.country ? ", " + d.sys.country : ""}` });
      info.createEl("div", { cls: "hb-row-sub", text: `${d.weather?.[0]?.description || ""} · 💧${d.main?.humidity}% · 💨${Math.round(d.wind?.speed || 0)} m/s` });
      w.createEl("div", { cls: "hb-weather-temp", text: `${Math.round(d.main?.temp)}°` });
      const edit = wBody.createEl("a", { cls: "hb-faint is-clickable", text: "⚙️ change location" });
      edit.addEventListener("click", config);
    } catch (err) {
      wBody.empty();
      empty(wBody, `Weather unavailable (${err.message})`);
      const re = wBody.createEl("a", { cls: "is-clickable", text: "Reconfigure" });
      re.addEventListener("click", config);
    }
  }
  load();
});

// ============================================================
//  ROW: PROJECTS · ACTION ITEMS
// ============================================================
widget(6, "🚀 Active projects", {}, body => {
  const projects = arr(dv.pages('"01-Projects" or "Projects"')
    .where(p => p.type === "project" && p.status === "active")
    .sort(p => p.created, "desc"));
  if (!projects.length) return empty(body, "No active projects.");
  const created = p => {
    if (p.created && typeof p.created !== "string") return p.created.toISODate?.() ?? String(p.created);
    if (p.created && !p.created.includes("{{")) return p.created;
    return p.file.cday?.toISODate?.() ?? "";
  };
  table(body, ["Project", "Status", "Started"], projects.map(p => [
    td => link(td, p.file.name, p.file.path),
    td => td.createEl("span", { cls: "hb-badge hb-badge-ok", text: p.status }),
    created(p),
  ]));
});

widget(6, "✅ Next action items", {}, body => {
  const tasks = arr(dv.pages('"01-Projects" or "Projects"').file.tasks).filter(t => !t.completed);
  if (!tasks.length) return empty(body, "No pending action items across projects. 🎉");
  const list = body.createEl("div", { cls: "hb-tasks" });
  for (const t of tasks.slice(0, 7)) {
    const r = list.createEl("div", { cls: "hb-task" });
    r.createEl("span", { cls: "hb-task-box" });
    r.createEl("span", { cls: "hb-task-text", text: (t.text || "").trim() || "Untitled action item" });
    if (t.link?.path) link(r, t.link.path.split("/").pop().replace(/\.md$/, ""), t.link.path, "hb-task-src");
  }
  if (tasks.length > 7) body.createEl("div", { cls: "hb-faint", text: `+ ${tasks.length - 7} more` });
});

// ============================================================
//  ROW: MEMORY PIPELINE · VAULT PULSE
// ============================================================
widget(4, "🧠 Memory pipeline", { action: "Kanban →", actionPath: "04-Archives/Memory-Review/Memory-Board.kanban" }, body => {
  const total = memTasks.length;
  const pct = total ? Math.round((memDone / total) * 100) : 100;
  const big = body.createEl("div", { cls: "hb-big" });
  big.createEl("span", { cls: "hb-big-value", text: `${pct}%` });
  big.createEl("span", { cls: "hb-muted", text: "of candidate facts reviewed" });
  const track = body.createEl("div", { cls: "hb-progress" });
  track.createEl("div", { cls: "hb-progress-fill" }).style.width = `${pct}%`;
  const stats = body.createEl("div", { cls: "hb-stat-pair" });
  [[memDone, "promoted"], [memOpen, "pending review"]].forEach(([n, l]) => {
    const s = stats.createEl("div");
    s.createEl("div", { cls: "hb-stat-n", text: String(n) });
    s.createEl("div", { cls: "hb-faint", text: l });
  });
  body.createEl("div", { cls: "hb-faint hb-push", text: "Nightly: consolidate_memory.py → sync_to_hermes.py" });
});

widget(8, "🌐 Vault pulse · recent edits", {}, body => {
  const files = vault.getFiles();
  const notes = files.filter(f => f.extension === "md").length;
  const canvases = files.filter(f => f.extension === "canvas").length;
  const stats = body.createEl("div", { cls: "hb-inline-stats" });
  [[notes, "notes"], [canvases, "canvases"], [dailyPages.length, "archived sessions"]].forEach(([n, l]) => {
    const s = stats.createEl("span");
    s.createEl("strong", { text: n.toLocaleString() });
    s.appendText(` ${l}`);
  });
  const self = dv.current()?.file?.path;
  const recent = arr(dv.pages()
    .where(p => p.file.path !== self && !p.file.path.startsWith("04-Archives/Daily/") && !p.file.path.startsWith("Daily/"))
    .sort(p => p.file.mtime, "desc")).slice(0, 6);
  table(body, ["Note", "Folder", "Edited"], recent.map(f => [
    td => link(td, f.file.name, f.file.path),
    f.file.folder || "(root)",
    timeAgo(f.file.mtime),
  ]));
});

// ============================================================
//  ROW: PERSONALITY · AGENT ROSTER
// ============================================================
widget(6, "🎭 Behavioral analyses", { action: "Full dashboard →", actionPath: "_System/Templates/Personality-Judgment-Dashboard.md" }, body => {
  if (!analyses.length) return empty(body, "No analyses yet — start one from Quick actions.");
  table(body, ["Subject", "Primary style", "Confidence"], analyses.slice(0, 5).map(a => {
    const conf = a.confidence ? String(a.confidence).trim() : "Review";
    const cls = { high: "hb-badge-ok", medium: "hb-badge-warn" }[conf.toLowerCase()] || "hb-badge-info";
    return [
      td => link(td, String(a.subject), a.file.path),
      a.primary_style ?? "—",
      td => td.createEl("span", { cls: `hb-badge ${cls}`, text: conf }),
    ];
  }));
});

widget(6, "🤖 Agent roster", { action: "Chat correlation →", actionPath: "04-Archives/Daily/Chat-Correlation.md" }, async body => {
  const teamFile = getFile("02-Areas/Skills/Team-Profiles-Index.md", "Skills-Notes/Team-Profiles-Index.md");
  if (!teamFile) return empty(body, "02-Areas/Skills/Team-Profiles-Index.md not found.");
  const rows = (await vault.read(teamFile)).split("\n")
    .filter(l => l.trim().startsWith("|") && !/^\|[\s:-]+\|/.test(l.trim()) && !l.toLowerCase().includes("profile |"))
    .map(l => l.split("|").map(c => c.trim()).filter(Boolean))
    .filter(c => c.length >= 2);
  if (!rows.length) return empty(body, "No profiles configured yet.");
  table(body, ["Profile", "Specialization"], rows.map(c => [
    td => td.createEl("strong", { cls: "hb-accent", text: c[0] }),
    c[1],
  ]));
});

// ============================================================
//  ROW: SKILLS · RESEARCH
// ============================================================
widget(6, "⚡ Skill competencies", { action: "Full catalog →", actionPath: "02-Areas/Skills/Installed-Skills-Index.md" }, async body => {
  const mapFile = getFile("_System/Scripts/tag_skill_map.json", "Scripts/tag_skill_map.json");
  if (!mapFile) return empty(body, "Maintain skills in 02-Areas/Skills/Installed-Skills-Index.md.");
  const map = JSON.parse(await vault.read(mapFile));
  const cats = Object.entries(map).filter(([, s]) => Array.isArray(s) && s.length).slice(0, 6);
  const grid = body.createEl("div", { cls: "hb-tiles" });
  for (const [cat, skills] of cats) {
    const t = grid.createEl("div", { cls: "hb-tile" });
    const h = t.createEl("div", { cls: "hb-tile-head" });
    h.createEl("span", { cls: "hb-field-label", text: cat });
    h.createEl("span", { cls: "hb-badge hb-badge-info", text: String(skills.length) });
    t.createEl("div", { cls: "hb-row-sub", text: skills.map(s => s.replace(/-/g, " ")).join(", ") });
  }
});

widget(6, "🔬 Active research", {}, body => {
  const notes = arr(dv.pages('"03-Resources/Research" or "Research"')
    .where(p => p.file.name !== "README")
    .sort(p => p.file.mtime, "desc")).slice(0, 6);
  if (!notes.length) return empty(body, "No research notes yet — use 03-Resources/Research/.");
  const list = body.createEl("div", { cls: "hb-rows" });
  notes.forEach(r => row(list, {
    title: r.file.name,
    sub: arr(r.file.tags).slice(0, 4).join(" ") || r.file.folder,
    badge: timeAgo(r.file.mtime),
    path: r.file.path,
  }));
});

// ============================================================
//  ROW: KNOWLEDGE HUBS · HEALTH · TAGS
// ============================================================
widget(4, "🗺️ Knowledge hubs", {}, body => {
  const list = body.createEl("div", { cls: "hb-rows" });
  [
    ["Agentic Architecture", "03-Resources/MOCs/Agentic-Architecture-MOC.md", "Multi-agent systems & orchestration", "MOC", "hb-badge-blue"],
    ["AI & Machine Learning", "03-Resources/MOCs/AI-ML-MOC.md", "Models, embeddings & evaluation", "MOC", "hb-badge-blue"],
    ["Cybersecurity", "03-Resources/MOCs/Cybersecurity-MOC.md", "Threats, defenses & compliance", "MOC", "hb-badge-blue"],
    ["Technology Stack", "03-Resources/MOCs/Technology-Stack-MOC.md", "Frameworks, databases, infra", "MOC", "hb-badge-blue"],
    ["Vault Master MOC", "MOC.md", "Complete index of the brain", "MOC", "hb-badge-blue"],
    ["Memory Pipeline", "_System/Canvases/Memory-Pipeline.canvas", "Cron export, staging & durable facts", "Canvas", "hb-badge-purple"],
    ["Personality Judgment", "_System/Canvases/Personality-Judgment-Canvas.canvas", "11-dimension behavioral framework", "Canvas", "hb-badge-purple"],
  ].forEach(([title, path, sub, badge, badgeCls]) => row(list, { title, sub, badge, badgeCls, path }));
});

widget(4, "🛡️ Vault health", { action: "Report →", actionPath: "04-Archives/Audit-Reports/Vault-Audit-Report.md" }, async body => {
  const report = getFile("04-Archives/Audit-Reports/Vault-Audit-Report.md", "Skills-Notes/Vault-Audit-Report.md");
  if (!report) return empty(body, "No audit yet — generated on first vault_audit.py run.");
  const txt = await vault.read(report);
  const summary = txt.match(/## Summary\r?\n\r?\n([\s\S]*?)\r?\n---/)?.[1] || "";
  const checks = [...summary.matchAll(/-\s+\*\*([^*]+)\*\*:\s*(\d+)/g)];
  if (!checks.length) empty(body, "Audit summary not found in report.");
  const issues = checks.reduce((s, m) => s + parseInt(m[2]), 0);
  if (checks.length) {
    const big = body.createEl("div", { cls: "hb-big" });
    big.createEl("span", { cls: `hb-big-value ${issues ? "is-warn" : ""}`.trim(), text: String(issues) });
    big.createEl("span", { cls: "hb-muted", text: issues ? "open issues" : "issues — all clear" });
  }
  const list = body.createEl("div", { cls: "hb-checks" });
  for (const [, label, count] of checks) {
    const r = list.createEl("div", { cls: "hb-check" });
    r.createEl("span", { text: label });
    r.createEl("span", { cls: `hb-badge ${+count ? "hb-badge-warn" : "hb-badge-ok"}`, text: count });
  }
  const gen = txt.match(/Generated:\s*([^\n]+)/)?.[1];
  if (gen) body.createEl("div", { cls: "hb-faint hb-push", text: `Last audit: ${gen.trim()}` });
});

widget(4, "🏷️ Top tags", {}, body => {
  const counts = {};
  for (const p of arr(dv.pages())) for (const t of arr(p.file.tags)) {
    const tag = t.startsWith("#") ? t : `#${t}`;
    counts[tag] = (counts[tag] || 0) + 1;
  }
  const top = Object.entries(counts).sort((a, b) => b[1] - a[1]).slice(0, 18);
  if (!top.length) return empty(body, "No tags indexed.");
  const wrap = body.createEl("div", { cls: "hb-pills" });
  for (const [tag, n] of top) {
    const pill = wrap.createEl("button", { cls: "hb-pill" });
    pill.createEl("span", { text: tag });
    pill.createEl("span", { cls: "hb-pill-n", text: String(n) });
    pill.addEventListener("click", () => {
      app.internalPlugins.getPluginById("global-search")?.instance?.openGlobalSearch(`tag:${tag}`);
    });
  }
});

// ============================================================
//  ROW: RECENT SESSIONS
// ============================================================
widget(12, "📜 Recent sessions", { action: "Full timeline →", actionPath: "04-Archives/Daily/Timeline.md" }, body => {
  if (!dailyPages.length) return empty(body, "No archived sessions in 04-Archives/Daily/.");
  table(body, ["Session", "Folder", "Modified"], dailyPages.slice(0, 8).map(p => [
    td => link(td, p.file.name, p.file.path),
    p.file.folder ?? "",
    td => { td.setText(timeAgo(p.file.mtime)); td.title = p.file.mtime?.toISO?.() ?? ""; },
  ]));
});

await Promise.all(jobs);
```
