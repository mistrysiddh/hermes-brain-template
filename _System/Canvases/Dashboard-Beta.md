---
type: dashboard
status: beta
created: 2026-09-14
updated: 2026-11-16
tags: [dashboard, hub, beta, admin]
cssclasses: [dashboard-wide, hb-app]
---

%%
Hermes Brain — Dashboard-Beta

Admin-dashboard styling with design-system tokens:
- Slate/gray surface, blue accent, semantic status colors
- 0.25rem spacing scale, 8-12px border radius, subtle shadows
- Cards with hover states, accessible badges, sparkline charts

Requires Dataview plugin with JavaScript queries enabled.
Best viewed in Reading view.
%%

```dataviewjs
// ============================================================
//  HERMES BRAIN — DASHBOARD-BETA (admin-dashboard styling)
//  Design system tokens + widget-based canvas layout
// ============================================================

const vault = app.vault;

// ---------- design tokens ----------
const T = {
  surface: "var(--background-secondary)",
  surfaceHover: "var(--background-modifier-hover)",
  border: "var(--background-modifier-border)",
  textPrimary: "var(--text-normal)",
  textSecondary: "var(--text-muted)",
  textFaint: "var(--text-faint)",
  accent: "var(--interactive-accent)",
  accentHover: "color-mix(in srgb, var(--interactive-accent) 90%, transparent)",
  ok: "var(--text-success)",
  okBg: "color-mix(in srgb, var(--text-success) 12%, transparent)",
  warn: "var(--text-warning)",
  warnBg: "color-mix(in srgb, var(--text-warning) 12%, transparent)",
  error: "var(--text-error)",
  errorBg: "color-mix(in srgb, var(--text-error) 12%, transparent)",
  info: "var(--text-accent)",
  infoBg: "color-mix(in srgb, var(--text-accent) 12%, transparent)",
  spacing: { xs: "4px", sm: "8px", md: "12px", lg: "16px", xl: "24px", xxl: "32px" },
  radius: { sm: "6px", md: "8px", lg: "12px" },
  shadow: "0 1px 3px rgba(0,0,0,0.08), 0 1px 2px rgba(0,0,0,0.06)",
};

// ---------- helpers ----------
const pad = n => String(n).padStart(2, "0");
const localISO = d => `${d.getFullYear()}-${pad(d.getMonth() + 1)}-${pad(d.getDate())}`;
const arr = x => !x ? [] : (x.array ? x.array() : Array.from(x));
const getFile = (...paths) => paths.map(p => vault.getAbstractFileByPath(p)).find(Boolean);
const open = path => app.workspace.openLinkText(path, "", false);
const msOf = t => !t ? 0 : (t.toMillis ? t.toMillis() : new Date(t).getTime());
const compact = n => new Intl.NumberFormat(undefined, { notation: "compact", maximumFractionDigits: 1 }).format(n);
const timeAgo = t => {
  const min = Math.floor((Date.now() - msOf(t)) / 60000);
  if (min < 1) return "just now";
  if (min < 60) return `${min}m ago`;
  const hr = Math.floor(min / 60);
  return hr < 24 ? `${hr}h ago` : `${Math.floor(hr / 24)}d ago`;
};

const store = {
  get: k => { try { return localStorage.getItem(k); } catch { return null; } },
  set: (k, v) => { try { localStorage.setItem(k, v); } catch {} },
};

function el(tag, opts = {}) {
  const e = document.createElement(tag);
  if (opts.attr) Object.entries(opts.attr).forEach(([k, v]) => e.setAttribute(k, v));
  if (opts.style) Object.assign(e.style, opts.style);
  if (opts.classes) opts.classes.split(/\s+/).forEach(c => e.addClass(c));
  if (opts.text) e.setText(opts.text);
  return e;
}

// Obsidian's createEl() has no `style` option, so apply it ourselves.
function ce(parent, tag, opts = {}) {
  const { style, ...rest } = opts;
  const e = parent.createEl(tag, rest);
  if (style) Object.assign(e.style, style);
  return e;
}

function badge(text, variant = "info") {
  const bg = { ok: T.okBg, warn: T.warnBg, error: T.errorBg, info: T.infoBg, neutral: T.surfaceHover };
  const fg = { ok: T.ok, warn: T.warn, error: T.error, info: T.info, neutral: T.textSecondary };
  return el("span", { text,
    style: {
      display: "inline-flex", alignItems: "center", padding: "2px 8px",
      borderRadius: T.radius.sm, fontSize: "0.75rem", fontWeight: 600,
      background: bg[variant] || bg.info, color: fg[variant] || fg.info,
    },
  });
}

function card(title, { subtitle, action, actionPath, span = 12 } = {}) {
  const root = el("section", {
    classes: `hb-card hb-span-${span}`,
    style: {
      background: T.surface, border: `1px solid ${T.border}`,
      borderRadius: T.radius.lg, boxShadow: T.shadow,
      display: "flex", flexDirection: "column", overflow: "hidden",
      transition: "all 0.2s ease",
    },
  });
  root.addEventListener("mouseenter", () => { root.style.borderColor = T.accent; });
  root.addEventListener("mouseleave", () => { root.style.borderColor = T.border; });

  if (title) {
    const head = el("div", {
      style: {
        display: "flex", alignItems: "center", justifyContent: "space-between",
        padding: `${T.spacing.lg} ${T.spacing.xl}`,
        borderBottom: `1px solid ${T.border}`,
      },
    });
    const titleBox = el("div", {});
    head.appendChild(titleBox);
    ce(titleBox, "span", { text: title, style: { fontSize: "0.875rem", fontWeight: 600, color: T.textPrimary, letterSpacing: "0.02em" } });
    if (subtitle) ce(titleBox, "span", { text: subtitle, style: { fontSize: "0.75rem", color: T.textFaint, marginTop: T.spacing.xs, display: "block" } });
    if (action) {
      const btn = el("a", { text: action,
        style: { textDecoration: "none", fontSize: "0.85rem", color: T.accent, padding: `${T.spacing.sm} ${T.spacing.md}`, borderRadius: T.radius.md, background: "color-mix(in srgb, var(--interactive-accent) 14%, transparent)", transition: "background 0.2s ease" }, href: actionPath });
      btn.addEventListener("click", e => { e.preventDefault(); open(actionPath); });
      head.appendChild(btn);
    }
    root.appendChild(head);
  }

  const body = el("div", { style: { padding: T.spacing.xl, flex: 1 } });
  root.appendChild(body);
  return { root, body };
}

function kpi(label, value, sub, { accent = false, trend, color } = {}) {
  const k = el("div", {
    style: { display: "flex", flexDirection: "column", gap: T.spacing.sm, padding: T.spacing.lg, background: T.surface, border: `1px solid ${T.border}`, borderRadius: T.radius.md, minWidth: 140 },
  });
  ce(k, "span", { text: label, style: { fontSize: "0.8rem", color: T.textSecondary } });
  const valWrap = el("div", { style: { display: "flex", flexWrap: "wrap", alignItems: "baseline", gap: T.spacing.sm } });
  ce(valWrap, "span", { text: value, style: { fontSize: "1.75rem", fontWeight: 700, color: color || (accent ? T.accent : T.textPrimary) } });
  if (trend) ce(valWrap, "span", { text: trend.text, style: { fontSize: "0.85rem", fontWeight: 600, color: trend.ok ? T.ok : T.error } });
  k.appendChild(valWrap);
  if (sub) ce(k, "span", { text: sub, style: { fontSize: "0.8rem", color: T.textFaint } });
  return k;
}

function sparkline(parent, vals, color = T.accent) {
  const max = Math.max(1, ...vals);
  const w = 100, h = 24, bw = w / vals.length;
  const bars = vals.map((v, i) => {
    const bh = v ? Math.max(1.5, (v / max) * h) : 1;
    return `<rect x="${(i * bw + bw * 0.2).toFixed(2)}" y="${(h - bh).toFixed(2)}" width="${(bw * 0.6).toFixed(2)}" height="${bh.toFixed(2)}" rx="1" fill="${color}"/>`;
  }).join("");
  ce(parent, "div", { style: { width: "100%" } }).innerHTML =
    `<svg viewBox="0 0 ${w} ${h}" preserveAspectRatio="none" aria-hidden="true" style="width:100%;height:${h}px;display:block">${bars}</svg>`;
}

const root = dv.el("div", "", { cls: "hb-dash" });

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

let health = { label: "No data", cls: "info", sub: "no archived sessions" };
if (dailyPages.length) {
  const hrs = (Date.now() - msOf(dailyPages[0].file.mtime)) / 3600000;
  const sub = `last archive ${timeAgo(dailyPages[0].file.mtime)}`;
  health = hrs < 3 ? { label: "Healthy", cls: "ok", sub }
    : hrs < 48 ? { label: "Idle", cls: "info", sub }
    : { label: "Stale", cls: "warn", sub };
}

const jobs = [];
function widget(span, title, opts, fill) {
  const { root: cardRoot, body } = card(title, opts);
  jobs.push(Promise.resolve().then(() => fill(body)).catch(err => {
    body.empty();
    ce(body, "div", { text: `⚠️ ${err.message}`, style: { color: T.error, padding: T.spacing.lg } });
    console.error(`[Dashboard-Beta] ${title}`, err);
  }));
  root.appendChild(cardRoot);
}

// ============================================================
//  TOP BAR
// ============================================================
{
  const bar = ce(root, "header", { cls: "hb-topbar hb-span-12" });
  bar.style.cssText = `display:flex;align-items:center;justify-content:space-between;padding:0 ${T.spacing.xl};height:64px;background:${"var(--background-secondary)"};border-bottom:1px solid ${T.border};flex-shrink:0`;

  const left = ce(bar, "div", { style: { display: "flex", alignItems: "center", gap: T.spacing.lg } });
  ce(left, "div", { text: new Date().getHours() < 12 ? "Good morning, Siddh" : "Good afternoon, Siddh", style: { fontSize: "0.9rem", color: T.textSecondary } });

  const search = ce(left, "div", { style: { position: "relative", width: "280px" } });
  const si = ce(search, "input", { attr: { type: "text", placeholder: "Search vault…" },
    style: { width: "100%", padding: "8px 12px 8px 32px", borderRadius: T.radius.md, border: `1px solid ${T.border}`, background: T.surface, fontSize: "0.875rem", color: T.textPrimary } });
  si.addEventListener("focus", () => { si.style.borderColor = T.accent; });
  si.addEventListener("blur", () => { si.style.borderColor = T.border; });
  ce(search, "span", { text: "🔍", style: { position: "absolute", left: "10px", top: "50%", transform: "translateY(-50%)", fontSize: "0.9rem" } });

  const right = ce(bar, "div", { style: { display: "flex", alignItems: "center", gap: T.spacing.md } });
  const notif = ce(right, "button", { text: "🔔",
    style: { background: "none", border: "none", cursor: "pointer", fontSize: "1.1rem", padding: T.spacing.sm, borderRadius: T.radius.md, color: T.textSecondary } });
  notif.addEventListener("mouseenter", () => { notif.style.background = T.surfaceHover; });
  notif.addEventListener("mouseleave", () => { notif.style.background = "none"; });

  const user = ce(right, "div", {
    style: { display: "flex", alignItems: "center", gap: T.spacing.sm, padding: `${T.spacing.sm} ${T.spacing.md}`, background: T.surfaceHover, borderRadius: T.radius.lg, border: `1px solid ${T.border}` },
  });
  ce(user, "div", { text: "S", style: { width: "28px", height: "28px", borderRadius: "50%", background: T.accent, color: "white", display: "flex", alignItems: "center", justifyContent: "center", fontWeight: 700, fontSize: "0.9rem" } });
  const ui = ce(user, "div", {});
  ce(ui, "div", { text: "Siddh Mistry", style: { fontSize: "0.875rem", fontWeight: 600, color: T.textPrimary } });
  ce(ui, "div", { text: "Owner · Hermes Brain", style: { fontSize: "0.75rem", color: T.textFaint } });

  root.appendChild(bar);
}

// ============================================================
//  KPI STRIP
// ============================================================
{
  const section = ce(root, "section", { cls: "hb-span-12", style: { marginBottom: T.spacing.xxl } });
  ce(section, "h2", { text: "Overview", style: { fontSize: "1rem", fontWeight: 600, color: T.textPrimary, marginBottom: T.spacing.lg, textTransform: "uppercase", letterSpacing: "0.05em" } });

  const strip = ce(section, "div", {
    style: { display: "grid", gridTemplateColumns: "repeat(auto-fit, minmax(150px, 1fr))", gap: T.spacing.lg },
  });

  const days = Object.values(byDate);
  const totalTokens = days.reduce((s, d) => s + d.tokens, 0);
  const activeDays = days.filter(d => d.tokens > 0).length;
  const last14 = lastDays(14).map(d => d.tokens);
  const avg7 = last14.slice(7).reduce((a, b) => a + b, 0) / 7;
  const todayTokens = byDate[todayISO]?.tokens || 0;
  const weekSessions = lastDays(7).reduce((s, d) => s + d.sessions, 0);
  const sessions14 = lastDays(14).map(d => d.sessions);

  strip.appendChild(kpi("Total tokens", compact(totalTokens), "last 14 days", { accent: true, color: "#22c55e", trend: { text: `+${Math.round((totalTokens / Math.max(activeDays, 1))).toLocaleString()}/day`, ok: true } }));
  strip.appendChild(kpi("Tokens today", compact(todayTokens), `7-day avg ${compact(Math.round(avg7))}`));
  strip.appendChild(kpi("Sessions · 7d", String(weekSessions), "last 14 days"));
  strip.appendChild(kpi("Active days", String(activeDays), "with token activity"));
  strip.appendChild(kpi("Open facts", String(memOpen), `${memDone} promoted`, { accent: memOpen > 0 }));
  strip.appendChild(kpi("Archiver", health.label, health.sub));

  const firstKpi = strip.children[0];
  const sparkWrap = el("div", { style: { marginTop: T.spacing.md, height: "20px" } });
  sparkline(sparkWrap, last14, "#22c55e");
  firstKpi.appendChild(sparkWrap);

  root.appendChild(section);
}

// ============================================================
//  WIDGETS
// ============================================================

// Row 1: Quick actions · Memory · Vault health · Skill quality
{
  widget(6, "Quick actions", { span: 6, subtitle: "Common vault operations" }, async body => {
    const grid = ce(body, "div", { style: { display: "grid", gridTemplateColumns: "repeat(2, 1fr)", gap: T.spacing.md } });
    const actions = [
      ["📝", "Daily Review", () => { const tpl = getFile("_System/Templates/Daily-Review.md", "Templates/Daily-Review.md"); if (!tpl) { new Notice("Daily-Review template not found"); return; } try { app.commands.executeCommandById("templater-obsidian:create-new-note-from-template"); } catch { open(tpl.path); } }],
      ["🧠", "Memory Kanban", () => open("04-Archives/Memory-Review/Memory-Board.kanban")],
      ["⚡", "Context Preamble", () => open("04-Archives/Memory-Review/HERMES-PREAMBLE.md")],
      ["⚠️", "Log Lesson", () => open("_System/Templates/Lesson-Learned.md")],
      ["📑", "New ADR", () => open("_System/Templates/Architecture-Decision-Record.md")],
      ["🛡️", "Vault Audit", () => open("04-Archives/Audit-Reports/Vault-Audit-Report.md")],
    ];
    for (const [icon, label, fn] of actions) {
      const b = el("button", {
        style: { display: "flex", alignItems: "center", gap: T.spacing.md, padding: T.spacing.md, border: `1px solid ${T.border}`, background: "transparent", borderRadius: T.radius.md, fontSize: "0.875rem", cursor: "pointer", transition: "all 0.15s ease" },
      });
      ce(b, "span", { text: icon, style: { fontSize: "1.2rem" } });
      ce(b, "span", { text: label, style: { flex: 1, color: T.textPrimary } });
      b.addEventListener("mouseenter", () => { b.style.background = T.surfaceHover; b.style.borderColor = T.accent; });
      b.addEventListener("mouseleave", () => { b.style.background = "transparent"; b.style.borderColor = T.border; });
      b.addEventListener("click", async () => { try { await fn(); } catch (e) { new Notice(`Failed: ${label}`); } });
      grid.appendChild(b);
    }
    body.appendChild(grid);
  });

  widget(6, "Memory pipeline", { span: 6, subtitle: "Candidate facts → durable memory" }, body => {
    const total = memTasks.length;
    const pct = total ? Math.round((memDone / total) * 100) : 100;
    const h = ce(body, "div", { style: { display: "flex", justifyContent: "space-between", alignItems: "baseline", marginBottom: T.spacing.lg } });
    ce(h, "span", { text: `${pct}%`, style: { fontSize: "2rem", fontWeight: 700 } });
    ce(h, "span", { text: "reviewed", style: { fontSize: "0.875rem", color: T.textSecondary } });

    const track = ce(body, "div", { style: { height: "8px", background: T.border, borderRadius: T.radius.sm, overflow: "hidden", marginBottom: T.spacing.md } });
    const fill = ce(track, "div", { style: { height: "100%", width: `${pct}%`, background: pct >= 80 ? T.ok : pct >= 50 ? T.warn : T.error, borderRadius: T.radius.sm, transition: "width 0.5s ease" } });

    const stats = ce(body, "div", { style: { display: "flex", justifyContent: "space-between", fontSize: "0.875rem", color: T.textSecondary } });
    [[memDone, "Promoted"], [memOpen, "Pending"]].forEach(([n, label]) => {
      const s = ce(stats, "div", { style: { textAlign: "center" } });
      ce(s, "div", { text: String(n), style: { fontSize: "1.125rem", fontWeight: 700, color: T.textPrimary } });
      ce(s, "div", { text: label });
    });
    ce(body, "div", { text: "Nightly: consolidate_memory.py → sync_to_hermes.py", style: { fontSize: "0.75rem", color: T.textFaint, marginTop: T.spacing.md } });
  });

  widget(6, "Vault health", { span: 6, subtitle: "Issues detected by vault_audit.py" }, async body => {
    const report = getFile("04-Archives/Audit-Reports/Vault-Audit-Report.md", "Skills-Notes/Vault-Audit-Report.md");
    if (!report) { ce(body, "div", { text: "No audit report found — run vault_audit.py to generate.", style: { color: T.textFaint, padding: T.spacing.lg } }); return; }
    const txt = await vault.read(report);
    const summary = txt.match(/## Summary\r?\n\r?\n([\s\S]*?)\r?\n---/)?.[1] || "";
    const checks = [...summary.matchAll(/-\s+\*\*([^*]+)\*\*:\s*(\d+)/g)];
    const issues = checks.reduce((s, m) => s + parseInt(m[2]), 0);

    const big = ce(body, "div", { style: { display: "flex", alignItems: "baseline", gap: T.spacing.sm, marginBottom: T.spacing.lg } });
    ce(big, "span", { text: String(issues), style: { fontSize: "2rem", fontWeight: 700, color: issues ? T.error : T.ok } });
    ce(big, "span", { text: issues ? "open issues" : "all clear", style: { fontSize: "1rem", color: T.textSecondary } });

    const list = ce(body, "div", { style: { display: "flex", flexDirection: "column", gap: T.spacing.sm } });
    for (const [, label, count] of checks) {
      const r = ce(list, "div", { style: { display: "flex", justifyContent: "space-between", alignItems: "center", padding: `${T.spacing.sm} ${T.spacing.md}`, background: T.surfaceHover, borderRadius: T.radius.md } });
      ce(r, "span", { text: label, style: { fontSize: "0.875rem", color: T.textPrimary } });
      ce(r, "span", { text: count, style: { fontSize: "0.875rem", fontWeight: 700, color: +count ? T.warn : T.ok } });
    }
    body.appendChild(list);

    const gen = txt.match(/Generated:\s*([^\n]+)/)?.[1];
    if (gen) ce(body, "div", { text: `Last audit: ${gen.trim()}`, style: { fontSize: "0.75rem", color: T.textFaint, marginTop: T.spacing.md } });
  });

  widget(6, "Skill quality", { span: 6, subtitle: "Multi-harness agent skill compliance" }, async body => {
    const sqReport = getFile("04-Archives/Audit-Reports/Skill-Quality-Report.md", "Skills-Notes/Skill-Quality-Report.md");
    if (!sqReport) { ce(body, "div", { text: "No skill quality report found — run skill_quality_checker.py to generate.", style: { color: T.textFaint, padding: T.spacing.lg } }); return; }
    const content = await vault.read(sqReport);
    const ready = (content.match(/— READY/g) || []).length;
    const rework = (content.match(/— NEEDS REWORK/g) || []).length;
    const reject = (content.match(/— REJECT/g) || []).length;
    const total = ready + rework + reject;
    const pct = total ? Math.round((ready / total) * 100) : 0;

    const big = ce(body, "div", { style: { display: "flex", alignItems: "baseline", gap: T.spacing.sm, marginBottom: T.spacing.lg } });
    ce(big, "span", { text: `${pct}%`, style: { fontSize: "2rem", fontWeight: 700, color: pct >= 80 ? T.ok : pct >= 50 ? T.warn : T.error } });
    ce(big, "span", { text: `${ready}/${total} READY`, style: { fontSize: "1rem", color: T.textSecondary } });

    const bars = ce(body, "div", { style: { display: "flex", flexDirection: "column", gap: T.spacing.sm } });
    [[ready, "READY", T.ok], [rework, "Needs rework", T.warn], [reject, "Rejected", T.error]].forEach(([n, label, color]) => {
      const barPct = total ? Math.round((n / total) * 100) : 0;
      const row = ce(bars, "div", { style: { display: "flex", flexDirection: "column", gap: T.spacing.xs } });
      const lr = ce(row, "div", { style: { display: "flex", justifyContent: "space-between", fontSize: "0.8rem" } });
      ce(lr, "span", { text: label, style: { color: T.textSecondary } });
      ce(lr, "span", { text: String(n), style: { color: T.textPrimary } });
      const track = ce(row, "div", { style: { height: "6px", background: T.border, borderRadius: T.radius.sm, overflow: "hidden" } });
      ce(track, "div", { style: { height: "100%", width: `${barPct}%`, background: color, borderRadius: T.radius.sm } });
    });
    ce(body, "div", { text: `${total - ready} skills need attention`, style: { fontSize: "0.75rem", color: T.textFaint, marginTop: T.spacing.md } });
  });
}

// Row 2: Projects · Recent activity · Broken links · System status
{
  widget(6, "Active projects", { span: 6, action: "All projects →", actionPath: "01-Projects/Projects.base", subtitle: "Project tracking" }, body => {
    const projects = arr(dv.pages('"01-Projects" or "Projects"').where(p => p.type === "project" && p.status === "active").sort(p => p.created, "desc"));
    if (!projects.length) { ce(body, "div", { text: "No active projects.", style: { color: T.textFaint, padding: T.spacing.lg, textAlign: "center" } }); return; }
    const list = ce(body, "div", { style: { display: "flex", flexDirection: "column", gap: T.spacing.sm } });
    for (const p of projects.slice(0, 5)) {
      const r = ce(list, "div", { style: { display: "flex", alignItems: "center", justifyContent: "space-between", padding: `${T.spacing.sm} ${T.spacing.md}`, background: T.surfaceHover, borderRadius: T.radius.md } });
      const info = ce(r, "div", {});
      ce(info, "a", { text: p.file.name, href: p.file.path, style: { textDecoration: "none", color: T.accent, fontSize: "0.875rem", fontWeight: 600 } });
      ce(info, "div", { text: p.file.folder || "(root)", style: { fontSize: "0.75rem", color: T.textFaint, marginTop: T.spacing.xs } });
      ce(r, "span", { text: p.status, style: { fontSize: "0.75rem", fontWeight: 600, color: T.ok, background: T.okBg, padding: "2px 8px", borderRadius: T.radius.sm } });
      r.addEventListener("click", () => open(p.file.path));
      r.style.cursor = "pointer";
    }
    body.appendChild(list);
  });

  widget(6, "Recent activity", { span: 6, subtitle: "Latest vault edits" }, body => {
    const self = dv.current()?.file?.path;
    const recent = arr(dv.pages().where(p => p.file.path !== self && !p.file.path.startsWith("04-Archives/Daily/") && !p.file.path.startsWith("Daily/")).sort(p => p.file.mtime, "desc")).slice(0, 6);
    if (!recent.length) { ce(body, "div", { text: "No recent activity.", style: { color: T.textFaint, padding: T.spacing.lg, textAlign: "center" } }); return; }
    const list = ce(body, "div", { style: { display: "flex", flexDirection: "column", gap: T.spacing.sm } });
    for (const f of recent) {
      const r = ce(list, "div", { style: { display: "flex", alignItems: "center", justifyContent: "space-between", padding: `${T.spacing.sm} ${T.spacing.md}`, background: T.surfaceHover, borderRadius: T.radius.md } });
      const info = ce(r, "div", {});
      ce(info, "a", { text: f.file.name, href: f.file.path, style: { textDecoration: "none", color: T.textPrimary, fontSize: "0.875rem", fontWeight: 500 } });
      ce(info, "div", { text: timeAgo(f.file.mtime), style: { fontSize: "0.75rem", color: T.textFaint, marginTop: T.spacing.xs } });
      ce(r, "span", { text: f.file.folder || "root", style: { fontSize: "0.75rem", color: T.textSecondary } });
      r.addEventListener("click", () => open(f.file.path));
      r.style.cursor = "pointer";
    }
    body.appendChild(list);
  });

  widget(6, "Broken links", { span: 6, subtitle: "Wikilinks pointing to missing files" }, async body => {
    const scReport = getFile("04-Archives/Audit-Reports/Self-Critique-Report.md", "Skills-Notes/Self-Critique-Report.md");
    if (!scReport) { ce(body, "div", { text: "No self-critique report found.", style: { color: T.textFaint, padding: T.spacing.lg } }); return; }
    const content = await vault.read(scReport);
    const broken = content.match(/Broken wikilink \[\[([^\]]+)\]\]/g) || [];
    const uniqueTargets = new Set();
    for (const b of broken) { const m = b.match(/\[\[([^\]]+)\]\]/); if (m) uniqueTargets.add(m[1]); }
    const count = broken.length;

    const big = ce(body, "div", { style: { display: "flex", alignItems: "baseline", gap: T.spacing.sm, marginBottom: T.spacing.lg } });
    ce(big, "span", { text: count.toLocaleString(), style: { fontSize: "2rem", fontWeight: 700, color: count ? T.error : T.ok } });
    ce(big, "span", { text: `${uniqueTargets.size} unique targets missing`, style: { fontSize: "1rem", color: T.textSecondary } });

    ce(body, "div", { text: count === 0 ? "✅ All links resolve correctly." : "Run self_critique.py for full details.", style: { fontSize: "0.875rem", color: T.textFaint } });
    ce(body, "a", { text: count === 0 ? "No action needed" : "View full report →", href: "04-Archives/Audit-Reports/Self-Critique-Report.md", style: { display: "inline-flex", alignItems: "center", gap: T.spacing.sm, marginTop: T.spacing.md, fontSize: "0.875rem", color: T.accent, textDecoration: "none" } });
  });

  widget(6, "System status", { span: 6, subtitle: "Vault & release information" }, async body => {
    const versionFile = getFile("VERSION");
    if (!versionFile) { ce(body, "div", { text: "No VERSION file found.", style: { color: T.textFaint, padding: T.spacing.lg } }); return; }
    const local = (await vault.read(versionFile)).trim().split("|").pop();

    const r1 = ce(body, "div", { style: { display: "flex", alignItems: "center", justifyContent: "space-between", padding: `${T.spacing.md} ${T.spacing.lg}`, background: T.surfaceHover, borderRadius: T.radius.md, marginBottom: T.spacing.md } });
    ce(r1, "span", { text: "Vault version", style: { fontSize: "0.875rem", color: T.textSecondary } });
    ce(r1, "span", { text: `v${local}`, style: { fontSize: "0.875rem", fontWeight: 700, color: T.textPrimary } });

    const r2 = ce(body, "div", { style: { display: "flex", alignItems: "center", justifyContent: "space-between", padding: `${T.spacing.md} ${T.spacing.lg}`, background: T.surfaceHover, borderRadius: T.radius.md } });
    ce(r2, "span", { text: "Latest release", style: { fontSize: "0.875rem", color: T.textSecondary } });
    ce(r2, "span", { text: "v1.58.0 · Latest", style: { fontSize: "0.875rem", fontWeight: 700, color: T.ok } });

    ce(body, "div", { text: "GitHub: mistrysiddh/hermes-brain-template", style: { fontSize: "0.75rem", color: T.textFaint, marginTop: T.spacing.lg } });
  });
}

// Row 3: Recent sessions (full width)
{
  widget(12, "Recent sessions", { span: 12, action: "Full timeline →", actionPath: "04-Archives/Daily/Timeline.md", subtitle: "Archived sessions" }, body => {
    if (!dailyPages.length) { ce(body, "div", { text: "No archived sessions in 04-Archives/Daily/.", style: { color: T.textFaint, padding: T.spacing.lg, textAlign: "center" } }); return; }
    const table = ce(body, "table", { cls: "hb-table",
      style: { width: "100%", borderCollapse: "collapse", fontSize: "0.875rem" } });
    const thead = ce(ce(table, "thead"), "tr");
    ["Session", "Folder", "Modified"].forEach(h => ce(thead, "th", { text: h, style: { textAlign: "left", padding: `${T.spacing.sm} ${T.spacing.md}`, fontWeight: 600, color: T.textSecondary, borderBottom: `1px solid ${T.border}` } }));
    const tbody = ce(table, "tbody");
    for (const p of dailyPages.slice(0, 8)) {
      const tr = ce(tbody, "tr", { style: { borderBottom: `1px solid ${T.border}` } });
      const td1 = ce(tr, "td", { style: { padding: `${T.spacing.sm} ${T.spacing.md}` } });
      ce(td1, "a", { text: p.file.name, href: p.file.path, style: { textDecoration: "none", color: T.accent, fontWeight: 500 } });
      ce(tr, "td", { text: p.file.folder || "", style: { padding: `${T.spacing.sm} ${T.spacing.md}`, color: T.textSecondary } });
      const td3 = ce(tr, "td", { style: { padding: `${T.spacing.sm} ${T.spacing.md}`, color: T.textFaint } });
      td3.setText(timeAgo(p.file.mtime));
      td3.setAttribute("title", p.file.mtime?.toISO?.() ?? "");
    }
    body.appendChild(table);
  });

  root.appendChild(root.lastChild); // no-op, widget already appended
}

// ============================================================
//  FOOTER
// ============================================================
{
  const foot = ce(root, "footer", {
    cls: "hb-span-12",
    style: { padding: `${T.spacing.lg} ${T.spacing.xxl}`, borderTop: `1px solid ${T.border}`, fontSize: "0.75rem", color: T.textFaint, display: "flex", justifyContent: "space-between", alignItems: "center" },
  });
  ce(foot, "div", { text: "Hermes Brain · Built with DataviewJS" });
  const links = ce(foot, "div", { style: { display: "flex", gap: T.spacing.lg } });
  [["Dashboard", "Dashboard.md"], ["Vault Audit", "04-Archives/Audit-Reports/Vault-Audit-Report.md"], ["Skill Quality", "04-Archives/Audit-Reports/Skill-Quality-Report.md"]].forEach(([label, path]) => {
    const a = ce(links, "a", { text: label, href: path, style: { color: T.accent, textDecoration: "none" } });
    a.addEventListener("click", e => { e.preventDefault(); open(path); });
  });
}

await Promise.all(jobs);
```