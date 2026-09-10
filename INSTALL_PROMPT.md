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
  prompt 2 for the cron job, or prompt 3 if you just want to pull updates.
- Only run **one** archiving cron job per vault — see the Security notes in
  the main [README.md](README.md).
