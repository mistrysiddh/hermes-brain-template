---
layout: default
title: Setup & Installation
nav_order: 1
has_children: false
---

# Setup & Installation

This guide covers multiple ways to get Hermes Brain running on your system.

## Prerequisites

- **Obsidian** (v1.5.0+ recommended) — [Download](https://obsidian.md/download)
- **Git** — For version control and updates
- **Python 3.10+** — For custom automation scripts
- **Node.js 18+** — Optional, for some plugins
- **Hermes Agent** (optional) — For AI integration

## Quick Install (One-Liner)

### Windows (PowerShell, Run as Administrator)
```powershell
Set-ExecutionPolicy Bypass -Scope Process -Force; `
[System.Net.ServicePointManager]::SecurityProtocol = [System.Net.ServicePointManager]::SecurityProtocol -bor 3072; `
iex ((New-Object System.Net.WebClient).DownloadString('https://raw.githubusercontent.com/mistrysiddh/hermes-brain-template/main/_System/Scripts/Installers/install.ps1'))
```

### macOS / Linux (Bash)
```bash
curl -fsSL https://raw.githubusercontent.com/mistrysiddh/hermes-brain-template/main/_System/Scripts/Installers/install.sh | bash
```

## Manual Setup

### 1. Clone the Template
```bash
git clone https://github.com/mistrysiddh/hermes-brain-template.git hermes-brain
cd hermes-brain
```

### 2. Open in Obsidian
1. Open Obsidian
2. Click "Open folder as vault"
3. Select the cloned `hermes-brain` folder
4. Trust the vault when prompted

### 3. Install Community Plugins
The template requires these community plugins (auto-installed via the installer, or manual):

| Plugin | Purpose |
|--------|---------|
| **Dataview** | Query and display data from notes |
| **Kanban** | Visual project/task boards |
| **Smart Connections** | AI-powered semantic linking |
| **Obsidian Local REST API** | Programmatic vault access |
| **Calendar** | Daily notes navigation |
| **Templater** | Advanced templating |

To install manually:
1. Settings → Community Plugins → Browse
2. Search and install each plugin
3. Enable them in the Community Plugins list

### 4. Configure Themes
The template includes **Nemoclaw** (default) and **Tokyo Night** themes:
1. Settings → Appearance → Themes
2. Select "Nemoclaw" or "Tokyo Night"
3. Enable "Dark mode" for best experience

### 5. Run Initial Sync
```bash
# Sync templates, scripts, and configs
python _System/Scripts/sync_to_hermes.py
```

## Post-Install Configuration

### AI Integration (Hermes Agent)
If you use Hermes Agent for AI features:

1. Install Hermes Agent: `pip install hermes-agent`
2. Configure your API keys in `config.yaml`
3. Enable `obsidian-local-rest-api` plugin
4. Test connection: `hermes brain status`

### Environment Variables
Create a `.env` file in the vault root (never commit this):
```bash
# API Keys (replace with your own)
OPENAI_API_KEY=your_key_here
ANTHROPIC_API_KEY=your_key_here
GEMINI_API_KEY=your_key_here

# Local AI (optional)
OLLAMA_HOST=http://localhost:11434
LOCAL_MODEL=phi3:mini
```

### Daily Notes Setup
1. Settings → Core Plugins → Daily Notes → Enable
2. Set "New file location" to `04-📦 04-Archives/Daily`
3. Set "Template file location" to `03-📚 03-Resources/Templates/Daily-Note.md`

## Troubleshooting

### Plugins Not Loading
- Restart Obsidian completely
- Check Settings → Community Plugins → "Safe mode" is OFF
- Verify plugin versions match `.obsidian/community-plugins.json`

### Dataview Queries Empty
- Run "Dataview: Rebuild Index" from Command Palette (Ctrl/Cmd+P)
- Wait for indexing to complete

### REST API Connection Failed
- Ensure `obsidian-local-rest-api` is enabled
- Check Settings → obsidian-local-rest-api → Port (default 27123)
- Verify no firewall blocking localhost

### Theme Looks Wrong
- Settings → Appearance → Base color scheme: "Dark"
- Disable any conflicting CSS snippets
- Restart Obsidian

## Updating the Template

```bash
cd hermes-brain
git pull origin main
# Re-run sync script
python _System/Scripts/sync_to_hermes.py
```

## Uninstalling

### Windows
```powershell
.\_System\Scripts\Installers\uninstall.ps1
```

### macOS / Linux
```bash
bash _System/Scripts/Installers/uninstall.sh
```

---

**Next:** [Vault Structure](structure.md) · [Scripts Reference](scripts.md)