---
type: moc
status: active
created: {{date}}
tags: [moc, cybersecurity, threat-modeling, hardening, privacy]
---

# Cybersecurity Framework MOC

Central map of content for cybersecurity practices, threat modeling, and privacy-first tooling.

## 🛡️ System Hardening

### Core Practices
- [[../Research/Linux-Hardening.md|Linux Hardening Checklist]]
- [[../Research/SSH-Hardening.md|SSH Configuration & Key Management]]
- [[../Research/Firewall-Rules.md|Firewall Rules (nftables/iptables)]]
- [[../Research/Auditd-Setup.md|System Auditing with auditd]]

### Container Security
- [[../Research/Docker-Security.md|Docker Hardening & Rootless Containers]]
- [[../Research/Container-Scanning.md|Image Scanning (Trivy, Grype, Syft)]]
- [[../Research/K8s-Security.md|Kubernetes RBAC & Network Policies]]

## 🔍 Threat Modeling

### Frameworks
- [[../Research/STRIDE-Modeling.md|STRIDE Threat Modeling]]
- [[../Research/ATTACK-Mapping.md|MITRE ATT&CK Mapping]]
- [[../Research/DREAD-Scoring.md|DREAD Risk Assessment]]

### Practical Application
- [[01-Projects/Threat-Model-Hermes.md|Hermes Agent Threat Model]]
- [[01-Projects/Threat-Model-SelfHosted.md|Self-Hosted Stack Threat Model]]

## 🔐 Identity & Access

### Authentication
- [[../Research/MFA-Implementation.md|MFA Strategies (TOTP, WebAuthn, FIDO2)]]
- [[../Research/Password-Managers.md|Password Manager Comparison]]
- [[../Research/SSH-Certificates.md|SSH Certificate Authority]]

### Secrets Management
- [[../Research/SOPS-Secrets.md|SOPS + Age for Git Secrets]]
- [[../Research/HashiCorp-Vault.md|Vault for Dynamic Secrets]]
- [[../Research/1Password-CLI.md|1Password CLI Integration]]

## 🕵️ Monitoring & Detection

### Log Analysis
- [[../Research/Syslog-Centralization.md|Centralized Logging (rsyslog, Vector)]]
- [[../Research/Log-Analysis-Tools.md|Tools: jq, awk, lnav, grep patterns]]
- [[../Research/Alert-Rules.md|Actionable Alert Design]]

### Network Monitoring
- [[../Research/Zeek-Suricata.md|Zeek/Suricata IDS/IPS]]
- [[../Research/PCAP-Analysis.md|Packet Capture Analysis]]
- [[../Research/DNS-Monitoring.md|DNS Exfiltration Detection]]

## 🛡️ Privacy-First Tooling

### Communication
- [[../Research/Signal-Matrix.md|Signal vs Matrix vs Session]]
- [[../Research/Email-Encryption.md|PGP/GnuPG & Autocrypt]]
- [[../Research/Anonymous-Networks.md|Tor, I2P, VPN Comparison]]

### Data Protection
- [[../Research/Full-Disk-Encryption.md|LUKS / BitLocker / FileVault]]
- [[../Research/Backup-Encryption.md|Encrypted Backups (Borg, Restic, Rclone)]]
- [[../Research/Secure-Deletion.md|Secure Erase & Shredding]]

## 🧪 Offensive Security (Learning)

### Skills to Develop
- Network reconnaissance (nmap, masscan)
- Web application testing (Burp, OWASP ZAP)
- Binary analysis (Ghidra, radare2)
- Exploit development basics

### Practice Environments
- [[01-Projects/HackTheBox-Lab.md|HTB/TryHackMe Lab Notes]]
- [[01-Projects/VulnHub-Walkthroughs.md|VulnHub Machine Writeups]]

---

## Related MOCs
- [[Technology-Stack-MOC|Technology Stack]]
- [[AI-ML-MOC|AI/ML Workflows]]
- [[Agentic-Architecture-MOC|Agentic Systems]]

## Quick Links
- [[01-Projects/Hermes-Agent-Vault-Setup|Hermes Agent Vault Setup]]
- [[02-Areas/Skills/Installed-Skills-Index|Installed Skills Index]]
- [[_System/Scripts/skill_forecast.py|Skill Forecast]]
- [[03-Resources/Research/Cybersecurity-Certifications|Cert Path: OSCP, OSWE, CRTO]]
