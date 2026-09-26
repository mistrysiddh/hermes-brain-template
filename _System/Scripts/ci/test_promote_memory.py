#!/usr/bin/env python3
"""
test_promote_memory.py — Unit tests for promote_memory.py.
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

from promote_memory import MemoryPromoter


class PromoteMemoryTests(unittest.TestCase):
    def setUp(self):
        self.test_dir = tempfile.mkdtemp(prefix="hb-ci-promote-")
        self.vault = Path(self.test_dir) / "Vault"
        self.vault.mkdir()
        (self.vault / "02-Areas").mkdir(parents=True)
        (self.vault / "04-Archives" / "Memory-Review").mkdir(parents=True)
        (self.vault / "02-Areas" / "User-Profile.md").write_text("# User Profile\n", encoding="utf-8")

        self.hermes_mem = Path(self.test_dir) / "MEMORY.md"
        self.promoter = MemoryPromoter(self.vault, self.hermes_mem)

    def tearDown(self):
        shutil.rmtree(self.test_dir, ignore_errors=True)

    def test_promotion_lifecycle(self):
        candidate_file = self.vault / "04-Archives" / "Memory-Review" / "candidate_ci_test.md"
        candidate_file.write_text("""---
type: memory-candidate
status: pending-review
category: user_preference
source: "ci-test"
---

# 🧠 Memory Candidate: Tab Indentation

### Candidate Fact
> Prefer 2-space indentation over tabs for YAML configurations.
""", encoding="utf-8")

        cands = self.promoter.list_candidates()
        self.assertEqual(len(cands), 1)
        self.assertIn("2-space indentation", cands[0]["fact"])

        res = self.promoter.promote_to_hermes(cands[0]["fact"], cands[0]["category"], candidate_file)
        self.assertEqual(res["status"], "success")

        # Verify target memory has entry
        self.assertTrue(self.hermes_mem.exists())
        self.assertIn("2-space indentation", self.hermes_mem.read_text(encoding="utf-8"))

        # Verify candidate moved to Reviewed/
        reviewed_dest = self.vault / "04-Archives" / "Memory-Review" / "Reviewed" / "candidate_ci_test.md"
        self.assertTrue(reviewed_dest.exists())

        # Verify no open candidates left
        remaining = self.promoter.list_candidates()
        self.assertEqual(len(remaining), 0)


if __name__ == "__main__":
    unittest.main()
