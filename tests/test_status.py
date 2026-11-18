"""Tests for skills/work-ethic/scripts/status.js, run with `python3 -m unittest`."""

import datetime
import json
import os
import shutil
import subprocess
import tempfile
import unittest

SCRIPT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "skills", "work-ethic", "scripts", "status.js"))
NODE = shutil.which("node") or "node"


def days_ago(days):
    time = datetime.datetime.now(datetime.timezone.utc) - datetime.timedelta(days=days)
    return time.isoformat().replace("+00:00", "Z")


@unittest.skipIf(shutil.which("node") is None, "node is not installed")
class Status(unittest.TestCase):
    def setUp(self):
        self.data = tempfile.mkdtemp()
        self.env = dict(os.environ, CLAUDE_PLUGIN_DATA=self.data)

    def tearDown(self):
        shutil.rmtree(self.data, ignore_errors=True)

    def log(self, *records, raw=""):
        with open(os.path.join(self.data, "slips.jsonl"), "a", encoding="utf-8") as file:
            file.write("".join(json.dumps(record) + "\n" for record in records) + raw)

    def status(self, *args):
        result = subprocess.run([NODE, SCRIPT, *args], capture_output=True, encoding="utf-8", env=self.env)
        self.assertEqual(result.returncode, 0, result.stderr)
        return result.stdout.strip().splitlines()

    def slip(self, rule, days=0, check="reply", kind="hard"):
        return {"time": days_ago(days), "check": check, "rule": rule, "kind": kind, "detail": "x"}

    def test_counts_each_rule_of_the_last_7_days_most_first(self):
        self.log(self.slip("dash"), self.slip("gate-length", 1), self.slip("dash", 2),
                 self.slip("trailer", 3, check="commit"), self.slip("dash", 9))

        self.assertEqual(self.status(), [
            "slips in 7 days: 4",
            "reply dash (hard): 2",
            "commit trailer (hard): 1",
            "reply gate-length (hard): 1",
        ])

    def test_days_flag_widens_the_window(self):
        self.log(self.slip("dash"), self.slip("dash", 9))

        self.assertEqual(self.status("--days", "30"), ["slips in 30 days: 2", "reply dash (hard): 2"])

    def test_broken_lines_are_skipped(self):
        self.log(self.slip("bullets", kind="soft"), raw="not json\n{}\n")

        self.assertEqual(self.status(), ["slips in 7 days: 1", "reply bullets (soft): 1"])

    def test_missing_log_shows_0(self):
        self.assertEqual(self.status(), ["slips in 7 days: 0"])

    def test_data_flag_wins_over_the_environment(self):
        other = tempfile.mkdtemp()
        self.addCleanup(shutil.rmtree, other, True)
        with open(os.path.join(other, "slips.jsonl"), "w", encoding="utf-8") as file:
            file.write(json.dumps(self.slip("opener")) + "\n")

        self.assertEqual(self.status("--data", other), ["slips in 7 days: 1", "reply opener (hard): 1"])

    def test_bad_days_value_fails(self):
        result = subprocess.run([NODE, SCRIPT, "--days", "soon"], capture_output=True, encoding="utf-8",
                                env=self.env)

        self.assertEqual(result.returncode, 1)
        self.assertTrue(result.stderr.strip())


if __name__ == "__main__":
    unittest.main()
