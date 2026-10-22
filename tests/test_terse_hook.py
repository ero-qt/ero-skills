"""Tests for skills/terse-replies/scripts/terse-hook.js, run with `python3 -m unittest`."""

import json
import os
import shutil
import subprocess
import tempfile
import unittest

SCRIPT = os.path.join(os.path.dirname(__file__), "..", "skills", "terse-replies", "scripts", "terse-hook.js")
NODE = shutil.which("node") or "node"


@unittest.skipIf(shutil.which("node") is None, "node is not installed")
class TerseHook(unittest.TestCase):
    def setUp(self):
        self.data = tempfile.mkdtemp()

    def tearDown(self):
        shutil.rmtree(self.data, ignore_errors=True)

    def run_hook(self, mode, prompt=""):
        env = dict(os.environ, CLAUDE_PLUGIN_DATA=self.data)
        result = subprocess.run([NODE, SCRIPT, mode], input=json.dumps({"prompt": prompt}), capture_output=True,
                                encoding="utf-8", env=env, check=True)
        if not result.stdout.strip():
            return {}
        return json.loads(result.stdout)["hookSpecificOutput"]

    # A prompt without a level command gets a reminder at the default level, full.
    def test_prompt_without_command_reminds_at_full(self):
        output = self.run_hook("prompt", "fix the build")

        self.assertEqual(output["hookEventName"], "UserPromptSubmit")
        self.assertIn("TERSE FULL", output["additionalContext"])
        self.assertIn("caveman: fragments, no articles, no filler.", output["additionalContext"])

    # A level command switches the level for this prompt and every later one.
    def test_level_command_switches_and_sticks(self):
        self.run_hook("prompt", "terse ultra")
        output = self.run_hook("prompt", "next task")

        self.assertIn("TERSE ULTRA", output["additionalContext"])
        self.assertIn("`path:l:c`", output["additionalContext"])

    # "normal replies" turns the reminder off until a level command turns it back on.
    def test_normal_replies_turns_reminder_off(self):
        self.run_hook("prompt", "normal replies please")

        self.assertEqual(self.run_hook("prompt", "next task"), {})
        self.assertIn("TERSE LITE", self.run_hook("prompt", "terse lite")["additionalContext"])

    # The session start text repeats the level, so it comes back after a compaction.
    def test_session_start_states_the_level(self):
        self.run_hook("prompt", "terse ultra")
        output = self.run_hook("session")

        self.assertEqual(output["hookEventName"], "SessionStart")
        self.assertIn("TERSE ULTRA", output["additionalContext"])


if __name__ == "__main__":
    unittest.main()
