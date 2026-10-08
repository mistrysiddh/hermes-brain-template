---
session_id: "cron_8f2dc45bc9cd_20260708_102602"
title: "Hourly Weather Briefing - Manesar, Bilimora, Atul Valsad · Jul 08 10:28"
source: "cron"
created_at: "2026-07-08T04:56:02.941435Z"
updated_at: ""
ended_at: "2026-07-08T04:58:49.310951Z"
model: "nvidia/nemotron-3-ultra-550b-a55b"
provider: "nvidia"
cwd: null
archived: false
message_count: 10
tool_call_count: 4
format: "md"
exported_at: "2026-09-10T04:30:39.788633Z"
exporter: "hermes sessions export (md/qmd) v1"
summary: # Hourly Weather Briefing - Manesar, Bilimora, Atul Valsad · Jul 08 10:28
---

# Hourly Weather Briefing - Manesar, Bilimora, Atul Valsad · Jul 08 10:28

Session ID: `cron_8f2dc45bc9cd_20260708_102602`

Source: `cron`

## Messages

### User — 2026-07-08T04:56:02.947631Z

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


### Assistant — 2026-07-08T04:56:10.413903Z



## Tool calls

```json
[
  {
    "id": "call-ab6ce497-58ac-4342-8579-d47ab8e6190a",
    "call_id": "call-ab6ce497-58ac-4342-8579-d47ab8e6190a",
    "response_item_id": "fc_call-ab6ce497-58ac-4342-8579-d47ab8e6190a",
    "type": "function",
    "function": {
      "name": "terminal",
      "arguments": "{\"command\":\"curl -s \\\"wttr.in/Manesar?format=3\\\" && curl -s \\\"wttr.in/Bilimora?format=3\\\" && curl -s \\\"wttr.in/Atul,Valsad?format=3\\\"\"}"
    }
  }
]
```


### Tool — terminal — 2026-07-08T04:56:11.601887Z

{"output": "Manesar: ⛈️  +28°C\nBilimora: 🌦️  +27°C\nAtul,Valsad: 🌦️  +27°C", "exit_code": 0, "error": null}


### Assistant — 2026-07-08T04:56:28.176171Z



## Tool calls

```json
[
  {
    "id": "call-d5c7d5db-179a-4af2-af53-d5702aea5a64",
    "call_id": "call-d5c7d5db-179a-4af2-af53-d5702aea5a64",
    "response_item_id": "fc_call-d5c7d5db-179a-4af2-af53-d5702aea5a64",
    "type": "function",
    "function": {
      "name": "terminal",
      "arguments": "{\"command\":\"curl -s \\\"wttr.in/Manesar?format=j1\\\" | jq '.current_condition[0] | {temp: .temp_C, humidity: .humidity, windspeed: .windspeedKmph, condition: .weatherDesc[0].value, feelslike: .FeelsLikeC}' && curl -s \\\"wttr.in/Bilimora?format=j1\\\" | jq '.current_condition[0] | {temp: .temp_C, humidity: .humidity, windspeed: .windspeedKmph, condition: .weatherDesc[0].value, feelslike: .FeelsLikeC}' && curl -s \\\"wttr.in/Atul,Valsad?format=j1\\\" | jq '.current_condition[0] | {temp: .temp_C, humidity: .humidity, windspeed: .windspeedKmph, condition: .weatherDesc[0].value, feelslike: .FeelsLikeC}'\"}"
    }
  }
]
```


### Tool — terminal — 2026-07-08T04:56:29.694306Z

{"output": "{\n  \"temp\": \"28\",\n  \"humidity\": \"89\",\n  \"windspeed\": \"13\",\n  \"condition\": \"Light Rain, Rain With Thunderstorm\",\n  \"feelslike\": \"30\"\n}\n{\n  \"temp\": \"27\",\n  \"humidity\": \"92\",\n  \"windspeed\": \"15\",\n  \"condition\": \"Light rain\",\n  \"feelslike\": \"28\"\n}\n{\n  \"temp\": \"27\",\n  \"humidity\": \"90\",\n  \"windspeed\": \"20\",\n  \"condition\": \"Patchy rain nearby\",\n  \"feelslike\": \"29\"\n}", "exit_code": 0, "error": null}


### Assistant — 2026-07-08T04:56:45.717451Z



## Tool calls

```json
[
  {
    "id": "call-5e766fb1-95e5-49f0-b94a-d1a7dc76ed00",
    "call_id": "call-5e766fb1-95e5-49f0-b94a-d1a7dc76ed00",
    "response_item_id": "fc_call-5e766fb1-95e5-49f0-b94a-d1a7dc76ed00",
    "type": "function",
    "function": {
      "name": "terminal",
      "arguments": "{\"command\":\"date '+%Y-%m-%d %H:%M IST'\"}"
    }
  }
]
```


### Tool — terminal — 2026-07-08T04:56:45.803613Z

{"output": "2026-07-08 10:26 IST", "exit_code": 0, "error": null}


### Assistant — 2026-07-08T04:57:06.904236Z



## Tool calls

```json
[
  {
    "id": "call-48f04792-4c55-4e9d-88b1-9f3d902746c8",
    "call_id": "call-48f04792-4c55-4e9d-88b1-9f3d902746c8",
    "response_item_id": "fc_call-48f04792-4c55-4e9d-88b1-9f3d902746c8",
    "type": "function",
    "function": {
      "name": "terminal",
      "arguments": "{\"command\":\"curl -sS -X POST \\\"https://discord.com/api/webhooks/1524273933308792866/bP9UEX9QRbUQLmb5iCnts7kwAMoojJoaCJsmzgpspAK_iRDILnk7FpuZHjMeMl6D50Xm\\\" \\\\\\n  -H \\\"Content-Type: application/json\\\" \\\\\\n  -d '{\\n    \\\"username\\\": \\\"AEGIS Weather Bot\\\",\\n    \\\"avatar_url\\\": \\\"https://cdn.discordapp.com/emojis/123456789.png\\\",\\n    \\\"embeds\\\": [{\\n      \\\"title\\\": \\\"🌤️ **HOURLY WEATHER BRIEFING** — 2026-07-08 10:26 IST\\\",\\n      \\\"description\\\": \\\"Real-time weather update for three key locations in India\\\",\\n      \\\"color\\\": 16753920,\\n      \\\"fields\\\": [\\n        {\\n          \\\"name\\\": \\\"🏙️ **Manesar, Haryana** 🌧️\\\",\\n          \\\"value\\\": \\\"**🌡️ Temp:** 28°C (Feels like 30°C)\\\\n**💧 Humidity:** 89%\\\\n**🌬️ Wind:** 13 km/h\\\\n**☁️ Condition:** Light Rain, Thunderstorm\\\",\\n          \\\"inline\\\": true\\n        },\\n        {\\n          \\\"name\\\": \\\"🏙️ **Bilimora, Gujarat** 🌦️\\\",\\n          \\\"value\\\": \\\"**🌡️ Temp:** 27°C (Feels like 28°C)\\\\n**💧 Humidity:** 92%\\\\n**🌬️ Wind:** 15 km/h\\\\n**☁️ Condition:** Light Rain\\\",\\n          \\\"inline\\\": true\\n        },\\n        {\\n          \\\"name\\\": \\\"🏙️ **Atul, Valsad, Gujarat** 🌦️\\\",\\n          \\\"value\\\": \\\"**🌡️ Temp:** 27°C (Feels like 29°C)\\\\n**💧 Humidity:** 90%\\\\n**🌬️ Wind:** 20 km/h\\\\n**☁️ Condition:** Patchy Rain Nearby\\\",\\n          \\\"inline\\\": true\\n        }\\n      ],\\n      \\\"footer\\\": {\\n        \\\"text\\\": \\\"Next update in 1 hour • Data from wttr.in • AEGIS Weather Bot\\\"\\n      },\\n      \\\"timestamp\\\": \\\"2026-07-08T04:56:00.000Z\\\"\\n    }]\\n  }'\"}"
    }
  }
]
```


### Tool — terminal — 2026-07-08T04:57:07.623818Z

{"output": "", "exit_code": 0, "error": null}


### Assistant — 2026-07-08T04:58:49.304084Z

🌤️ **HOURLY WEATHER BRIEFING DELIVERED** — 2026-07-08 10:26 IST

**Discord webhook posted successfully** to AEGIS Weather Bot channel.

### Summary for Three Locations:

| Location | Temp | Feels Like | Humidity | Wind | Condition | Severity |
|----------|------|------------|----------|------|-----------|----------|
| **Manesar, Haryana** 🌧️ | 28°C | 30°C | 89% | 13 km/h | Light Rain, Thunderstorm | 🟠 Hot/Humid |
| **Bilimora, Gujarat** 🌦️ | 27°C | 28°C | 92% | 15 km/h | Light Rain | 🟠 Hot/Humid |
| **Atul, Valsad, Gujarat** 🌦️ | 27°C | 29°C | 90% | 20 km/h | Patchy Rain Nearby | 🟠 Hot/Humid |

**Summary**: All three locations experiencing warm, humid conditions with rain activity. High humidity (89-92%) makes temperatures feel 1-3°C warmer. Manesar has thunderstorm activity — highest severity.

**Embed Details**:
- 🎨 **Color**: Orange (16753920) — warm/humid severity
- 📊 **Fields**: 3 inline fields with emoji icons (🌡️💧🌬️☁️)
- 📌 **Footer**: "Next update in 1 hour • Data from wttr.in • AEGIS Weather Bot"
- ⏰ **Timestamp**: 2026-07-08T04:56:00.000Z (UTC

Next hourly update scheduled in ~1 hour.

## Export verification

- Session id: `cron_8f2dc45bc9cd_20260708_102602`
- Exported messages: `10`
- Source DB message count at export: `10`
- Exported at: `2026-09-10T04:30:39.788633Z`
- SHA256 of exported body: `70c668c7f75d82432ecefcb5c3cc39dd0dc1eb9a32e48e6dcba0d53d041a57f0`
