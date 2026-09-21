#!/usr/bin/env python3
"""
test_consolidate_memory.py — content-correctness tests for consolidate_memory.py.

Unlike the CI runtime smoke-test (which only checks that a report file gets
written), this asserts on the ACTUAL CONTENTS of what consolidate_memory.py
produces — since this script gates what a human eventually copies into
Hermes's permanent MEMORY.md/USER.md, "it ran without crashing" isn't enough.

Run directly:
    python3 Scripts/ci/test_consolidate_memory.py

Exits non-zero (with a clear assertion message) on any failure, for CI use.
Uses only stdlib (unittest) — no pytest dependency, consistent with the rest
of this repo's Scripts/.
"""
import json
import os
import shutil
import subprocess
import sys
import tempfile
import unittest

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
CONSOLIDATE_SCRIPT = os.path.join(os.path.dirname(SCRIPT_DIR), "consolidate_memory.py")
if not os.path.exists(CONSOLIDATE_SCRIPT):
    CONSOLIDATE_SCRIPT = os.path.join(os.path.dirname(os.path.dirname(SCRIPT_DIR)), "_System", "Scripts", "consolidate_memory.py")


def write(path, content):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        f.write(content)


def run_consolidate(vault_root):
    result = subprocess.run(
        [sys.executable, CONSOLIDATE_SCRIPT, vault_root],
        capture_output=True, text=True,
    )
    return result


class ConsolidateMemoryTests(unittest.TestCase):
    def setUp(self):
        self.vault = tempfile.mkdtemp(prefix="hb-consolidate-test-")
        self.mr_dir = os.path.join(self.vault, "Memory-Review")

    def tearDown(self):
        shutil.rmtree(self.vault, ignore_errors=True)

    def _candidates_text(self):
        path = os.path.join(self.mr_dir, "Promotion-Candidates.md")
        with open(path, encoding="utf-8") as f:
            return f.read()

    def _excluded_text(self):
        path = os.path.join(self.mr_dir, "Excluded-Sensitive.md")
        if not os.path.exists(path):
            return ""
        with open(path, encoding="utf-8") as f:
            return f.read()

    def test_exact_duplicate_is_deduped(self):
        """Two identical facts on the same date should appear only once."""
        write(
            os.path.join(self.mr_dir, "Supermemory-All-Memory-Entries.md"),
            "## 2026-01-01\n"
            "- User prefers dark mode in all applications\n"
            "- User prefers dark mode in all applications\n",
        )
        result = run_consolidate(self.vault)
        self.assertEqual(result.returncode, 0, msg=f"stderr: {result.stderr}")

        candidates = self._candidates_text()
        occurrences = candidates.count("User prefers dark mode in all applications")
        self.assertEqual(
            occurrences, 1,
            msg=f"Expected the exact-duplicate fact to appear exactly once, "
                f"found {occurrences}. Full candidates file:\n{candidates}",
        )
        self.assertIn("Deduped/skipped: **1**", candidates)

    def test_near_duplicate_is_fuzzy_deduped(self):
        """Two near-identical rephrasings should collapse to one candidate."""
        write(
            os.path.join(self.mr_dir, "Supermemory-All-Memory-Entries.md"),
            "## 2026-01-01\n"
            "- User works as a technical trainer and AI builder\n"
            "- User works as a technical trainer and an AI builder\n",
        )
        result = run_consolidate(self.vault)
        self.assertEqual(result.returncode, 0, msg=f"stderr: {result.stderr}")

        candidates = self._candidates_text()
        # Count checkbox lines under the date heading — should be 1, not 2.
        bullet_count = candidates.count("- [ ] User works as a technical trainer")
        self.assertEqual(
            bullet_count, 1,
            msg=f"Expected near-duplicate facts to fuzzy-dedupe to 1 candidate, "
                f"found {bullet_count}. Full candidates file:\n{candidates}",
        )

    def test_secret_looking_string_is_scrubbed(self):
        """A fact containing an API-key-shaped string must never reach
        Promotion-Candidates.md, and must land in Excluded-Sensitive.md."""
        secret_fact = "The deploy script uses api_key: sk-abcdef1234567890ABCDEF1234567890"
        write(
            os.path.join(self.mr_dir, "Supermemory-All-Memory-Entries.md"),
            f"## 2026-01-01\n- {secret_fact}\n",
        )
        result = run_consolidate(self.vault)
        self.assertEqual(result.returncode, 0, msg=f"stderr: {result.stderr}")

        candidates = self._candidates_text()
        self.assertNotIn(
            "sk-abcdef1234567890ABCDEF1234567890", candidates,
            msg=f"Secret-looking string leaked into Promotion-Candidates.md:\n{candidates}",
        )
        self.assertIn("Sensitive excluded: **1**", candidates)

        excluded = self._excluded_text()
        self.assertIn(
            "sk-abcdef1234567890ABCDEF1234567890", excluded,
            msg=f"Expected the secret to be logged in Excluded-Sensitive.md for audit, "
                f"got:\n{excluded}",
        )

    def test_normal_fact_is_not_flagged_as_secret(self):
        """A plain fact must NOT be misclassified as sensitive (false positive check)."""
        write(
            os.path.join(self.mr_dir, "Supermemory-All-Memory-Entries.md"),
            "## 2026-01-01\n- User's timezone is Asia/Kolkata (IST, UTC+05:30)\n",
        )
        result = run_consolidate(self.vault)
        self.assertEqual(result.returncode, 0, msg=f"stderr: {result.stderr}")

        candidates = self._candidates_text()
        self.assertIn(
            "User's timezone is Asia/Kolkata", candidates,
            msg=f"Normal fact was incorrectly excluded. Candidates:\n{candidates}\n"
                f"Excluded:\n{self._excluded_text()}",
        )

    def test_decided_candidate_does_not_reappear(self):
        """A candidate checked off [x] in a previous run must not resurface
        on the next run, even if the same fact source still contains it.

        This is a regression test for the exact bug fixed in v1.1.0: the
        script previously compared full 40-char hashes against 8-char
        prefix keys, so already-approved candidates kept reappearing."""
        fact = "User's GitHub username is a placeholder-example-user"
        write(
            os.path.join(self.mr_dir, "Supermemory-All-Memory-Entries.md"),
            f"## 2026-01-01\n- {fact}\n",
        )

        # First run: candidate appears fresh.
        result1 = run_consolidate(self.vault)
        self.assertEqual(result1.returncode, 0, msg=f"stderr: {result1.stderr}")
        candidates1 = self._candidates_text()
        self.assertIn(fact, candidates1)

        # Simulate the user checking the box in Obsidian.
        candidates1 = candidates1.replace("- [ ] " + fact, "- [x] " + fact)
        write(os.path.join(self.mr_dir, "Promotion-Candidates.md"), candidates1)

        # Second run: same fact still in the source file, but should now be
        # archived to Consolidation-Log.md and absent from the fresh candidates list.
        result2 = run_consolidate(self.vault)
        self.assertEqual(result2.returncode, 0, msg=f"stderr: {result2.stderr}")
        candidates2 = self._candidates_text()
        self.assertNotIn(
            fact, candidates2,
            msg=f"Decided candidate reappeared after being checked off — "
                f"this is the v1.1.0 regression. Candidates:\n{candidates2}",
        )

        log_path = os.path.join(self.mr_dir, "Consolidation-Log.md")
        self.assertTrue(os.path.exists(log_path), msg="Consolidation-Log.md was not created")
        with open(log_path, encoding="utf-8") as f:
            log = f.read()
        self.assertIn(fact, log, msg=f"Decided candidate not found in Consolidation-Log.md:\n{log}")

    def test_state_file_is_valid_json(self):
        """The persisted state file must round-trip as valid JSON (a
        corrupted state file would silently reset dedup/decided history)."""
        write(
            os.path.join(self.mr_dir, "Supermemory-All-Memory-Entries.md"),
            "## 2026-01-01\n- A simple fact for state-file validation\n",
        )
        result = run_consolidate(self.vault)
        self.assertEqual(result.returncode, 0, msg=f"stderr: {result.stderr}")

        state_path = os.path.join(self.mr_dir, ".consolidate_state.json")
        self.assertTrue(os.path.exists(state_path))
        with open(state_path, encoding="utf-8") as f:
            state = json.load(f)  # raises if invalid
        self.assertIn("decided_hashes", state)
        self.assertIn("first_seen", state)


if __name__ == "__main__":
    unittest.main(verbosity=2)
