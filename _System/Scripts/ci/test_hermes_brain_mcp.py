#!/usr/bin/env python3
"""
test_hermes_brain_mcp.py — Unit and integration tests for hermes_brain_mcp.py.

Asserts protocol correctness, JSON-RPC compliance, tool execution, and resource
reading for hermes-brain-mcp without external dependencies.
"""
import os
import sys
import json
import shutil
import tempfile
import unittest
from pathlib import Path

# Add _System/Scripts to path
SCRIPT_DIR = Path(__file__).resolve().parent
SCRIPTS_DIR = SCRIPT_DIR.parent
sys.path.insert(0, str(SCRIPTS_DIR))

from hermes_brain_mcp import VaultCore, MCPServer


class HermesBrainMCPTests(unittest.TestCase):
    def setUp(self):
        self.test_dir = tempfile.mkdtemp(prefix="hb-mcp-test-")
        self.vault_path = Path(self.test_dir)

        # Create vault structure
        (self.vault_path / "01-Projects" / "ADR").mkdir(parents=True)
        (self.vault_path / "02-Areas").mkdir(parents=True)
        (self.vault_path / "03-Resources").mkdir(parents=True)
        (self.vault_path / "04-Archives" / "Daily").mkdir(parents=True)
        (self.vault_path / "04-Archives" / "Memory-Review").mkdir(parents=True)

        # Create dummy notes
        (self.vault_path / "MOC.md").write_text("# MOC\nCentral Map of Content", encoding="utf-8")
        (self.vault_path / "02-Areas" / "User-Profile.md").write_text("# User Profile\nPrefer TypeScript and Python.", encoding="utf-8")
        (self.vault_path / "01-Projects" / "Project-Alpha.md").write_text("# Project Alpha\nWorking on autonomous agents.", encoding="utf-8")
        (self.vault_path / "01-Projects" / "ADR" / "ADR-001.md").write_text("---\nstatus: accepted\n---\n# ADR 001: Use SQLite", encoding="utf-8")

        self.vault = VaultCore(self.vault_path)
        self.server = MCPServer(self.vault)

    def tearDown(self):
        shutil.rmtree(self.test_dir, ignore_errors=True)

    def test_initialize(self):
        req = {"jsonrpc": "2.0", "id": 1, "method": "initialize"}
        resp = self.server.handle_request(req)
        self.assertEqual(resp["jsonrpc"], "2.0")
        self.assertEqual(resp["result"]["serverInfo"]["name"], "hermes-brain-mcp")
        self.assertIn("tools", resp["result"]["capabilities"])

    def test_tools_list(self):
        req = {"jsonrpc": "2.0", "id": 2, "method": "tools/list"}
        resp = self.server.handle_request(req)
        tools = {t["name"] for t in resp["result"]["tools"]}
        expected = {"vault_search", "read_note", "get_user_profile", "get_active_adrs", "stage_memory_candidate", "vault_stats"}
        self.assertTrue(expected.issubset(tools))

    def test_resources_list_and_read(self):
        list_req = {"jsonrpc": "2.0", "id": 3, "method": "resources/list"}
        list_resp = self.server.handle_request(list_req)
        uris = {r["uri"] for r in list_resp["result"]["resources"]}
        self.assertIn("vault://MOC", uris)
        self.assertIn("vault://User-Profile", uris)

        read_req = {"jsonrpc": "2.0", "id": 4, "method": "resources/read", "params": {"uri": "vault://MOC"}}
        read_resp = self.server.handle_request(read_req)
        self.assertIn("Central Map of Content", read_resp["result"]["contents"][0]["text"])

    def test_vault_search(self):
        req = {
            "jsonrpc": "2.0", "id": 5, "method": "tools/call",
            "params": {"name": "vault_search", "arguments": {"query": "autonomous"}}
        }
        resp = self.server.handle_request(req)
        data = json.loads(resp["result"]["content"][0]["text"])
        self.assertEqual(len(data), 1)
        self.assertEqual(data[0]["path"], "01-Projects/Project-Alpha.md")

    def test_get_user_profile(self):
        req = {"jsonrpc": "2.0", "id": 6, "method": "tools/call", "params": {"name": "get_user_profile"}}
        resp = self.server.handle_request(req)
        data = json.loads(resp["result"]["content"][0]["text"])
        self.assertEqual(data["status"], "ok")
        self.assertIn("TypeScript and Python", data["content"])

    def test_get_active_adrs(self):
        req = {"jsonrpc": "2.0", "id": 7, "method": "tools/call", "params": {"name": "get_active_adrs"}}
        resp = self.server.handle_request(req)
        data = json.loads(resp["result"]["content"][0]["text"])
        self.assertEqual(len(data), 1)
        self.assertEqual(data[0]["title"], "ADR-001")
        self.assertEqual(data[0]["status"], "accepted")

    def test_stage_memory_candidate(self):
        req = {
            "jsonrpc": "2.0", "id": 8, "method": "tools/call",
            "params": {
                "name": "stage_memory_candidate",
                "arguments": {
                    "fact": "Always use UTC timestamps in telemetry reports.",
                    "category": "architectural_rule",
                    "source": "cron_test"
                }
            }
        }
        resp = self.server.handle_request(req)
        data = json.loads(resp["result"]["content"][0]["text"])
        self.assertEqual(data["status"], "staged")
        candidate_file = self.vault_path / data["path"]
        self.assertTrue(candidate_file.exists())
        content = candidate_file.read_text(encoding="utf-8")
        self.assertIn("Always use UTC timestamps in telemetry reports.", content)


if __name__ == "__main__":
    unittest.main()
