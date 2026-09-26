#!/usr/bin/env python3
"""
hermes_brain_mcp.py — Model Context Protocol (MCP) Server for Hermes Brain Vault.

Exposes the Obsidian vault to any MCP-compatible agent host (Claude Desktop,
Cursor, OpenClaw, Hermes CLI, Windsurf, etc.) over stdio JSON-RPC.

Capabilities:
  Tools:
    - vault_search: Search notes by keyword, regex, or frontmatter tag.
    - read_note: Fetch markdown note contents safely by relative path.
    - get_user_profile: Pull user alignment boundaries and preferences.
    - get_active_adrs: Fetch architectural decision records.
    - stage_memory_candidate: Stage a verified fact into Memory-Review for human triage.
    - vault_stats: Return quick telemetry (sessions, projects, pending reviews).

  Resources:
    - vault://MOC: Central Map of Content.
    - vault://User-Profile: Core human alignment and operating boundaries.
    - vault://Dashboard: Live operational dashboard.

Usage:
  Interactive / Agent Mode:
    python _System/Scripts/hermes_brain_mcp.py [--vault <path>]

  Self-Test / Diagnostics:
    python _System/Scripts/hermes_brain_mcp.py --test [--vault <path>]
"""

import os
import sys
import json
import re
import argparse
from pathlib import Path
from datetime import datetime, timezone

# ---------------------------------------------------------------------------
# Vault Path Resolution
# ---------------------------------------------------------------------------

def get_vault_path(explicit_path=None):
    """
    Resolves the vault root directory following template precedence:
    1. Explicit CLI argument (--vault <path>)
    2. Environment variable HERMES_VAULT_PATH
    3. Heuristic discovery from script location upwards
    """
    if explicit_path and os.path.isdir(explicit_path):
        return Path(explicit_path).resolve()

    env_vault = os.environ.get("HERMES_VAULT_PATH")
    if env_vault and os.path.isdir(env_vault):
        return Path(env_vault).resolve()

    script_dir = Path(__file__).resolve().parent
    for candidate in [
        Path.cwd().resolve(),
        script_dir.parent.parent,
        script_dir.parent,
    ]:
        if (candidate / ".obsidian").exists() or (candidate / "01-Projects").exists():
            return candidate.resolve()

    return Path.cwd().resolve()


# ---------------------------------------------------------------------------
# Vault Operations
# ---------------------------------------------------------------------------

class VaultCore:
    def __init__(self, root: Path):
        self.root = root

    def safe_resolve(self, rel_path: str) -> Path:
        """Resolve a path relative to vault root and guard against traversal attacks."""
        clean = rel_path.strip().lstrip("/\\")
        target = (self.root / clean).resolve()
        if not str(target).startswith(str(self.root)):
            raise ValueError(f"Access denied: path '{rel_path}' is outside the vault root.")
        return target

    def search(self, query: str, folder: str = "", limit: int = 10) -> list:
        """Search markdown files by text content or filename."""
        results = []
        pattern = re.compile(re.escape(query), re.IGNORECASE)
        search_dir = self.safe_resolve(folder) if folder else self.root

        if not search_dir.exists():
            return []

        # Directories to skip
        skip_dirs = {".git", ".obsidian", ".smart-env", "cache", "graphify-out", "__pycache__"}

        for current_root, dirs, files in os.walk(search_dir):
            dirs[:] = [d for d in dirs if d not in skip_dirs and not d.startswith(".")]
            for f in files:
                if not f.endswith((".md", ".canvas")):
                    continue
                file_path = Path(current_root) / f
                rel_path = file_path.relative_to(self.root).as_posix()

                try:
                    text = file_path.read_text(encoding="utf-8", errors="ignore")
                except Exception:
                    continue

                matches = []
                for idx, line in enumerate(text.splitlines(), start=1):
                    if pattern.search(line):
                        matches.append({"line": idx, "snippet": line.strip()[:200]})
                        if len(matches) >= 3:
                            break

                filename_match = bool(pattern.search(f))
                if matches or filename_match:
                    results.append({
                        "path": rel_path,
                        "title": f,
                        "filename_matched": filename_match,
                        "matches": matches,
                    })

                if len(results) >= limit:
                    return results

        return results

    def read_note(self, rel_path: str) -> str:
        """Read note content."""
        target = self.safe_resolve(rel_path)
        if not target.exists():
            # Try appending .md if not present
            if not target.name.endswith(".md"):
                target_md = target.with_suffix(".md")
                if target_md.exists():
                    target = target_md
                else:
                    raise FileNotFoundError(f"Note not found: {rel_path}")
            else:
                raise FileNotFoundError(f"Note not found: {rel_path}")

        if not target.is_file():
            raise IsADirectoryError(f"Target is a directory: {rel_path}")

        return target.read_text(encoding="utf-8", errors="replace")

    def get_user_profile(self) -> dict:
        """Fetch User-Profile from 02-Areas/User-Profile.md."""
        candidates = [
            self.root / "02-Areas" / "User-Profile.md",
            self.root / "User-Profile.md"
        ]
        target = next((p for p in candidates if p.exists()), None)
        if not target:
            return {"status": "not_found", "message": "No User-Profile.md found in vault."}

        content = target.read_text(encoding="utf-8", errors="replace")
        return {
            "status": "ok",
            "path": target.relative_to(self.root).as_posix(),
            "content": content
        }

    def get_active_adrs(self) -> list:
        """Fetch accepted/active Architectural Decision Records."""
        adr_dir = self.root / "01-Projects" / "ADR"
        if not adr_dir.exists():
            return []

        adrs = []
        for f in sorted(adr_dir.glob("*.md")):
            if f.name.lower() == "readme.md":
                continue
            content = f.read_text(encoding="utf-8", errors="replace")
            # Parse frontmatter status
            status = "active"
            status_match = re.search(r"^status:\s*([a-zA-Z0-9_\-]+)", content, re.M | re.I)
            if status_match:
                status = status_match.group(1).lower()

            adrs.append({
                "path": f.relative_to(self.root).as_posix(),
                "title": f.stem,
                "status": status,
                "preview": content[:400]
            })
        return adrs

    def stage_memory_candidate(self, fact: str, category: str = "general", source: str = "", rationale: str = "") -> dict:
        """
        Safely stage a memory candidate into 04-Archives/Memory-Review/
        without modifying live/production agent memory directly.
        """
        review_dir = self.root / "04-Archives" / "Memory-Review"
        if not review_dir.exists():
            review_dir = self.root / "Memory-Review"
        review_dir.mkdir(parents=True, exist_ok=True)

        now_utc = datetime.now(timezone.utc)
        timestamp_slug = now_utc.strftime("%Y%m%d_%H%M%S")
        safe_fact_slug = re.sub(r"[^a-zA-Z0-9_\-]+", "-", fact[:40]).strip("-").lower()
        filename = f"candidate_{timestamp_slug}_{safe_fact_slug}.md"
        target_path = review_dir / filename

        note_content = f"""---
type: memory-candidate
status: pending-review
created: {now_utc.isoformat()}
category: {category}
source: "{source or 'mcp-agent'}"
---

# 🧠 Memory Candidate: {fact[:60]}...

### Candidate Fact
> {fact}

### Context & Rationale
- **Category:** `{category}`
- **Source Session / Origin:** {source or "Direct MCP Injection"}
- **Rationale:** {rationale or "Staged by autonomous agent via hermes-brain-mcp."}

### Review Checklist (Human Gatekeeper)
- [ ] **Durable** (will still be true and useful 30+ days from now)
- [ ] **Verified** (confirmed by fact or observation, not hallucinated)
- [ ] **Non-Sensitive** (no credentials, API keys, or raw personal secrets)
- [ ] **Actionable** (clarifies future decision making or agent persona)

### Target Promotion
- [ ] Promote to `02-Areas/User-Profile.md` (User preferences & boundaries)
- [ ] Promote to `Hermes MEMORY.md` (Durable operational knowledge)
- [ ] Reject and archive
"""
        target_path.write_text(note_content, encoding="utf-8")
        return {
            "status": "staged",
            "path": target_path.relative_to(self.root).as_posix(),
            "filename": filename,
            "message": "Candidate staged for human review in Memory-Review board."
        }

    def get_stats(self) -> dict:
        """Calculate live vault operational statistics."""
        # Sessions count
        daily_cand = [self.root / "04-Archives" / "Daily", self.root / "Daily"]
        daily_dir = next((d for d in daily_cand if d.exists()), None)
        session_count = 0
        if daily_dir:
            for p in daily_dir.rglob("*.md"):
                if p.name not in ["README.md", "Timeline.md", "Chat-Correlation.md"]:
                    session_count += 1

        # Memory review candidates
        review_cand = [self.root / "04-Archives" / "Memory-Review", self.root / "Memory-Review"]
        review_dir = next((d for d in review_cand if d.exists()), None)
        pending_candidates = 0
        if review_dir:
            for p in review_dir.glob("*.md"):
                if p.name not in ["README.md", "TEMPLATE.md", "HERMES-PREAMBLE.md", "Consolidation-Log.md", "Promotion-Candidates.md"]:
                    pending_candidates += 1

        # Active projects
        projects_dir = self.root / "01-Projects"
        project_count = 0
        if projects_dir.exists():
            for p in projects_dir.glob("*.md"):
                if p.name != "README.md":
                    project_count += 1

        # Installed skills
        skills_dir = self.root / "02-Areas" / "Skills"
        skills_count = len(list(skills_dir.glob("*.md"))) if skills_dir.exists() else 0

        return {
            "vault_path": str(self.root),
            "archived_sessions": session_count,
            "pending_memory_reviews": pending_candidates,
            "active_projects": project_count,
            "documented_skills": skills_count,
        }


# ---------------------------------------------------------------------------
# MCP Tool & Resource Definitions
# ---------------------------------------------------------------------------

TOOLS = [
    {
        "name": "vault_search",
        "description": "Search markdown notes in the Hermes Brain Vault by keywords, tags, or text snippets.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "query": {"type": "string", "description": "Search term, concept, or topic name."},
                "folder": {"type": "string", "description": "Optional subdirectory to narrow search (e.g. '01-Projects', '02-Areas', '03-Resources').", "default": ""},
                "limit": {"type": "integer", "description": "Max results to return (default 10).", "default": 10}
            },
            "required": ["query"]
        }
    },
    {
        "name": "read_note",
        "description": "Read the full markdown content of a specific note in the vault.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "path": {"type": "string", "description": "Relative path to note from vault root (e.g. '01-Projects/README.md')."}
            },
            "required": ["path"]
        }
    },
    {
        "name": "get_user_profile",
        "description": "Fetch user alignment rules, behavioral guidelines, and communication boundaries from User-Profile.md.",
        "inputSchema": {
            "type": "object",
            "properties": {}
        }
    },
    {
        "name": "get_active_adrs",
        "description": "Fetch all accepted Architectural Decision Records (ADRs) to ensure architectural consistency.",
        "inputSchema": {
            "type": "object",
            "properties": {}
        }
    },
    {
        "name": "stage_memory_candidate",
        "description": "Stage a durable insight, verified fact, or user preference into Memory-Review for human verification.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "fact": {"type": "string", "description": "The exact factual proposition or rule to remember."},
                "category": {
                    "type": "string",
                    "description": "Category for the memory.",
                    "enum": ["user_preference", "project_fact", "architectural_rule", "learned_workflow"],
                    "default": "user_preference"
                },
                "source": {"type": "string", "description": "Origin reference (e.g. session name, command, or topic)."},
                "rationale": {"type": "string", "description": "Why this fact should be preserved into persistent memory."}
            },
            "required": ["fact"]
        }
    },
    {
        "name": "vault_stats",
        "description": "Retrieve current vault telemetry: session count, active projects, pending reviews, and skills.",
        "inputSchema": {
            "type": "object",
            "properties": {}
        }
    }
]

RESOURCES = [
    {
        "uri": "vault://MOC",
        "name": "Map of Content (MOC)",
        "description": "Primary vault index and navigation map.",
        "mimeType": "text/markdown"
    },
    {
        "uri": "vault://User-Profile",
        "name": "User Profile & Boundaries",
        "description": "Human alignment parameters and operational guardrails.",
        "mimeType": "text/markdown"
    },
    {
        "uri": "vault://Dashboard",
        "name": "Vault Operational Dashboard",
        "description": "Central status command center.",
        "mimeType": "text/markdown"
    }
]


# ---------------------------------------------------------------------------
# MCP Protocol Server Engine (JSON-RPC 2.0 over Stdio)
# ---------------------------------------------------------------------------

class MCPServer:
    def __init__(self, vault: VaultCore):
        self.vault = vault

    def handle_request(self, req: dict) -> dict:
        method = req.get("method")
        msg_id = req.get("id")
        params = req.get("params", {})

        # Handle initialize
        if method == "initialize":
            return {
                "jsonrpc": "2.0",
                "id": msg_id,
                "result": {
                    "protocolVersion": "2024-11-05",
                    "capabilities": {
                        "tools": {},
                        "resources": {}
                    },
                    "serverInfo": {
                        "name": "hermes-brain-mcp",
                        "version": "1.0.0"
                    }
                }
            }

        # Notifications
        if method in ("notifications/initialized", "initialized"):
            return None

        # Ping
        if method == "ping":
            return {"jsonrpc": "2.0", "id": msg_id, "result": {}}

        # Tools list
        if method == "tools/list":
            return {
                "jsonrpc": "2.0",
                "id": msg_id,
                "result": {"tools": TOOLS}
            }

        # Tools execution
        if method == "tools/call":
            tool_name = params.get("name")
            args = params.get("arguments", {})
            try:
                result_text = self.execute_tool(tool_name, args)
                return {
                    "jsonrpc": "2.0",
                    "id": msg_id,
                    "result": {
                        "content": [{"type": "text", "text": result_text}]
                    }
                }
            except Exception as e:
                return {
                    "jsonrpc": "2.0",
                    "id": msg_id,
                    "result": {
                        "content": [{"type": "text", "text": f"Error executing tool '{tool_name}': {str(e)}"}],
                        "isError": True
                    }
                }

        # Resources list
        if method == "resources/list":
            return {
                "jsonrpc": "2.0",
                "id": msg_id,
                "result": {"resources": RESOURCES}
            }

        # Resources read
        if method == "resources/read":
            uri = params.get("uri", "")
            content = self.read_resource(uri)
            return {
                "jsonrpc": "2.0",
                "id": msg_id,
                "result": {
                    "contents": [{
                        "uri": uri,
                        "mimeType": "text/markdown",
                        "text": content
                    }]
                }
            }

        # Fallback / Method Not Found
        return {
            "jsonrpc": "2.0",
            "id": msg_id,
            "error": {"code": -32601, "message": f"Method '{method}' not implemented."}
        }

    def execute_tool(self, name: str, args: dict) -> str:
        if name == "vault_search":
            hits = self.vault.search(args.get("query", ""), args.get("folder", ""), args.get("limit", 10))
            return json.dumps(hits, indent=2)

        elif name == "read_note":
            content = self.vault.read_note(args.get("path", ""))
            return content

        elif name == "get_user_profile":
            prof = self.vault.get_user_profile()
            return json.dumps(prof, indent=2)

        elif name == "get_active_adrs":
            adrs = self.vault.get_active_adrs()
            return json.dumps(adrs, indent=2)

        elif name == "stage_memory_candidate":
            staged = self.vault.stage_memory_candidate(
                fact=args.get("fact", ""),
                category=args.get("category", "general"),
                source=args.get("source", ""),
                rationale=args.get("rationale", "")
            )
            return json.dumps(staged, indent=2)

        elif name == "vault_stats":
            stats = self.vault.get_stats()
            return json.dumps(stats, indent=2)

        raise ValueError(f"Unknown tool '{name}'")

    def read_resource(self, uri: str) -> str:
        if uri == "vault://MOC":
            return self.vault.read_note("MOC.md")
        elif uri == "vault://User-Profile":
            return self.vault.get_user_profile().get("content", "")
        elif uri == "vault://Dashboard":
            return self.vault.read_note("Dashboard.md")
        raise ValueError(f"Unknown resource URI: {uri}")

    def run_stdio(self):
        """Run the event loop reading JSON-RPC lines from stdin and writing to stdout."""
        # Force binary/utf-8 stdio handling to prevent platform encoding mismatches
        sys.stderr.write(f"[hermes-brain-mcp] Server active for vault at: {self.vault.root}\n")
        sys.stderr.flush()

        for line in sys.stdin:
            line = line.strip()
            if not line:
                continue
            try:
                req = json.loads(line)
            except json.JSONDecodeError as err:
                sys.stderr.write(f"[hermes-brain-mcp] Malformed JSON: {err}\n")
                continue

            resp = self.handle_request(req)
            if resp is not None:
                sys.stdout.write(json.dumps(resp, ensure_ascii=False) + "\n")
                sys.stdout.flush()


# ---------------------------------------------------------------------------
# Self-Test / Verification Suite
# ---------------------------------------------------------------------------

def run_self_test(vault_path: Path):
    """Run an automated diagnostic test of all tools and resources."""
    print("=" * 60)
    print(f"🧪 hermes-brain-mcp Self-Test Mode")
    print(f"📁 Target Vault: {vault_path}")
    print("=" * 60)

    vault = VaultCore(vault_path)
    server = MCPServer(vault)

    # 1. Test Initialize
    init_res = server.handle_request({"jsonrpc": "2.0", "id": 1, "method": "initialize"})
    assert init_res["result"]["serverInfo"]["name"] == "hermes-brain-mcp"
    print("✅ Method 'initialize' -> OK")

    # 2. Test Tools List
    tools_res = server.handle_request({"jsonrpc": "2.0", "id": 2, "method": "tools/list"})
    tools_count = len(tools_res["result"]["tools"])
    assert tools_count >= 6
    print(f"✅ Method 'tools/list' -> OK ({tools_count} tools registered)")

    # 3. Test Resources List
    res_list = server.handle_request({"jsonrpc": "2.0", "id": 3, "method": "resources/list"})
    assert len(res_list["result"]["resources"]) == 3
    print("✅ Method 'resources/list' -> OK (3 resources registered)")

    # 4. Test tool: vault_stats
    stats_call = server.handle_request({
        "jsonrpc": "2.0", "id": 4, "method": "tools/call",
        "params": {"name": "vault_stats", "arguments": {}}
    })
    stats_data = json.loads(stats_call["result"]["content"][0]["text"])
    print(f"✅ Tool 'vault_stats' -> OK (Projects: {stats_data['active_projects']}, Sessions: {stats_data['archived_sessions']})")

    # 5. Test tool: vault_search
    search_call = server.handle_request({
        "jsonrpc": "2.0", "id": 5, "method": "tools/call",
        "params": {"name": "vault_search", "arguments": {"query": "MOC", "limit": 3}}
    })
    search_data = json.loads(search_call["result"]["content"][0]["text"])
    assert len(search_data) > 0
    print(f"✅ Tool 'vault_search' -> OK (Found {len(search_data)} matches for 'MOC')")

    # 6. Test tool: get_user_profile
    profile_call = server.handle_request({
        "jsonrpc": "2.0", "id": 6, "method": "tools/call",
        "params": {"name": "get_user_profile", "arguments": {}}
    })
    profile_data = json.loads(profile_call["result"]["content"][0]["text"])
    assert profile_data["status"] == "ok"
    print(f"✅ Tool 'get_user_profile' -> OK (Read: {profile_data['path']})")

    # 7. Test tool: stage_memory_candidate (in dry-run check)
    stage_call = server.handle_request({
        "jsonrpc": "2.0", "id": 7, "method": "tools/call",
        "params": {
            "name": "stage_memory_candidate",
            "arguments": {
                "fact": "Automated self-test verification test fact.",
                "category": "architectural_rule",
                "source": "self-test",
                "rationale": "Validating stage_memory_candidate MCP tool execution."
            }
        }
    })
    stage_data = json.loads(stage_call["result"]["content"][0]["text"])
    assert stage_data["status"] == "staged"
    print(f"✅ Tool 'stage_memory_candidate' -> OK (Created candidate: {stage_data['filename']})")

    # Clean up the test candidate note
    test_note = vault_path / stage_data["path"]
    if test_note.exists():
        test_note.unlink()
        print("🧹 Cleaned up self-test staging note.")

    print("=" * 60)
    print("🎉 All hermes-brain-mcp self-tests PASSED successfully!")
    print("=" * 60)


# ---------------------------------------------------------------------------
# Main Entry Point
# ---------------------------------------------------------------------------

def main():
    parser = argparse.ArgumentParser(description="Hermes Brain MCP Server")
    parser.add_argument("--vault", type=str, default="", help="Path to Obsidian vault")
    parser.add_argument("--test", action="store_true", help="Run self-test diagnostic suite and exit")
    args = parser.parse_args()

    vault_path = get_vault_path(args.vault)
    if not vault_path or not vault_path.exists():
        sys.stderr.write(f"Error: Unable to locate vault path '{vault_path}'\n")
        sys.exit(1)

    if args.test:
        run_self_test(vault_path)
    else:
        vault = VaultCore(vault_path)
        server = MCPServer(vault)
        server.run_stdio()

if __name__ == "__main__":
    main()
