/**
 * Hermes Brain — Showcase Website Logic & Interactive Simulator Suite
 * Features: Tokyo Night/Nemoclaw theme, Command Palette (Ctrl+K), Multi-Agent ADR simulator,
 * Personality matrix, Template gallery, Token calculator, Neural canvas, MCP tester.
 */

document.addEventListener("DOMContentLoaded", () => {
  initThemeSwitcher();
  initMobileMenu();
  initCommandPalette();
  initNeuralCanvas();
  initCopyButtons();
  initTerminalTabs();
  initMockupTabs();
  initPipelineSimulator();
  initAdrSimulator();
  initPersonalityMatrix();
  initTemplateGallery();
  initTokenCalculator();
  initParaExplorer();
  initMcpSimulator();
  initInstallWizard();
  initFaqAccordion();
});

/* ==========================================================================
   Toast Notifications
   ========================================================================== */
function showToast(message = "Copied to clipboard!") {
  let toast = document.querySelector(".toast-notice");
  if (!toast) {
    toast = document.createElement("div");
    toast.className = "toast-notice";
    document.body.appendChild(toast);
  }
  toast.innerHTML = `
    <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="#10b981" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
      <polyline points="20 6 9 17 4 12"></polyline>
    </svg>
    <span>${message}</span>
  `;
  toast.classList.add("visible");
  setTimeout(() => {
    toast.classList.remove("visible");
  }, 2400);
}

/* ==========================================================================
   Theme Switcher (Tokyo Night ↔ Nemoclaw)
   ========================================================================== */
function initThemeSwitcher() {
  const toggleBtn = document.getElementById("theme-toggle-btn");
  const currentTheme = localStorage.getItem("hermes_theme") || "tokyo";

  if (currentTheme === "nemoclaw") {
    document.body.classList.add("theme-nemoclaw");
    updateThemeBtn(true);
  }

  if (toggleBtn) {
    toggleBtn.addEventListener("click", () => {
      const isNemoclaw = document.body.classList.toggle("theme-nemoclaw");
      localStorage.setItem("hermes_theme", isNemoclaw ? "nemoclaw" : "tokyo");
      updateThemeBtn(isNemoclaw);
      showToast(isNemoclaw ? "Switched to Nemoclaw Theme (Amber)" : "Switched to Tokyo Night Theme (Violet)");
    });
  }

  function updateThemeBtn(isNemoclaw) {
    if (!toggleBtn) return;
    const label = toggleBtn.querySelector(".theme-label");
    const icon = toggleBtn.querySelector(".theme-icon");
    if (label) label.innerText = isNemoclaw ? "Nemoclaw" : "Tokyo Night";
    if (icon) icon.innerText = isNemoclaw ? "🔥" : "🌙";
    toggleBtn.title = isNemoclaw ? "Switch to Tokyo Night Theme (Violet)" : "Switch to Nemoclaw Theme (Amber)";
  }
}

/* ==========================================================================
   Mobile Navigation Drawer Toggle
   ========================================================================== */
function initMobileMenu() {
  const toggleBtn = document.getElementById("mobile-menu-toggle");
  const drawer = document.getElementById("mobile-nav-drawer");
  if (!toggleBtn || !drawer) return;

  toggleBtn.addEventListener("click", (e) => {
    e.stopPropagation();
    drawer.classList.toggle("open");
  });

  drawer.querySelectorAll(".drawer-link, .btn-primary").forEach((link) => {
    link.addEventListener("click", () => {
      drawer.classList.remove("open");
    });
  });

  document.addEventListener("click", (e) => {
    if (!toggleBtn.contains(e.target) && !drawer.contains(e.target)) {
      drawer.classList.remove("open");
    }
  });
}

/* ==========================================================================
   Global Command Palette (Ctrl+K / Cmd+K / Slash)
   ========================================================================== */
const COMMAND_INDEX = [
  { title: "Memory Pipeline Simulator", subtitle: "4-stage session-to-durable memory pipeline", url: "#pipeline", type: "Section" },
  { title: "Multi-Agent ADR Simulator", subtitle: "Argus, Codex, Ledger & Vox architecture review", url: "#adr-sim", type: "Interactive" },
  { title: "11-Dimension Personality Matrix", subtitle: "Interactive slider generator for User-Profile.md", url: "#personality", type: "Interactive" },
  { title: "Obsidian Template Gallery", subtitle: "Raw Markdown sources for ADR, Charter, Lessons", url: "#templates", type: "Templates" },
  { title: "Token Economy Calculator", subtitle: "Calculate monthly token & API cost reduction", url: "#calculator", type: "Tool" },
  { title: "Interactive Knowledge Graph", subtitle: "Live zoomable 2D/3D Vis-network vault graph", url: "#graph-view", type: "Graph" },
  { title: "PARA Method Vault Hierarchy", subtitle: "01-Projects, 02-Areas, 03-Resources, 04-Archives", url: "#para", type: "Architecture" },
  { title: "Built-In MCP Server", subtitle: "JSON-RPC tools for Claude Desktop & Cursor", url: "#mcp", type: "MCP" },
  { title: "One-Line Terminal Install", subtitle: "Windows PowerShell & Linux Bash curl commands", url: "#install", type: "Install" },
  { title: "Hermes 1-Paste Chat Prompt", subtitle: "Automated install prompt for Hermes/OpenClaw", url: "#install", type: "Install" },
  { title: "Frequently Asked Questions", subtitle: "Privacy, local LLM requirements, update scripts", url: "#faq", type: "Docs" }
];

function initCommandPalette() {
  const backdrop = document.getElementById("cmd-backdrop");
  const input = document.getElementById("cmd-input");
  const list = document.getElementById("cmd-results");
  const triggerBtn = document.getElementById("cmd-trigger-btn");
  let selectedIndex = 0;

  function openPalette() {
    if (!backdrop) return;
    backdrop.classList.add("open");
    if (input) {
      input.value = "";
      input.focus();
    }
    renderResults(COMMAND_INDEX);
  }

  function closePalette() {
    if (!backdrop) return;
    backdrop.classList.remove("open");
  }

  function renderResults(items) {
    if (!list) return;
    selectedIndex = 0;
    if (items.length === 0) {
      list.innerHTML = `<li style="padding: 18px; text-align: center; color: var(--text-dim);">No matching sections found.</li>`;
      return;
    }

    list.innerHTML = items
      .map((item, idx) => `
        <li class="cmd-item ${idx === 0 ? "selected" : ""}" data-url="${item.url}" data-idx="${idx}">
          <div class="cmd-item-left">
            <span class="cmd-item-type">${item.type}</span>
            <div>
              <div style="font-weight: 600; color: #fff;">${item.title}</div>
              <div style="font-size: 0.78rem; color: var(--text-dim);">${item.subtitle}</div>
            </div>
          </div>
          <span style="font-size: 0.75rem; color: var(--text-dim);">↵ Jump</span>
        </li>
      `)
      .join("");

    list.querySelectorAll(".cmd-item").forEach((el) => {
      el.addEventListener("click", () => {
        const url = el.getAttribute("data-url");
        if (url) {
          window.location.hash = url;
          closePalette();
        }
      });
    });
  }

  // Keyboard shortcut listener
  window.addEventListener("keydown", (e) => {
    if ((e.ctrlKey || e.metaKey) && e.key.toLowerCase() === "k") {
      e.preventDefault();
      if (backdrop && backdrop.classList.contains("open")) closePalette();
      else openPalette();
    } else if (e.key === "Escape") {
      closePalette();
    } else if (e.key === "/" && !["INPUT", "TEXTAREA"].includes(document.activeElement.tagName)) {
      e.preventDefault();
      openPalette();
    } else if (backdrop && backdrop.classList.contains("open")) {
      const items = list.querySelectorAll(".cmd-item");
      if (e.key === "ArrowDown") {
        e.preventDefault();
        selectedIndex = (selectedIndex + 1) % items.length;
        updateSelected(items);
      } else if (e.key === "ArrowUp") {
        e.preventDefault();
        selectedIndex = (selectedIndex - 1 + items.length) % items.length;
        updateSelected(items);
      } else if (e.key === "Enter" && items[selectedIndex]) {
        e.preventDefault();
        items[selectedIndex].click();
      }
    }
  });

  function updateSelected(items) {
    items.forEach((it, idx) => it.classList.toggle("selected", idx === selectedIndex));
    if (items[selectedIndex]) items[selectedIndex].scrollIntoView({ block: "nearest" });
  }

  if (input) {
    input.addEventListener("input", () => {
      const q = input.value.toLowerCase().trim();
      const filtered = COMMAND_INDEX.filter(
        (it) => it.title.toLowerCase().includes(q) || it.subtitle.toLowerCase().includes(q) || it.type.toLowerCase().includes(q)
      );
      renderResults(filtered);
    });
  }

  if (triggerBtn) triggerBtn.addEventListener("click", openPalette);
  if (backdrop) {
    backdrop.addEventListener("click", (e) => {
      if (e.target === backdrop) closePalette();
    });
  }
}

/* ==========================================================================
   Multi-Agent ADR Simulator (Argus, Codex, Ledger, Vox)
   ========================================================================== */
const ADR_PRESETS = [
  {
    title: "Public GitHub Commits",
    proposal: "Auto-commit and push daily session markdown archives directly to a public GitHub repository.",
    argus: { verdict: "BLOCK", text: "Critical hazard. Even with regex redaction, zero-day token leakage to public GitHub commits is an irreversible security boundary breach. Prohibited under User-Profile rules." },
    codex: { verdict: "PASS", text: "Technically straightforward git push operation via cron, but lacks atomic rollback mechanisms if an upstream push fails mid-write." },
    ledger: { verdict: "PASS", text: "Minimal token consumption. Plain git command execution adds negligible overhead to context window." },
    vox: { verdict: "BLOCK", text: "Direct violation of Siddh's User-Profile boundary: 'Never make commits/pushes to git from cron jobs (local file edits only)'." },
    consensus: { status: "REJECTED (3-1)", note: "Proposal rejected due to explicit operator boundary violations and credential exposure risk. Local archiving only." }
  },
  {
    title: "SQLite to Redis",
    proposal: "Switch local agent session indexing from SQLite to a local Redis cache instance running on HermesPi.",
    argus: { verdict: "PASS", text: "Approved with condition: must bind strictly to 127.0.0.1 or wireguard subnet with 'protected-mode yes' enabled and strong auth token." },
    codex: { verdict: "PASS", text: "Excellent upgrade for high-frequency chat sync hooks. Key-value TTLs align cleanly with session life cycles." },
    ledger: { verdict: "PASS", text: "Fast in-memory reads reduce prompt indexing latency from 180ms to 4ms. Zero token penalty." },
    vox: { verdict: "PASS", text: "Aligns with Siddh's technical stack preferences (Linux/HermesPi/Docker self-hosted services)." },
    consensus: { status: "APPROVED (UNANIMOUS)", note: "Architectural decision accepted. Proceed with ADR-005: Redis Session Cache with protected-mode yes." }
  },
  {
    title: "Unrestricted Shell Exec",
    proposal: "Grant the agent unrestricted root shell execution privileges with auto-approval for all bash commands.",
    argus: { verdict: "BLOCK", text: "Extreme danger. Unconstrained shell access circumvents safety boundaries and could accidentally corrupt host filesystem or expose secrets." },
    codex: { verdict: "WARN", text: "Requires explicit sandboxing (Docker isolated container) and dry-run confirmation before applying state changes." },
    ledger: { verdict: "PASS", text: "Command output truncation is required; unbounded stdout risks overflowing context window limit." },
    vox: { verdict: "BLOCK", text: "Contradicts operator requirement: destructive actions require explicit approval before execution." },
    consensus: { status: "REJECTED", note: "Auto-execution rejected. Commands must require operator interactive confirmation." }
  }
];

function initAdrSimulator() {
  const proposalInput = document.getElementById("adr-proposal-input");
  const evalBtn = document.getElementById("adr-eval-btn");
  const presetsContainer = document.getElementById("adr-presets");
  const argusSpeech = document.getElementById("adr-argus-speech");
  const argusBadge = document.getElementById("adr-argus-badge");
  const codexSpeech = document.getElementById("adr-codex-speech");
  const codexBadge = document.getElementById("adr-codex-badge");
  const ledgerSpeech = document.getElementById("adr-ledger-speech");
  const ledgerBadge = document.getElementById("adr-ledger-badge");
  const voxSpeech = document.getElementById("adr-vox-speech");
  const voxBadge = document.getElementById("adr-vox-badge");
  const consensusBox = document.getElementById("adr-consensus-box");

  if (!evalBtn || !proposalInput) return;

  // Render Preset buttons
  if (presetsContainer) {
    presetsContainer.innerHTML = ADR_PRESETS.map(
      (p, i) => `<button class="adr-preset-btn" data-preset="${i}">💡 ${p.title}</button>`
    ).join("");

    presetsContainer.querySelectorAll(".adr-preset-btn").forEach((btn) => {
      btn.addEventListener("click", () => {
        const idx = parseInt(btn.getAttribute("data-preset"));
        const data = ADR_PRESETS[idx];
        proposalInput.value = data.proposal;
        applyAdrEvaluation(data);
      });
    });
  }

  evalBtn.addEventListener("click", () => {
    const text = proposalInput.value.trim();
    if (!text) {
      showToast("Please enter an architecture proposal first!");
      return;
    }
    // Check if matches preset, else generate synthetic
    const match = ADR_PRESETS.find((p) => text.toLowerCase().includes(p.title.toLowerCase()) || p.proposal.toLowerCase().includes(text.toLowerCase()));
    if (match) {
      applyAdrEvaluation(match);
    } else {
      generateDynamicAdrEvaluation(text);
    }
  });

  function applyAdrEvaluation(data) {
    setAgentCard(argusBadge, argusSpeech, data.argus.verdict, data.argus.text);
    setAgentCard(codexBadge, codexSpeech, data.codex.verdict, data.codex.text);
    setAgentCard(ledgerBadge, ledgerSpeech, data.ledger.verdict, data.ledger.text);
    setAgentCard(voxBadge, voxSpeech, data.vox.verdict, data.vox.text);

    if (consensusBox) {
      const isApproved = data.consensus.status.includes("APPROVED");
      consensusBox.innerHTML = `
        <div>
          <span style="font-size: 0.75rem; text-transform: uppercase; letter-spacing: 0.05em; color: var(--text-dim);">Consensus Decision</span>
          <div style="font-size: 1.25rem; font-weight: 700; color: ${isApproved ? "var(--accent-emerald)" : "var(--accent-rose)"}; margin-top: 2px;">
            ${data.consensus.status}
          </div>
          <p style="font-size: 0.88rem; color: var(--text-muted); margin-top: 4px;">${data.consensus.note}</p>
        </div>
        <button class="copy-btn" onclick="navigator.clipboard.writeText('${escapeHtml(data.consensus.note)}'); showToast('ADR verdict copied!');">
          <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><rect x="9" y="9" width="13" height="13" rx="2" ry="2"></rect><path d="M5 15H4a2 2 0 0 1-2-2V4a2 2 0 0 1 2-2h9a2 2 0 0 1 2 2v1"></path></svg>
          <span>Copy Record</span>
        </button>
      `;
    }
  }

  function setAgentCard(badge, speech, verdict, text) {
    if (badge) {
      badge.innerText = verdict;
      badge.className = `agent-verdict-badge ${verdict === "PASS" ? "badge-pass" : verdict === "WARN" ? "badge-warn" : "badge-block"}`;
    }
    if (speech) speech.innerText = text;
  }

  function generateDynamicAdrEvaluation(proposal) {
    const isSecuritySensitive = /secret|token|password|auth|root|key|credential|public/i.test(proposal);
    const isPerformance = /cache|index|token|speed|fast|sqlite|db/i.test(proposal);

    const argus = isSecuritySensitive
      ? { verdict: "BLOCK", text: "Security flags detected. Proposal touches authentication, credential storage, or public boundary." }
      : { verdict: "PASS", text: "No sensitive credential leakage or unmitigated network surface expansion detected." };

    const codex = { verdict: "PASS", text: `Verified implementation feasibility for: '${proposal.slice(0, 35)}...'. Clean fit within PARA structure.` };
    const ledger = isPerformance
      ? { verdict: "PASS", text: "Optimizes agent cycle throughput. Low impact on overall token budget." }
      : { verdict: "WARN", text: "Verify context size when notes generated by this change are injected at runtime." };
    const vox = isSecuritySensitive
      ? { verdict: "BLOCK", text: "Safety boundaries require explicit human confirmation before committing." }
      : { verdict: "PASS", text: "Matches operator tone and operational autonomy preferences." };

    const isBlocked = argus.verdict === "BLOCK" || vox.verdict === "BLOCK";
    const consensus = {
      status: isBlocked ? "REJECTED (REQUIRES REVISION)" : "APPROVED WITH SAFEGUARDS",
      note: isBlocked
        ? "Proposal contains potential boundary or credential exposure hazards. Revise with explicit security guards."
        : "Architectural consensus reached. Complies with PARA standards and operator boundaries."
    };

    applyAdrEvaluation({ argus, codex, ledger, vox, consensus });
  }

  // Load default preset on init
  applyAdrEvaluation(ADR_PRESETS[0]);
}

/* ==========================================================================
   11-Dimension Personality Framework Matrix
   ========================================================================== */
function initPersonalityMatrix() {
  const sliders = {
    autonomy: document.getElementById("slider-autonomy"),
    verbosity: document.getElementById("slider-verbosity"),
    skepticism: document.getElementById("slider-skepticism"),
    formality: document.getElementById("slider-formality"),
    tools: document.getElementById("slider-tools")
  };

  const previewEl = document.getElementById("personality-profile-preview");
  const copyBtn = document.getElementById("copy-personality-btn");

  function updateProfile() {
    const autoVal = sliders.autonomy ? parseInt(sliders.autonomy.value) : 6;
    const verbVal = sliders.verbosity ? parseInt(sliders.verbosity.value) : 2;
    const skepVal = sliders.skepticism ? parseInt(sliders.skepticism.value) : 8;
    const formVal = sliders.formality ? parseInt(sliders.formality.value) : 4;
    const toolVal = sliders.tools ? parseInt(sliders.tools.value) : 7;

    // Update tags
    document.getElementById("tag-autonomy").innerText = `${autoVal}/10`;
    document.getElementById("tag-verbosity").innerText = `${verbVal}/10`;
    document.getElementById("tag-skepticism").innerText = `${skepVal}/10`;
    document.getElementById("tag-formality").innerText = `${formVal}/10`;
    document.getElementById("tag-tools").innerText = `${toolVal}/10`;

    const profileMarkdown = `---
type: alignment_profile
framework_version: 11-dimension-v2
updated: ${new Date().toISOString().split("T")[0]}
---

## 🗣️ Communication & Alignment Directives

- **Autonomy Level [${autoVal}/10]:** ${autoVal > 6 ? "Execute safe self-contained commands automatically; ask confirmation only for breaking operations." : "Ask explicit confirmation before modifying production configs or running filesystem writes."}
- **Verbosity & Preamble [${verbVal}/10]:** ${verbVal < 4 ? "Strictly concise. Commands first, diffs second, zero conversational fluff or repeating the prompt." : "Provide structured explanations with trade-off analysis alongside code changes."}
- **Fact Skepticism [${skepVal}/10]:** ${skepVal > 6 ? "Strict verification. Challenge unverified assertions; stage candidate facts only after multiple empirical observations." : "Accept user assumptions directly without requiring citations."}
- **Interpersonal Tone [${formVal}/10]:** ${formVal > 5 ? "Warm, approachable, with playful developer banter and zero emotional dependency." : "Crisp, technical, and strictly utilitarian."}
- **Tool Proactivity [${toolVal}/10]:** ${toolVal > 5 ? "Autonomously leverage vault search and MCP read tools to resolve context before asking the user." : "Wait for explicit user instructions before invoking external tools."}`;

    if (previewEl) previewEl.innerText = profileMarkdown;
  }

  Object.values(sliders).forEach((s) => {
    if (s) s.addEventListener("input", updateProfile);
  });

  if (copyBtn) {
    copyBtn.addEventListener("click", () => {
      if (previewEl) {
        navigator.clipboard.writeText(previewEl.innerText).then(() => {
          showToast("Profile snippet copied for User-Profile.md!");
        });
      }
    });
  }

  updateProfile();
}

/* ==========================================================================
   Live Template Gallery
   ========================================================================== */
const TEMPLATE_SOURCES = {
  adr: {
    title: "Architecture Decision Record (ADR)",
    target: "01-Projects/ADR/ADR-<Number>-<Title>.md",
    badge: "📑 Architecture ADR",
    code: `---
type: adr
status: proposed
date: {{date}}
deciders: [User, Codex, Argus, Ledger, Vox]
tags: [adr, architecture]
---

# ADR-XXX: Title

## Context & Problem Statement
What technical dilemma or infrastructure requirement prompted this decision?

## Decision Drivers
- Security boundary preservation (Argus)
- Maintainability and code simplicity (Codex)
- Token economy and context limits (Ledger)
- Human alignment (Vox)

## Considered Options
1. Option A:
2. Option B:

## Multi-Agent Review Matrix
| Persona | Verdict | Reasoning |
|---------|---------|-----------|
| **Argus** (Security) | Pass/Block | Vulnerability & boundary check |
| **Codex** (Code) | Pass/Block | Architecture & implementation review |
| **Ledger** (Tokens) | Pass/Block | Context token budget impact |
| **Vox** (Alignment) | Pass/Block | Operator preference compliance |

## Decision Outcome
Chosen option:
- Direct Consequences:
- Follow-up Actions:`
  },
  project: {
    title: "Project Charter & Dashboard",
    target: "01-Projects/<Project-Name>.md",
    badge: "🟢 Active Project",
    code: `---
type: project
status: active
priority: high
created: {{date}}
deadline: 
tags: [project, para/projects]
---

# Project: Title

> **Executive Objective:** One clear sentence describing the definition of done.

## 🎯 Key Milestones & Deliverables
- [ ] Milestone 1: Core engine & schemas
- [ ] Milestone 2: Automated tests passing
- [ ] Milestone 3: Obsidian vault documentation update

## 🛠️ Multi-Agent Squad Roles
- **Codex**: Implementation & refactoring
- **Argus**: Security boundaries & audit checks
- **Ledger**: Token efficiency & prompt caching

## 📋 Active Tasks (Dataview)
\`\`\`dataview
TASK FROM "01-Projects"
WHERE !completed AND file.name = this.file.name
\`\`\``
  },
  lesson: {
    title: "Lesson Learned (Post-Mortem)",
    target: "02-Areas/Skills/Lessons-Learned/<Topic>.md",
    badge: "⚠️ Operational Post-Mortem",
    code: `---
type: lesson_learned
severity: medium
date: {{date}}
trigger: agent_correction
tags: [lesson, self-correction]
---

# Lesson Learned: Title

## 💥 The Incident / Mistake
What action did the agent take that required operator correction?

## 🔍 Root Cause Analysis
Why did this occur? (e.g. Over-aggressive tool execution, missing file check, outdated context).

## 🛡️ Preventative Rule
Standing directive to be injected into \`User-Profile.md\` or relevant Skill:
- **Rule:** Never execute X without first checking Y.
- **Verification:** Run automated test before declaring task done.`
  },
  daily: {
    title: "Daily Review & Chat Audit",
    target: "04-Archives/Daily/YYYY/MM/YYYY-MM-DD-Review.md",
    badge: "📅 Evening Reflection",
    code: `---
type: daily_review
date: {{date}}
tags: [review, daily, audit]
---

# Daily Review: {{date}}

## 💬 Today's Archived Chat Sessions
\`\`\`dataview
TABLE length(file.tasks) AS "Tasks", tokens.total AS "Tokens"
FROM "04-Archives/Daily"
WHERE file.cday = this.file.cday
\`\`\`

## 🧠 Memory Candidates Staged
- [ ] Review pending cards in [[Memory-Board.kanban]]

## 📝 Key Insights & Observations
- Insight 1:
- Insight 2:`
  }
};

function initTemplateGallery() {
  const tabs = document.querySelectorAll(".template-tab-btn");
  const titleEl = document.getElementById("template-title");
  const targetEl = document.getElementById("template-target");
  const badgeEl = document.getElementById("template-badge");
  const codeEl = document.getElementById("template-raw-code");
  const copyBtn = document.getElementById("copy-template-btn");

  let currentKey = "adr";

  function renderTemplate(key) {
    currentKey = key;
    const tpl = TEMPLATE_SOURCES[key];
    if (!tpl) return;

    tabs.forEach((t) => t.classList.toggle("active", t.getAttribute("data-tpl") === key));

    if (titleEl) titleEl.innerText = tpl.title;
    if (targetEl) targetEl.innerText = tpl.target;
    if (badgeEl) badgeEl.innerText = tpl.badge;
    if (codeEl) codeEl.innerText = tpl.code;
  }

  tabs.forEach((tab) => {
    tab.addEventListener("click", () => {
      const key = tab.getAttribute("data-tpl");
      renderTemplate(key);
    });
  });

  if (copyBtn) {
    copyBtn.addEventListener("click", () => {
      const tpl = TEMPLATE_SOURCES[currentKey];
      if (tpl) {
        navigator.clipboard.writeText(tpl.code).then(() => {
          showToast(`Copied ${tpl.title} template to clipboard!`);
        });
      }
    });
  }

  renderTemplate("adr");
}

/* ==========================================================================
   Token Economy & Context Budget Calculator
   ========================================================================== */
function initTokenCalculator() {
  const sliderSessions = document.getElementById("calc-sessions");
  const sliderLength = document.getElementById("calc-length");
  const valSessions = document.getElementById("calc-val-sessions");
  const valLength = document.getElementById("calc-val-length");

  const kpiMonthlyRaw = document.getElementById("kpi-monthly-raw");
  const kpiMonthlyVault = document.getElementById("kpi-monthly-vault");
  const kpiSavedTokens = document.getElementById("kpi-saved-tokens");
  const kpiCostSaved = document.getElementById("kpi-cost-saved");

  function calculate() {
    const sessionsPerDay = sliderSessions ? parseInt(sliderSessions.value) : 10;
    const tokensPerSession = sliderLength ? parseInt(sliderLength.value) : 4000;

    if (valSessions) valSessions.innerText = `${sessionsPerDay} chats/day`;
    if (valLength) valLength.innerText = `${tokensPerSession.toLocaleString()} tokens`;

    // Calculation:
    // Naive raw log injection: Every turn carries historical uncompressed sessions (accumulates exponentially ~ 30 days * sessions)
    const monthlyRaw = sessionsPerDay * 30 * tokensPerSession;
    // Hermes Brain staging: Extracts only ~3% of durable facts, keeping active prompt context lean (~180 tokens/candidate)
    const monthlyVault = Math.round(monthlyRaw * 0.08);
    const tokensSaved = monthlyRaw - monthlyVault;
    // Estimated LLM API pricing ($3.00 per 1M context tokens avg across Claude 3.5 Sonnet / GPT-4o)
    const dollarsSaved = ((tokensSaved / 1000000) * 3.0).toFixed(2);

    if (kpiMonthlyRaw) kpiMonthlyRaw.innerText = formatNumber(monthlyRaw);
    if (kpiMonthlyVault) kpiMonthlyVault.innerText = formatNumber(monthlyVault);
    if (kpiSavedTokens) kpiSavedTokens.innerText = `${formatNumber(tokensSaved)} (92%)`;
    if (kpiCostSaved) kpiCostSaved.innerText = `$${dollarsSaved} / mo`;
  }

  function formatNumber(num) {
    if (num >= 1000000) return (num / 1000000).toFixed(1) + "M";
    if (num >= 1000) return (num / 1000).toFixed(0) + "k";
    return num.toString();
  }

  if (sliderSessions) sliderSessions.addEventListener("input", calculate);
  if (sliderLength) sliderLength.addEventListener("input", calculate);

  calculate();
}

/* ==========================================================================
   Copy to Clipboard (Global)
   ========================================================================== */
function initCopyButtons() {
  document.querySelectorAll(".copy-btn").forEach((btn) => {
    btn.addEventListener("click", () => {
      let textToCopy = "";
      const targetId = btn.getAttribute("data-target");
      if (targetId) {
        const el = document.getElementById(targetId);
        if (el) textToCopy = el.innerText.trim();
      } else {
        const pre = btn.closest(".wizard-code-block, .terminal-body")?.querySelector("pre, .terminal-cmd");
        if (pre) textToCopy = pre.innerText.replace(/^\$\s*/, "").trim();
      }

      if (textToCopy) {
        navigator.clipboard.writeText(textToCopy).then(() => {
          btn.classList.add("copied");
          const originalHtml = btn.innerHTML;
          btn.innerHTML = `
            <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
              <polyline points="20 6 9 17 4 12"></polyline>
            </svg> Copied
          `;
          showToast();
          setTimeout(() => {
            btn.classList.remove("copied");
            btn.innerHTML = originalHtml;
          }, 2000);
        });
      }
    });
  });
}

/* ==========================================================================
   Terminal Header Tab Switcher (Hero)
   ========================================================================== */
const TERMINAL_COMMANDS = {
  powershell: `irm https://raw.githubusercontent.com/mistrysiddh/hermes-brain-template/main/_System/Scripts/Installers/install.ps1 | iex`,
  bash: `curl -fsSL https://raw.githubusercontent.com/mistrysiddh/hermes-brain-template/main/_System/Scripts/Installers/install.sh | bash`,
  hermes: `Clone https://github.com/mistrysiddh/hermes-brain-template into my Hermes Brain vault and wire up hourly archiving.`
};

function initTerminalTabs() {
  const tabs = document.querySelectorAll(".terminal-tabs .tab-btn");
  const cmdEl = document.getElementById("hero-terminal-cmd");
  const promptEl = document.getElementById("hero-terminal-prompt");

  tabs.forEach((tab) => {
    tab.addEventListener("click", () => {
      tabs.forEach((t) => t.classList.remove("active"));
      tab.classList.add("active");
      const type = tab.getAttribute("data-term");
      if (cmdEl && TERMINAL_COMMANDS[type]) {
        cmdEl.innerText = TERMINAL_COMMANDS[type];
        if (promptEl) {
          promptEl.innerText = type === "powershell" ? "PS >" : type === "bash" ? "$ " : "🤖 >";
        }
      }
    });
  });
}

/* ==========================================================================
   Mockup Switcher (Hero Graphic)
   ========================================================================== */
function initMockupTabs() {
  const tabs = document.querySelectorAll(".mockup-tab");
  const imgEl = document.getElementById("mockup-display-img");
  const livePreviewEl = document.getElementById("mockup-live-preview");

  tabs.forEach((tab) => {
    tab.addEventListener("click", () => {
      tabs.forEach((t) => t.classList.remove("active"));
      tab.classList.add("active");
      const view = tab.getAttribute("data-view");

      if (view === "graph") {
        if (imgEl) {
          imgEl.src = "./assets/graph-view-screenshot.png";
          imgEl.style.display = "block";
        }
        if (livePreviewEl) livePreviewEl.style.display = "none";
      } else if (view === "terminal") {
        if (imgEl) {
          imgEl.src = "./assets/install-demo.png";
          imgEl.style.display = "block";
        }
        if (livePreviewEl) livePreviewEl.style.display = "none";
      } else if (view === "dashboard") {
        if (imgEl) imgEl.style.display = "none";
        if (livePreviewEl) livePreviewEl.style.display = "block";
      }
    });
  });
}

/* ==========================================================================
   Memory Pipeline Simulator (4-Stage Visualizer)
   ========================================================================== */
const PIPELINE_DATA = [
  {
    step: 1,
    title: "1. Hourly / Instant Session Archiving",
    leftBadge: "RAW AGENT SESSION",
    leftBadgeClass: "badge-raw",
    rightBadge: "AUTO-SCRUBBED ARCHIVE (.md)",
    rightBadgeClass: "badge-clean",
    leftContent: `[00:14:02] USER: Configure my Redis cache on prod-01 with password: SecretAuthPass9823!
[00:14:08] HERMES: Connected to 10.0.4.12 using key ~/.ssh/prod_rsa.
Configuring Redis with protected-mode yes.
Cache TTL set to 3600s. All tests passing!
[00:14:20] Token telemetry: prompt_tokens: 1420, completion_tokens: 382.`,
    rightContent: `---
session_id: 20260927-hermes-01
created: 2026-09-27T00:14:02Z
tokens: { prompt: 1420, completion: 382, total: 1802 }
tags: [session, cache, infrastructure]
---
# Chat Session: Redis Infrastructure Config

- **User**: Configure my Redis cache on prod-01 with password: <span class="highlight-redacted">[REDACTED]</span>
- **Hermes**: Connected to 10.0.4.12 using key <span class="highlight-redacted">[REDACTED_SSH_KEY]</span>.
  Configuring Redis with protected-mode yes.
  Cache TTL set to 3600s. All tests passing!`
  },
  {
    step: 2,
    title: "2. Memory Candidate Extraction",
    leftBadge: "UNCHECKED FACT",
    leftBadgeClass: "badge-raw",
    rightBadge: "4-CRITERIA VALIDATION",
    rightBadgeClass: "badge-clean",
    leftContent: `Extracted Candidate Fact:
"User prefers Redis session caches configured with protected-mode enabled and standard 3600s TTL across all environments."

Attribute: Argus (Security Specialist)
Observed in: session-20260927-hermes-01`,
    rightContent: `## Memory Review Criteria Check:
- [x] Durable (matters in 6+ months)? -> YES (System standard)
- [x] Non-sensitive (no passwords/PII)? -> YES (Scrubbed)
- [x] Verified (observed in prod setup)? -> YES (Verified config)
- [x] Actionable (guides future agent turns)? -> YES

Staged to: 04-Archives/Memory-Review/Candidate-20260927-Redis-Standard.md`
  },
  {
    step: 3,
    title: "3. Human-in-the-Loop Triage (Kanban)",
    leftBadge: "STAGED KANBAN CARDS",
    leftBadgeClass: "badge-kanban",
    rightBadge: "HUMAN VERDICT",
    rightBadgeClass: "badge-promoted",
    leftContent: `[Obsidian Kanban Board: Memory-Board.kanban]

├── 📋 PENDING REVIEW (3)
│   ├── [ ] Redis protected-mode standard (infrastructure)
│   ├── [ ] Preferred terminal: Windows Terminal + pwsh 7
│   └── [ ] Temporary test token for Ollama (reject)
├── ⏳ IN EVALUATION (1)
│   └── [ ] Rust compilation flags for HermesPi
└── ✅ APPROVED & PROMOTED (142)`,
    rightContent: `Human Review Action:
[v] Promote to Durable Memory (MEMORY.md)
[v] Promote to User Operating Profile (02-Areas/User-Profile.md)
[ ] Reject & Purge

Verdict: APPROVED by Siddh Mistry.
Reason: Established core infrastructure policy.`
  },
  {
    step: 4,
    title: "4. Permanent Injection & Nocturnal Dream Cycle",
    leftBadge: "DURABLE INJECTION",
    leftBadgeClass: "badge-promoted",
    rightBadge: "DREAM CYCLE SYNTHESIS",
    rightBadgeClass: "badge-clean",
    leftContent: `// Added to 02-Areas/User-Profile.md & MEMORY.md:

<span class="highlight-promoted">### Infrastructure Defaults
- Always enforce \`protected-mode yes\` on Redis instances.
- Default cache TTL: 3600s unless explicit override requested.
- Primary environment: HermesPi (RPi 4B+) & Local Linux nodes.</span>

*Now injected into every future Hermes/OpenClaw conversation turn.*`,
    rightContent: `[dream_cycle.py / consolidate_memory.py execution]
- Analyzed 48 recent sessions in 04-Archives/Daily/
- Detected cross-session affinity: Redis, Docker, Self-Hosting
- Updated: 03-Resources/MOCs/Technology-Stack-MOC.md
- Updated: 02-Areas/Skills/Personality-Judgment-Framework.md
- Total token economy: 18,400 tokens preserved.`
  }
];

function initPipelineSimulator() {
  const stepButtons = document.querySelectorAll(".step-btn");
  const stepTitle = document.getElementById("pipeline-step-title");
  const leftBadge = document.getElementById("pipeline-left-badge");
  const rightBadge = document.getElementById("pipeline-right-badge");
  const leftCode = document.getElementById("pipeline-left-code");
  const rightCode = document.getElementById("pipeline-right-code");
  const nextBtn = document.getElementById("pipeline-next-btn");
  const prevBtn = document.getElementById("pipeline-prev-btn");

  let currentStep = 0;

  function renderStep(index) {
    currentStep = index;
    const data = PIPELINE_DATA[index];

    stepButtons.forEach((btn, i) => {
      btn.classList.toggle("active", i === index);
    });

    if (stepTitle) stepTitle.innerText = data.title;
    if (leftBadge) {
      leftBadge.innerText = data.leftBadge;
      leftBadge.className = `pane-badge ${data.leftBadgeClass}`;
    }
    if (rightBadge) {
      rightBadge.innerText = data.rightBadge;
      rightBadge.className = `pane-badge ${data.rightBadgeClass}`;
    }
    if (leftCode) leftCode.innerHTML = data.leftContent;
    if (rightCode) rightCode.innerHTML = data.rightContent;

    if (prevBtn) prevBtn.disabled = index === 0;
    if (nextBtn) {
      nextBtn.innerText = index === PIPELINE_DATA.length - 1 ? "Restart Cycle ↺" : "Next Stage →";
    }
  }

  stepButtons.forEach((btn, index) => {
    btn.addEventListener("click", () => renderStep(index));
  });

  if (nextBtn) {
    nextBtn.addEventListener("click", () => {
      const nextIndex = (currentStep + 1) % PIPELINE_DATA.length;
      renderStep(nextIndex);
    });
  }

  if (prevBtn) {
    prevBtn.addEventListener("click", () => {
      if (currentStep > 0) renderStep(currentStep - 1);
    });
  }

  renderStep(0);
}

/* ==========================================================================
   Vault PARA Structure Explorer
   ========================================================================== */
const PARA_DETAILS = {
  "01-Projects": {
    title: "01-Projects — Active Charters & ADRs",
    path: "01-Projects/",
    desc: "Contains active initiatives with concrete deadlines and deliverables. Includes Architectural Decision Records (ADR) with 4-agent peer review personas (Argus for security, Codex for code, Ledger for token efficiency, Vox for human alignment).",
    files: [
      { name: "Hermes-Agent-Vault-Setup.md", desc: "Master hub note and deployment charter" },
      { name: "ADR/ADR-001-Memory-Pipeline.md", desc: "Architectural record of staging protocol" },
      { name: "Projects.base", desc: "Obsidian Dataview live database of active projects" }
    ]
  },
  "02-Areas": {
    title: "02-Areas — Long-Term Standards & Alignment",
    path: "02-Areas/",
    desc: "Long-term standards and alignment boundaries that don't have an expiration date. Houses your core human alignment profile, 11-dimension Personality Judgment Framework, and the installed skills roster.",
    files: [
      { name: "User-Profile.md", desc: "Explicit operating boundaries, secrets redaction, tone preferences" },
      { name: "Skills/Personality-Judgment-Framework.md", desc: "11-dimension cognitive & behavioral evaluation schema" },
      { name: "Skills/Installed-Skills-Index.md", desc: "Master catalog of agent tools, skills, and hooks" },
      { name: "Team-Profiles-Index.md", desc: "Persona specifications for multi-agent squads" }
    ]
  },
  "03-Resources": {
    title: "03-Resources — Knowledge Hubs & MOCs",
    path: "03-Resources/",
    desc: "Domain knowledge libraries, technical reference guides, and curated Maps of Content (MOCs) covering Tech Stack, Cybersecurity, AI/ML Workflows, and Agentic Multi-Agent Architecture.",
    files: [
      { name: "MOCs/Technology-Stack-MOC.md", desc: "Linux, Docker, Kubernetes, self-hosting, automation" },
      { name: "MOCs/Cybersecurity-MOC.md", desc: "Hardening, threat modeling, privacy tooling" },
      { name: "MOCs/AI-ML-MOC.md", desc: "Local LLM inference, Ollama, MLOps patterns" },
      { name: "MOCs/Agentic-Architecture-MOC.md", desc: "Multi-agent coordination, delegation, verification" }
    ]
  },
  "04-Archives": {
    title: "04-Archives — Chronological Sessions & Staging",
    path: "04-Archives/",
    desc: "Completed initiatives, historical logs, and the 3-stage memory triage pipeline. Includes chronological Daily timeline, chat correlation logs, and the visual Memory Review Kanban board.",
    files: [
      { name: "Daily/YYYY/MM/DD/*.md", desc: "Redacted raw chat session exports" },
      { name: "Daily/Timeline.md", desc: "Dataview chronological session browser" },
      { name: "Memory-Review/Memory-Board.kanban", desc: "Interactive 3-stage visual promotion Kanban board" },
      { name: "Audit-Reports/Token-Usage.log", desc: "Live prompt and completion token accounting" }
    ]
  },
  "_System": {
    title: "_System — Automation Engine & Core",
    path: "_System/",
    desc: "The operational heart of Hermes Brain. Reusable note templates, cross-platform Python and Shell automation scripts, MCP server, and Obsidian visual canvases.",
    files: [
      { name: "Scripts/hermes_brain_mcp.py", desc: "Model Context Protocol (MCP) server for Claude & Cursor" },
      { name: "Scripts/hourly_archive.py", desc: "Automated session harvester with secret scrubbing" },
      { name: "Scripts/dream_cycle.py", desc: "Nocturnal memory consolidation and distillation engine" },
      { name: "Canvases/Memory-Pipeline.canvas", desc: "Visual interactive Obsidian canvas" }
    ]
  }
};

function initParaExplorer() {
  const items = document.querySelectorAll(".tree-item");
  const titleEl = document.getElementById("para-detail-title");
  const pathEl = document.getElementById("para-detail-path");
  const descEl = document.getElementById("para-detail-desc");
  const filesContainer = document.getElementById("para-detail-files");

  items.forEach((item) => {
    item.addEventListener("click", () => {
      items.forEach((i) => i.classList.remove("active"));
      item.classList.add("active");
      const key = item.getAttribute("data-para");
      const info = PARA_DETAILS[key];

      if (info) {
        if (titleEl) titleEl.innerText = info.title;
        if (pathEl) pathEl.innerText = info.path;
        if (descEl) descEl.innerText = info.desc;
        if (filesContainer) {
          filesContainer.innerHTML = info.files
            .map(
              (f) => `
            <div class="file-pill">
              <span class="file-pill-name">📄 ${f.name}</span>
              <span class="file-pill-desc">${f.desc}</span>
            </div>
          `
            )
            .join("");
        }
      }
    });
  });
}

/* ==========================================================================
   Interactive MCP Simulator
   ========================================================================== */
const MCP_SIMULATIONS = {
  vault_search: {
    command: `tools/call: vault_search(query="redis protected-mode")`,
    response: `{
  "status": "success",
  "matches": [
    {
      "path": "02-Areas/User-Profile.md",
      "line": 42,
      "snippet": "Always enforce 'protected-mode yes' on Redis instances across all environments."
    },
    {
      "path": "01-Projects/ADR/ADR-004-Caching.md",
      "line": 15,
      "snippet": "Decision: Adopt Redis with authentication and isolated networking."
    }
  ],
  "total_hits": 2
}`
  },
  read_note: {
    command: `tools/call: read_note(path="02-Areas/User-Profile.md")`,
    response: `{
  "path": "02-Areas/User-Profile.md",
  "frontmatter": {
    "type": "profile",
    "status": "active",
    "updated": "2026-09-27"
  },
  "content": "# User Profile & Alignment Boundaries\\n\\n- Operator: Siddh Mistry (@mistrysiddh)\\n- Communication: Commands first, explain only if asked\\n- Security Rule: Never leak API keys or credentials; replace with [REDACTED]\\n- Infrastructure: HermesPi (RPi 4B+ 8GB), Linux, Docker"
}`
  },
  get_user_profile: {
    command: `tools/call: get_user_profile()`,
    response: `{
  "operator": "Siddh Mistry",
  "preferred_tone": "Concise and practical, with occasional warmth and playful banter",
  "do_not_do": [
    "Never commit API keys, secrets, or passwords",
    "Never push git commits directly from background cron jobs",
    "No marketing fluff or preamble"
  ],
  "target_environments": ["HermesPi", "Local Linux Docker", "ThinkPad"]
}`
  },
  stage_memory_candidate: {
    command: `tools/call: stage_memory_candidate(fact="User prefers uv over pip for Python package management", category="preferences")`,
    response: `{
  "status": "staged",
  "file_created": "04-Archives/Memory-Review/Candidate-20260927-uv-preference.md",
  "kanban_updated": true,
  "requires_human_approval": true,
  "verdict_pending": "Promote to MEMORY.md upon user sign-off"
}`
  },
  vault_stats: {
    command: `tools/call: vault_stats()`,
    response: `{
  "vault_version": "1.22.20",
  "total_sessions_archived": 248,
  "pending_memory_candidates": 3,
  "active_projects": 4,
  "installed_skills": 18,
  "token_telemetry": {
    "total_prompt_tokens": 1420950,
    "total_completion_tokens": 312400,
    "last_archived_hours_ago": 0.4
  }
}`
  }
};

function initMcpSimulator() {
  const toolItems = document.querySelectorAll(".mcp-tool-item");
  const outputEl = document.getElementById("mcp-term-output");
  const runBtn = document.getElementById("mcp-run-btn");

  let activeTool = "vault_search";

  function runSimulation(toolKey) {
    activeTool = toolKey;
    const sim = MCP_SIMULATIONS[toolKey];
    if (!sim || !outputEl) return;

    outputEl.innerHTML = `
      <span style="color: var(--accent-purple-light);">$ hermes_brain_mcp.py --stdio</span>
      <br><span style="color: var(--accent-cyan);">> Requesting ${sim.command}</span>
      <br><br><span style="color: #94a3b8;">// Awaiting JSON-RPC response...</span>
    `;

    setTimeout(() => {
      outputEl.innerHTML = `
        <span style="color: var(--accent-purple-light);">$ hermes_brain_mcp.py --stdio</span>
        <br><span style="color: var(--accent-cyan);">> ${sim.command}</span>
        <br><br><span style="color: var(--accent-emerald);">// Response received [200 OK]:</span>
        <pre style="margin-top: 8px; color: #e2e8f0;">${escapeHtml(sim.response)}</pre>
      `;
    }, 280);
  }

  toolItems.forEach((item) => {
    item.addEventListener("click", () => {
      toolItems.forEach((i) => i.classList.remove("active"));
      item.classList.add("active");
      const key = item.getAttribute("data-tool");
      runSimulation(key);
    });
  });

  if (runBtn) {
    runBtn.addEventListener("click", () => runSimulation(activeTool));
  }

  runSimulation("vault_search");
}

function escapeHtml(str) {
  return str.replace(/&/g, "&amp;").replace(/</g, "&lt;").replace(/>/g, "&gt;");
}

/* ==========================================================================
   Install Wizard Tabs
   ========================================================================== */
function initInstallWizard() {
  const tabs = document.querySelectorAll(".wizard-tab");
  const panes = document.querySelectorAll(".wizard-pane");

  tabs.forEach((tab) => {
    tab.addEventListener("click", () => {
      tabs.forEach((t) => t.classList.remove("active"));
      panes.forEach((p) => p.classList.remove("active"));

      tab.classList.add("active");
      const targetId = tab.getAttribute("data-wizard");
      const targetPane = document.getElementById(targetId);
      if (targetPane) targetPane.classList.add("active");
    });
  });
}

/* ==========================================================================
   FAQ Accordion
   ========================================================================== */
function initFaqAccordion() {
  const items = document.querySelectorAll(".faq-item");
  items.forEach((item) => {
    const trigger = item.querySelector(".faq-trigger");
    if (trigger) {
      trigger.addEventListener("click", () => {
        const isOpen = item.classList.contains("open");
        items.forEach((i) => i.classList.remove("open"));
        if (!isOpen) {
          item.classList.add("open");
        }
      });
    }
  });
}

/* ==========================================================================
   Neural Canvas Particle Effect
   ========================================================================== */
function initNeuralCanvas() {
  const canvas = document.getElementById("neural-canvas");
  if (!canvas) return;
  const ctx = canvas.getContext("2d");

  let width = (canvas.width = window.innerWidth);
  let height = (canvas.height = window.innerHeight);

  window.addEventListener("resize", () => {
    width = canvas.width = window.innerWidth;
    height = canvas.height = window.innerHeight;
  });

  const nodeCount = Math.floor((width * height) / 22000);
  const nodes = [];

  for (let i = 0; i < nodeCount; i++) {
    nodes.push({
      x: Math.random() * width,
      y: Math.random() * height,
      vx: (Math.random() - 0.5) * 0.45,
      vy: (Math.random() - 0.5) * 0.45,
      radius: Math.random() * 1.8 + 1,
      color: Math.random() > 0.5 ? "rgba(124, 58, 237, " : "rgba(56, 189, 248, "
    });
  }

  function draw() {
    ctx.clearRect(0, 0, width, height);

    for (let i = 0; i < nodes.length; i++) {
      const n = nodes[i];
      n.x += n.vx;
      n.y += n.vy;

      if (n.x < 0 || n.x > width) n.vx *= -1;
      if (n.y < 0 || n.y > height) n.vy *= -1;

      ctx.beginPath();
      ctx.arc(n.x, n.y, n.radius, 0, Math.PI * 2);
      ctx.fillStyle = n.color + "0.65)";
      ctx.fill();

      // Connect neighboring nodes
      for (let j = i + 1; j < nodes.length; j++) {
        const n2 = nodes[j];
        const dx = n.x - n2.x;
        const dy = n.y - n2.y;
        const dist = Math.sqrt(dx * dx + dy * dy);

        if (dist < 110) {
          ctx.beginPath();
          ctx.moveTo(n.x, n.y);
          ctx.lineTo(n2.x, n2.y);
          ctx.strokeStyle = `rgba(148, 163, 184, ${0.15 * (1 - dist / 110)})`;
          ctx.lineWidth = 0.6;
          ctx.stroke();
        }
      }
    }

    requestAnimationFrame(draw);
  }

  draw();
}
