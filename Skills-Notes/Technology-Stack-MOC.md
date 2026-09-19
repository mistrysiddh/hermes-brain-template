---
type: moc
status: active
created: {{date}}
tags: [moc, technology, linux, docker, kubernetes, self-hosting]
---

# Technology Stack MOC

Central map of content for infrastructure, containerization, and self-hosting technologies.

## 🐧 Linux & Systems

### Core Skills
- [[virtualbox-vm-setup]] — VM provisioning with raw disk boot
- [[vmware-vm-setup]] — macOS guests on VMware Workstation

### Topics
- [[../Research/Linux-Hardening.md|Linux Hardening]] (create if needed)
- [[../Research/Systemd-Services.md|Systemd Service Management]]
- [[../Research/SSH-Hardening.md|SSH Security]]

## 🐳 Docker & Containers

### Skills Needed
- Docker Compose orchestration
- Multi-stage builds
- Container security scanning
- Volume management patterns

### Projects
- [[../Projects/Local-AI-Stack.md|Local AI Inference Stack]] (Ollama, OpenWebUI, etc.)
- [[../Projects/HermesPi-Setup.md|HermesPi Raspberry Pi Setup]]

## ☸️ Kubernetes (Learning)

### Target Skills
- kubectl workflows
- Helm charts
- Kustomize overlays
- Local clusters (k3d, kind, minikube)

### Resources
- [[../Research/K8s-Local-Development.md|Local K8s Development]]
- [[../Research/GitOps-Flux.md|GitOps with Flux]]

## 🏠 Self-Hosting

### Current Stack
- **HermesPi** (Raspberry Pi 4B+ 8GB) — Local Ollama endpoint
  - Models: phi3:mini (2.2GB), llama3.2:3b (2.0GB)
  - OpenWebUI at `http://100.93.0.4:3000`
  - Argon40 fan, temps ~55-60°C
- **Tailscale** — Secure networking (IP 100.93.0.4)
- **ntfy** — Push notifications

### Planned Services
- [[../Projects/SearXNG-Instance.md|SearXNG Search]]
- [[../Projects/Immich-Photos.md|Immich Photo Backup]]
- [[../Projects/Paperless-NGX.md|Document Archive]]

## 🔧 Automation & CI/CD

### Skills
- [[automated-information-briefings]] — Scheduled research digests
- [[ntfy-notifications]] — Cross-platform push notifications
- [[ai-ml-research-briefing]] — AI/ML paper monitoring

### Patterns
- [[../Research/Cron-vs-Systemd-Timers.md|Cron vs systemd Timers]]
- [[../Research/GitHub-Actions-Patterns.md|GitHub Actions for Self-Hosted]]

---

## Related MOCs
- [[Cybersecurity-MOC|Cybersecurity Framework]]
- [[AI-ML-MOC|AI/ML Workflows]]
- [[Agentic-Architecture-MOC|Agentic Systems]]

## Quick Links
- [[../Projects/Hermes-Agent-Vault-Setup.md|Hermes Agent Vault Setup]]
- [[../Skills-Notes/Installed-Skills-Index.md|Installed Skills]]
- [[../Scripts/skill_forecast.py|Skill Forecast (run for suggestions)]]