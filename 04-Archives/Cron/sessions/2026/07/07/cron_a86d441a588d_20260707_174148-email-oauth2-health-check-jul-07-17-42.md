---
session_id: "cron_a86d441a588d_20260707_174148"
title: "Email OAuth2 Health Check · Jul 07 17:42"
source: "cron"
created_at: "2026-07-07T12:11:50.590573Z"
updated_at: ""
ended_at: "2026-07-07T12:12:03.928084Z"
model: "nvidia/nemotron-3-ultra-550b-a55b"
provider: "nvidia"
cwd: null
archived: false
message_count: 4
tool_call_count: 1
format: "md"
exported_at: "2026-09-10T04:30:38.674268Z"
exporter: "hermes sessions export (md/qmd) v1"
summary: # Email OAuth2 Health Check · Jul 07 17:42
---

# Email OAuth2 Health Check · Jul 07 17:42

Session ID: `cron_a86d441a588d_20260707_174148`

Source: `cron`

## Messages

### User — 2026-07-07T12:11:50.628421Z

[IMPORTANT: The following skill(s) were listed for this job but could not be found and were skipped: discord. Start your response with a brief notice so the user is aware, e.g.: '⚠️ Skill(s) not found and skipped: discord']
[IMPORTANT: The user has invoked the "himalaya" skill, indicating they want you to follow its instructions. The full skill content is loaded below.]

---
name: himalaya
description: "Himalaya CLI: IMAP/SMTP email from terminal."
version: 1.1.0
author: community
license: MIT
platforms: [linux, macos, windows]
metadata:
  hermes:
    tags: [Email, IMAP, SMTP, CLI, Communication]
    homepage: https://github.com/pimalaya/himalaya
prerequisites:
  commands: [himalaya]
---

# Himalaya Email CLI

Himalaya is a CLI email client that lets you manage emails from the terminal using IMAP, SMTP, Notmuch, or Sendmail backends.

This skill is separate from the Hermes Email gateway adapter. The gateway
adapter lets people email the agent and uses Hermes' built-in IMAP/SMTP
adapter; this skill lets the agent operate a mailbox from terminal tools and
requires the external `himalaya` CLI.

## References

- `references/configuration.md` (config file setup + IMAP/SMTP authentication)
- `references/message-composition.md` (MML syntax for composing emails)

## Prerequisites

1. Himalaya CLI installed (`himalaya --version` to verify)
2. A configuration file at `~/.config/himalaya/config.toml`
3. IMAP/SMTP credentials configured (password stored securely)

### Installation

```bash
# Pre-built binary (Linux/macOS — recommended)
curl -sSL https://raw.githubusercontent.com/pimalaya/himalaya/master/install.sh | PREFIX=~/.local sh

# macOS via Homebrew
brew install himalaya

# Or via cargo (any platform with Rust)
cargo install himalaya --locked
```

## Configuration Setup

Run the interactive wizard to set up an account:

```bash
himalaya account configure
```

Or create `~/.config/himalaya/config.toml` manually:

```toml
[accounts.personal]
email = "you@example.com"
display-name = "Your Name"
default = true

backend.type = "imap"
backend.host = "imap.example.com"
backend.port = 993
backend.encryption.type = "tls"
backend.login = "you@example.com"
backend.auth.type = "password"
backend.auth.cmd = "pass show email/imap"  # or use keyring

message.send.backend.type = "smtp"
message.send.backend.host = "smtp.example.com"
message.send.backend.port = 587
message.send.backend.encryption.type = "start-tls"
message.send.backend.login = "you@example.com"
message.send.backend.auth.type = "password"
message.send.backend.auth.cmd = "pass show email/smtp"

# Folder aliases (himalaya v1.2.0+ syntax). Required whenever the
# server's folder names don't match himalaya's canonical names
# (inbox/sent/drafts/trash). Gmail is the common case — see
# `references/configuration.md` for the `[Gmail]/Sent Mail` mapping.
folder.aliases.inbox = "INBOX"
folder.aliases.sent = "Sent"
folder.aliases.drafts = "Drafts"
folder.aliases.trash = "Trash"
```

> **Heads up on the alias syntax.** Pre-v1.2.0 docs used a
> `[accounts.NAME.folder.alias]` sub-section (singular `alias`).
> v1.2.0 silently ignores that form — TOML parses fine, but the
> alias resolver never reads it, so every lookup falls through to
> the canonical name. On Gmail this means save-to-Sent fails *after*
> SMTP delivery succeeds, and `himalaya message send` exits non-zero.
> Any caller (agent, script, user) that retries on that exit code
> will re-run the entire send — including SMTP — producing duplicate
> emails to recipients. Always use `folder.aliases.X` (plural, dotted
> keys, directly under `[accounts.NAME]`).

## Hermes Integration Notes

- **Reading, listing, searching, moving, deleting** all work directly through the terminal tool
- **Composing/replying/forwarding** — piped input (`cat << EOF | himalaya template send`) is recommended for reliability. Interactive `$EDITOR` mode works with `pty=true` + background + process tool, but requires knowing the editor and its commands
- Use `--output json` for structured output that's easier to parse programmatically
- The `himalaya account configure` wizard requires interactive input — use PTY mode: `terminal(command="himalaya account configure", pty=true)`

## Common Operations

### List Folders

```bash
himalaya folder list
```

### List Emails

List emails in INBOX (default):

```bash
himalaya envelope list
```

List emails in a specific folder:

```bash
himalaya envelope list --folder "Sent"
```

List with pagination:

```bash
himalaya envelope list --page 1 --page-size 20
```

### Search Emails

```bash
himalaya envelope list from john@example.com subject meeting
```

### Read an Email

Read email by ID (shows plain text):

```bash
himalaya message read 42
```

Export raw MIME:

```bash
himalaya message export 42 --full
```

### Reply to an Email

To reply non-interactively from Hermes, read the original message, compose a reply, and pipe it:

```bash
# Get the reply template, edit it, and send
himalaya template reply 42 | sed 's/^$/\nYour reply text here\n/' | himalaya template send
```

Or build the reply manually:

```bash
cat << 'EOF' | himalaya template send
From: you@example.com
To: sender@example.com
Subject: Re: Original Subject
In-Reply-To: <original-message-id>

Your reply here.
EOF
```

Reply-all (interactive — needs $EDITOR, use template approach above instead):

```bash
himalaya message reply 42 --all
```

### Forward an Email

```bash
# Get forward template and pipe with modifications
himalaya template forward 42 | sed 's/^To:.*/To: newrecipient@example.com/' | himalaya template send
```

### Write a New Email

**Non-interactive (use this from Hermes)** — pipe the message via stdin:

```bash
cat << 'EOF' | himalaya template send
From: you@example.com
To: recipient@example.com
Subject: Test Message

Hello from Himalaya!
EOF
```

Or with headers flag:

```bash
himalaya message write -H "To:recipient@example.com" -H "Subject:Test" "Message body here"
```

Note: `himalaya message write` without piped input opens `$EDITOR`. This works with `pty=true` + background mode, but piping is simpler and more reliable.

### Move/Copy Emails

Move to folder (target folder comes first, then the message ID):

```bash
himalaya message move "Archive" 42
```

Copy to folder (target folder comes first, then the message ID):

```bash
himalaya message copy "Important" 42
```

### Delete an Email

```bash
himalaya message delete 42
```

### Manage Flags

Add flag:

```bash
himalaya flag add 42 --flag seen
```

Remove flag:

```bash
himalaya flag remove 42 --flag seen
```

## Multiple Accounts

List accounts:

```bash
himalaya account list
```

Use a specific account:

```bash
himalaya --account work envelope list
```

## Attachments

Save attachments from a message:

```bash
himalaya attachment download 42
```

Save to specific directory:

```bash
himalaya attachment download 42 --downloads-dir ~/Downloads
```

## Output Formats

Most commands support `--output` for structured output:

```bash
himalaya envelope list --output json
himalaya envelope list --output plain
```

## Debugging

Enable debug logging:

```bash
RUST_LOG=debug himalaya envelope list
```

Full trace with backtrace:

```bash
RUST_LOG=trace RUST_BACKTRACE=1 himalaya envelope list
```

## Tips

- Use `himalaya --help` or `himalaya <command> --help` for detailed usage.
- Message IDs are relative to the current folder; re-list after folder changes.
- For composing rich emails with attachments, use MML syntax (see `references/message-composition.md`).
- Store passwords securely using `pass`, system keyring, or a command that outputs the password.

The user has provided the following instruction alongside the skill invocation: [IMPORTANT: You are running as a scheduled cron job. DELIVERY: Your final response will be automatically delivered to the user — do NOT use send_message or try to deliver the output yourself. Just produce your report/output as your final response and the system handles the rest. SILENT: If there is genuinely nothing new to report, respond with exactly "[SILENT]" (nothing else) to suppress delivery. Never combine [SILENT] with content — either report your findings normally, or say [SILENT] and nothing more.]

Check M365 email connectivity via himalaya. Run a lightweight test to verify OAuth2 tokens are valid.

Steps:
1. Run: `himalaya envelope list --folder INBOX --output json --page-size 1`
2. If command succeeds (exit code 0): respond with exactly "[SILENT]" to suppress delivery.
3. If command fails (exit code != 0): output this alert message directly:
   "⚠️ **M365 Email Auth Failure** - himalaya failed to fetch INBOX. OAuth2 tokens likely expired or Conditional Access blocking. Check: `himalaya account configure` or re-authenticate."

DO NOT try to use any Discord tools. Simply output the response text directly (either the [SILENT] token or the alert). The system scheduler handles the delivery.


### Assistant — 2026-07-07T12:11:58.922878Z



## Tool calls

```json
[
  {
    "id": "call-a6a11052-34f1-436e-aa44-da0784420191",
    "call_id": "call-a6a11052-34f1-436e-aa44-da0784420191",
    "response_item_id": "fc_call-a6a11052-34f1-436e-aa44-da0784420191",
    "type": "function",
    "function": {
      "name": "terminal",
      "arguments": "{\"command\":\"himalaya envelope list --folder INBOX --output json --page-size 1\"}"
    }
  }
]
```


### Tool — terminal — 2026-07-07T12:12:00.134297Z

{"output": "[{\"id\":\"29069\",\"flags\":[],\"subject\":\"New sign-in to your Read AI account\",\"from\":{\"name\":\"Read Support\",\"addr\":\"support@e.read.ai\"},\"to\":{\"name\":null,\"addr\":\"hello@mistrysiddh.com\"},\"date\":\"2026-07-07 11:42+00:00\",\"has_attachment\":false}]", "exit_code": 0, "error": null}


### Assistant — 2026-07-07T12:12:03.909036Z

[SILENT]

## Export verification

- Session id: `cron_a86d441a588d_20260707_174148`
- Exported messages: `4`
- Source DB message count at export: `4`
- Exported at: `2026-09-10T04:30:38.674268Z`
- SHA256 of exported body: `fd4c6d9ac5fa9b93d702102d4d4203003780513b0cf11079226e6192f50a1f16`
