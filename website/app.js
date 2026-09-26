/**
 * Hermes Brain — Showcase Website Logic & Interactive Simulator
 */

document.addEventListener("DOMContentLoaded", () => {
  initNeuralCanvas();
  initCopyButtons();
  initTerminalTabs();
  initMockupTabs();
  initPipelineSimulator();
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
   Copy to Clipboard
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
