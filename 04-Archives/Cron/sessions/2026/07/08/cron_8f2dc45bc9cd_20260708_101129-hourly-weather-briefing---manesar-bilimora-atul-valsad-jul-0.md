---
session_id: "cron_8f2dc45bc9cd_20260708_101129"
title: "Hourly Weather Briefing - Manesar, Bilimora, Atul Valsad · Jul 08 10:12"
source: "cron"
created_at: "2026-07-08T04:41:29.611018Z"
updated_at: ""
ended_at: "2026-07-08T04:42:16.207861Z"
model: "nvidia/nemotron-3-ultra-550b-a55b"
provider: "nvidia"
cwd: null
archived: false
message_count: 14
tool_call_count: 8
format: "md"
exported_at: "2026-09-10T04:30:39.754560Z"
exporter: "hermes sessions export (md/qmd) v1"
summary: # Hourly Weather Briefing - Manesar, Bilimora, Atul Valsad · Jul 08 10:12
---

# Hourly Weather Briefing - Manesar, Bilimora, Atul Valsad · Jul 08 10:12

Session ID: `cron_8f2dc45bc9cd_20260708_101129`

Source: `cron`

## Messages

### User — 2026-07-08T04:41:29.614183Z

[IMPORTANT: The following skill(s) were listed for this job but could not be found and were skipped: terminal. Start your response with a brief notice so the user is aware, e.g.: '⚠️ Skill(s) not found and skipped: terminal']
[IMPORTANT: The user has invoked the "discord-webhook-delivery" skill, indicating they want you to follow its instructions. The full skill content is loaded below.]

---
name: discord-webhook-delivery
description: "Send messages to Discord channels via webhook from cron jobs, scripts, or CLI. Covers webhook creation, payload formatting, rate limits, and common patterns for automated delivery."
version: 1.0.0
author: agent
license: MIT
platforms: [linux, macos, windows]
metadata:
  hermes:
    tags: [discord, webhook, automation, cron, notifications]
prerequisites:
  commands: [curl, jq]
---

# Discord Webhook Delivery

Use this when you need to post messages to Discord from non-interactive contexts (cron jobs, scripts, CI/CD, background agents) where the Hermes `discord` tool cannot send messages (it only supports `fetch_messages`, `search_members`, `create_thread`).

## When to Use

- Cron job summaries/alerts → Discord channel
- Script notifications → Discord
- CI/CD pipeline status → Discord
- Any automated message where you control the sender

## Quick Setup

### 1. Create Webhook in Discord

1. Open Discord → Server Settings → Integrations → Webhooks → New Webhook
2. Choose channel, name it (e.g., "AEGIS Cron"), copy **Webhook URL**
3. Save URL securely (env var, `pass`, or config file)

### 2. Basic POST (curl)

```bash
WEBHOOK_URL="https://discord.com/api/webhooks/XXX/YYY"

curl -X POST "$WEBHOOK_URL" \
  -H "Content-Type: application/json" \
  -d '{"content": "Hello from cron!", "username": "AEGIS Cron"}'
```

### 3. Rich Embed (recommended for briefings)

```bash
curl -X POST "$WEBHOOK_URL" \
  -H "Content-Type: application/json" \
  -d '{
    "username": "AEGIS Briefing",
    "avatar_url": "https://example.com/icon.png",
    "embeds": [{
      "title": "Daily Email Briefing — 2026-07-07",
      "description": "12 new emails in last 24h",
      "color": 5814783,
      "fields": [
        {"name": "🎯 Training/Meetings", "value": "10 emails", "inline": true},
        {"name": "🔒 Security/Newsletters", "value": "6 emails", "inline": true},
        {"name": "💼 Professional", "value": "1 email", "inline": true}
      ],
      "footer": {"text": "Generated at 02:30 IST"},
      "timestamp": "2026-07-07T02:30:00+05:30"
    }]
  }'
```

## Rate Limits

| Limit | Value | Handling |
|-------|-------|----------|
| Requests | 30/min per webhook | Sleep 2s between posts; batch multiple items into one embed |
| Payload size | 8 MB | Truncate long content |
| Embeds per message | 10 | Split if needed |
| Character limit | 2000 (content), 6000 (embed description) | Use fields for long lists |

**Best practice**: One webhook call per cron run. Build the full embed in script, post once.

## Common Patterns

### Cron Job Template

```bash
#!/bin/bash
# ~/scripts/discord-briefing.sh
set -euo pipefail

WEBHOOK_URL="${DISCORD_WEBHOOK_BRIEFING:-}"
[[ -z "$WEBHOOK_URL" ]] && { echo "WEBHOOK_URL not set"; exit 1; }

# ... fetch data, build JSON ...
PAYLOAD=$(jq -n \
  --arg title "Daily Briefing — $(date +%F)" \
  --arg desc "$SUMMARY" \
  --argjson fields "$FIELDS_JSON" \
  '{
    "username": "AEGIS",
    "embeds": [{
      "title": $title,
      "description": $desc,
      "color": 5814783,
      "fields": $fields,
      "timestamp": (now | todateiso8601)
    }]
  }')

curl -sS -X POST "$WEBHOOK_URL" \
  -H "Content-Type: application/json" \
  -d "$PAYLOAD" >/dev/null
```

### Herses Cron Job with Webhook

In `cronjob` prompt, use `terminal` toolset and call the script:

```yaml
skills: ["terminal"]
script: "~/scripts/discord-briefing.sh"
enabled_toolsets: ["terminal"]
no_agent: true  # script IS the job, stdout delivered verbatim
```

### Python Helper (for complex builds)

```python
import json, os, subprocess, datetime

WEBHOOK = os.environ["DISCORD_WEBHOOK_BRIEFING"]

def post_briefing(categories: dict, total: int):
    fields = []
    for name, (count, emoji) in categories.items():
        fields.append({"name": f"{emoji} {name}", "value": f"{count} emails", "inline": True})
    
    payload = {
        "username": "AEGIS Briefing",
        "embeds": [{
            "title": f"Daily Email Briefing — {datetime.date.today()}",
            "description": f"{total} new emails in last 24h",
            "color": 0x5865F2,  # Discord blurple
            "fields": fields,
            "timestamp": datetime.datetime.now(datetime.timezone.utc).isoformat()
        }]
    }
    subprocess.run(["curl", "-sS", "-X", "POST", WEBHOOK,
                    "-H", "Content-Type: application/json",
                    "-d", json.dumps(payload)], check=True)
```

## Pitfalls & Fixes

| Problem | Cause | Fix |
|---------|-------|-----|
| "404 Not Found" | Webhook URL wrong/deleted | Re-create webhook, update URL |
| "401 Unauthorized" | Invalid token in URL | Regenerate webhook |
| "429 Too Many Requests" | Rate limit hit | Add `sleep 2` between calls; batch into single embed |
| Message not appearing | Wrong channel perms | Webhook must have "Send Messages" in target channel |
| Markdown not rendering | Discord uses subset | Use `**bold**`, `*italic*`, `` `code` ``, `> quote` — no HTML |
| Embed truncated | Field value > 1024 chars | Truncate or split across fields |

## Security

- **Never commit webhook URLs** to git — use env vars or `pass`
- Rotate webhooks periodically (Discord → Integrations → Regenerate)
- Use separate webhooks per purpose (briefing, alerts, errors) for revocation granularity

## References

- `references/discord-webhook-api.md` — Discord webhook API spec (subset used here)
- `templates/briefing-embed.json` — starter embed structure
- `scripts/post-briefing.py` — reusable Python poster

## Related Skills

- `cronjob` — Hermes cron scheduler (use `no_agent: true` with script)
- `himalaya` — email fetching (pairs with this for email→Discord pipelines)

The user has provided the following instruction alongside the skill invocation: [IMPORTANT: You are running as a scheduled cron job. DELIVERY: Your final response will be automatically delivered to the user — do NOT use send_message or try to deliver the output yourself. Just produce your report/output as your final response and the system handles the rest. SILENT: If there is genuinely nothing new to report, respond with exactly "[SILENT]" (nothing else) to suppress delivery. Never combine [SILENT] with content — either report your findings normally, or say [SILENT] and nothing more.]

Fetch current weather from wttr.in for three locations in India:
1. Manesar (Haryana)
2. Bilimora (Gujarat)
3. Atul, Valsad (Gujarat)

For each location, get the weather using wttr.in format:
- curl -s "wttr.in/Manesar?format=3" 
- curl -s "wttr.in/Bilimora?format=3"
- curl -s "wttr.in/Atul,Valsad?format=3"

Create a creative, visually appealing Discord embed message with:
- A header like "🌤️ **HOURLY WEATHER BRIEFING** — [Current IST Time]"
- Each location as a separate field with emoji icons (🌡️ temp, 💧 humidity, 🌬️ wind, ☁️ condition)
- Color-code based on weather severity (green=pleasant, yellow=warm, orange=hot, red=extreme)
- Add a footer with "Next update in 1 hour • Data from wttr.in • AEGIS Weather Bot"
- Use Discord markdown formatting for readability

POST the embed directly to Discord using the webhook URL:
https://discord.com/api/webhooks/1524273933308792866/bP9UEX9QRbUQLmb5iCnts7kwAMoojJoaCJsmzgpspAK_iRDILnk7FpuZHjMeMl6D50Xm

Use curl with JSON payload. Build the full embed in the script and post once.


### Assistant — 2026-07-08T04:41:33.176642Z



## Tool calls

```json
[
  {
    "id": "call-d060da20-c7c6-46bd-bb21-e8a3a193b4d4",
    "call_id": "call-d060da20-c7c6-46bd-bb21-e8a3a193b4d4",
    "response_item_id": "fc_call-d060da20-c7c6-46bd-bb21-e8a3a193b4d4",
    "type": "function",
    "function": {
      "name": "terminal",
      "arguments": "{\"command\":\"curl -s \\\"wttr.in/Manesar?format=3\\\"\"}"
    }
  },
  {
    "id": "call-41c3bdf4-dcf2-459e-b416-f1f43406199f",
    "call_id": "call-41c3bdf4-dcf2-459e-b416-f1f43406199f",
    "response_item_id": "fc_call-41c3bdf4-dcf2-459e-b416-f1f43406199f",
    "type": "function",
    "function": {
      "name": "terminal",
      "arguments": "{\"command\":\"curl -s \\\"wttr.in/Bilimora?format=3\\\"\"}"
    }
  },
  {
    "id": "call-f1204ca8-05fe-4871-bc77-b2b9c2a1c4bf",
    "call_id": "call-f1204ca8-05fe-4871-bc77-b2b9c2a1c4bf",
    "response_item_id": "fc_call-f1204ca8-05fe-4871-bc77-b2b9c2a1c4bf",
    "type": "function",
    "function": {
      "name": "terminal",
      "arguments": "{\"command\":\"curl -s \\\"wttr.in/Atul,Valsad?format=3\\\"\"}"
    }
  }
]
```


### Tool — terminal — 2026-07-08T04:41:33.712352Z

{"output": "Manesar: ⛈️  +28°C", "exit_code": 0, "error": null}


### Tool — terminal — 2026-07-08T04:41:35.227691Z

{"output": "Bilimora: 🌦️  +27°C", "exit_code": 0, "error": null}


### Tool — terminal — 2026-07-08T04:41:36.739265Z

{"output": "Atul,Valsad: 🌦️  +27°C", "exit_code": 0, "error": null}


### Assistant — 2026-07-08T04:41:38.609988Z



## Tool calls

```json
[
  {
    "id": "call-608aa84f-b72c-4cbc-a159-eef2300d20c3",
    "call_id": "call-608aa84f-b72c-4cbc-a159-eef2300d20c3",
    "response_item_id": "fc_call-608aa84f-b72c-4cbc-a159-eef2300d20c3",
    "type": "function",
    "function": {
      "name": "terminal",
      "arguments": "{\"command\":\"curl -s \\\"wttr.in/Manesar?format=%l:+%t+%h+%w+%C\\\"\"}"
    }
  },
  {
    "id": "call-0e1c0e37-ad30-40ee-9a41-2a5086c7ba8f",
    "call_id": "call-0e1c0e37-ad30-40ee-9a41-2a5086c7ba8f",
    "response_item_id": "fc_call-0e1c0e37-ad30-40ee-9a41-2a5086c7ba8f",
    "type": "function",
    "function": {
      "name": "terminal",
      "arguments": "{\"command\":\"curl -s \\\"wttr.in/Bilimora?format=%l:+%t+%h+%w+%C\\\"\"}"
    }
  },
  {
    "id": "call-b5590f66-b681-45dc-9653-25f1be76219d",
    "call_id": "call-b5590f66-b681-45dc-9653-25f1be76219d",
    "response_item_id": "fc_call-b5590f66-b681-45dc-9653-25f1be76219d",
    "type": "function",
    "function": {
      "name": "terminal",
      "arguments": "{\"command\":\"curl -s \\\"wttr.in/Atul,Valsad?format=%l:+%t+%h+%w+%C\\\"\"}"
    }
  }
]
```


### Tool — terminal — 2026-07-08T04:41:39.087160Z

{"output": "Manesar: +28°C 89% ←13km/h Light Rain, Rain With Thunderstorm", "exit_code": 0, "error": null}


### Tool — terminal — 2026-07-08T04:41:40.623366Z

{"output": "Bilimora: +27°C 92% ↑15km/h Light rain", "exit_code": 0, "error": null}


### Tool — terminal — 2026-07-08T04:41:43.331341Z

{"output": "Atul,Valsad: +27°C 90% ↗20km/h Patchy rain nearby", "exit_code": 0, "error": null}


### Assistant — 2026-07-08T04:41:53.257478Z



## Tool calls

```json
[
  {
    "id": "call-c8819328-2534-49e0-a5eb-7afc071d8223",
    "call_id": "call-c8819328-2534-49e0-a5eb-7afc071d8223",
    "response_item_id": "fc_call-c8819328-2534-49e0-a5eb-7afc071d8223",
    "type": "function",
    "function": {
      "name": "terminal",
      "arguments": "{\"command\":\"date '+%Y-%m-%d %H:%M:%S %Z'\"}"
    }
  }
]
```


### Tool — terminal — 2026-07-08T04:41:53.342807Z

{"output": "2026-07-08 10:11:53 IST", "exit_code": 0, "error": null}


### Assistant — 2026-07-08T04:42:14.429414Z



## Tool calls

```json
[
  {
    "id": "call-3d60ff91-80b2-4a9b-9058-6cb2359df92f",
    "call_id": "call-3d60ff91-80b2-4a9b-9058-6cb2359df92f",
    "response_item_id": "fc_call-3d60ff91-80b2-4a9b-9058-6cb2359df92f",
    "type": "function",
    "function": {
      "name": "terminal",
      "arguments": "{\"command\":\"curl -sS -X POST \\\"https://discord.com/api/webhooks/1524273933308792866/bP9UEX9QRbUQLmb5iCnts7kwAMoojJoaCJsmzgpspAK_iRDILnk7FpuZHjMeMl6D50Xm\\\" \\\\\\n  -H \\\"Content-Type: application/json\\\" \\\\\\n  -d '{\\n    \\\"username\\\": \\\"AEGIS Weather Bot\\\",\\n    \\\"avatar_url\\\": \\\"https://cdn.discordapp.com/embed/avatars/0.png\\\",\\n    \\\"embeds\\\": [{\\n      \\\"title\\\": \\\"🌤️ **HOURLY WEATHER BRIEFING** — 2026-07-08 10:11 IST\\\",\\n      \\\"description\\\": \\\"Real-time conditions across three key locations in North & West India\\\",\\n      \\\"color\\\": 16753920,\\n      \\\"fields\\\": [\\n        {\\n          \\\"name\\\": \\\"🏢 **Manesar, Haryana** ⛈️\\\",\\n          \\\"value\\\": \\\"🌡️ **28°C**  \\\\n💧 **89%** Humidity  \\\\n🌬️ **13 km/h** ← West  \\\\n☁️ Light Rain + Thunderstorm\\\",\\n          \\\"inline\\\": true\\n        },\\n        {\\n          \\\"name\\\": \\\"🏭 **Bilimora, Gujarat** 🌦️\\\",\\n          \\\"value\\\": \\\"🌡️ **27°C**  \\\\n💧 **92%** Humidity  \\\\n🌬️ **15 km/h** ↑ South  \\\\n☁️ Light Rain\\\",\\n          \\\"inline\\\": true\\n        },\\n        {\\n          \\\"name\\\": \\\"🏭 **Atul, Valsad, Gujarat** 🌦️\\\",\\n          \\\"value\\\": \\\"🌡️ **27°C**  \\\\n💧 **90%** Humidity  \\\\n🌬️ **20 km/h** ↗ Southwest  \\\\n☁️ Patchy Rain Nearby\\\",\\n          \\\"inline\\\": true\\n        }\\n      ],\\n      \\\"footer\\\": {\\n        \\\"text\\\": \\\"Next update in 1 hour • Data from wttr.in • AEGIS Weather Bot\\\"\\n      },\\n      \\\"timestamp\\\": \\\"2026-07-08T04:41:53Z\\\"\\n    }]\\n  }'\"}"
    }
  }
]
```


### Tool — terminal — 2026-07-08T04:42:15.162557Z

{"output": "", "exit_code": 0, "error": null}


### Assistant — 2026-07-08T04:42:16.191793Z

[SILENT]

## Export verification

- Session id: `cron_8f2dc45bc9cd_20260708_101129`
- Exported messages: `14`
- Source DB message count at export: `14`
- Exported at: `2026-09-10T04:30:39.754560Z`
- SHA256 of exported body: `75f25bf3be086ec379ca9405bfc105a948139b8b6ed03e6d7081b4ebc1fa0f64`
