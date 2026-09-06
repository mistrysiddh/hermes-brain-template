# Hermes Install Prompt

Copy-paste blocks below straight into a Hermes Agent chat. No manual cloning,
no running scripts by hand — Hermes does it for you and asks the same
questions the installer would (where to put the vault, which embedding
backend, etc).

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
   - Linux/macOS: chmod +x install.sh && ./install.sh
   - Windows: powershell -ExecutionPolicy Bypass -File .\install.ps1
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
vault's `Daily/YYYY/MM/DD/` folder automatically — the same pipeline this
template's `Welcome.md` / `Projects/Hermes-Agent-Vault-Setup.md` describe.

Paste this into Hermes (after the vault is installed, or on its own if you
already have a Hermes Brain vault set up):

```
Create a cron job named "hermes-brain-archive-hourly" that runs every hour
(cron expression: 0 * * * *) and exports my Hermes chat sessions from the
last hour as redacted markdown into my Hermes Brain vault's Daily folder,
organized as Daily/YYYY/MM/DD/<session>.md, matching the structure documented
in that vault's Daily/README.md. Use env.HERMES_VAULT_PATH for the vault
location if it's set, otherwise ask me for the vault path first. Before
creating it, check with `cronjob_manage(action='list')` that no other job is
already archiving into the same Daily/ folder — only one archiving job should
ever write there, to avoid manifest.jsonl race conditions.
```

If you'd rather set the cron job up yourself directly, the underlying pattern
is documented in Hermes's `hermes-chat-archiving` skill — the schedule is
`0 * * * *` (hourly) and the target is `<vault>/Daily/YYYY/MM/DD/`.

## 3. Master prompt (install + hourly cron in one paste)

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
   - Linux/macOS: chmod +x install.sh && ./install.sh
   - Windows: powershell -ExecutionPolicy Bypass -File .\install.ps1
4. Let the installer's own prompts run (embedding backend choice, Obsidian
   detection, HERMES_VAULT_PATH registration) — relay its questions to me
   and pass my answers through if you're driving it non-interactively.
5. Confirm env.HERMES_VAULT_PATH is set afterward
   (`hermes config get env.HERMES_VAULT_PATH`).

PART 2 — Hourly archiving cron job
6. Check with `cronjob_manage(action='list')` that no other job is already
   archiving into this vault's Daily/ folder — only one archiving job should
   ever write there, to avoid manifest.jsonl race conditions.
7. If clear, create a cron job named "hermes-brain-archive-hourly" that runs
   every hour (cron expression: 0 * * * *) and exports my Hermes chat
   sessions from the last hour as redacted markdown into
   <vault>/Daily/YYYY/MM/DD/<session>.md, matching the structure documented
   in the vault's Daily/README.md. Use env.HERMES_VAULT_PATH for the vault
   location.
8. Tell me the final vault path and confirm the cron job was created.
```

This is just prompts 1 and 2 combined — use it if you know you want both up
front; use the separate prompts above if you'd rather review/approve the
cron job after seeing the vault installed first.

---

## Notes

- Both prompts are safe to paste as-is — nothing in them touches secrets or
  runs destructive commands. Hermes will still ask for your input at the
  decision points above (vault location, embedding backend, whether you want
  the cron job).
- If you already ran `install.sh`/`install.ps1` by hand, skip straight to
  prompt 2 for the cron job.
- Only run **one** archiving cron job per vault — see the Security notes in
  the main [README.md](README.md).
