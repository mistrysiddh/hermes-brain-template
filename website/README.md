# Hermes Brain — Official Website & Interactive Showcase

This directory contains the official showcase website and interactive documentation for **Hermes Brain** (the Obsidian Vault Template for Hermes Agent and OpenClaw).

## 🚀 Instant Local Preview

The website is built with vanilla modern HTML5, CSS3, and ES6 JavaScript. It has **zero dependencies** and requires **no build step**.

You can run it in two ways:

### Option 1: Direct File Open
Double click `index.html` in your file explorer, or open it directly in your browser.

### Option 2: Local HTTP Server (Python)
From this `website/` directory:
```bash
python -m http.server 8000
```
Then visit: `http://localhost:8000`

---

## 🌟 Interactive Features Included

- **Neural Synapse Particle Background**: Lightweight HTML5 canvas rendering glowing cognitive connections that react to viewport changes.
- **Interactive 4-Stage Memory Pipeline Simulator**: Step through the real-world flow of session logs:
  1. *Hourly Archival & Secret Scrubbing*
  2. *Candidate Extraction & 4-Criteria Validation*
  3. *Human-in-the-Loop Kanban Board Review*
  4. *Permanent MEMORY.md Injection & Dream Cycle Consolidation*
- **PARA Method Vault Explorer**: Interactive file tree allowing users to inspect `01-Projects`, `02-Areas`, `03-Resources`, `04-Archives`, and `_System`.
- **Model Context Protocol (MCP) Simulator**: Test stdio JSON-RPC tool calls (`vault_search`, `read_note`, `get_user_profile`, `stage_memory_candidate`, `vault_stats`) with realistic live responses.
- **Multi-Platform Install Wizard**: Tabbed instructions for Windows PowerShell (`irm`), Linux/macOS (`curl`), Hermes 1-Paste Chat Prompt, GitHub Template Clone, Scratch Trial, and GitHub Codespaces.
- **1-Click Copy with Animated Toast Feedback**: Copy any command or prompt with immediate visual feedback.
- **Aesthetic**: Custom Tokyo Night & Nemoclaw dark glassmorphism theme with glowing neon accents.

---

## 🌐 Deploying to GitHub Pages

To host this website on GitHub Pages:
1. Go to your repository on GitHub.
2. Navigate to **Settings** → **Pages**.
3. Under **Build and deployment**:
   - **Source**: Deploy from a branch
   - **Branch**: `main` (or default branch), folder: `/ (root)` or use a GitHub Actions workflow.
4. If serving from root, the included root `index.html` forwards directly to `website/index.html`.
