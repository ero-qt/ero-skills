"""Tests for skills/work-loop/scripts/state.sh, run with `python3 -m unittest`."""

import os
import subprocess
import tempfile
import unittest

SCRIPT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "skills", "work-loop", "scripts", "state.sh"))


class Upstream(unittest.TestCase):
    def test_branch_without_upstream_is_reported_as_not_pushed(self):
        with tempfile.TemporaryDirectory() as repo:
            subprocess.run(["git", "init", "-q", "-b", "topic"], cwd=repo, check=True)
            result = subprocess.run(["bash", SCRIPT], cwd=repo, capture_output=True, encoding="utf-8")
        self.assertIn("branch topic isn't pushed (no upstream)", result.stdout)


if __name__ == "__main__":
    unittest.main()
