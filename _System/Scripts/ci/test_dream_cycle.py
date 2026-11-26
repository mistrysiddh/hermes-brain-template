#!/usr/bin/env python3
"""
test_dream_cycle.py — Unit tests for dream_cycle.py (v2).
"""
import os
import sys
import shutil
import tempfile
import unittest
from pathlib import Path

SCRIPT_DIR = Path(__file__).resolve().parent
SCRIPTS_DIR = SCRIPT_DIR.parent
sys.path.insert(0, str(SCRIPTS_DIR))

from dream_cycle import extract_session_data, detect_contradictions, check_and_draft_adrs, auto_stage_memory_candidates


class DreamCycleV2Tests(unittest.TestCase):
    def setUp(self):
        self.test_dir = tempfile.mkdtemp(prefix="hb-ci-dream-")
        self.vault = Path(self.test_dir)
        (self.vault / "01-Projects" / "ADR").mkdir(parents=True)
        (self.vault / "02-Areas").mkdir(parents=True)
        (self.vault / "03-Resources" / "Research").mkdir(parents=True)
        (self.vault / "04-Archives" / "Daily" / "2026" / "09" / "26").mkdir(parents=True)
        (self.vault / "04-Archives" / "Memory-Review").mkdir(parents=True)

        # Create active ADR
        (self.vault / "01-Projects" / "ADR" / "ADR-001.md").write_text(
            "---\nstatus: accepted\n---\n# ADR 001\nStandardized on sqlite database.", encoding="utf-8"
        )

        # Create session 1
        self.s1_file = self.vault / "04-Archives" / "Daily" / "2026" / "09" / "26" / "sess-1.md"
        self.s1_file.write_text(
            "# Sess 1\nRule: Always sanitize inputs before DB queries.\nConnecting to postgres backend.\nTags: #db #postgres",
            encoding="utf-8"
        )

    def tearDown(self):
        shutil.rmtree(self.test_dir, ignore_errors=True)

    def test_contradiction_detection(self):
        data = extract_session_data(self.s1_file)
        self.assertIsNotNone(data)
        conflicts = detect_contradictions([data], self.vault)
        # ADR-001 says sqlite, session uses postgres -> should flag drift
        self.assertTrue(len(conflicts) >= 1)
        self.assertIn("ADR Divergence", conflicts[0]["type"])

    def test_auto_stage_memory(self):
        data = extract_session_data(self.s1_file)
        staged = auto_stage_memory_candidates([data], self.vault)
        self.assertTrue(len(staged) >= 1)
        self.assertIn("sanitize inputs", staged[0]["fact"])
        # Verify file exists on disk in Memory-Review
        candidate_file = self.vault / "04-Archives" / "Memory-Review" / staged[0]["file"]
        self.assertTrue(candidate_file.exists())


if __name__ == "__main__":
    unittest.main()
