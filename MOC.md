---
type: moc
status: active
tags: [moc, hub]
---

# MOC — Hermes Brain Vault

Map of Content: a hand-curated index for finding things by topic, organized across the **PARA structure** (`01-Projects/`, `02-Areas/`, `03-Resources/`, `04-Archives/`, and `_System/`).

## 🧭 Dashboards & Primary Orientation
- [[Welcome]] — orientation & system overview
- [[Dashboard]] — live linear view: active projects, open memory candidates, recent sessions, installed skills
- [[_System/Canvases/Dashboard-Beta|Dashboard-Beta]] — responsive widescreen card layout (KPI strip, activity heatmap, session calendar, weather, quick actions)
- [[01-Projects/Hermes-Agent-Vault-Setup|Hermes-Agent-Vault-Setup]] — master hub note: vault architecture, memory pipeline, and status
- [[01-Projects/README|01-Projects Index]] — active goals, deliverables, and ADRs

## 🌐 Specialized MOCs (Knowledge Domain Hubs)
- [[03-Resources/MOCs/Technology-Stack-MOC|Technology Stack MOC]] — Linux, Docker, Kubernetes, self-hosting, automation
- [[03-Resources/MOCs/Cybersecurity-MOC|Cybersecurity Framework MOC]] — Hardening, threat modeling, privacy tooling, monitoring
- [[03-Resources/MOCs/AI-ML-MOC|AI/ML Workflows MOC]] — LLM integration, agentic patterns, MLOps, research automation
- [[03-Resources/MOCs/Agentic-Architecture-MOC|Agentic Architecture MOC]] — Multi-agent orchestration, delegation, verification

## 🧠 Memory Pipeline & Archival
- [[_System/Canvases/Memory-Pipeline.canvas|Memory-Pipeline Canvas]] — visual pipeline: Daily → Memory-Review → Durable Facts
- [[04-Archives/Daily/README|Daily Archive Index]] — raw chat archive conventions & session logs
- [[04-Archives/Daily/Timeline|Daily Timeline]] — live chronological session browse (Dataview)
- [[04-Archives/Daily/Chat-Correlation|Chat Correlation]] — live pattern/agent profile breakdown (Dataview)
- [[04-Archives/Memory-Review/TEMPLATE|Memory Review Criteria]] — durable / non-sensitive / verified / actionable standards
- [[04-Archives/Memory-Review/Memory-Board.kanban|Memory Review Board]] — 3-stage visual promotion Kanban board
- [[03-Resources/Guides/Dataview-Query-Library|Dataview Query Library]] — copy-paste Dataview queries for this vault
- [[03-Resources/Guides/Kanban-Usage|Kanban Usage Guide]] — board workflow, card/project note links

## 👥 Areas of Responsibility, Team & Skills
- [[02-Areas/README|02-Areas Index]] — long-term responsibilities, standards, and skill profiles
- [[02-Areas/User-Profile|User Profile & Boundaries]] — human alignment parameters, preferences, and operating rules
- [[02-Areas/Skills/Installed-Skills-Index|Installed Skills Index]] — catalog of agent skills available in the environment
- [[02-Areas/Skills/Team-Profiles-Index|Team Profiles Index]] — specialized agent team profiles & persona definitions

## 🎭 Analysis Frameworks
- [[02-Areas/Skills/Personality-Judgment-Framework|Personality Judgment Framework]] — 11-dimension framework for communication patterns & behavioral analysis
- [[_System/Templates/Personality-Judgment-Analysis|Personality Judgment Analysis Template]] — standard template for analyses
- [[_System/Templates/Personality-Judgment-Dashboard|Personality Judgment Dashboard]] — Dataview dashboard tracking analyses & anomalies
- [[_System/Canvases/Personality-Judgment-Canvas.canvas|Personality Judgment Canvas]] — interactive canvas of the 11-dimension framework

## 🔬 Research & Inquiries
- [[03-Resources/Research/README|Research Inquiries Index]] — technical investigations and synthesis
- [[03-Resources/Research/Weekly-Synthesis-2026-W39|Weekly Synthesis Sample]] — sample weekly synthesis and findings

## ⚙️ System & Templates
- [[_System/README|System Architecture Index]] — templates, automation scripts, and visual canvases
- **Templates** (`_System/Templates/` folder — see [[_System/Templates/README|Templates Catalog]], [[_System/Templates/Templates-Review|Review Hub]], & [[_System/Templates/Template-Showcase|Raw Source Showcase]]):
  - [[_System/Templates/Project|Project.md]] — new project charter
  - [[_System/Templates/Architecture-Decision-Record|Architecture-Decision-Record.md]] — architecture decision record
  - [[_System/Templates/Daily-Review|Daily-Review.md]] — daily reflection & agent alignment review
  - [[_System/Templates/Research-Note|Research-Note.md]] — technical research inquiry
  - [[_System/Templates/Lesson-Learned|Lesson-Learned.md]] — agent operational lesson learned
  - [[_System/Templates/Personality-Judgment-Analysis|Personality-Judgment-Analysis.md]] — 7-dimension cognitive evaluation
  - [[_System/Templates/Personality-Judgment-Dashboard|Personality-Judgment-Dashboard.md]] — Dataview KPI tracker and matrix
- **Automation Scripts** (`_System/Scripts/` folder):
  - `hourly_archive.py` / `archive_now.py` — session archiving
  - `dream_cycle.py` — nocturnal memory distillation & synthesis
  - `sync_to_hermes.py` — bidirectional sync to agent memory & preamble
  - `vault_audit.py` — health check and integrity reporter

---
_See [[SETUP.md]] in repo root for environment setup and script automation._
