---
layout: default
title: Hermes Brain Template
---

# Hermes Brain Template

A comprehensive knowledge vault for AI agents and self-hosted systems.

[View the template on GitHub](https://github.com/mistrysiddh/hermes-brain-template) · [Report a bug](https://github.com/mistrysiddh/hermes-brain-template/issues) · [Request a feature](https://github.com/mistrysiddh/hermes-brain-template/issues)

## What is Hermes Brain?

Hermes Brain is a self-hosted, AI-powered knowledge management system built on Obsidian. It's designed for AI builders, Linux enthusiasts, cybersecurity professionals, and automation engineers who want to:

- 🧠 **Organize knowledge** with a PARA-inspired structure (Projects, Areas, Resources, Archives)
- 🤖 **Integrate AI agents** for semantic search, automated tagging, and skill forecasting
- ⚙️ **Automate workflows** with custom scripts, Kanban boards, and cron jobs
- 🔒 **Maintain privacy** with zero-data-leak guarantees and local-first design
- 📚 **Learn and grow** with structured lesson logs, skill tracking, and project retrospectives

## 🚀 Quick Start

### Option A: One-Click Install (Recommended)
<details>
<summary>Windows PowerShell</summary>

```powershell
# Run as Administrator
Set-ExecutionPolicy Bypass -Scope Process -Force; `
[System.Net.ServicePointManager]::SecurityProtocol = [System.Net.ServicePointManager]::SecurityProtocol -bor 3072; `
iex ((New-Object System.Net.WebClient).DownloadString('https://raw.githubusercontent.com/mistrysiddh/hermes-brain-template/main/_System/Scripts/Installers/install.ps1'))
```
</details>

<details>
<summary>macOS / Linux</summary>

```bash
curl -fsSL https://raw.githubusercontent.com/mistrysiddh/hermes-brain-template/main/_System/Scripts/Installers/install.sh | bash
```
</details>

### Option B: Clone & Use (for developers/contributors)
If you want to work with the template directly or contribute:

```bash
git clone https://github.com/mistrysiddh/hermes-brain-template.git
cd hermes-brain-template
# Follow the setup instructions in SETUP.md
```

## 📖 Documentation

- [Installation Guide](SETUP.md)
- [Directory Structure](#vault-structure)
- [AI Agent Integration](https://hermes-agent.nousresearch.com/)
- [Custom Scripts Reference](_System/Scripts/)
- [Kanban Workflow](https://github.com/mistrysiddh/hermes-brain-template/projects)
- [Release Notes](https://github.com/mistrysiddh/hermes-brain-template/releases)

## 🏗️ Vault Structure

The Hermes Brain template follows a PARA-inspired organization:

```
hermes-brain/
├── 00-📥 Inbox/                 # Temporary holding for new items
├── 01-🎯 01-Areas/             # Spheres of activity with ongoing responsibilities
│   ├── User-Profile.md
│   ├── Cybersecurity.md
│   ├── AI-Development.md
│   └── ...
├── 02-🚧 02-Projects/          # Short-term efforts with clear goals and deadlines
│   ├── Active/
│   ├── On Hold/
│   └── Completed/
├── 03-📚 03-Resources/         # Reference materials that don't fit elsewhere
│   ├── MOCs/                   # Maps of Content
│   │   ├── Technology-Stack-MOC.md
│   │   ├── Cybersecurity-MOC.md
│   │   └── ...
│   ├── Templates/              # Reusable note templates
│   ├── Canvases/               # Visual planning spaces
│   └── ...
└── 04-📦 04-Archives/          # Inactive items from the above categories
    ├── Daily/
    ├── Projects/
    └── Resources/
```

## 🛠️ Built With

- [Obsidian](https://obsidian.md/) - Knowledge base foundation
- [Dataview](https://github.com/blacksmithgu/obsidian-dataview) - Data querying
- [Kanban](https://github.com/mgmeyers/obsidian-kanban) - Project visualization
- [Smart Connections](https://github.com/montrosed/smart-connections) - AI-powered linking
- [Obsidian Local REST API](https://github.com/WrathofDawn/obsidian-local-rest-api) - Programmatic access
- [Nemoclaw Theme](https://github.com/mistrysiddh/nemoclaw) - NVIDIA-inspired dark theme
- Custom Python scripts for automation and AI integration

## 🤝 Contributing

We welcome contributions! Please see our [Contributing Guide](CONTRIBUTING.md) for details.

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Submit a pull request

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🙏 Acknowledgments

- The Obsidian community for incredible plugins and themes
- Nous Research for Hermes Agent and AI research
- All contributors who have helped shape this template