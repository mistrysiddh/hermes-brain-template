---
type: moc
status: active
created: {{date}}
tags: [moc, agentic, multi-agent, orchestration, autonomous]
---

# Agentic Architecture MOC

Central map of content for agentic systems, multi-agent orchestration, and autonomous AI workflows.

## 🏗️ Core Architectural Patterns

### Agentic OS Design
- [[agentic-architecture]] — Design patterns for Agentic Operating Systems
- [[../Research/Agentic-OS-Principles.md|Core Principles: Autonomy, Delegation, Verification]]
- [[../Research/State-Management.md|Agent State & Memory Persistence]]
- [[../Research/Tool-Use-Architecture.md|Tool Calling & Function Execution]]

### Orchestration Models
- **Supervisor/Worker** — Central coordinator delegates to specialists
- **Peer-to-Peer** — Agents negotiate and collaborate directly
- **Hierarchical** — Tree of agents with escalation paths
- **Swarm** — Emergent behavior from simple agents

### Communication Protocols
- [[../Research/Agent-Communication.md|Message Passing Patterns]]
- [[../Research/Event-Driven-Agents.md|Event Sourcing for Agents]]
- [[../Research/Shared-Memory.md|Shared Context vs. Explicit Messages]]

## 🤝 Multi-Agent Collaboration

### Group Chat Systems
- [[multi-agent-groupchat-collaboration]] — Verified bot group chats
- [[../Research/Group-Chat-Moderation.md|Moderation & Fact-Checking]]
- [[../Research/Consensus-Mechanisms.md|Voting, Weighted Decisions]]

### Skill & Knowledge Sharing
- [[../Research/Skill-Registry.md|Shared Skill Registry]]
- [[../Research/Context-Synchronization.md|Syncing Context Across Agents]]
- [[../Research/Conflict-Resolution.md|Merge Reconciliation for Agent Outputs]]

## 🛠️ Delegation & Coding Agents

### CLI-Based Delegation
- [[claude-code]] — Claude Code CLI delegation
- [[codex]] — OpenAI Codex CLI patterns
- [[opencode]] — Opencode CLI workflows

### Autonomous Coding Patterns
- [[../Research/Feature-Branch-Delegation.md|Delegating Full Features]]
- [[../Research/PR-Review-Automation.md|Automated PR Reviews]]
- [[../Research/Test-Driven-Delegation.md|TDD with Agents]]

## 🔍 Verification & Safety

### Output Verification
- [[../Research/Output-Validation.md|Schema & Contract Checking]]
- [[../Research/Hallucination-Detection.md|Fact Verification Pipelines]]
- [[../Research/Regression-Testing.md|Agent Behavior Regression Tests]]

### Guardrails
- [[../Research/Permission-Scoping.md|Least-Privilege Tool Access]]
- [[../Research/Rate-Limiting.md|Cost & Rate Control]]
- [[../Research/Audit-Trails.md|Immutable Decision Logs]]

## 📦 Hermes-Specific Agentic Patterns

### Skill System as Agents
- Each skill = autonomous capability module
- Skill discovery & installation = agent onboarding
- Skill forecast = capability planning

### Plugin Architecture
- [[hermes-desktop-plugin-dev]] — UI panes as agent interfaces
- [[inspecting-hermes-desktop-dom]] — DOM introspection for agents
- [[hermes-plugin-discovery]] — Plugin ecosystem navigation

### Session & Memory Integration
- [[../Research/Session-Aware-Agents.md|Agents with Session Context]]
- [[../Research/Long-Term-Agent-Memory.md|Persistent Agent Memory]]
- [[../Research/Cross-Session-Learning.md|Learning Across Conversations]]

## 🎯 Current Projects

### Active
- **Agentic OS Repository** — Multi-agent framework setup
- **Hermes Skill Pipeline** — Automated skill development → testing → publishing
- **Local Agent Swarm** — HermesPi + desktop agents collaboration

### Planned
- [[../Projects/Self-Healing-Infrastructure.md|Self-Healing Agent Ops]]
- [[../Projects/Autonomous-Research-Agents.md|Paper-to-Production Pipeline]]
- [[../Projects/Agent-Marketplace.md|Skill/Agent Sharing Platform]]

---

## Related MOCs
- [[Technology-Stack-MOC|Technology Stack]]
- [[Cybersecurity-MOC|Cybersecurity Framework]]
- [[AI-ML-MOC|AI/ML Workflows]]

## Quick Links
- [[../Skills-Notes/Installed-Skills-Index.md|Installed Skills]]
- [[../Scripts/skill_forecast.py|Skill Forecast (run for suggestions)]]
- [[../Projects/Hermes-Agent-Vault-Setup.md|Hermes Agent Vault Setup]]