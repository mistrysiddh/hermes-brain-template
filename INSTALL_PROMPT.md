# Hermes Install Prompt

Copy-paste blocks below straight into a Hermes/OpenClaw Agent chat. No manual cloning,
no running scripts by hand — Hermes/OpenClaw does it for you and asks the same
questions the installer would (where to put the vault, which embedding
backend, etc).

> [!TIP]
> **Prefer a terminal one-liner instead of chatting?**
> - **Windows (PowerShell):** `irm https://raw.githubusercontent.com/mistrysiddh/hermes-brain-template/main/_System/Scripts/Installers/install.ps1 | iex`
> - **Linux / macOS:** `curl -fsSL https://raw.githubusercontent.com/mistrysiddh/hermes-brain-template/main/_System/Scripts/Installers/install.sh | bash`

---

## 1. One-shot install prompt

Paste this into Hermes:

```
Clone https://github.com/mistrysiddh/hermes-brain-template into a new
"Hermes Brain" vault for me. Steps:

1. Ask me where I want the vault folder to live (default: ~/Hermes Brain on
   Linux/macOS, or %USERPROFILE%\Hermes Brain on Windows).
2. Clone the repo into that location (or download+extract if git isn't
   available).
3. Run the platform-appropriate installer from inside it:
   - Linux/macOS: chmod +x _System/Scripts/Installers/install.sh && ./_System/Scripts/Installers/install.sh
   - Windows: powershell -ExecutionPolicy Bypass -File .\\_System\\Scripts\\Installers\\install.ps1
4. Let the installer's own prompts run (embedding backend choice, Obsidian
   detection, HERMES_VAULT_PATH registration) — relay its questions to me
   and pass my answers through if you're driving it non-interactively.
5. When it's done, tell me the final vault path and confirm
   env.HERMES_VAULT_PATH is set (`hermes config get env.HERMES_VAULT_PATH`).
6. Ask me if I also want the hourly session-archiving cron job set up (see
   the second prompt below) — if yes, run it.
```

## 2. Hourly session-archive cron job prompt

This makes Hermes export every chat session from the last hour into your new
vault's `04-Archives/Daily/YYYY/MM/DD/` folder automatically — the same pipeline this
template's `Welcome.md` / `01-Projects/Hermes-Agent-Vault-Setup.md` describe.
The script now also extracts **token usage** (prompt + completion tokens)
from each session and appends daily totals to `04-Archives/Audit-Reports/Token-Usage.log`,
which the Dashboard reads live.

Paste this into Hermes (after the vault is installed, or on its own if you
already have a Hermes Brain vault set up):

```
Create a cron job named "hermes-brain-archive-hourly" that runs every hour
(cron expression: 0 * * * *) and exports my Hermes chat sessions from the
last hour as redacted markdown into my Hermes Brain vault's 04-Archives/Daily folder,
organized as 04-Archives/Daily/YYYY/MM/DD/<session>.md, matching the structure documented
in that vault's 04-Archives/Daily/README.md. The script also exports a JSONL copy to
extract token usage (prompt + completion tokens) and appends daily totals to
04-Archives/Audit-Reports/Token-Usage.log. Execute: python "<vault>/_System/Scripts/hourly_archive.py". Use env.HERMES_VAULT_PATH for the vault
location if it's set, otherwise ask me for the vault path first.


IMPORTANT — idempotency: before creating anything, call
`cronjob_manage(action='list')` and check for a job already named
"hermes-brain-archive-hourly" (or any other job whose command targets this
same vault's 04-Archives/Daily/ folder). If one already exists, do NOT create a
duplicate — just tell me it's already set up and leave it alone. Only
create the job if no matching one exists.
```

If you'd rather set the cron job up yourself directly, the underlying pattern
is documented in Hermes's `hermes-chat-archiving` skill — the schedule is
`0 * * * *` (hourly) and the target is `<vault>/04-Archives/Daily/YYYY/MM/DD/`.

---

## 2b. Real-time session syncing hooks (instant updates)

For instant syncing without waiting for the hourly cron, configure Hermes shell hooks in your `~/.hermes/config.yaml`.
This automatically creates a new `.md` file in `04-Archives/Daily/YYYY/MM/DD/` when any chat starts, and continuously updates old or ongoing chats on every turn:

```yaml
hooks:
  on_session_start:
    - _hermes_brain: true
      command: '"<vault>/_System/Scripts/hermes_session_sync.cmd" --hook --event on_session_start'
      timeout: 30
  post_llm_call:
    - _hermes_brain: true
      command: '"<vault>/_System/Scripts/hermes_session_sync.cmd" --hook --event post_llm_call'
      timeout: 30
  on_session_end:
    - _hermes_brain: true
      command: '"<vault>/_System/Scripts/hermes_session_sync.cmd" --hook --event on_session_end'
      timeout: 30
  on_session_finalize:
    - _hermes_brain: true
      command: '"<vault>/_System/Scripts/hermes_session_sync.cmd" --hook --event on_session_finalize'
      timeout: 30
hooks_auto_accept: true
```
*(On Linux/macOS, use `hermes_session_sync.sh` instead of `.cmd`)*

---

## 2c. Optional: Weekly vault audit + agent performance cron jobs

These run less frequently (weekly/monthly) and keep your vault healthy
while giving you insights into agent usage:

**Vault audit (weekly, Sunday 2 AM):**
```
Create a cron job named "hermes-brain-vault-audit-weekly" that runs
weekly on Sunday at 2 AM (cron: 0 2 * * 0) and runs:
python3 _System/Scripts/vault_audit.py
inside the vault (using env.HERMES_VAULT_PATH). This checks for broken
wikilinks, stale Memory-Review entries (>30 days), duplicate sessions,
and orphaned files, writing a report to 04-Archives/Audit-Reports/Vault-Audit-Report.md.

Idempotency: first call `cronjob_manage(action='list')` and check whether a
job named "hermes-brain-vault-audit-weekly" already exists. If it does,
don't create another — just confirm it's already set up.
```

**Agent performance (weekly, Monday 3 AM):**
```
Create a cron job named "hermes-brain-agent-perf-weekly" that runs
weekly on Monday at 3 AM (cron: 0 3 * * 1) and runs:
python3 _System/Scripts/agent_performance.py
inside the vault. This analyzes session archives and skill usage to
produce 04-Archives/Audit-Reports/Agent-Performance.md with skill frequency, tool
usage, daily trends, and top sessions by tokens.

Idempotency: first call `cronjob_manage(action='list')` and check whether a
job named "hermes-brain-agent-perf-weekly" already exists. If it does,
don't create another — just confirm it's already set up.
```

## 3. Upgrade prompt (pull the latest template into an existing vault)

If you already have a Hermes Brain vault installed and just want the latest
template changes (new Dashboard features, bug fixes, updated plugins, etc.)
without losing anything you've hand-edited, paste this:

```
I already have a Hermes Brain vault installed and want to update it to the
latest version of the template. Steps:

1. Find my vault: use env.HERMES_VAULT_PATH if it's set
   (`hermes config get env.HERMES_VAULT_PATH`), otherwise ask me for the
   vault folder path.
2. Check the vault's current version — read the VERSION file at the vault
   root if present.
3. From inside the vault folder, run the platform-appropriate update script:
   - Linux/macOS: chmod +x update.sh && ./update.sh
   - Windows: powershell -ExecutionPolicy Bypass -File .\update.ps1
4. This turns the vault into a local git repo (first run only) tracking the
   template as a read-only remote, then fetches and merges. If I have
   uncommitted changes, the script will ask whether to snapshot them first —
   relay that prompt to me.
5. If the merge reports conflicts, list the conflicting files for me and
   stop — don't try to resolve them yourself, since conflicts mean I
   hand-edited something the template also changed.
6. On success, tell me the new version (check VERSION again) and that my
   personal content (Daily/, Memory-Review/*, Projects/* beyond README,
   plugin data.json files) was untouched — it's protected by the vault's own
   .gitignore the whole way through.
```

This is a **pull only** — it never pushes anything from your vault anywhere.
The `template` git remote it creates has push explicitly disabled.

## 4. Master prompt (install + hourly cron in one paste)

Want everything done in a single paste — install the vault AND set up the
hourly archiving cron job, no follow-up needed? Use this:

```
Set up a Hermes Brain vault for me end-to-end:

PART 1 — Install
1. Ask me where I want the vault folder to live (default: ~/Hermes Brain on
   Linux/macOS, or %USERPROFILE%\Hermes Brain on Windows).
2. Clone https://github.com/mistrysiddh/hermes-brain-template into that
   location (or download+extract if git isn't available).
3. Run the platform-appropriate installer from inside it:
   - Linux/macOS: chmod +x _System/Scripts/Installers/install.sh && ./_System/Scripts/Installers/install.sh
   - Windows: powershell -ExecutionPolicy Bypass -File .\\_System\\Scripts\\Installers\\install.ps1
4. Let the installer's own prompts run (embedding backend choice, Obsidian
   detection, HERMES_VAULT_PATH registration) — relay its questions to me
   and pass my answers through if you're driving it non-interactively.
5. Confirm env.HERMES_VAULT_PATH is set afterward
   (`hermes config get env.HERMES_VAULT_PATH`).

PART 2 — Hourly archiving cron job
6. Check with `cronjob_manage(action='list')` for a job already named
   "hermes-brain-archive-hourly" (or any job whose command targets this
   vault's 04-Archives/Daily/ folder). If one already exists, skip creating it — just
   tell me it's already set up.
7. If none exists, create a cron job named "hermes-brain-archive-hourly"
   that runs every hour (cron expression: 0 * * * *) and exports my Hermes
   chat sessions from the last hour as redacted markdown into
   <vault>/04-Archives/Daily/YYYY/MM/DD/<session>.md, matching the structure documented
   in the vault's 04-Archives/Daily/README.md. The script also exports a JSONL copy to
   extract token usage (prompt + completion tokens) and appends daily totals to
   04-Archives/Audit-Reports/Token-Usage.log. Use env.HERMES_VAULT_PATH for the vault
   location.
8. **Optional: Vault audit + Agent performance cron jobs** — same
   idempotency check first (list, look for a matching name), only create if
   missing:
   - "hermes-brain-vault-audit-weekly" (Sunday 2 AM): runs `python3 _System/Scripts/vault_audit.py` → writes `04-Archives/Audit-Reports/Vault-Audit-Report.md`
   - "hermes-brain-agent-perf-weekly" (Monday 3 AM): runs `python3 _System/Scripts/agent_performance.py` → writes `04-Archives/Audit-Reports/Agent-Performance.md`
9. Tell me the final vault path and confirm, for each cron job, whether it
   was newly created or already existed.
```

This is just prompts 1 and 2 combined — use it if you know you want both up
front; use the separate prompts above if you'd rather review/approve the
cron job after seeing the vault installed first.

---

## Notes

- Both prompts are safe to paste as-is — nothing in them touches secrets or runs destructive commands. Hermes will still ask for your input at the decision points above (vault location, embedding backend, whether you want the cron job).
- If you already ran `install.sh`/`install.ps1` by hand, skip straight to prompt 2 for the cron job, or prompt 3 if you just want to pull updates.
- Only run **one** archiving cron job per vault — see the Security notes in the main [README.md](README.md).
- **Optional instant archive**: After installing, you also have `_System/Scripts/archive_now.py` (or `.ps1`) available for manual, on-demand exports (e.g., after a long chat session). It exports sessions from a configurable time window (default: last 5 minutes) and uses the same lock file as the hourly cron to avoid conflicts. See `04-Archives/Daily/README.md` for details.
- **Optional session enrichment**: After archiving (hourly or instant), you can run `_System/Scripts/enrich_session.py` (or `.ps1`) to add a simple summary frontmatter to session markdown files that don't already have one, making sessions more glanceable.
