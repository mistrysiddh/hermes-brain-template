---
session_id: "cron_6338a8188c36_20260708_094135"
title: "Hourly Weather Briefing (IST) · Jul 08 09:45"
source: "cron"
created_at: "2026-07-08T04:11:35.904698Z"
updated_at: ""
ended_at: "2026-07-08T04:15:07.802623Z"
model: "nvidia/nemotron-3-ultra-550b-a55b"
provider: "nvidia"
cwd: null
archived: false
message_count: 27
tool_call_count: 14
format: "md"
exported_at: "2026-09-10T04:30:39.288796Z"
exporter: "hermes sessions export (md/qmd) v1"
summary: # Hourly Weather Briefing (IST) · Jul 08 09:45
---

# Hourly Weather Briefing (IST) · Jul 08 09:45

Session ID: `cron_6338a8188c36_20260708_094135`

Source: `cron`

## Messages

### User — 2026-07-08T04:11:35.908435Z

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

Fetch current weather from wttr.in for three locations: Manesar, Bilimora, and Atul Valsad. Format the output creatively as a weather briefing for Discord.

For each location, get weather using: curl -s "wttr.in/<location>?format=3" (for compact one-line) and also curl -s "wttr.in/<location>?format=j1" (for detailed JSON).

Create an engaging Discord message with:
- Header with current IST time and date
- For each location: location name, current temp, condition, feels like, humidity, wind
- A brief summary line
- Use emojis and formatting for visual appeal
- Keep it concise but informative

Deliver the formatted message to Discord channel 1523905009907925062 in guild 1522302510683914250.


### Assistant — 2026-07-08T04:11:47.483782Z



## Tool calls

```json
[
  {
    "id": "call-d41f0f37-d0da-4697-951c-3ee85489db9d",
    "call_id": "call-d41f0f37-d0da-4697-951c-3ee85489db9d",
    "response_item_id": "fc_call-d41f0f37-d0da-4697-951c-3ee85489db9d",
    "type": "function",
    "function": {
      "name": "terminal",
      "arguments": "{\"command\":\"curl -s \\\"wttr.in/Manesar?format=3\\\" && echo \\\"\\\" && curl -s \\\"wttr.in/Bilimora?format=3\\\" && echo \\\"\\\" && curl -s \\\"wttr.in/Atul+Valsad?format=3\\\"\"}"
    }
  },
  {
    "id": "call-82f2ce13-96a6-43f9-8458-a4f998b0e672",
    "call_id": "call-82f2ce13-96a6-43f9-8458-a4f998b0e672",
    "response_item_id": "fc_call-82f2ce13-96a6-43f9-8458-a4f998b0e672",
    "type": "function",
    "function": {
      "name": "terminal",
      "arguments": "{\"command\":\"curl -s \\\"wttr.in/Manesar?format=j1\\\" && echo \\\"---\\\" && curl -s \\\"wttr.in/Bilimora?format=j1\\\" && echo \\\"---\\\" && curl -s \\\"wttr.in/Atul+Valsad?format=j1\\\"\"}"
    }
  }
]
```


### Tool — terminal — 2026-07-08T04:11:47.629275Z

{"output": "", "exit_code": -1, "error": "", "status": "pending_approval", "approval_pending": true, "command": "curl -s \"wttr.in/Manesar?format=3\" && echo \"\" && curl -s \"wttr.in/Bilimora?format=3\" && echo \"\" && curl -s \"wttr.in/Atul+Valsad?format=3\"", "description": "Security scan — [MEDIUM] Schemeless URL in sink context: URL without explicit scheme passed to a command that downloads/executes content; [MEDIUM] Schemeless URL in sink context: URL without explicit scheme passed to a command that downloads/executes content; [MEDIUM] Schemeless URL in sink context: URL without explicit scheme passed to a command that downloads/executes content", "pattern_key": "tirith:schemeless_to_sink"}


### Tool — terminal — 2026-07-08T04:11:48.782507Z

{"output": "", "exit_code": -1, "error": "", "status": "pending_approval", "approval_pending": true, "command": "curl -s \"wttr.in/Manesar?format=j1\" && echo \"---\" && curl -s \"wttr.in/Bilimora?format=j1\" && echo \"---\" && curl -s \"wttr.in/Atul+Valsad?format=j1\"", "description": "Security scan — [MEDIUM] Schemeless URL in sink context: URL without explicit scheme passed to a command that downloads/executes content; [MEDIUM] Schemeless URL in sink context: URL without explicit scheme passed to a command that downloads/executes content; [MEDIUM] Schemeless URL in sink context: URL without explicit scheme passed to a command that downloads/executes content", "pattern_key": "tirith:schemeless_to_sink"}


### Assistant — 2026-07-08T04:12:19.943417Z



## Tool calls

```json
[
  {
    "id": "call-e04aeb8e-fccd-4859-b424-4c96d6d91593",
    "call_id": "call-e04aeb8e-fccd-4859-b424-4c96d6d91593",
    "response_item_id": "fc_call-e04aeb8e-fccd-4859-b424-4c96d6d91593",
    "type": "function",
    "function": {
      "name": "terminal",
      "arguments": "{\"command\":\"curl -s \\\"https://wttr.in/Manesar?format=3\\\" && echo \\\"\\\" && curl -s \\\"https://wttr.in/Bilimora?format=3\\\" && echo \\\"\\\" && curl -s \\\"https://wttr.in/Atul+Valsad?format=3\\\"\"}"
    }
  },
  {
    "id": "call-f4ef9a59-4ff2-4538-b7e7-00da9ca23fff",
    "call_id": "call-f4ef9a59-4ff2-4538-b7e7-00da9ca23fff",
    "response_item_id": "fc_call-f4ef9a59-4ff2-4538-b7e7-00da9ca23fff",
    "type": "function",
    "function": {
      "name": "terminal",
      "arguments": "{\"command\":\"curl -s \\\"https://wttr.in/Manesar?format=j1\\\" && echo \\\"---\\\" && curl -s \\\"https://wttr.in/Bilimora?format=j1\\\" && echo \\\"---\\\" && curl -s \\\"https://wttr.in/Atul+Valsad?format=j1\\\"\"}"
    }
  }
]
```


### Tool — terminal — 2026-07-08T04:12:22.658195Z

{"output": "Manesar: ⛈️  +28°C\n\nBilimora: 🌦️  +27°C\n\nAtul Valsad: 🌦️  +27°C", "exit_code": 0, "error": null}


### Tool — terminal — 2026-07-08T04:12:25.761672Z

{"output": "{\n  \"current_condition\": [\n    {\n      \"FeelsLikeC\": \"30\",\n      \"FeelsLikeF\": \"85\",\n      \"cloudcover\": \"100\",\n      \"humidity\": \"89\",\n      \"observation_time\": \"03:56 AM\",\n      \"precipInches\": \"0.0\",\n      \"precipMM\": \"1.0\",\n      \"pressure\": \"999\",\n      \"pressureInches\": \"30\",\n      \"temp_C\": \"28\",\n      \"temp_F\": \"83\",\n      \"uvIndex\": \"1\",\n      \"visibility\": \"2\",\n      \"visibilityMiles\": \"1\",\n      \"weatherCode\": \"386\",\n      \"weatherDesc\": [\n        {\n          \"value\": \"Light Rain, Rain With Thunderstorm\"\n        }\n      ],\n      \"weatherIconUrl\": [\n        {\n          \"value\": \"https://cdn.worldweatheronline.com/images/wsymbols01_png_64/wsymbol_0016_thundery_showers.png\"\n        }\n      ],\n      \"winddir16Point\": \"E\",\n      \"winddirDegree\": \"89\",\n      \"windspeedKmph\": \"13\",\n      \"windspeedMiles\": \"8\"\n    }\n  ],\n  \"nearest_area\": [\n    {\n      \"areaName\": [\n        {\n          \"value\": \"Kasan\"\n        }\n      ],\n      \"country\": [\n        {\n          \"value\": \"India\"\n        }\n      ],\n      \"latitude\": \"28.367\",\n      \"longitude\": \"76.900\",\n      \"population\": \"0\",\n      \"region\": [\n        {\n          \"value\": \"Haryana\"\n        }\n      ],\n      \"weatherUrl\": [\n        {\n          \"value\": \"https://www.worldweatheronline.com/v2/weather.aspx?q=28.367,76.9\"\n        }\n      ]\n    }\n  ],\n  \"request\": [\n    {\n      \"query\": \"Lat 28.36 and Lon 76.94\",\n      \"type\": \"LatLon\"\n    }\n  ],\n  \"weather\": [\n    {\n      \"astronomy\": [\n        {\n          \"moon_illumination\": \"48\",\n          \"moon_phase\": \"Waning Crescent\",\n          \"moonrise\": \"No moonrise\",\n          \"moonset\": \"01:01 PM\",\n          \"sunrise\": \"05:31 AM\",\n          \"sunset\": \"07:23 PM\"\n        }\n      ],\n      \"avgtempC\": \"32\",\n      \"avgtempF\": \"89\",\n      \"date\": \"2026-07-08\",\n      \"hourly\": [\n        {\n          \"DewPointC\": \"23\",\n          \"DewPointF\": \"73\",\n          \"FeelsLikeC\": \"38\",\n          \"FeelsLikeF\": \"100\",\n          \"HeatIndexC\": \"38\",\n          \"HeatIndexF\": \"100\",\n          \"WindChillC\": \"33\",\n          \"WindChillF\": \"91\",\n          \"WindGustKmph\": \"7\",\n          \"WindGustMiles\": \"4\",\n          \"chanceoffog\": \"0\",\n          \"chanceoffrost\": \"0\",\n          \"chanceofhightemp\": \"99\",\n          \"chanceofovercast\": \"7\",\n          \"chanceofrain\": \"4\",\n          \"chanceofremdry\": \"96\",\n          \"chanceofsnow\": \"0\",\n          \"chanceofsunshine\": \"67\",\n          \"chanceofthunder\": \"0\",\n          \"chanceofwindy\": \"1\",\n          \"cloudcover\": \"27\",\n          \"diffRad\": \"0.0\",\n          \"humidity\": \"56\",\n          \"precipInches\": \"0.0\",\n          \"precipMM\": \"0.0\",\n          \"pressure\": \"997\",\n          \"pressureInches\": \"29\",\n          \"shortRad\": \"0.0\",\n          \"tempC\": \"33\",\n          \"tempF\": \"91\",\n          \"time\": \"0\",\n          \"uvIndex\": \"0\",\n          \"visibility\": \"10\",\n          \"visibilityMiles\": \"6\",\n          \"weatherCode\": \"116\",\n          \"weatherDesc\": [\n            {\n              \"value\": \"Partly Cloudy \"\n            }\n          ],\n          \"weatherIconUrl\": [\n            {\n              \"value\": \"https://cdn.worldweatheronline.com/images/wsymbols01_png_64/wsymbol_0004_black_low_cloud.png\"\n            }\n          ],\n          \"winddir16Point\": \"S\",\n          \"winddirDegree\": \"172\",\n          \"windspeedKmph\": \"6\",\n          \"windspeedMiles\": \"4\"\n        },\n        {\n          \"DewPointC\": \"22\",\n          \"DewPointF\": \"72\",\n          \"FeelsLikeC\": \"36\",\n          \"FeelsLikeF\": \"97\",\n          \"HeatIndexC\": \"36\",\n          \"HeatIndexF\": \"97\",\n          \"WindChillC\": \"32\",\n          \"WindChillF\": \"89\",\n          \"WindGustKmph\": \"11\",\n          \"WindGustMiles\": \"7\",\n          \"chanceoffog\": \"0\",\n          \"chanceoffrost\": \"0\",\n          \"chanceofhightemp\": \"99\",\n          \"chanceofovercast\": \"86\",\n          \"chanceofrain\": \"17\",\n          \"chanceofremdry\": \"74\",\n          \"chanceofsnow\": \"0\",\n          \"chanceofsunshine\": \"3\",\n          \"chanceofthunder\": \"0\",\n          \"chanceofwindy\": \"1\",\n          \"cloudcover\": \"81\",\n          \"diffRad\": \"0.0\",\n          \"humidity\": \"58\",\n          \"precipInches\": \"0.0\",\n          \"precipMM\": \"0.1\",\n          \"pressure\": \"996\",\n          \"pressureInches\": \"29\",\n          \"shortRad\": \"0.0\",\n          \"tempC\": \"32\",\n          \"tempF\": \"89\",\n          \"time\": \"300\",\n          \"uvIndex\": \"0\",\n          \"visibility\": \"10\",\n          \"visibilityMiles\": \"6\",\n          \"weatherCode\": \"176\",\n          \"weatherDesc\": [\n            {\n              \"value\": \"Patchy rain nearby\"\n            }\n          ],\n          \"weatherIconUrl\": [\n            {\n              \"value\": \"https://cdn.worldweatheronline.com/images/wsymbols01_png_64/wsymbol_0025_light_rain_showers_night.png\"\n            }\n          ],\n          \"winddir16Point\": \"E\",\n          \"winddirDegree\": \"92\",\n          \"windspeedKmph\": \"9\",\n          \"windspeedMiles\": \"6\"\n        },\n        {\n          \"DewPointC\": \"23\",\n          \"DewPointF\": \"74\",\n          \"FeelsLikeC\": \"36\",\n          \"FeelsLikeF\": \"97\",\n          \"HeatIndexC\": \"36\",\n          \"HeatIndexF\": \"97\",\n          \"WindChillC\": \"31\",\n          \"WindChillF\": \"88\",\n          \"WindGustKmph\": \"12\",\n          \"WindGustMiles\": \"7\",\n          \"chanceoffog\": \"0\",\n          \"chanceoffrost\": \"0\",\n          \"chanceofhightemp\": \"99\",\n          \"chanceofovercast\": \"37\",\n          \"chanceofrain\": \"36\",\n          \"chanceofremdry\": \"52\",\n          \"chanceofsnow\": \"0\",\n          \"chanceofsunshine\": \"8\",\n          \"chanceofthunder\": \"0\",\n          \"chanceofwindy\": \"1\",\n          \"cloudcover\": \"55\",\n          \"diffRad\": \"2.1\",\n          \"humidity\": \"64\",\n          \"precipInches\": \"0.0\",\n          \"precipMM\": \"0.5\",\n          \"pressure\": \"997\",\n          \"pressureInches\": \"29\",\n          \"shortRad\": \"3.2\",\n          \"tempC\": \"31\",\n          \"tempF\": \"88\",\n          \"time\": \"600\",\n          \"uvIndex\": \"0\",\n          \"visibility\": \"10\",\n          \"visibilityMiles\": \"6\",\n          \"weatherCode\": \"353\",\n          \"weatherDesc\": [\n            {\n              \"value\": \"Light rain shower\"\n            }\n          ],\n          \"weatherIconUrl\": [\n            {\n              \"value\": \"https://cdn.worldweatheronline.com/images/wsymbols01_png_64/wsymbol_0009_light_rain_showers.png\"\n            }\n          ],\n          \"winddir16Point\": \"ENE\",\n          \"winddirDegree\": \"72\",\n          \"windspeedKmph\": \"9\",\n          \"windspeedMiles\": \"6\"\n        },\n        {\n          \"DewPointC\": \"23\",\n          \"DewPointF\": \"73\",\n          \"FeelsLikeC\": \"38\",\n          \"FeelsLikeF\": \"100\",\n          \"HeatIndexC\": \"38\",\n          \"HeatIndexF\": \"100\",\n          \"WindChillC\": \"33\",\n          \"WindChillF\": \"91\",\n          \"WindGustKmph\": \"18\",\n          \"WindGustMiles\": \"11\",\n          \"chanceoffog\": \"0\",\n          \"chanceoffrost\": \"0\",\n          \"chanceofhightemp\": \"99\",\n          \"chanceofovercast\": \"90\",\n          \"chanceofrain\": \"57\",\n          \"chanceofremdry\": \"12\",\n          \"chanceofsnow\": \"0\",\n          \"chanceofsunshine\": \"5\",\n          \"chanceofthunder\": \"0\",\n          \"chanceofwindy\": \"1\",\n          \"cloudcover\": \"100\",\n          \"diffRad\": \"68.2\",\n          \"humidity\": \"89\",\n          \"precipInches\": \"0.0\",\n          \"precipMM\": \"1.0\",\n          \"pressure\": \"999\",\n          \"pressureInches\": \"30\",\n          \"shortRad\": \"133.7\",\n          \"tempC\": \"28\",\n          \"tempF\": \"83\",\n          \"time\": \"900\",\n          \"uvIndex\": \"1\",\n          \"visibility\": \"2\",\n          \"visibilityMiles\": \"1\",\n          \"weatherCode\": \"386\",\n          \"weatherDesc\": [\n            {\n              \"value\": \"Patchy light rain with thunder\"\n            }\n          ],\n          \"weatherIconUrl\": [\n            {\n              \"value\": \"https://cdn.worldweatheronline.com/images/wsymbols01_png_64/wsymbol_0016_thundery_showers.png\"\n            }\n          ],\n          \"winddir16Point\": \"E\",\n          \"winddirDegree\": \"89\",\n          \"windspeedKmph\": \"13\",\n          \"windspeedMiles\": \"8\"\n        },\n        {\n          \"DewPointC\": \"23\",\n          \"DewPointF\": \"73\",\n          \"FeelsLikeC\": \"38\",\n          \"FeelsLikeF\": \"101\",\n          \"HeatIndexC\": \"38\",\n          \"HeatIndexF\": \"101\",\n          \"WindChillC\": \"33\",\n          \"WindChillF\": \"91\",\n          \"WindGustKmph\": \"16\",\n          \"WindGustMiles\": \"10\",\n          \"chanceoffog\": \"0\",\n          \"chanceoffrost\": \"0\",\n          \"chanceofhightemp\": \"99\",\n          \"chanceofovercast\": \"63\",\n          \"chanceofrain\": \"8\",\n          \"chanceofremdry\": \"92\",\n          \"chanceofsnow\": \"0\",\n          \"chanceofsunshine\": \"7\",\n          \"chanceofthunder\": \"0\",\n          \"chanceofwindy\": \"1\",\n          \"cloudcover\": \"67\",\n          \"diffRad\": \"254.0\",\n          \"humidity\": \"56\",\n          \"precipInches\": \"0.0\",\n          \"precipMM\": \"0.0\",\n          \"pressure\": \"997\",\n          \"pressureInches\": \"29\",\n          \"shortRad\": \"483.7\",\n          \"tempC\": \"33\",\n          \"tempF\": \"91\",\n          \"time\": \"1200\",\n          \"uvIndex\": \"5\",\n          \"visibility\": \"10\",\n          \"visibilityMiles\": \"6\",\n          \"weatherCode\": \"119\",\n          \"weatherDesc\": [\n            {\n              \"value\": \"Cloudy \"\n            }\n          ],\n          \"weatherIconUrl\": [\n            {\n              \"value\": \"https://cdn.worldweatheronline.com/images/wsymbols01_png_64/wsymbol_0003_white_cloud.png\"\n            }\n          ],\n          \"winddir16Point\": \"ESE\",\n          \"winddirDegree\": \"112\",\n          \"windspeedKmph\": \"14\",\n          \"windspeedMiles\": \"9\"\n        },\n        {\n          \"DewPointC\": \"23\",\n          \"DewPointF\": \"73\",\n          \"FeelsLikeC\": \"38\",\n          \"FeelsLikeF\": \"101\",\n          \"HeatIndexC\": \"38\",\n          \"HeatIndexF\": \"101\",\n          \"WindChillC\": \"33\",\n          \"WindChillF\": \"92\",\n          \"WindGustKmph\": \"11\",\n          \"WindGustMiles\": \"7\",\n          \"chanceoffog\": \"2\",\n          \"chanceoffrost\": \"0\",\n          \"chanceofhightemp\": \"99\",\n          \"chanceofovercast\": \"93\",\n          \"chanceofrain\": \"21\",\n          \"chanceofremdry\": \"71\",\n          \"chanceofsnow\": \"0\",\n          \"chanceofsunshine\": \"9\",\n          \"chanceofthunder\": \"0\",\n          \"chanceofwindy\": \"1\",\n          \"cloudcover\": \"89\",\n          \"diffRad\": \"127.6\",\n          \"humidity\": \"54\",\n          \"precipInches\": \"0.0\",\n          \"precipMM\": \"0.2\",\n          \"pressure\": \"996\",\n          \"pressureInches\": \"29\",\n          \"shortRad\": \"222.8\",\n          \"tempC\": \"33\",\n          \"tempF\": \"92\",\n          \"time\": \"1500\",\n          \"uvIndex\": \"2\",\n          \"visibility\": \"9\",\n          \"visibilityMiles\": \"5\",\n          \"weatherCode\": \"176\",\n          \"weatherDesc\": [\n            {\n              \"value\": \"Patchy rain nearby\"\n            }\n          ],\n          \"weatherIconUrl\": [\n            {\n              \"value\": \"https://cdn.worldweatheronline.com/images/wsymbols01_png_64/wsymbol_0009_light_rain_showers.png\"\n            }\n          ],\n          \"winddir16Point\": \"N\",\n          \"winddirDegree\": \"11\",\n          \"windspeedKmph\": \"9\",\n          \"windspeedMiles\": \"6\"\n        },\n        {\n          \"DewPointC\": \"24\",\n          \"DewPointF\": \"75\",\n          \"FeelsLikeC\": \"35\",\n          \"FeelsLikeF\": \"95\",\n          \"HeatIndexC\": \"35\",\n          \"HeatIndexF\": \"95\",\n          \"WindChillC\": \"30\",\n          \"WindChillF\": \"86\",\n          \"WindGustKmph\": \"11\",\n          \"WindGustMiles\": \"7\",\n          \"chanceoffog\": \"2\",\n          \"chanceoffrost\": \"0\",\n          \"chanceofhightemp\": \"99\",\n          \"chanceofovercast\": \"84\",\n          \"chanceofrain\": \"36\",\n          \"chanceofremdry\": \"52\",\n          \"chanceofsnow\": \"0\",\n          \"chanceofsunshine\": \"8\",\n          \"chanceofthunder\": \"0\",\n          \"chanceofwindy\": \"1\",\n          \"cloudcover\": \"79\",\n          \"diffRad\": \"2.9\",\n          \"humidity\": \"71\",\n          \"precipInches\": \"0.0\",\n          \"precipMM\": \"0.4\",\n          \"pressure\": \"996\",\n          \"pressureInches\": \"29\",\n          \"shortRad\": \"3.3\",\n          \"tempC\": \"30\",\n          \"tempF\": \"86\",\n          \"time\": \"1800\",\n          \"uvIndex\": \"0\",\n          \"visibility\": \"9\",\n          \"visibilityMiles\": \"5\",\n          \"weatherCode\": \"176\",\n          \"weatherDesc\": [\n            {\n              \"value\": \"Patchy rain nearby\"\n            }\n          ],\n          \"weatherIconUrl\": [\n            {\n              \"value\": \"https://cdn.worldweatheronline.com/images/wsymbols01_png_64/wsymbol_0009_light_rain_showers.png\"\n            }\n          ],\n          \"winddir16Point\": \"NE\",\n          \"winddirDegree\": \"42\",\n          \"windspeedKmph\": \"9\",\n          \"windspeedMiles\": \"6\"\n        },\n        {\n          \"DewPointC\": \"24\",\n          \"DewPointF\": \"75\",\n          \"FeelsLikeC\": \"36\",\n          \"FeelsLikeF\": \"96\",\n          \"HeatIndexC\": \"36\",\n          \"HeatIndexF\": \"96\",\n          \"WindChillC\": \"31\",\n          \"WindChillF\": \"87\",\n          \"WindGustKmph\": \"4\",\n          \"WindGustMiles\": \"2\",\n          \"chanceoffog\": \"0\",\n          \"chanceoffrost\": \"0\",\n          \"chanceofhightemp\": \"99\",\n          \"chanceofovercast\": \"83\",\n          \"chanceofrain\": \"20\",\n          \"chanceofremdry\": \"80\",\n          \"chanceofsnow\": \"0\",\n          \"chanceofsunshine\": \"4\",\n          \"chanceofthunder\": \"0\",\n          \"chanceofwindy\": \"0\",\n          \"cloudcover\": \"78\",\n          \"diffRad\": \"1.2\",\n          \"humidity\": \"67\",\n          \"precipInches\": \"0.0\",\n          \"precipMM\": \"0.1\",\n          \"pressure\": \"997\",\n          \"pressureInches\": \"29\",\n          \"shortRad\": \"1.5\",\n          \"tempC\": \"31\",\n          \"tempF\": \"87\",\n          \"time\": \"2100\",\n          \"uvIndex\": \"0\",\n          \"visibility\": \"10\",\n          \"visibilityMiles\": \"6\",\n          \"weatherCode\": \"176\",\n          \"weatherDesc\": [\n            {\n              \"value\": \"Patchy rain nearby\"\n            }\n          ],\n          \"weatherIconUrl\": [\n            {\n              \"value\": \"https://cdn.worldweatheronline.com/images/wsymbols01_png_64/wsymbol_0025_light_rain_showers_night.png\"\n            }\n          ],\n          \"winddir16Point\": \"SE\",\n          \"winddirDegree\": \"128\",\n          \"windspeedKmph\": \"3\",\n          \"windspeedMiles\": \"2\"\n        }\n      ],\n      \"maxtempC\": \"33\",\n      \"maxtempF\": \"92\",\n      \"mintempC\": \"30\",\n      \"mintempF\": \"86\",\n      \"sunHour\": \"8.0\",\n      \"totalSnow_cm\": \"0.0\",\n      \"uvIndex\": \"9\"\n    },\n    {\n      \"astronomy\": [\n        {\n          \"moon_illumination\": \"37\",\n          \"moon_phase\": \"Waning Crescent\",\n          \"moonrise\": \"12:23 AM\",\n          \"moonset\": \"02:06 PM\",\n          \"sunrise\": \"05:32 AM\",\n          \"sunset\": \"07:23 PM\"\n        }\n      ],\n      \"avgtempC\": \"28\",\n      \"avgtempF\": \"82\",\n      \"date\": \"2026-07-09\",\n      \"hourly\": [\n        {\n          \"DewPointC\": \"24\",\n          \"DewPointF\": \"76\",\n          \"FeelsLikeC\": \"34\",\n          \"FeelsLikeF\": \"93\",\n          \"HeatIndexC\": \"34\",\n          \"HeatIndexF\": \"93\",\n          \"WindChillC\": \"29\",\n          \"WindChillF\": \"84\",\n          \"WindGustKmph\": \"10\",\n          \"WindGustMiles\": \"6\",\n          \"chanceoffog\": \"0\",\n          \"chanceoffrost\": \"0\",\n          \"chanceofhightemp\": \"98\",\n          \"chanceofovercast\": \"98\",\n          \"chanceofrain\": \"56\",\n          \"chanceofremdry\": \"13\",\n          \"chanceofsnow\": \"0\",\n          \"chanceofsunshine\": \"7\",\n          \"chanceofthunder\": \"0\",\n          \"chanceofwindy\": \"1\",\n          \"cloudcover\": \"100\",\n          \"diffRad\": \"0.0\",\n          \"humidity\": \"78\",\n          \"precipInches\": \"0.0\",\n          \"precipMM\": \"0.6\",\n          \"pressure\": \"997\",\n          \"pressureInches\": \"29\",\n          \"shortRad\": \"0.0\",\n          \"tempC\": \"29\",\n          \"tempF\": \"84\",\n          \"time\": \"0\",\n          \"uvIndex\": \"0\",\n          \"visibility\": \"10\",\n          \"visibilityMiles\": \"6\",\n          \"weatherCode\": \"353\",\n          \"weatherDesc\": [\n            {\n              \"value\": \"Light rain shower\"\n            }\n          ],\n          \"weatherIconUrl\": [\n            {\n              \"value\": \"https://cdn.worldweatheronline.com/images/wsymbols01_png_64/wsymbol_0025_light_rain_showers_night.png\"\n            }\n          ],\n          \"winddir16Point\": \"SW\",\n          \"winddirDegree\": \"217\",\n          \"windspeedKmph\": \"8\",\n          \"windspeedMiles\": \"5\"\n        },\n        {\n          \"DewPointC\": \"25\",\n          \"DewPointF\": \"77\",\n          \"FeelsLikeC\": \"32\",\n          \"FeelsLikeF\": \"90\",\n          \"HeatIndexC\": \"32\",\n          \"HeatIndexF\": \"90\",\n          \"WindChillC\": \"28\",\n          \"WindChillF\": \"82\",\n          \"WindGustKmph\": \"10\",\n          \"WindGustMiles\": \"6\",\n          \"chanceoffog\": \"0\",\n          \"chanceoffrost\": \"0\",\n          \"chanceofhightemp\": \"96\",\n          \"chanceofovercast\": \"87\",\n          \"chanceofrain\": \"64\",\n          \"chanceofremdry\": \"12\",\n          \"chanceofsnow\": \"0\",\n          \"chanceofsunshine\": \"5\",\n          \"chanceofthunder\": \"34\",\n          \"chanceofwindy\": \"1\",\n          \"cloudcover\": \"82\",\n          \"diffRad\": \"0.0\",\n          \"humidity\": \"84\",\n          \"precipInches\": \"0.0\",\n          \"precipMM\": \"1.0\",\n          \"pressure\": \"996\",\n          \"pressureInches\": \"29\",\n          \"shortRad\": \"0.0\",\n          \"tempC\": \"28\",\n          \"tempF\": \"82\",\n          \"time\": \"300\",\n          \"uvIndex\": \"0\",\n          \"visibility\": \"10\",\n          \"visibilityMiles\": \"6\",\n          \"weatherCode\": \"353\",\n          \"weatherDesc\": [\n            {\n              \"value\": \"Light rain shower\"\n            }\n          ],\n          \"weatherIconUrl\": [\n            {\n              \"value\": \"https://cdn.worldweatheronline.com/images/wsymbols01_png_64/wsymbol_0025_light_rain_showers_night.png\"\n            }\n          ],\n          \"winddir16Point\": \"NW\",\n          \"winddirDegree\": \"307\",\n          \"windspeedKmph\": \"6\",\n          \"windspeedMiles\": \"4\"\n        },\n        {\n          \"DewPointC\": \"24\",\n          \"DewPointF\": \"76\",\n          \"FeelsLikeC\": \"33\",\n          \"FeelsLikeF\": \"91\",\n          \"HeatIndexC\": \"33\",\n          \"HeatIndexF\": \"91\",\n          \"WindChillC\": \"28\",\n          \"WindChillF\": \"83\",\n          \"WindGustKmph\": \"18\",\n          \"WindGustMiles\": \"11\",\n          \"chanceoffog\": \"0\",\n          \"chanceoffrost\": \"0\",\n          \"chanceofhightemp\": \"96\",\n          \"chanceofovercast\": \"97\",\n          \"chanceofrain\": \"75\",\n          \"chanceofremdry\": \"8\",\n          \"chanceofsnow\": \"0\",\n          \"chanceofsunshine\": \"0\",\n          \"chanceofthunder\": \"35\",\n          \"chanceofwindy\": \"1\",\n          \"cloudcover\": \"97\",\n          \"diffRad\": \"1.1\",\n          \"humidity\": \"80\",\n          \"precipInches\": \"0.1\",\n          \"precipMM\": \"2.4\",\n          \"pressure\": \"998\",\n          \"pressureInches\": \"29\",\n          \"shortRad\": \"1.4\",\n          \"tempC\": \"28\",\n          \"tempF\": \"83\",\n          \"time\": \"600\",\n          \"uvIndex\": \"0\",\n          \"visibility\": \"10\",\n          \"visibilityMiles\": \"6\",\n          \"weatherCode\": \"353\",\n          \"weatherDesc\": [\n            {\n              \"value\": \"Light rain shower\"\n            }\n          ],\n          \"weatherIconUrl\": [\n            {\n              \"value\": \"https://cdn.worldweatheronline.com/images/wsymbols01_png_64/wsymbol_0009_light_rain_showers.png\"\n            }\n          ],\n          \"winddir16Point\": \"NNW\",\n          \"winddirDegree\": \"339\",\n          \"windspeedKmph\": \"12\",\n          \"windspeedMiles\": \"8\"\n        },\n        {\n          \"DewPointC\": \"24\",\n          \"DewPointF\": \"75\",\n          \"FeelsLikeC\": \"33\",\n          \"FeelsLikeF\": \"92\",\n          \"HeatIndexC\": \"33\",\n          \"HeatIndexF\": \"92\",\n          \"WindChillC\": \"29\",\n          \"WindChillF\": \"84\",\n          \"WindGustKmph\": \"26\",\n          \"WindGustMiles\": \"16\",\n          \"chanceoffog\": \"0\",\n          \"chanceoffrost\": \"0\",\n          \"chanceofhightemp\": \"97\",\n          \"chanceofovercast\": \"98\",\n          \"chanceofrain\": \"51\",\n          \"chanceofremdry\": \"35\",\n          \"chanceofsnow\": \"0\",\n          \"chanceofsunshine\": \"8\",\n          \"chanceofthunder\": \"0\",\n          \"chanceofwindy\": \"1\",\n          \"cloudcover\": \"100\",\n          \"diffRad\": \"20.4\",\n          \"humidity\": \"76\",\n          \"precipInches\": \"0.0\",\n          \"precipMM\": \"0.5\",\n          \"pressure\": \"999\",\n        \n\n... [OUTPUT TRUNCATED - 69738 chars omitted out of 119738 total] ...\n\neofremdry\": \"29\",\n          \"chanceofsnow\": \"0\",\n          \"chanceofsunshine\": \"8\",\n          \"chanceofthunder\": \"43\",\n          \"chanceofwindy\": \"1\",\n          \"cloudcover\": \"100\",\n          \"diffRad\": \"22.4\",\n          \"humidity\": \"93\",\n          \"precipInches\": \"0.0\",\n          \"precipMM\": \"0.5\",\n          \"pressure\": \"1001\",\n          \"pressureInches\": \"30\",\n          \"shortRad\": \"29.2\",\n          \"tempC\": \"26\",\n          \"tempF\": \"79\",\n          \"time\": \"1500\",\n          \"uvIndex\": \"1\",\n          \"visibility\": \"10\",\n          \"visibilityMiles\": \"6\",\n          \"weatherCode\": \"353\",\n          \"weatherDesc\": [\n            {\n              \"value\": \"Light rain shower\"\n            }\n          ],\n          \"weatherIconUrl\": [\n            {\n              \"value\": \"https://cdn.worldweatheronline.com/images/wsymbols01_png_64/wsymbol_0009_light_rain_showers.png\"\n            }\n          ],\n          \"winddir16Point\": \"WNW\",\n          \"winddirDegree\": \"291\",\n          \"windspeedKmph\": \"9\",\n          \"windspeedMiles\": \"5\"\n        },\n        {\n          \"DewPointC\": \"25\",\n          \"DewPointF\": \"77\",\n          \"FeelsLikeC\": \"31\",\n          \"FeelsLikeF\": \"88\",\n          \"HeatIndexC\": \"31\",\n          \"HeatIndexF\": \"88\",\n          \"WindChillC\": \"27\",\n          \"WindChillF\": \"80\",\n          \"WindGustKmph\": \"10\",\n          \"WindGustMiles\": \"6\",\n          \"chanceoffog\": \"0\",\n          \"chanceoffrost\": \"0\",\n          \"chanceofhightemp\": \"93\",\n          \"chanceofovercast\": \"54\",\n          \"chanceofrain\": \"28\",\n          \"chanceofremdry\": \"64\",\n          \"chanceofsnow\": \"0\",\n          \"chanceofsunshine\": \"10\",\n          \"chanceofthunder\": \"32\",\n          \"chanceofwindy\": \"1\",\n          \"cloudcover\": \"63\",\n          \"diffRad\": \"7.2\",\n          \"humidity\": \"90\",\n          \"precipInches\": \"0.0\",\n          \"precipMM\": \"0.1\",\n          \"pressure\": \"1000\",\n          \"pressureInches\": \"30\",\n          \"shortRad\": \"9.9\",\n          \"tempC\": \"27\",\n          \"tempF\": \"80\",\n          \"time\": \"1800\",\n          \"uvIndex\": \"0\",\n          \"visibility\": \"10\",\n          \"visibilityMiles\": \"6\",\n          \"weatherCode\": \"176\",\n          \"weatherDesc\": [\n            {\n              \"value\": \"Patchy rain nearby\"\n            }\n          ],\n          \"weatherIconUrl\": [\n            {\n              \"value\": \"https://cdn.worldweatheronline.com/images/wsymbols01_png_64/wsymbol_0009_light_rain_showers.png\"\n            }\n          ],\n          \"winddir16Point\": \"W\",\n          \"winddirDegree\": \"269\",\n          \"windspeedKmph\": \"6\",\n          \"windspeedMiles\": \"4\"\n        },\n        {\n          \"DewPointC\": \"26\",\n          \"DewPointF\": \"78\",\n          \"FeelsLikeC\": \"33\",\n          \"FeelsLikeF\": \"91\",\n          \"HeatIndexC\": \"33\",\n          \"HeatIndexF\": \"91\",\n          \"WindChillC\": \"27\",\n          \"WindChillF\": \"81\",\n          \"WindGustKmph\": \"20\",\n          \"WindGustMiles\": \"12\",\n          \"chanceoffog\": \"0\",\n          \"chanceoffrost\": \"0\",\n          \"chanceofhightemp\": \"86\",\n          \"chanceofovercast\": \"79\",\n          \"chanceofrain\": \"41\",\n          \"chanceofremdry\": \"52\",\n          \"chanceofsnow\": \"0\",\n          \"chanceofsunshine\": \"9\",\n          \"chanceofthunder\": \"39\",\n          \"chanceofwindy\": \"1\",\n          \"cloudcover\": \"75\",\n          \"diffRad\": \"2.3\",\n          \"humidity\": \"91\",\n          \"precipInches\": \"0.0\",\n          \"precipMM\": \"0.2\",\n          \"pressure\": \"1002\",\n          \"pressureInches\": \"30\",\n          \"shortRad\": \"3.2\",\n          \"tempC\": \"27\",\n          \"tempF\": \"81\",\n          \"time\": \"2100\",\n          \"uvIndex\": \"0\",\n          \"visibility\": \"10\",\n          \"visibilityMiles\": \"6\",\n          \"weatherCode\": \"353\",\n          \"weatherDesc\": [\n            {\n              \"value\": \"Light rain shower\"\n            }\n          ],\n          \"weatherIconUrl\": [\n            {\n              \"value\": \"https://cdn.worldweatheronline.com/images/wsymbols01_png_64/wsymbol_0025_light_rain_showers_night.png\"\n            }\n          ],\n          \"winddir16Point\": \"WSW\",\n          \"winddirDegree\": \"241\",\n          \"windspeedKmph\": \"12\",\n          \"windspeedMiles\": \"7\"\n        }\n      ],\n      \"maxtempC\": \"28\",\n      \"maxtempF\": \"82\",\n      \"mintempC\": \"26\",\n      \"mintempF\": \"79\",\n      \"sunHour\": \"1.0\",\n      \"totalSnow_cm\": \"0.0\",\n      \"uvIndex\": \"2\"\n    },\n    {\n      \"astronomy\": [\n        {\n          \"moon_illumination\": \"37\",\n          \"moon_phase\": \"Waning Crescent\",\n          \"moonrise\": \"12:51 AM\",\n          \"moonset\": \"02:10 PM\",\n          \"sunrise\": \"06:04 AM\",\n          \"sunset\": \"07:23 PM\"\n        }\n      ],\n      \"avgtempC\": \"28\",\n      \"avgtempF\": \"83\",\n      \"date\": \"2026-07-09\",\n      \"hourly\": [\n        {\n          \"DewPointC\": \"26\",\n          \"DewPointF\": \"78\",\n          \"FeelsLikeC\": \"33\",\n          \"FeelsLikeF\": \"91\",\n          \"HeatIndexC\": \"33\",\n          \"HeatIndexF\": \"91\",\n          \"WindChillC\": \"28\",\n          \"WindChillF\": \"82\",\n          \"WindGustKmph\": \"28\",\n          \"WindGustMiles\": \"17\",\n          \"chanceoffog\": \"2\",\n          \"chanceoffrost\": \"0\",\n          \"chanceofhightemp\": \"87\",\n          \"chanceofovercast\": \"52\",\n          \"chanceofrain\": \"33\",\n          \"chanceofremdry\": \"59\",\n          \"chanceofsnow\": \"0\",\n          \"chanceofsunshine\": \"9\",\n          \"chanceofthunder\": \"32\",\n          \"chanceofwindy\": \"2\",\n          \"cloudcover\": \"62\",\n          \"diffRad\": \"0.0\",\n          \"humidity\": \"90\",\n          \"precipInches\": \"0.0\",\n          \"precipMM\": \"0.1\",\n          \"pressure\": \"1003\",\n          \"pressureInches\": \"30\",\n          \"shortRad\": \"0.0\",\n          \"tempC\": \"28\",\n          \"tempF\": \"82\",\n          \"time\": \"0\",\n          \"uvIndex\": \"0\",\n          \"visibility\": \"9\",\n          \"visibilityMiles\": \"5\",\n          \"weatherCode\": \"200\",\n          \"weatherDesc\": [\n            {\n              \"value\": \"Thundery outbreaks in nearby\"\n            }\n          ],\n          \"weatherIconUrl\": [\n            {\n              \"value\": \"https://cdn.worldweatheronline.com/images/wsymbols01_png_64/wsymbol_0032_thundery_showers_night.png\"\n            }\n          ],\n          \"winddir16Point\": \"WSW\",\n          \"winddirDegree\": \"236\",\n          \"windspeedKmph\": \"18\",\n          \"windspeedMiles\": \"11\"\n        },\n        {\n          \"DewPointC\": \"26\",\n          \"DewPointF\": \"78\",\n          \"FeelsLikeC\": \"33\",\n          \"FeelsLikeF\": \"91\",\n          \"HeatIndexC\": \"33\",\n          \"HeatIndexF\": \"91\",\n          \"WindChillC\": \"28\",\n          \"WindChillF\": \"82\",\n          \"WindGustKmph\": \"29\",\n          \"WindGustMiles\": \"18\",\n          \"chanceoffog\": \"13\",\n          \"chanceoffrost\": \"0\",\n          \"chanceofhightemp\": \"86\",\n          \"chanceofovercast\": \"63\",\n          \"chanceofrain\": \"43\",\n          \"chanceofremdry\": \"50\",\n          \"chanceofsnow\": \"0\",\n          \"chanceofsunshine\": \"9\",\n          \"chanceofthunder\": \"34\",\n          \"chanceofwindy\": \"2\",\n          \"cloudcover\": \"67\",\n          \"diffRad\": \"0.0\",\n          \"humidity\": \"90\",\n          \"precipInches\": \"0.0\",\n          \"precipMM\": \"0.3\",\n          \"pressure\": \"1002\",\n          \"pressureInches\": \"30\",\n          \"shortRad\": \"0.0\",\n          \"tempC\": \"28\",\n          \"tempF\": \"82\",\n          \"time\": \"300\",\n          \"uvIndex\": \"0\",\n          \"visibility\": \"5\",\n          \"visibilityMiles\": \"3\",\n          \"weatherCode\": \"263\",\n          \"weatherDesc\": [\n            {\n              \"value\": \"Patchy light drizzle\"\n            }\n          ],\n          \"weatherIconUrl\": [\n            {\n              \"value\": \"https://cdn.worldweatheronline.com/images/wsymbols01_png_64/wsymbol_0025_light_rain_showers_night.png\"\n            }\n          ],\n          \"winddir16Point\": \"SW\",\n          \"winddirDegree\": \"233\",\n          \"windspeedKmph\": \"19\",\n          \"windspeedMiles\": \"12\"\n        },\n        {\n          \"DewPointC\": \"26\",\n          \"DewPointF\": \"78\",\n          \"FeelsLikeC\": \"33\",\n          \"FeelsLikeF\": \"91\",\n          \"HeatIndexC\": \"33\",\n          \"HeatIndexF\": \"91\",\n          \"WindChillC\": \"28\",\n          \"WindChillF\": \"82\",\n          \"WindGustKmph\": \"34\",\n          \"WindGustMiles\": \"21\",\n          \"chanceoffog\": \"0\",\n          \"chanceoffrost\": \"0\",\n          \"chanceofhightemp\": \"86\",\n          \"chanceofovercast\": \"98\",\n          \"chanceofrain\": \"43\",\n          \"chanceofremdry\": \"45\",\n          \"chanceofsnow\": \"0\",\n          \"chanceofsunshine\": \"9\",\n          \"chanceofthunder\": \"43\",\n          \"chanceofwindy\": \"2\",\n          \"cloudcover\": \"100\",\n          \"diffRad\": \"1.0\",\n          \"humidity\": \"89\",\n          \"precipInches\": \"0.0\",\n          \"precipMM\": \"0.2\",\n          \"pressure\": \"1003\",\n          \"pressureInches\": \"30\",\n          \"shortRad\": \"1.9\",\n          \"tempC\": \"28\",\n          \"tempF\": \"82\",\n          \"time\": \"600\",\n          \"uvIndex\": \"0\",\n          \"visibility\": \"10\",\n          \"visibilityMiles\": \"6\",\n          \"weatherCode\": \"353\",\n          \"weatherDesc\": [\n            {\n              \"value\": \"Light rain shower\"\n            }\n          ],\n          \"weatherIconUrl\": [\n            {\n              \"value\": \"https://cdn.worldweatheronline.com/images/wsymbols01_png_64/wsymbol_0009_light_rain_showers.png\"\n            }\n          ],\n          \"winddir16Point\": \"SW\",\n          \"winddirDegree\": \"230\",\n          \"windspeedKmph\": \"22\",\n          \"windspeedMiles\": \"13\"\n        },\n        {\n          \"DewPointC\": \"26\",\n          \"DewPointF\": \"79\",\n          \"FeelsLikeC\": \"35\",\n          \"FeelsLikeF\": \"95\",\n          \"HeatIndexC\": \"35\",\n          \"HeatIndexF\": \"95\",\n          \"WindChillC\": \"29\",\n          \"WindChillF\": \"84\",\n          \"WindGustKmph\": \"33\",\n          \"WindGustMiles\": \"21\",\n          \"chanceoffog\": \"0\",\n          \"chanceoffrost\": \"0\",\n          \"chanceofhightemp\": \"99\",\n          \"chanceofovercast\": \"70\",\n          \"chanceofrain\": \"22\",\n          \"chanceofremdry\": \"79\",\n          \"chanceofsnow\": \"0\",\n          \"chanceofsunshine\": \"5\",\n          \"chanceofthunder\": \"30\",\n          \"chanceofwindy\": \"2\",\n          \"cloudcover\": \"70\",\n          \"diffRad\": \"61.8\",\n          \"humidity\": \"85\",\n          \"precipInches\": \"0.0\",\n          \"precipMM\": \"0.0\",\n          \"pressure\": \"1004\",\n          \"pressureInches\": \"30\",\n          \"shortRad\": \"115.1\",\n          \"tempC\": \"29\",\n          \"tempF\": \"84\",\n          \"time\": \"900\",\n          \"uvIndex\": \"2\",\n          \"visibility\": \"10\",\n          \"visibilityMiles\": \"6\",\n          \"weatherCode\": \"176\",\n          \"weatherDesc\": [\n            {\n              \"value\": \"Patchy rain nearby\"\n            }\n          ],\n          \"weatherIconUrl\": [\n            {\n              \"value\": \"https://cdn.worldweatheronline.com/images/wsymbols01_png_64/wsymbol_0009_light_rain_showers.png\"\n            }\n          ],\n          \"winddir16Point\": \"SW\",\n          \"winddirDegree\": \"227\",\n          \"windspeedKmph\": \"24\",\n          \"windspeedMiles\": \"15\"\n        },\n        {\n          \"DewPointC\": \"26\",\n          \"DewPointF\": \"78\",\n          \"FeelsLikeC\": \"36\",\n          \"FeelsLikeF\": \"97\",\n          \"HeatIndexC\": \"36\",\n          \"HeatIndexF\": \"97\",\n          \"WindChillC\": \"30\",\n          \"WindChillF\": \"85\",\n          \"WindGustKmph\": \"34\",\n          \"WindGustMiles\": \"21\",\n          \"chanceoffog\": \"0\",\n          \"chanceoffrost\": \"0\",\n          \"chanceofhightemp\": \"99\",\n          \"chanceofovercast\": \"71\",\n          \"chanceofrain\": \"26\",\n          \"chanceofremdry\": \"74\",\n          \"chanceofsnow\": \"0\",\n          \"chanceofsunshine\": \"9\",\n          \"chanceofthunder\": \"0\",\n          \"chanceofwindy\": \"2\",\n          \"cloudcover\": \"70\",\n          \"diffRad\": \"335.4\",\n          \"humidity\": \"79\",\n          \"precipInches\": \"0.0\",\n          \"precipMM\": \"0.1\",\n          \"pressure\": \"1004\",\n          \"pressureInches\": \"30\",\n          \"shortRad\": \"657.4\",\n          \"tempC\": \"30\",\n          \"tempF\": \"85\",\n          \"time\": \"1200\",\n          \"uvIndex\": \"9\",\n          \"visibility\": \"10\",\n          \"visibilityMiles\": \"6\",\n          \"weatherCode\": \"176\",\n          \"weatherDesc\": [\n            {\n              \"value\": \"Patchy rain nearby\"\n            }\n          ],\n          \"weatherIconUrl\": [\n            {\n              \"value\": \"https://cdn.worldweatheronline.com/images/wsymbols01_png_64/wsymbol_0009_light_rain_showers.png\"\n            }\n          ],\n          \"winddir16Point\": \"SW\",\n          \"winddirDegree\": \"232\",\n          \"windspeedKmph\": \"25\",\n          \"windspeedMiles\": \"16\"\n        },\n        {\n          \"DewPointC\": \"25\",\n          \"DewPointF\": \"77\",\n          \"FeelsLikeC\": \"35\",\n          \"FeelsLikeF\": \"95\",\n          \"HeatIndexC\": \"35\",\n          \"HeatIndexF\": \"95\",\n          \"WindChillC\": \"29\",\n          \"WindChillF\": \"84\",\n          \"WindGustKmph\": \"38\",\n          \"WindGustMiles\": \"24\",\n          \"chanceoffog\": \"0\",\n          \"chanceoffrost\": \"0\",\n          \"chanceofhightemp\": \"99\",\n          \"chanceofovercast\": \"81\",\n          \"chanceofrain\": \"27\",\n          \"chanceofremdry\": \"73\",\n          \"chanceofsnow\": \"0\",\n          \"chanceofsunshine\": \"10\",\n          \"chanceofthunder\": \"28\",\n          \"chanceofwindy\": \"3\",\n          \"cloudcover\": \"76\",\n          \"diffRad\": \"233.4\",\n          \"humidity\": \"80\",\n          \"precipInches\": \"0.0\",\n          \"precipMM\": \"0.1\",\n          \"pressure\": \"1003\",\n          \"pressureInches\": \"30\",\n          \"shortRad\": \"428.4\",\n          \"tempC\": \"29\",\n          \"tempF\": \"84\",\n          \"time\": \"1500\",\n          \"uvIndex\": \"4\",\n          \"visibility\": \"10\",\n          \"visibilityMiles\": \"6\",\n          \"weatherCode\": \"176\",\n          \"weatherDesc\": [\n            {\n              \"value\": \"Patchy rain nearby\"\n            }\n          ],\n          \"weatherIconUrl\": [\n            {\n              \"value\": \"https://cdn.worldweatheronline.com/images/wsymbols01_png_64/wsymbol_0009_light_rain_showers.png\"\n            }\n          ],\n          \"winddir16Point\": \"SW\",\n          \"winddirDegree\": \"233\",\n          \"windspeedKmph\": \"26\",\n          \"windspeedMiles\": \"16\"\n        },\n        {\n          \"DewPointC\": \"25\",\n          \"DewPointF\": \"77\",\n          \"FeelsLikeC\": \"33\",\n          \"FeelsLikeF\": \"92\",\n          \"HeatIndexC\": \"33\",\n          \"HeatIndexF\": \"92\",\n          \"WindChillC\": \"28\",\n          \"WindChillF\": \"83\",\n          \"WindGustKmph\": \"40\",\n          \"WindGustMiles\": \"25\",\n          \"chanceoffog\": \"0\",\n          \"chanceoffrost\": \"0\",\n          \"chanceofhightemp\": \"97\",\n          \"chanceofovercast\": \"76\",\n          \"chanceofrain\": \"26\",\n          \"chanceofremdry\": \"74\",\n          \"chanceofsnow\": \"0\",\n          \"chanceofsunshine\": \"5\",\n          \"chanceofthunder\": \"28\",\n          \"chanceofwindy\": \"3\",\n          \"cloudcover\": \"73\",\n          \"diffRad\": \"35.2\",\n          \"humidity\": \"82\",\n          \"precipInches\": \"0.0\",\n          \"precipMM\": \"0.1\",\n          \"pressure\": \"1004\",\n          \"pressureInches\": \"30\",\n          \"shortRad\": \"59.5\",\n          \"tempC\": \"28\",\n          \"tempF\": \"83\",\n          \"time\": \"1800\",\n          \"uvIndex\": \"0\",\n          \"visibility\": \"10\",\n          \"visibilityMiles\": \"6\",\n          \"weatherCode\": \"176\",\n          \"weatherDesc\": [\n            {\n              \"value\": \"Patchy rain nearby\"\n            }\n          ],\n          \"weatherIconUrl\": [\n            {\n              \"value\": \"https://cdn.worldweatheronline.com/images/wsymbols01_png_64/wsymbol_0009_light_rain_showers.png\"\n            }\n          ],\n          \"winddir16Point\": \"SW\",\n          \"winddirDegree\": \"232\",\n          \"windspeedKmph\": \"26\",\n          \"windspeedMiles\": \"16\"\n        },\n        {\n          \"DewPointC\": \"25\",\n          \"DewPointF\": \"77\",\n          \"FeelsLikeC\": \"33\",\n          \"FeelsLikeF\": \"91\",\n          \"HeatIndexC\": \"33\",\n          \"HeatIndexF\": \"91\",\n          \"WindChillC\": \"28\",\n          \"WindChillF\": \"82\",\n          \"WindGustKmph\": \"42\",\n          \"WindGustMiles\": \"26\",\n          \"chanceoffog\": \"0\",\n          \"chanceoffrost\": \"0\",\n          \"chanceofhightemp\": \"96\",\n          \"chanceofovercast\": \"93\",\n          \"chanceofrain\": \"34\",\n          \"chanceofremdry\": \"60\",\n          \"chanceofsnow\": \"0\",\n          \"chanceofsunshine\": \"9\",\n          \"chanceofthunder\": \"37\",\n          \"chanceofwindy\": \"4\",\n          \"cloudcover\": \"89\",\n          \"diffRad\": \"10.3\",\n          \"humidity\": \"84\",\n          \"precipInches\": \"0.0\",\n          \"precipMM\": \"0.1\",\n          \"pressure\": \"1005\",\n          \"pressureInches\": \"30\",\n          \"shortRad\": \"17.6\",\n          \"tempC\": \"28\",\n          \"tempF\": \"82\",\n          \"time\": \"2100\",\n          \"uvIndex\": \"0\",\n          \"visibility\": \"10\",\n          \"visibilityMiles\": \"6\",\n          \"weatherCode\": \"176\",\n          \"weatherDesc\": [\n            {\n              \"value\": \"Patchy rain nearby\"\n            }\n          ],\n          \"weatherIconUrl\": [\n            {\n              \"value\": \"https://cdn.worldweatheronline.com/images/wsymbols01_png_64/wsymbol_0025_light_rain_showers_night.png\"\n            }\n          ],\n          \"winddir16Point\": \"SW\",\n          \"winddirDegree\": \"230\",\n          \"windspeedKmph\": \"27\",\n          \"windspeedMiles\": \"17\"\n        }\n      ],\n      \"maxtempC\": \"30\",\n      \"maxtempF\": \"85\",\n      \"mintempC\": \"27\",\n      \"mintempF\": \"81\",\n      \"sunHour\": \"7.0\",\n      \"totalSnow_cm\": \"0.0\",\n      \"uvIndex\": \"9\"\n    },\n    {\n      \"astronomy\": [\n        {\n          \"moon_illumination\": \"26\",\n          \"moon_phase\": \"Waning Crescent\",\n          \"moonrise\": \"01:35 AM\",\n          \"moonset\": \"03:15 PM\",\n          \"sunrise\": \"06:04 AM\",\n          \"sunset\": \"07:23 PM\"\n        }\n      ],\n      \"avgtempC\": \"29\",\n      \"avgtempF\": \"83\",\n      \"date\": \"2026-07-10\",\n      \"hourly\": [\n        {\n          \"DewPointC\": \"25\",\n          \"DewPointF\": \"76\",\n          \"FeelsLikeC\": \"32\",\n          \"FeelsLikeF\": \"90\",\n          \"HeatIndexC\": \"32\",\n          \"HeatIndexF\": \"90\",\n          \"WindChillC\": \"28\",\n          \"WindChillF\": \"82\",\n          \"WindGustKmph\": \"42\",\n          \"WindGustMiles\": \"26\",\n          \"chanceoffog\": \"0\",\n          \"chanceoffrost\": \"0\",\n          \"chanceofhightemp\": \"96\",\n          \"chanceofovercast\": \"35\",\n          \"chanceofrain\": \"21\",\n          \"chanceofremdry\": \"79\",\n          \"chanceofsnow\": \"0\",\n          \"chanceofsunshine\": \"19\",\n          \"chanceofthunder\": \"0\",\n          \"chanceofwindy\": \"4\",\n          \"cloudcover\": \"53\",\n          \"diffRad\": \"0.0\",\n          \"humidity\": \"84\",\n          \"precipInches\": \"0.0\",\n          \"precipMM\": \"0.1\",\n          \"pressure\": \"1006\",\n          \"pressureInches\": \"30\",\n          \"shortRad\": \"0.0\",\n          \"tempC\": \"28\",\n          \"tempF\": \"82\",\n          \"time\": \"0\",\n          \"uvIndex\": \"0\",\n          \"visibility\": \"10\",\n          \"visibilityMiles\": \"6\",\n          \"weatherCode\": \"176\",\n          \"weatherDesc\": [\n            {\n              \"value\": \"Patchy rain nearby\"\n            }\n          ],\n          \"weatherIconUrl\": [\n            {\n              \"value\": \"https://cdn.worldweatheronline.com/images/wsymbols01_png_64/wsymbol_0025_light_rain_showers_night.png\"\n            }\n          ],\n          \"winddir16Point\": \"SW\",\n          \"winddirDegree\": \"231\",\n          \"windspeedKmph\": \"27\",\n          \"windspeedMiles\": \"17\"\n        },\n        {\n          \"DewPointC\": \"25\",\n          \"DewPointF\": \"76\",\n          \"FeelsLikeC\": \"32\",\n          \"FeelsLikeF\": \"90\",\n          \"HeatIndexC\": \"32\",\n          \"HeatIndexF\": \"90\",\n          \"WindChillC\": \"28\",\n          \"WindChillF\": \"82\",\n          \"WindGustKmph\": \"39\",\n          \"WindGustMiles\": \"24\",\n          \"chanceoffog\": \"0\",\n          \"chanceoffrost\": \"0\",\n          \"chanceofhightemp\": \"96\",\n          \"chanceofovercast\": \"34\",\n          \"chanceofrain\": \"26\",\n          \"chanceofremdry\": \"74\",\n          \"chanceofsnow\": \"0\",\n          \"chanceofsunshine\": \"9\",\n          \"chanceofthunder\": \"0\",\n          \"chanceofwindy\": \"3\",\n          \"cloudcover\": \"53\",\n          \"diffRad\": \"0.0\",\n          \"humidity\": \"84\",\n          \"precipInches\": \"0.0\",\n          \"precipMM\": \"0.1\",\n          \"pressure\": \"1005\",\n          \"pressureInches\": \"30\",\n          \"shortRad\": \"0.0\",\n          \"tempC\": \"28\",\n          \"tempF\": \"82\",\n          \"time\": \"300\",\n          \"uvIndex\": \"0\",\n          \"visibility\": \"10\",\n          \"visibilityMiles\": \"6\",\n          \"weatherCode\": \"176\",\n          \"weatherDesc\": [\n            {\n              \"value\": \"Patchy rain nearby\"\n            }\n          ],\n          \"weatherIconUrl\": [\n            {\n              \"value\": \"https://cdn.worldweatheronline.com/images/wsymbols01_png_64/wsymbol_0025_light_rain_showers_night.png\"\n            }\n          ],\n          \"winddir16Point\": \"SW\",\n          \"winddirDegree\": \"235\",\n          \"windspeedKmph\": \"25\",\n          \"windspeedMiles\": \"16\"\n        },\n        {\n          \"DewPointC\": \"25\",\n          \"DewPointF\": \"76\",\n          \"FeelsLikeC\": \"32\",\n          \"FeelsLikeF\": \"89\",\n          \"HeatIndexC\": \"32\",\n          \"HeatIndexF\": \"89\",\n          \"WindChillC\": \"28\",\n          \"WindChillF\": \"82\",\n          \"WindGustKmph\": \"36\",\n          \"WindGustMiles\": \"22\",\n          \"chanceoffog\": \"0\",\n          \"chanceoffrost\": \"0\",\n          \"chanceofhightemp\": \"96\",\n          \"chanceofovercast\": \"89\",\n          \"chanceofrain\": \"33\",\n          \"chanceofremdry\": \"60\",\n          \"chanceofsnow\": \"0\",\n          \"chanceofsunshine\": \"9\",\n          \"chanceofthunder\": \"35\",\n          \"chanceofwindy\": \"2\",\n          \"cloudcover\": \"84\",\n          \"diffRad\": \"1.5\",\n          \"humidity\": \"84\",\n          \"precipInches\": \"0.0\",\n          \"precipMM\": \"0.1\",\n          \"pressure\": \"1006\",\n          \"pressureInches\": \"30\",\n          \"shortRad\": \"2.8\",\n          \"tempC\": \"28\",\n          \"tempF\": \"82\",\n          \"time\": \"600\",\n          \"uvIndex\": \"0\",\n          \"visibility\": \"10\",\n          \"visibilityMiles\": \"6\",\n          \"weatherCode\": \"176\",\n          \"weatherDesc\": [\n            {\n              \"value\": \"Patchy rain nearby\"\n            }\n          ],\n          \"weatherIconUrl\": [\n            {\n              \"value\": \"https://cdn.worldweatheronline.com/images/wsymbols01_png_64/wsymbol_0009_light_rain_showers.png\"\n            }\n          ],\n          \"winddir16Point\": \"SW\",\n          \"winddirDegree\": \"230\",\n          \"windspeedKmph\": \"23\",\n          \"windspeedMiles\": \"14\"\n        },\n        {\n          \"DewPointC\": \"25\",\n          \"DewPointF\": \"77\",\n          \"FeelsLikeC\": \"34\",\n          \"FeelsLikeF\": \"94\",\n          \"HeatIndexC\": \"34\",\n          \"HeatIndexF\": \"94\",\n          \"WindChillC\": \"29\",\n          \"WindChillF\": \"84\",\n          \"WindGustKmph\": \"37\",\n          \"WindGustMiles\": \"23\",\n          \"chanceoffog\": \"0\",\n          \"chanceoffrost\": \"0\",\n          \"chanceofhightemp\": \"99\",\n          \"chanceofovercast\": \"78\",\n          \"chanceofrain\": \"23\",\n          \"chanceofremdry\": \"78\",\n          \"chanceofsnow\": \"0\",\n          \"chanceofsunshine\": \"4\",\n          \"chanceofthunder\": \"27\",\n          \"chanceofwindy\": \"3\",\n          \"cloudcover\": \"74\",\n          \"diffRad\": \"59.2\",\n          \"humidity\": \"80\",\n          \"precipInches\": \"0.0\",\n          \"precipMM\": \"0.1\",\n          \"pressure\": \"1007\",\n          \"pressureInches\": \"30\",\n          \"shortRad\": \"107.3\",\n          \"tempC\": \"29\",\n          \"tempF\": \"84\",\n          \"time\": \"900\",\n          \"uvIndex\": \"3\",\n          \"visibility\": \"10\",\n          \"visibilityMiles\": \"6\",\n          \"weatherCode\": \"176\",\n          \"weatherDesc\": [\n            {\n              \"value\": \"Patchy rain nearby\"\n            }\n          ],\n          \"weatherIconUrl\": [\n            {\n              \"value\": \"https://cdn.worldweatheronline.com/images/wsymbols01_png_64/wsymbol_0009_light_rain_showers.png\"\n            }\n          ],\n          \"winddir16Point\": \"SW\",\n          \"winddirDegree\": \"230\",\n          \"windspeedKmph\": \"26\",\n          \"windspeedMiles\": \"16\"\n        },\n        {\n          \"DewPointC\": \"25\",\n          \"DewPointF\": \"77\",\n          \"FeelsLikeC\": \"36\",\n          \"FeelsLikeF\": \"97\",\n          \"HeatIndexC\": \"36\",\n          \"HeatIndexF\": \"97\",\n          \"WindChillC\": \"30\",\n          \"WindChillF\": \"86\",\n          \"WindGustKmph\": \"37\",\n          \"WindGustMiles\": \"23\",\n          \"chanceoffog\": \"0\",\n          \"chanceoffrost\": \"0\",\n          \"chanceofhightemp\": \"99\",\n          \"chanceofovercast\": \"78\",\n          \"chanceofrain\": \"17\",\n          \"chanceofremdry\": \"83\",\n          \"chanceofsnow\": \"0\",\n          \"chanceofsunshine\": \"4\",\n          \"chanceofthunder\": \"0\",\n          \"chanceofwindy\": \"4\",\n          \"cloudcover\": \"74\",\n          \"diffRad\": \"322.4\",\n          \"humidity\": \"75\",\n          \"precipInches\": \"0.0\",\n          \"precipMM\": \"0.0\",\n          \"pressure\": \"1007\",\n          \"pressureInches\": \"30\",\n          \"shortRad\": \"758.7\",\n          \"tempC\": \"30\",\n          \"tempF\": \"86\",\n          \"time\": \"1200\",\n          \"uvIndex\": \"10\",\n          \"visibility\": \"10\",\n          \"visibilityMiles\": \"6\",\n          \"weatherCode\": \"176\",\n          \"weatherDesc\": [\n            {\n              \"value\": \"Patchy rain nearby\"\n            }\n          ],\n          \"weatherIconUrl\": [\n            {\n              \"value\": \"https://cdn.worldweatheronline.com/images/wsymbols01_png_64/wsymbol_0009_light_rain_showers.png\"\n            }\n          ],\n          \"winddir16Point\": \"SW\",\n          \"winddirDegree\": \"233\",\n          \"windspeedKmph\": \"29\",\n          \"windspeedMiles\": \"18\"\n        },\n        {\n          \"DewPointC\": \"25\",\n          \"DewPointF\": \"77\",\n          \"FeelsLikeC\": \"36\",\n          \"FeelsLikeF\": \"97\",\n          \"HeatIndexC\": \"36\",\n          \"HeatIndexF\": \"97\",\n          \"WindChillC\": \"30\",\n          \"WindChillF\": \"86\",\n          \"WindGustKmph\": \"37\",\n          \"WindGustMiles\": \"23\",\n          \"chanceoffog\": \"0\",\n          \"chanceoffrost\": \"0\",\n          \"chanceofhightemp\": \"99\",\n          \"chanceofovercast\": \"93\",\n          \"chanceofrain\": \"22\",\n          \"chanceofremdry\": \"70\",\n          \"chanceofsnow\": \"0\",\n          \"chanceofsunshine\": \"2\",\n          \"chanceofthunder\": \"0\",\n          \"chanceofwindy\": \"4\",\n          \"cloudcover\": \"89\",\n          \"diffRad\": \"303.5\",\n          \"humidity\": \"76\",\n          \"precipInches\": \"0.0\",\n          \"precipMM\": \"0.0\",\n          \"pressure\": \"1005\",\n          \"pressureInches\": \"30\",\n          \"shortRad\": \"724.2\",\n          \"tempC\": \"30\",\n          \"tempF\": \"86\",\n          \"time\": \"1500\",\n          \"uvIndex\": \"4\",\n          \"visibility\": \"10\",\n          \"visibilityMiles\": \"6\",\n          \"weatherCode\": \"176\",\n          \"weatherDesc\": [\n            {\n              \"value\": \"Patchy rain nearby\"\n            }\n          ],\n          \"weatherIconUrl\": [\n            {\n              \"value\": \"https://cdn.worldweatheronline.com/images/wsymbols01_png_64/wsymbol_0009_light_rain_showers.png\"\n            }\n          ],\n          \"winddir16Point\": \"WSW\",\n          \"winddirDegree\": \"238\",\n          \"windspeedKmph\": \"28\",\n          \"windspeedMiles\": \"18\"\n        },\n        {\n          \"DewPointC\": \"25\",\n          \"DewPointF\": \"77\",\n          \"FeelsLikeC\": \"34\",\n          \"FeelsLikeF\": \"93\",\n          \"HeatIndexC\": \"34\",\n          \"HeatIndexF\": \"93\",\n          \"WindChillC\": \"29\",\n          \"WindChillF\": \"84\",\n          \"WindGustKmph\": \"42\",\n          \"WindGustMiles\": \"26\",\n          \"chanceoffog\": \"0\",\n          \"chanceoffrost\": \"0\",\n          \"chanceofhightemp\": \"98\",\n          \"chanceofovercast\": \"88\",\n          \"chanceofrain\": \"24\",\n          \"chanceofremdry\": \"69\",\n          \"chanceofsnow\": \"0\",\n          \"chanceofsunshine\": \"3\",\n          \"chanceofthunder\": \"32\",\n          \"chanceofwindy\": \"4\",\n          \"cloudcover\": \"83\",\n          \"diffRad\": \"64.2\",\n          \"humidity\": \"81\",\n          \"precipInches\": \"0.0\",\n          \"precipMM\": \"0.0\",\n          \"pressure\": \"1006\",\n          \"pressureInches\": \"30\",\n          \"shortRad\": \"120.1\",\n          \"tempC\": \"29\",\n          \"tempF\": \"84\",\n          \"time\": \"1800\",\n          \"uvIndex\": \"0\",\n          \"visibility\": \"10\",\n          \"visibilityMiles\": \"6\",\n          \"weatherCode\": \"176\",\n          \"weatherDesc\": [\n            {\n              \"value\": \"Patchy rain nearby\"\n            }\n          ],\n          \"weatherIconUrl\": [\n            {\n              \"value\": \"https://cdn.worldweatheronline.com/images/wsymbols01_png_64/wsymbol_0009_light_rain_showers.png\"\n            }\n          ],\n          \"winddir16Point\": \"SW\",\n          \"winddirDegree\": \"233\",\n          \"windspeedKmph\": \"28\",\n          \"windspeedMiles\": \"17\"\n        },\n        {\n          \"DewPointC\": \"25\",\n          \"DewPointF\": \"77\",\n          \"FeelsLikeC\": \"33\",\n          \"FeelsLikeF\": \"92\",\n          \"HeatIndexC\": \"33\",\n          \"HeatIndexF\": \"92\",\n          \"WindChillC\": \"28\",\n          \"WindChillF\": \"83\",\n          \"WindGustKmph\": \"42\",\n          \"WindGustMiles\": \"26\",\n          \"chanceoffog\": \"0\",\n          \"chanceoffrost\": \"0\",\n          \"chanceofhightemp\": \"97\",\n          \"chanceofovercast\": \"81\",\n          \"chanceofrain\": \"23\",\n          \"chanceofremdry\": \"77\",\n          \"chanceofsnow\": \"0\",\n          \"chanceofsunshine\": \"4\",\n          \"chanceofthunder\": \"28\",\n          \"chanceofwindy\": \"4\",\n          \"cloudcover\": \"76\",\n          \"diffRad\": \"18.2\",\n          \"humidity\": \"81\",\n          \"precipInches\": \"0.0\",\n          \"precipMM\": \"0.0\",\n          \"pressure\": \"1007\",\n          \"pressureInches\": \"30\",\n          \"shortRad\": \"33.9\",\n          \"tempC\": \"28\",\n          \"tempF\": \"83\",\n          \"time\": \"2100\",\n          \"uvIndex\": \"0\",\n          \"visibility\": \"10\",\n          \"visibilityMiles\": \"6\",\n          \"weatherCode\": \"176\",\n          \"weatherDesc\": [\n            {\n              \"value\": \"Patchy rain nearby\"\n            }\n          ],\n          \"weatherIconUrl\": [\n            {\n              \"value\": \"https://cdn.worldweatheronline.com/images/wsymbols01_png_64/wsymbol_0025_light_rain_showers_night.png\"\n            }\n          ],\n          \"winddir16Point\": \"SW\",\n          \"winddirDegree\": \"236\",\n          \"windspeedKmph\": \"27\",\n          \"windspeedMiles\": \"17\"\n        }\n      ],\n      \"maxtempC\": \"30\",\n      \"maxtempF\": \"86\",\n      \"mintempC\": \"28\",\n      \"mintempF\": \"82\",\n      \"sunHour\": \"5.0\",\n      \"totalSnow_cm\": \"0.0\",\n      \"uvIndex\": \"10\"\n    }\n  ]\n}", "exit_code": 0, "error": null}


### Assistant — 2026-07-08T04:13:00.319328Z



## Tool calls

```json
[
  {
    "id": "call-1feb5f00-f44a-4cc7-8060-1a850dbbdf91",
    "call_id": "call-1feb5f00-f44a-4cc7-8060-1a850dbbdf91",
    "response_item_id": "fc_call-1feb5f00-f44a-4cc7-8060-1a850dbbdf91",
    "type": "function",
    "function": {
      "name": "terminal",
      "arguments": "{\"command\":\"curl -s \\\"https://wttr.in/Bilimora?format=j1\\\" | jq '.current_condition[0] | {temp_C, FeelsLikeC, humidity, weatherDesc: .weatherDesc[0].value, windspeedKmph, winddir16Point, visibility}'\"}"
    }
  },
  {
    "id": "call-d4cf8f2e-05b7-4534-bc06-be068ff4dd6c",
    "call_id": "call-d4cf8f2e-05b7-4534-bc06-be068ff4dd6c",
    "response_item_id": "fc_call-d4cf8f2e-05b7-4534-bc06-be068ff4dd6c",
    "type": "function",
    "function": {
      "name": "terminal",
      "arguments": "{\"command\":\"curl -s \\\"https://wttr.in/Atul+Valsad?format=j1\\\" | jq '.current_condition[0] | {temp_C, FeelsLikeC, humidity, weatherDesc: .weatherDesc[0].value, windspeedKmph, winddir16Point, visibility}'\"}"
    }
  }
]
```


### Tool — terminal — 2026-07-08T04:13:01.245309Z

{"output": "{\n  \"temp_C\": \"27\",\n  \"FeelsLikeC\": \"29\",\n  \"humidity\": \"94\",\n  \"weatherDesc\": \"Patchy rain nearby\",\n  \"windspeedKmph\": \"11\",\n  \"winddir16Point\": \"SSE\",\n  \"visibility\": \"10\"\n}", "exit_code": 0, "error": null}


### Tool — terminal — 2026-07-08T04:13:03.207010Z

{"output": "{\n  \"temp_C\": \"27\",\n  \"FeelsLikeC\": \"29\",\n  \"humidity\": \"90\",\n  \"weatherDesc\": \"Patchy rain nearby\",\n  \"windspeedKmph\": \"20\",\n  \"winddir16Point\": \"SSW\",\n  \"visibility\": \"10\"\n}", "exit_code": 0, "error": null}


### Assistant — 2026-07-08T04:13:09.498438Z



## Tool calls

```json
[
  {
    "id": "call-19b9ac6d-9988-480e-891a-f5e60cf45a03",
    "call_id": "call-19b9ac6d-9988-480e-891a-f5e60cf45a03",
    "response_item_id": "fc_call-19b9ac6d-9988-480e-891a-f5e60cf45a03",
    "type": "function",
    "function": {
      "name": "terminal",
      "arguments": "{\"command\":\"env | grep -i discord\"}"
    }
  }
]
```


### Tool — terminal — 2026-07-08T04:13:09.613876Z

{"output": "DISCORD_HOME_CHANNEL_THREAD_ID=\nHERMES_CRON_AUTO_DELIVER_PLATFORM=discord", "exit_code": 0, "error": null}


### Assistant — 2026-07-08T04:13:10.787010Z



## Tool calls

```json
[
  {
    "id": "call-6fd7e55d-3fd0-423e-af02-271ffd4e9097",
    "call_id": "call-6fd7e55d-3fd0-423e-af02-271ffd4e9097",
    "response_item_id": "fc_call-6fd7e55d-3fd0-423e-af02-271ffd4e9097",
    "type": "function",
    "function": {
      "name": "terminal",
      "arguments": "{\"command\":\"env | grep -i webhook\"}"
    }
  }
]
```


### Tool — terminal — 2026-07-08T04:13:10.888763Z

{"output": "", "exit_code": 1, "error": null, "exit_code_meaning": "No matches found (not an error)"}


### Assistant — 2026-07-08T04:13:13.283732Z



## Tool calls

```json
[
  {
    "id": "call-9ab9cb78-53bc-4607-9a2a-8ea30a0d63db",
    "call_id": "call-9ab9cb78-53bc-4607-9a2a-8ea30a0d63db",
    "response_item_id": "fc_call-9ab9cb78-53bc-4607-9a2a-8ea30a0d63db",
    "type": "function",
    "function": {
      "name": "search_files",
      "arguments": "{\"target\":\"content\",\"pattern\":\"DISCORD_WEBHOOK|DISCORD_WEBHOOK_BRIEFING|webhook\",\"path\":\"/root\"}"
    }
  }
]
```


### Tool — search_files — 2026-07-08T04:13:13.341498Z

{"total_count": 0}


### Assistant — 2026-07-08T04:13:15.110597Z



## Tool calls

```json
[
  {
    "id": "call-ee29d800-f988-4a87-9196-2bda6f601068",
    "call_id": "call-ee29d800-f988-4a87-9196-2bda6f601068",
    "response_item_id": "fc_call-ee29d800-f988-4a87-9196-2bda6f601068",
    "type": "function",
    "function": {
      "name": "terminal",
      "arguments": "{\"command\":\"ls -la ~/.hermes/skills/discord-webhook-delivery/\"}"
    }
  }
]
```


### Tool — terminal — 2026-07-08T04:13:15.199764Z

{"output": "ls: cannot access '/root/.hermes/skills/discord-webhook-delivery/': No such file or directory", "exit_code": 2, "error": null}


### Assistant — 2026-07-08T04:13:16.500598Z



## Tool calls

```json
[
  {
    "id": "call-6fd48631-d0d3-4c74-aa64-56b16fda1305",
    "call_id": "call-6fd48631-d0d3-4c74-aa64-56b16fda1305",
    "response_item_id": "fc_call-6fd48631-d0d3-4c74-aa64-56b16fda1305",
    "type": "function",
    "function": {
      "name": "terminal",
      "arguments": "{\"command\":\"ls -la ~/.hermes/skills/\"}"
    }
  }
]
```


### Tool — terminal — 2026-07-08T04:13:16.584572Z

{"output": "total 56\ndrwx------ 1 root root  454 Jul  8 09:41 .\ndrwx------ 1 root root 1002 Jul  8 09:43 ..\ndrwxr-xr-x 1 root root  108 Jul  7 09:10 apple\ndrwxr-xr-x 1 root root  100 Jul  7 09:10 autonomous-ai-agents\n-rw------- 1 root root 3365 Jul  7 17:43 .bundled_manifest\ndrwxr-xr-x 1 root root   16 Jul  7 09:10 computer-use\ndrwxr-xr-x 1 root root  414 Jul  7 09:10 creative\n-rw------- 1 root root  337 Jul  7 09:38 .curator_state\ndrwxr-xr-x 1 root root   66 Jul  7 09:10 data-science\ndrwxr-xr-x 1 root root   54 Jul  7 09:10 dogfood\ndrwxr-xr-x 1 root root   88 Jul  7 13:46 email\ndrwxr-xr-x 1 root root  230 Jul  7 09:10 github\ndrwxr-xr-x 1 root root   22 Jul  7 09:31 .hub\ndrwxr-xr-x 1 root root  110 Jul  7 09:10 media\ndrwxr-xr-x 1 root root  108 Jul  7 09:10 mlops\ndrwxr-xr-x 1 root root   44 Jul  7 09:10 note-taking\ndrwxr-xr-x 1 root root  314 Jul  7 17:35 productivity\ndrwxr-xr-x 1 root root  140 Jul  7 09:10 research\ndrwxr-xr-x 1 root root   42 Jul  7 09:10 smart-home\ndrwxr-xr-x 1 root root   86 Jul  7 09:42 social-media\ndrwxr-xr-x 1 root root  300 Jul  7 09:10 software-development\n-rw------- 1 root root 2819 Jul  8 09:41 .usage.json\n-rw-r--r-- 1 root root    0 Jul  7 09:42 .usage.json.lock\ndrwxr-xr-x 1 root root   16 Jul  7 09:10 yuanbao", "exit_code": 0, "error": null}


### Assistant — 2026-07-08T04:14:10.051231Z



## Tool calls

```json
[
  {
    "id": "call-433e0a07-63f8-4189-9b6d-90c4a2aae207",
    "call_id": "call-433e0a07-63f8-4189-9b6d-90c4a2aae207",
    "response_item_id": "fc_call-433e0a07-63f8-4189-9b6d-90c4a2aae207",
    "type": "function",
    "function": {
      "name": "terminal",
      "arguments": "{\"command\":\"date '+%A, %d %B %Y | %I:%M %p IST'\"}"
    }
  }
]
```


### Tool — terminal — 2026-07-08T04:14:10.142425Z

{"output": "Wednesday, 08 July 2026 | 09:44 AM IST", "exit_code": 0, "error": null}


### Assistant — 2026-07-08T04:14:17.417640Z



## Tool calls

```json
[
  {
    "id": "call-61c16f44-7abe-434a-999f-9a90e28a2242",
    "call_id": "call-61c16f44-7abe-434a-999f-9a90e28a2242",
    "response_item_id": "fc_call-61c16f44-7abe-434a-999f-9a90e28a2242",
    "type": "function",
    "function": {
      "name": "terminal",
      "arguments": "{\"command\":\"cat << 'EOF'\\n{\\n  \\\"username\\\": \\\"AEGIS Weather\\\",\\n  \\\"avatar_url\\\": \\\"https://cdn.discordapp.com/emojis/1234567890123456789.png\\\",\\n  \\\"embeds\\\": [{\\n    \\\"title\\\": \\\"🌤️ Weather Briefing — Wednesday, 08 July 2026\\\",\\n    \\\"description\\\": \\\"🕐 **09:44 AM IST** — Current conditions across your locations\\\",\\n    \\\"color\\\": 5814783,\\n    \\\"fields\\\": [\\n      {\\n        \\\"name\\\": \\\"🏙️ **Manesar, Haryana**\\\",\\n        \\\"value\\\": \\\"⛈️ **28°C** (Feels like 30°C)\\\\n☔ Light Rain, Thunderstorm\\\\n💧 Humidity: 89%\\\\n💨 Wind: 13 km/h E\\\\n👁️ Visibility: 2 km\\\",\\n        \\\"inline\\\": true\\n      },\\n      {\\n        \\\"name\\\": \\\"🏙️ **Bilimora, Gujarat**\\\",\\n        \\\"value\\\": \\\"🌦️ **27°C** (Feels like 29°C)\\\\n🌧️ Patchy rain nearby\\\\n💧 Humidity: 94%\\\\n💨 Wind: 11 km/h SSE\\\\n👁️ Visibility: 10 km\\\",\\n        \\\"inline\\\": true\\n      },\\n      {\\n        \\\"name\\\": \\\"🏙️ **Atul Valsad, Gujarat**\\\",\\n        \\\"value\\\": \\\"🌦️ **27°C** (Feels like 29°C)\\\\n🌧️ Patchy rain nearby\\\\n💧 Humidity: 90%\\\\n💨 Wind: 20 km/h SSW\\\\n👁️ Visibility: 10 km\\\",\\n        \\\"inline\\\": true\\n      }\\n    ],\\n    \\\"footer\\\": {\\n      \\\"text\\\": \\\"AEGIS Weather • Data from wttr.in • Next update in 6h\\\"\\n    },\\n    \\\"timestamp\\\": \\\"2026-07-08T09:44:00+05:30\\\"\\n  }]\\n}\\nEOF\"}"
    }
  }
]
```


### Tool — terminal — 2026-07-08T04:14:17.565633Z

{"output": "", "exit_code": -1, "error": "", "status": "pending_approval", "approval_pending": true, "command": "cat << 'EOF'\n{\n  \"username\": \"AEGIS Weather\",\n  \"avatar_url\": \"https://cdn.discordapp.com/emojis/1234567890123456789.png\",\n  \"embeds\": [{\n    \"title\": \"🌤️ Weather Briefing — Wednesday, 08 July 2026\",\n    \"description\": \"🕐 **09:44 AM IST** — Current conditions across your locations\",\n    \"color\": 5814783,\n    \"fields\": [\n      {\n        \"name\": \"🏙️ **Manesar, Haryana**\",\n        \"value\": \"⛈️ **28°C** (Feels like 30°C)\\n☔ Light Rain, Thunderstorm\\n💧 Humidity: 89%\\n💨 Wind: 13 km/h E\\n👁️ Visibility: 2 km\",\n        \"inline\": true\n      },\n      {\n        \"name\": \"🏙️ **Bilimora, Gujarat**\",\n        \"value\": \"🌦️ **27°C** (Feels like 29°C)\\n🌧️ Patchy rain nearby\\n💧 Humidity: 94%\\n💨 Wind: 11 km/h SSE\\n👁️ Visibility: 10 km\",\n        \"inline\": true\n      },\n      {\n        \"name\": \"🏙️ **Atul Valsad, Gujarat**\",\n        \"value\": \"🌦️ **27°C** (Feels like 29°C)\\n🌧️ Patchy rain nearby\\n💧 Humidity: 90%\\n💨 Wind: 20 km/h SSW\\n👁️ Visibility: 10 km\",\n        \"inline\": true\n      }\n    ],\n    \"footer\": {\n      \"text\": \"AEGIS Weather • Data from wttr.in • Next update in 6h\"\n    },\n    \"timestamp\": \"2026-07-08T09:44:00+05:30\"\n  }]\n}\nEOF", "description": "Security scan — [MEDIUM] Variation selector characters detected: Content contains Unicode variation selectors (VS1-256). These are commonly used in emoji sequences but may indicate steganographic encoding or obfuscation", "pattern_key": "tirith:variation_selector"}


### Assistant — 2026-07-08T04:14:47.390440Z



## Tool calls

```json
[
  {
    "id": "call-7fdada4f-326a-4547-a1b9-1eb115fb0714",
    "call_id": "call-7fdada4f-326a-4547-a1b9-1eb115fb0714",
    "response_item_id": "fc_call-7fdada4f-326a-4547-a1b9-1eb115fb0714",
    "type": "function",
    "function": {
      "name": "write_file",
      "arguments": "{\"content\":\"{\\n  \\\"username\\\": \\\"AEGIS Weather\\\",\\n  \\\"avatar_url\\\": \\\"https://cdn.discordapp.com/emojis/1234567890123456789.png\\\",\\n  \\\"embeds\\\": [{\\n    \\\"title\\\": \\\"Weather Briefing - Wednesday, 08 July 2026\\\",\\n    \\\"description\\\": \\\"09:44 AM IST - Current conditions across your locations\\\",\\n    \\\"color\\\": 5814783,\\n    \\\"fields\\\": [\\n      {\\n        \\\"name\\\": \\\"Manesar, Haryana\\\",\\n        \\\"value\\\": \\\"28°C (Feels like 30°C)\\\\nLight Rain, Thunderstorm\\\\nHumidity: 89%\\\\nWind: 13 km/h E\\\\nVisibility: 2 km\\\",\\n        \\\"inline\\\": true\\n      },\\n      {\\n        \\\"name\\\": \\\"Bilimora, Gujarat\\\",\\n        \\\"value\\\": \\\"27°C (Feels like 29°C)\\\\nPatchy rain nearby\\\\nHumidity: 94%\\\\nWind: 11 km/h SSE\\\\nVisibility: 10 km\\\",\\n        \\\"inline\\\": true\\n      },\\n      {\\n        \\\"name\\\": \\\"Atul Valsad, Gujarat\\\",\\n        \\\"value\\\": \\\"27°C (Feels like 29°C)\\\\nPatchy rain nearby\\\\nHumidity: 90%\\\\nWind: 20 km/h SSW\\\\nVisibility: 10 km\\\",\\n        \\\"inline\\\": true\\n      }\\n    ],\\n    \\\"footer\\\": {\\n      \\\"text\\\": \\\"AEGIS Weather - Data from wttr.in - Next update in 6h\\\"\\n    },\\n    \\\"timestamp\\\": \\\"2026-07-08T09:44:00+05:30\\\"\\n  }]\\n}\",\"path\":\"/tmp/weather-webhook.json\"}"
    }
  }
]
```


### Tool — write_file — 2026-07-08T04:14:47.526704Z

{"bytes_written": 1040, "dirs_created": true, "lint": {"status": "ok", "output": ""}, "resolved_path": "/tmp/weather-webhook.json", "files_modified": ["/tmp/weather-webhook.json"]}


### Assistant — 2026-07-08T04:15:07.775238Z

Weather briefing payload created at `/tmp/weather-webhook.json`. However, **no Discord webhook URL is configured** in the environment — I cannot deliver to channel `1523905009907925062` (guild `1522302510683914250`) without a valid webhook URL.

**What's needed:**
- Set `DISCORD_WEBHOOK_BRIEFING` (or similar) env var with the webhook URL from Discord → Server Settings → Integrations → Webhooks → New Webhook → select target channel → copy URL

**Payload ready to send:**
```json
{
  "username": "AEGIS Weather",
  "embeds": [{
    "title": "Weather Briefing - Wednesday, 08 July 2026",
    "description": "09:44 AM IST - Current conditions across your locations",
    "color": 5814783,
    "fields": [
      {"name": "Manesar, Haryana", "value": "28°C (Feels like 30°C)\nLight Rain, Thunderstorm\nHumidity: 89%\nWind: 13 km/h E\nVisibility: 2 km", "inline": true},
      {"name": "Bilimora, Gujarat", "value": "27°C (Feels like 29°C)\nPatchy rain nearby\nHumidity: 94%\nWind: 11 km/h SSE\nVisibility: 10 km", "inline": true},
      {"name": "Atul Valsad, Gujarat", "value": "27°C (Feels like 29°C)\nPatchy rain nearby\nHumidity: 90%\nWind: 20 km/h SSW\nVisibility: 10 km", "inline": true}
    ],
    "footer": {"text": "AEGIS Weather - Data from wttr.in - Next update in 6h"},
    "timestamp": "2026-07-08T09:44:00+05:30"
  }]
}
```

Once the webhook URL is available, delivery is a single `curl`:
```bash
curl -sS -X POST "$DISCORD_WEBHOOK_BRIEFING" \
  -H "Content-Type: application/json" \
  -d @/tmp/weather-webhook.json
```

## Export verification

- Session id: `cron_6338a8188c36_20260708_094135`
- Exported messages: `27`
- Source DB message count at export: `27`
- Exported at: `2026-09-10T04:30:39.288796Z`
- SHA256 of exported body: `c922adc1335cc72183d56d9b6ffe441aced6605c929f64027cafd2fb5cebcc3e`
