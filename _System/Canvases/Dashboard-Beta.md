---
type: dashboard
status: beta
created: 2026-09-14
updated: 2026-11-14
tags: [dashboard, hub, beta, admin]
cssclasses: [dashboard-wide, hb-app]
---

%%
Hermes Brain — Admin Dashboard

Design system:
- Slate/gray surface, blue accent, semantic status colors (ok/warn/error/info)
- 0.25rem spacing scale, 8-12px border radius, subtle shadows
- Sidebar navigation, top header, grid content area
- Cards with hover states, accessible focus indicators, semantic badges

Requires Dataview plugin with JavaScript queries enabled.
Best viewed in Reading view.
%%

```dataviewjs
// ============================================================
//  HERMES BRAIN — ADMIN DASHBOARD (production-quality UI)
//  Design system tokens, component architecture, admin layout
// ============================================================

const vault = app.vault;
// `dv` is provided globally by DataviewJS — do not redeclare it

// ---------- design tokens ----------
const TOKENS = {
  colors: {
    surface: "var(--background-secondary)",
    surfaceHover: "var(--background-modifier-hover)",
    border: "var(--background-modifier-border)",
    textPrimary: "var(--text-normal)",
    textSecondary: "var(--text-muted)",
    textFaint: "var(--text-faint)",
    accent: "var(--interactive-accent)",
    accentHover: "color-mix(in srgb, var(--interactive-accent) 90%, transparent)",
    success: "var(--text-success)",
    successBg: "color-mix(in srgb, var(--text-success) 12%, transparent)",
    warn: "var(--text-warning)",
    warnBg: "color-mix(in srgb, var(--text-warning) 12%, transparent)",
    error: "var(--text-error)",
    errorBg: "color-mix(in srgb, var(--text-error) 12%, transparent)",
    info: "var(--text-accent)",
    infoBg: "color-mix(in srgb, var(--text-accent) 12%, transparent)",
  },
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

// ---------- component factory ----------
function el(tag, opts = {}) {
  const e = dv.el(tag, opts.text !== undefined ? { text: opts.text } : {});
  if (opts.attr) Object.entries(opts.attr).forEach(([k, v]) => e.setAttribute(k, v));
  if (opts.style) Object.assign(e.style, opts.style);
  if (opts.classes) e.addClass(opts.classes);
  if (opts.text) e.setText(opts.text);
  return e;
}

function badge(text, variant = "info") {
  const bg = {
    ok: "var(--successBg)", warn: "var(--warnBg)", error: "var(--errorBg)",
    info: "var(--infoBg)", neutral: "var(--surfaceHover)",
  };
  const fg = {
    ok: "var(--success)", warn: "var(--warn)", error: "var(--error)",
    info: "var(--info)", neutral: "var(--textSecondary)",
  };
  return el("span", {
    text,
    style: {
      display: "inline-flex",
      alignItems: "center",
      padding: "2px 8px",
      borderRadius: TOKENS.radius.sm,
      fontSize: "0.75rem",
      fontWeight: 600,
      background: bg[variant] || bg.info,
      color: fg[variant] || fg.info,
    },
  });
}

function card(title, { subtitle, action, actionPath, span = 12 } = {}) {
  const root = el("section", {
    classes: `hb-card hb-span-${span}`,
    style: {
      background: TOKENS.colors.surface,
      border: `1px solid ${TOKENS.colors.border}`,
      borderRadius: TOKENS.radius.lg,
      boxShadow: TOKENS.colors.shadow,
      display: "flex",
      flexDirection: "column",
      transition: "all 0.2s ease",
      overflow: "hidden",
    },
  });
  root.addEventListener("mouseenter", () => { root.style.borderColor = TOKENS.colors.accent; });
  root.addEventListener("mouseleave", () => { root.style.borderColor = TOKENS.colors.border; });

  if (title) {
    const head = el("div", {
      style: {
        display: "flex",
        alignItems: "center",
        justifyContent: "space-between",
        padding: `${TOKENS.spacing.lg} ${TOKENS.spacing.xl}`,
        borderBottom: `1px solid ${TOKENS.colors.border}`,
      },
    });
    const titleBox = el("div", {});
    head.appendChild(titleBox);
    titleBox.createEl("span", { text: title, style: { fontSize: "0.875rem", fontWeight: 600, color: TOKENS.colors.textPrimary, letterSpacing: "0.02em" } });
    if (subtitle) titleBox.createEl("span", { text: subtitle, style: { fontSize: "0.75rem", color: TOKENS.colors.textFaint, marginTop: TOKENS.spacing.xs, display: "block" } });
    if (action) {
      const btn = el("a", {
        text: action,
        style: {
          textDecoration: "none",
          fontSize: "0.85rem",
          color: TOKENS.colors.accent,
          padding: `${TOKENS.spacing.sm} ${TOKENS.spacing.md}`,
          borderRadius: TOKENS.radius.md,
          background: TOKENS.colors.accentHover,
          transition: "background 0.2s ease",
        },
        href: actionPath,
      });
      btn.addEventListener("click", e => { e.preventDefault(); open(actionPath); });
      head.appendChild(btn);
    }
    root.appendChild(head);
  }

  const body = el("div", {
    style: { padding: TOKENS.spacing.xl, flex: 1 },
  });
  root.appendChild(body);
  return { root, body };
}

function kpi(label, value, sub, { accent = false, trend } = {}) {
  const k = el("div", {
    style: {
      display: "flex",
      flexDirection: "column",
      gap: TOKENS.spacing.sm,
      padding: TOKENS.spacing.lg,
      background: TOKENS.colors.surface,
      border: `1px solid ${TOKENS.colors.border}`,
      borderRadius: TOKENS.radius.md,
      minWidth: 140,
    },
  });
  k.createEl("span", { text: label, style: { fontSize: "0.8rem", color: TOKENS.colors.textSecondary } });
  const valWrap = el("div", { style: { display: "flex", alignItems: "baseline", gap: TOKENS.spacing.sm } });
  valWrap.createEl("span", { text: value, style: { fontSize: "1.75rem", fontWeight: 700, color: accent ? TOKENS.colors.accent : TOKENS.colors.textPrimary } });
  if (trend) {
    valWrap.createEl("span", {
      text: trend.text,
      style: { fontSize: "0.85rem", fontWeight: 600, color: trend.ok ? TOKENS.colors.success : TOKENS.colors.error },
    });
  }
  k.appendChild(valWrap);
  if (sub) k.createEl("span", { text: sub, style: { fontSize: "0.8rem", color: TOKENS.colors.textFaint } });
  return k;
}

function sparkline(parent, vals) {
  const max = Math.max(1, ...vals);
  const w = 100, h = 24, bw = w / vals.length;
  const bars = vals.map((v, i) => {
    const bh = v ? Math.max(1.5, (v / max) * h) : 1;
    return `<rect x="${(i * bw + bw * 0.2).toFixed(2)}" y="${(h - bh).toFixed(2)}" width="${(bw * 0.6).toFixed(2)}" height="${bh.toFixed(2)}" rx="1"/>`;
  }).join("");
  // innerHTML is safe here: vals come from parsed token log (numeric only), no user input
  parent.createEl("div", { style: { width: "100%" } }).innerHTML =
    `<svg viewBox="0 0 ${w} ${h}" preserveAspectRatio="none" aria-hidden="true" style="width:100%;height:${h}px;display:block">${bars}</svg>`;
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

let health = { label: "No data", cls: "info", sub: "no archived sessions" };
if (dailyPages.length) {
  const hrs = (Date.now() - msOf(dailyPages[0].file.mtime)) / 3600000;
  const sub = `last archive ${timeAgo(dailyPages[0].file.mtime)}`;
  health = hrs < 3 ? { label: "Healthy", cls: "ok", sub }
    : hrs < 48 ? { label: "Idle", cls: "info", sub }
    : { label: "Stale", cls: "warn", sub };
}

// ============================================================
//  LAYOUT: sidebar + header + main
// ============================================================

const root = dv.el("div", "", { cls: "hb-app" });
root.style.display = "flex";
root.style.flexDirection = "column";
root.style.height = "100vh";
root.style.overflow = "hidden";

// ---------- sidebar ----------
const sidebar = el("aside", {
  style: {
    width: "260px",
    flexShrink: 0,
    background: "var(--background-modifier-border)",
    display: "flex",
    flexDirection: "column",
    borderRight: `1px solid ${TOKENS.colors.border}`,
    overflowY: "auto",
  },
});

const brand = el("div", {
  style: {
    padding: TOKENS.spacing.xxl,
    borderBottom: `1px solid ${TOKENS.colors.border}`,
    background: "rgba(0,0,0,0.03)",
  },
});
brand.createEl("div", { text: "HERMES BRAIN", style: { fontSize: "1.125rem", fontWeight: 700, letterSpacing: "-0.02em" } });
brand.createEl("div", { text: "Admin Dashboard", style: { fontSize: "0.75rem", color: TOKENS.colors.textFaint, textTransform: "uppercase", letterSpacing: "0.05em", marginTop: TOKENS.spacing.xs } });
sidebar.appendChild(brand);

const nav = el("nav", { style: { padding: TOKENS.spacing.md, flex: 1 } });
const navItems = [
  { icon: "📊", label: "Overview", active: true },
  { icon: "🧠", label: "Memory Pipeline" },
  { icon: "🛡️", label: "Vault Health" },
  { icon: "🎯", label: "Skill Quality" },
  { icon: "🚀", label: "Projects" },
  { icon: "🔗", label: "Broken Links" },
  { icon: "🤖", label: "Agent Roster" },
  { icon: "⚙️", label: "Settings" },
];
navItems.forEach(item => {
  const btn = el("button", {
    text: `${item.icon}  ${item.label}`,
    style: {
      width: "100%",
      display: "flex",
      alignItems: "center",
      gap: TOKENS.spacing.md,
      padding: `${TOKENS.spacing.sm} ${TOKENS.spacing.md}`,
      border: "none",
      background: item.active ? "rgba(0,0,0,0.05)" : "transparent",
      color: item.active ? TOKENS.colors.textPrimary : TOKENS.colors.textSecondary,
      borderRadius: TOKENS.radius.md,
      fontSize: "0.9rem",
      cursor: "pointer",
      textAlign: "left",
      transition: "all 0.2s ease",
    },
  });
  btn.addEventListener("mouseenter", () => { if (!item.active) btn.style.background = "rgba(0,0,0,0.03)"; });
  btn.addEventListener("mouseleave", () => { if (!item.active) btn.style.background = "transparent"; });
  nav.appendChild(btn);
});
sidebar.appendChild(nav);

const foot = el("div", {
  style: {
    padding: TOKENS.spacing.lg,
    borderTop: `1px solid ${TOKENS.colors.border}`,
    fontSize: "0.75rem",
    color: TOKENS.colors.textFaint,
  },
});
foot.createEl("div", { text: `v${store.get("hb-dash-version") || "1.0.0"}` });
foot.createEl("div", { text: `Updated ${new Date().toLocaleDateString()}`, style: { marginTop: TOKENS.spacing.xs } });
sidebar.appendChild(foot);

root.appendChild(sidebar);

// ---------- header ----------
const header = el("header", {
  style: {
    height: "64px",
    background: "var(--background-secondary)",
    borderBottom: `1px solid ${TOKENS.colors.border}`,
    display: "flex",
    alignItems: "center",
    justifyContent: "space-between",
    padding: `0 ${TOKENS.spacing.xl}`,
    flexShrink: 0,
  },
});

const headerLeft = el("div", { style: { display: "flex", alignItems: "center", gap: TOKENS.spacing.lg } });
const greet = el("div", {
  text: new Date().getHours() < 12 ? "Good morning, Siddh" : "Good afternoon, Siddh",
  style: { fontSize: "0.9rem", color: TOKENS.colors.textSecondary },
});
headerLeft.appendChild(greet);

const search = el("div", { style: { position: "relative", width: "280px" } });
const searchInput = el("input", {
  attr: { type: "text", placeholder: "Search vault…" },
  style: {
    width: "100%",
    padding: "8px 12px 8px 32px",
    borderRadius: TOKENS.radius.md,
    border: `1px solid ${TOKENS.colors.border}`,
    background: TOKENS.colors.surface,
    fontSize: "0.875rem",
    color: TOKENS.colors.textPrimary,
  },
});
searchInput.addEventListener("focus", () => { searchInput.style.borderColor = TOKENS.colors.accent; });
searchInput.addEventListener("blur", () => { searchInput.style.borderColor = TOKENS.colors.border; });
search.appendChild(searchInput);
const searchIcon = el("span", {
  text: "🔍",
  style: { position: "absolute", left: "10px", top: "50%", transform: "translateY(-50%)", fontSize: "0.9rem" },
});
search.appendChild(searchIcon);
headerLeft.appendChild(search);
header.appendChild(headerLeft);

const headerRight = el("div", { style: { display: "flex", alignItems: "center", gap: TOKENS.spacing.md } });
const notif = el("button", {
  text: "🔔",
  style: {
    background: "none",
    border: "none",
    cursor: "pointer",
    fontSize: "1.1rem",
    padding: TOKENS.spacing.sm,
    borderRadius: TOKENS.radius.md,
    color: TOKENS.colors.textSecondary,
  },
});
notif.addEventListener("mouseenter", () => { notif.style.background = TOKENS.colors.surfaceHover; });
notif.addEventListener("mouseleave", () => { notif.style.background = "none"; });
headerRight.appendChild(notif);

const user = el("div", {
  style: {
    display: "flex",
    alignItems: "center",
    gap: TOKENS.spacing.sm,
    padding: `${TOKENS.spacing.sm} ${TOKENS.spacing.md}`,
    background: TOKENS.colors.surfaceHover,
    borderRadius: TOKENS.radius.lg,
    border: `1px solid ${TOKENS.colors.border}`,
  },
});
user.createEl("div", { text: "S", style: { width: "28px", height: "28px", borderRadius: "50%", background: TOKENS.colors.accent, color: "white", display: "flex", alignItems: "center", justifyContent: "center", fontWeight: 700, fontSize: "0.9rem" } });
const userInfo = el("div", {});
userInfo.createEl("div", { text: "Siddh Mistry", style: { fontSize: "0.875rem", fontWeight: 600, color: TOKENS.colors.textPrimary } });
userInfo.createEl("div", { text: "Owner · Hermes Brain", style: { fontSize: "0.75rem", color: TOKENS.colors.textFaint } });
user.appendChild(userInfo);
headerRight.appendChild(user);
header.appendChild(headerRight);

root.appendChild(header);

// ---------- main content ----------
const main = el("main", {
  style: {
    flex: 1,
    overflowY: "auto",
    background: "var(--background-modifier-hover)",
    padding: TOKENS.spacing.xxl,
  },
});
root.appendChild(main);

// ============================================================
//  SECTION: KPI STRIP
// ============================================================

{
  const section = el("section", { style: { marginBottom: TOKENS.spacing.xxl } });
  section.createEl("h2", {
    text: "Overview",
    style: { fontSize: "1rem", fontWeight: 600, color: TOKENS.colors.textPrimary, marginBottom: TOKENS.spacing.lg, textTransform: "uppercase", letterSpacing: "0.05em" },
  });

  const strip = el("div", {
    style: {
      display: "grid",
      gridTemplateColumns: "repeat(auto-fit, minmax(160px, 1fr))",
      gap: TOKENS.spacing.lg,
    },
  });

  const days = Object.values(byDate);
  const totalTokens = days.reduce((s, d) => s + d.tokens, 0);
  const activeDays = days.filter(d => d.tokens > 0).length;
  const last14 = lastDays(14).map(d => d.tokens);
  const avg7 = last14.slice(7).reduce((a, b) => a + b, 0) / 7;
  const todayTokens = byDate[todayISO]?.tokens || 0;
  const weekSessions = lastDays(7).reduce((s, d) => s + d.sessions, 0);
  const sessions14 = lastDays(14).map(d => d.sessions);

  strip.appendChild(kpi("Total tokens", compact(totalTokens), "last 14 days", { accent: true, trend: { text: `+${Math.round((totalTokens / Math.max(activeDays, 1))).toLocaleString()}/day`, ok: true } }));
  strip.appendChild(kpi("Tokens today", compact(todayTokens), `7-day avg ${compact(Math.round(avg7))}`));
  strip.appendChild(kpi("Sessions · 7d", String(weekSessions), "last 14 days"));
  strip.appendChild(kpi("Active days", String(activeDays), "with token activity"));
  strip.appendChild(kpi("Open facts", String(memOpen), `${memDone} promoted`, { accent: memOpen > 0 }));
  strip.appendChild(kpi("Archiver", health.label, health.sub));

  // sparkline wrapper under first KPI
  const firstKpi = strip.children[0];
  const sparkWrap = el("div", { style: { marginTop: TOKENS.spacing.md, height: "20px" } });
  sparkline(sparkWrap, last14);
  firstKpi.appendChild(sparkWrap);

  section.appendChild(strip);
  main.appendChild(section);
}

// ============================================================
//  SECTION: GRID ROW 1 — Quick Actions · Memory · Vault Health · Skill Quality
// ============================================================

{
  const row = el("div", {
    style: {
      display: "grid",
      gridTemplateColumns: "repeat(auto-fit, minmax(280px, 1fr))",
      gap: TOKENS.spacing.lg,
      marginBottom: TOKENS.spacing.xxl,
    },
  });

  // Quick actions card
  {
    const { root: cardRoot, body } = card("Quick actions", { span: 6, subtitle: "Common vault operations" });
    const grid = el("div", {
      style: {
        display: "grid",
        gridTemplateColumns: "repeat(2, 1fr)",
        gap: TOKENS.spacing.md,
      },
    });
    const actions = [
      ["📝", "Daily Review", () => {
        const tpl = getFile("_System/Templates/Daily-Review.md", "Templates/Daily-Review.md");
        if (!tpl) { new Notice("Daily-Review template not found"); return; }
        try { app.commands.executeCommandById("templater-obsidian:create-new-note-from-template"); }
        catch { open(tpl.path); }
      }],
      ["🧠", "Memory Kanban", () => open("04-Archives/Memory-Review/Memory-Board.kanban")],
      ["⚡", "Context Preamble", () => open("04-Archives/Memory-Review/HERMES-PREAMBLE.md")],
      ["⚠️", "Log Lesson", () => open("_System/Templates/Lesson-Learned.md")],
      ["📑", "New ADR", () => open("_System/Templates/Architecture-Decision-Record.md")],
      ["🛡️", "Vault Audit", () => open("04-Archives/Audit-Reports/Vault-Audit-Report.md")],
    ];
    actions.forEach(([icon, label, fn]) => {
      const b = el("button", {
        style: {
          display: "flex",
          alignItems: "center",
          gap: TOKENS.spacing.md,
          padding: TOKENS.spacing.md,
          border: `1px solid ${TOKENS.colors.border}`,
          background: "transparent",
          borderRadius: TOKENS.radius.md,
          fontSize: "0.875rem",
          cursor: "pointer",
          transition: "all 0.15s ease",
        },
      });
      b.createEl("span", { text: icon, style: { fontSize: "1.2rem" } });
      b.createEl("span", { text: label, style: { flex: 1, color: TOKENS.colors.textPrimary } });
      b.addEventListener("mouseenter", () => { b.style.background = TOKENS.colors.surfaceHover; b.style.borderColor = TOKENS.colors.accent; });
      b.addEventListener("mouseleave", () => { b.style.background = "transparent"; b.style.borderColor = TOKENS.colors.border; });
      b.addEventListener("click", async () => { try { await fn(); } catch (e) { new Notice(`Failed: ${label}`); } });
      grid.appendChild(b);
    });
    body.appendChild(grid);
    row.appendChild(cardRoot);
  }

  // Memory pipeline card
  {
    const { root: cardRoot, body } = card("Memory pipeline", { span: 6, subtitle: "Candidate facts → durable memory" });
    const total = memTasks.length;
    const pct = total ? Math.round((memDone / total) * 100) : 100;
    const headerRow = el("div", { style: { display: "flex", justifyContent: "space-between", alignItems: "baseline", marginBottom: TOKENS.spacing.lg } });
    headerRow.createEl("span", { text: `${pct}%`, style: { fontSize: "2rem", fontWeight: 700 } });
    headerRow.createEl("span", { text: "reviewed", style: { fontSize: "0.875rem", color: TOKENS.colors.textSecondary } });
    body.appendChild(headerRow);

    const track = el("div", {
      style: {
        height: "8px",
        background: TOKENS.colors.border,
        borderRadius: TOKENS.radius.sm,
        overflow: "hidden",
        marginBottom: TOKENS.spacing.md,
      },
    });
    const fill = el("div", {
      style: {
        height: "100%",
        width: `${pct}%`,
        background: pct >= 80 ? TOKENS.colors.success : pct >= 50 ? TOKENS.colors.warn : TOKENS.colors.error,
        borderRadius: TOKENS.radius.sm,
        transition: "width 0.5s ease",
      },
    });
    track.appendChild(fill);
    body.appendChild(track);

    const stats = el("div", {
      style: {
        display: "flex",
        justifyContent: "space-between",
        fontSize: "0.875rem",
        color: TOKENS.colors.textSecondary,
      },
    });
    [[memDone, "Promoted"], [memOpen, "Pending"]].forEach(([n, label]) => {
      const s = el("div", { style: { textAlign: "center" } });
      s.createEl("div", { text: String(n), style: { fontSize: "1.125rem", fontWeight: 700, color: TOKENS.colors.textPrimary } });
      s.createEl("div", { text: label });
      stats.appendChild(s);
    });
    body.appendChild(stats);
    body.createEl("div", {
      text: "Nightly: consolidate_memory.py → sync_to_hermes.py",
      style: { fontSize: "0.75rem", color: TOKENS.colors.textFaint, marginTop: TOKENS.spacing.md },
    });
    row.appendChild(cardRoot);
  }

  // Vault health card
  {
    const { root: cardRoot, body } = card("Vault health", { span: 6, subtitle: "Issues detected by vault_audit.py" });
    const report = getFile("04-Archives/Audit-Reports/Vault-Audit-Report.md", "Skills-Notes/Vault-Audit-Report.md");
    if (!report) {
      body.createEl("div", { text: "No audit report found — run vault_audit.py to generate.", style: { color: TOKENS.colors.textFaint, padding: TOKENS.spacing.lg } });
    } else {
      const txt = await vault.read(report);
      const summary = txt.match(/## Summary\r?\n\r?\n([\s\S]*?)\r?\n---/)?.[1] || "";
      const checks = [...summary.matchAll(/-\s+\*\*([^*]+)\*\*:\s*(\d+)/g)];
      const issues = checks.reduce((s, m) => s + parseInt(m[2]), 0);

      const big = el("div", {
        style: {
          display: "flex",
          alignItems: "baseline",
          gap: TOKENS.spacing.sm,
          marginBottom: TOKENS.spacing.lg,
        },
      });
      big.createEl("span", {
        text: String(issues),
        style: { fontSize: "2rem", fontWeight: 700, color: issues ? TOKENS.colors.error : TOKENS.colors.success },
      });
      big.createEl("span", {
        text: issues ? "open issues" : "all clear",
        style: { fontSize: "1rem", color: TOKENS.colors.textSecondary },
      });
      body.appendChild(big);

      const list = el("div", { style: { display: "flex", flexDirection: "column", gap: TOKENS.spacing.sm } });
      for (const [, label, count] of checks) {
        const r = el("div", {
          style: {
            display: "flex",
            justifyContent: "space-between",
            alignItems: "center",
            padding: `${TOKENS.spacing.sm} ${TOKENS.spacing.md}`,
            background: TOKENS.colors.surfaceHover,
            borderRadius: TOKENS.radius.md,
          },
        });
        r.createEl("span", { text: label, style: { fontSize: "0.875rem", color: TOKENS.colors.textPrimary } });
        r.createEl("span", {
          text: count,
          style: {
            fontSize: "0.875rem",
            fontWeight: 700,
            color: +count ? TOKENS.colors.warn : TOKENS.colors.success,
          },
        });
        list.appendChild(r);
      }
      body.appendChild(list);

      const gen = txt.match(/Generated:\s*([^\n]+)/)?.[1];
      if (gen) body.createEl("div", {
        text: `Last audit: ${gen.trim()}`,
        style: { fontSize: "0.75rem", color: TOKENS.colors.textFaint, marginTop: TOKENS.spacing.md },
      });
    }
    row.appendChild(cardRoot);
  }

  // Skill quality card
  {
    const { root: cardRoot, body } = card("Skill quality", { span: 6, subtitle: "Multi-harness agent skill compliance" });
    const sqReport = getFile("04-Archives/Audit-Reports/Skill-Quality-Report.md", "Skills-Notes/Skill-Quality-Report.md");
    if (!sqReport) {
      body.createEl("div", { text: "No skill quality report found — run skill_quality_checker.py to generate.", style: { color: TOKENS.colors.textFaint, padding: TOKENS.spacing.lg } });
    } else {
      const content = await vault.read(sqReport);
      const ready = (content.match(/— READY/g) || []).length;
      const rework = (content.match(/— NEEDS REWORK/g) || []).length;
      const reject = (content.match(/— REJECT/g) || []).length;
      const total = ready + rework + reject;
      const pct = total ? Math.round((ready / total) * 100) : 0;

      const big = el("div", {
        style: {
          display: "flex",
          alignItems: "baseline",
          gap: TOKENS.spacing.sm,
          marginBottom: TOKENS.spacing.lg,
        },
      });
      big.createEl("span", {
        text: `${pct}%`,
        style: { fontSize: "2rem", fontWeight: 700, color: pct >= 80 ? TOKENS.colors.success : pct >= 50 ? TOKENS.colors.warn : TOKENS.colors.error },
      });
      big.createEl("span", {
        text: `${ready}/${total} READY`,
        style: { fontSize: "1rem", color: TOKENS.colors.textSecondary },
      });
      body.appendChild(big);

      const bars = el("div", { style: { display: "flex", flexDirection: "column", gap: TOKENS.spacing.sm } });
      [[ready, "READY", TOKENS.colors.success], [rework, "Needs rework", TOKENS.colors.warn], [reject, "Rejected", TOKENS.colors.error]].forEach(([n, label, color]) => {
        const barPct = total ? Math.round((n / total) * 100) : 0;
        const row = el("div", { style: { display: "flex", flexDirection: "column", gap: TOKENS.spacing.xs } });
        const labelRow = el("div", {
          style: { display: "flex", justifyContent: "space-between", fontSize: "0.8rem" },
        });
        labelRow.createEl("span", { text: label, style: { color: TOKENS.colors.textSecondary } });
        labelRow.createEl("span", { text: String(n), style: { color: TOKENS.colors.textPrimary } });
        row.appendChild(labelRow);
        const track = el("div", {
          style: { height: "6px", background: TOKENS.colors.border, borderRadius: TOKENS.radius.sm, overflow: "hidden" },
        });
        const fill = el("div", {
          style: { height: "100%", width: `${barPct}%`, background: color, borderRadius: TOKENS.radius.sm },
        });
        track.appendChild(fill);
        row.appendChild(track);
        bars.appendChild(row);
      });
      body.appendChild(bars);

      body.createEl("div", {
        text: `${total - ready} skills need attention`,
        style: { fontSize: "0.75rem", color: TOKENS.colors.textFaint, marginTop: TOKENS.spacing.md },
      });
    }
    row.appendChild(cardRoot);
  }

  main.appendChild(row);
}

// ============================================================
//  SECTION: GRID ROW 2 — Projects · Recent Activity · Broken Links · System Status
// ============================================================

{
  const row = el("div", {
    style: {
      display: "grid",
      gridTemplateColumns: "repeat(auto-fit, minmax(280px, 1fr))",
      gap: TOKENS.spacing.lg,
      marginBottom: TOKENS.spacing.xxl,
    },
  });

  // Active projects
  {
    const { root: cardRoot, body } = card("Active projects", { span: 6, action: "All projects →", actionPath: "01-Projects/Projects.base", subtitle: "Project tracking" });
    const projects = arr(dv.pages('"01-Projects" or "Projects"').where(p => p.type === "project" && p.status === "active").sort(p => p.created, "desc"));
    if (!projects.length) {
      body.createEl("div", { text: "No active projects.", style: { color: TOKENS.colors.textFaint, padding: TOKENS.spacing.lg, textAlign: "center" } });
    } else {
      const list = el("div", { style: { display: "flex", flexDirection: "column", gap: TOKENS.spacing.sm } });
      projects.slice(0, 5).forEach(p => {
        const r = el("div", {
          style: {
            display: "flex",
            alignItems: "center",
            justifyContent: "space-between",
            padding: `${TOKENS.spacing.sm} ${TOKENS.spacing.md}`,
            background: TOKENS.colors.surfaceHover,
            borderRadius: TOKENS.radius.md,
          },
        });
        const info = el("div", {});
        info.createEl("a", {
          text: p.file.name,
          href: p.file.path,
          style: { textDecoration: "none", color: TOKENS.colors.accent, fontSize: "0.875rem", fontWeight: 600 },
        });
        info.createEl("div", { text: p.file.folder || "(root)", style: { fontSize: "0.75rem", color: TOKENS.colors.textFaint, marginTop: TOKENS.spacing.xs } });
        r.appendChild(info);
        r.createEl("span", {
          text: p.status,
          style: { fontSize: "0.75rem", fontWeight: 600, color: "var(--text-success)", background: TOKENS.colors.successBg, padding: "2px 8px", borderRadius: TOKENS.radius.sm },
        });
        r.addEventListener("click", () => open(p.file.path));
        r.style.cursor = "pointer";
        list.appendChild(r);
      });
      body.appendChild(list);
    }
    row.appendChild(cardRoot);
  }

  // Recent activity
  {
    const { root: cardRoot, body } = card("Recent activity", { span: 6, subtitle: "Latest vault edits" });
    const self = dv.current()?.file?.path;
    const recent = arr(dv.pages()
      .where(p => p.file.path !== self && !p.file.path.startsWith("04-Archives/Daily/") && !p.file.path.startsWith("Daily/"))
      .sort(p => p.file.mtime, "desc")).slice(0, 6);
    if (!recent.length) {
      body.createEl("div", { text: "No recent activity.", style: { color: TOKENS.colors.textFaint, padding: TOKENS.spacing.lg, textAlign: "center" } });
    } else {
      const list = el("div", { style: { display: "flex", flexDirection: "column", gap: TOKENS.spacing.sm } });
      recent.forEach(f => {
        const r = el("div", {
          style: {
            display: "flex",
            alignItems: "center",
            justifyContent: "space-between",
            padding: `${TOKENS.spacing.sm} ${TOKENS.spacing.md}`,
            background: TOKENS.colors.surfaceHover,
            borderRadius: TOKENS.radius.md,
          },
        });
        const info = el("div", {});
        info.createEl("a", {
          text: f.file.name,
          href: f.file.path,
          style: { textDecoration: "none", color: TOKENS.colors.textPrimary, fontSize: "0.875rem", fontWeight: 500 },
        });
        info.createEl("div", { text: timeAgo(f.file.mtime), style: { fontSize: "0.75rem", color: TOKENS.colors.textFaint, marginTop: TOKENS.spacing.xs } });
        r.appendChild(info);
        r.createEl("span", { text: f.file.folder || "root", style: { fontSize: "0.75rem", color: TOKENS.colors.textSecondary } });
        r.addEventListener("click", () => open(f.file.path));
        r.style.cursor = "pointer";
        list.appendChild(r);
      });
      body.appendChild(list);
    }
    row.appendChild(cardRoot);
  }

  // Broken links
  {
    const { root: cardRoot, body } = card("Broken links", { span: 6, subtitle: "Wikilinks pointing to missing files" });
    const scReport = getFile("04-Archives/Audit-Reports/Self-Critique-Report.md", "Skills-Notes/Self-Critique-Report.md");
    if (!scReport) {
      body.createEl("div", { text: "No self-critique report found.", style: { color: TOKENS.colors.textFaint, padding: TOKENS.spacing.lg } });
    } else {
      const content = await vault.read(scReport);
      const broken = content.match(/Broken wikilink \[\[([^\]]+)\]\]/g) || [];
      const uniqueTargets = new Set();
      for (const b of broken) {
        const m = b.match(/\[\[([^\]]+)\]\]/);
        if (m) uniqueTargets.add(m[1]);
      }
      const count = broken.length;

      const big = el("div", {
        style: {
          display: "flex",
          alignItems: "baseline",
          gap: TOKENS.spacing.sm,
          marginBottom: TOKENS.spacing.lg,
        },
      });
      big.createEl("span", {
        text: count.toLocaleString(),
        style: { fontSize: "2rem", fontWeight: 700, color: count ? TOKENS.colors.error : TOKENS.colors.success },
      });
      big.createEl("span", {
        text: `${uniqueTargets.size} unique targets missing`,
        style: { fontSize: "1rem", color: TOKENS.colors.textSecondary },
      });
      body.appendChild(big);

      body.createEl("div", {
        text: count === 0 ? "✅ All links resolve correctly." : "Run self_critique.py for full details.",
        style: { fontSize: "0.875rem", color: TOKENS.colors.textFaint },
      });
      body.createEl("a", {
        text: count === 0 ? "No action needed" : "View full report →",
        href: "04-Archives/Audit-Reports/Self-Critique-Report.md",
        style: {
          display: "inline-flex",
          alignItems: "center",
          gap: TOKENS.spacing.sm,
          marginTop: TOKENS.spacing.md,
          fontSize: "0.875rem",
          color: TOKENS.colors.accent,
          textDecoration: "none",
        },
      });
    }
    row.appendChild(cardRoot);
  }

  // System status
  {
    const { root: cardRoot, body } = card("System status", { span: 6, subtitle: "Vault & release information" });
    const versionFile = getFile("VERSION");
    if (!versionFile) {
      body.createEl("div", { text: "No VERSION file found.", style: { color: TOKENS.colors.textFaint, padding: TOKENS.spacing.lg } });
    } else {
      const local = (await vault.read(versionFile)).trim().split("|").pop();
      const statusRow = el("div", {
        style: {
          display: "flex",
          alignItems: "center",
          justifyContent: "space-between",
          padding: `${TOKENS.spacing.md} ${TOKENS.spacing.lg}`,
          background: TOKENS.colors.surfaceHover,
          borderRadius: TOKENS.radius.md,
          marginBottom: TOKENS.spacing.md,
        },
      });
      statusRow.createEl("span", { text: "Vault version", style: { fontSize: "0.875rem", color: TOKENS.colors.textSecondary } });
      statusRow.createEl("span", {
        text: `v${local}`,
        style: { fontSize: "0.875rem", fontWeight: 700, color: TOKENS.colors.textPrimary },
      });
      body.appendChild(statusRow);

      const latestRow = el("div", {
        style: {
          display: "flex",
          alignItems: "center",
          justifyContent: "space-between",
          padding: `${TOKENS.spacing.md} ${TOKENS.spacing.lg}`,
          background: TOKENS.colors.surfaceHover,
          borderRadius: TOKENS.radius.md,
        },
      });
      latestRow.createEl("span", { text: "Latest release", style: { fontSize: "0.875rem", color: TOKENS.colors.textSecondary } });
      latestRow.createEl("span", {
        text: "v1.57.0 · Latest",
        style: { fontSize: "0.875rem", fontWeight: 700, color: TOKENS.colors.success },
      });
      body.appendChild(latestRow);

      body.createEl("div", {
        text: "GitHub: mistrysiddh/hermes-brain-template",
        style: { fontSize: "0.75rem", color: TOKENS.colors.textFaint, marginTop: TOKENS.spacing.lg },
      });
    }
    row.appendChild(cardRoot);
  }

  main.appendChild(row);
}

// ============================================================
//  FOOTER
// ============================================================

{
  const foot = el("footer", {
    style: {
      padding: `${TOKENS.spacing.lg} ${TOKENS.spacing.xxl}`,
      borderTop: `1px solid ${TOKENS.colors.border}`,
      fontSize: "0.75rem",
      color: TOKENS.colors.textFaint,
      display: "flex",
      justifyContent: "space-between",
      alignItems: "center",
    },
  });
  foot.createEl("div", { text: "Hermes Brain · Built with DataviewJS" });
  const links = el("div", { style: { display: "flex", gap: TOKENS.spacing.lg } });
  [["Dashboard", "Dashboard.md"], ["Vault Audit", "04-Archives/Audit-Reports/Vault-Audit-Report.md"], ["Skill Quality", "04-Archives/Audit-Reports/Skill-Quality-Report.md"]].forEach(([label, path]) => {
    const a = el("a", { text: label, href: path, style: { color: TOKENS.colors.accent, textDecoration: "none" } });
    a.addEventListener("click", e => { e.preventDefault(); open(path); });
    links.appendChild(a);
  });
  foot.appendChild(links);
  main.appendChild(foot);
}

await Promise.all([]);
```