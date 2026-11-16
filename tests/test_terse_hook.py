"""Tests for skills/terse-replies/scripts/terse-hook.js, run with `python3 -m unittest`."""

import json
import os
import shutil
import subprocess
import tempfile
import unittest

SCRIPTS = os.path.join(os.path.dirname(__file__), "..", "skills", "terse-replies", "scripts")
SCRIPT = os.path.join(SCRIPTS, "terse-hook.js")
CHECK = os.path.join(SCRIPTS, "reply-check.js")
LONG_GATE = "\n".join([f"`file{index}.py`: change {index}" for index in range(17)] + ["`Add retry limit`", "Approve?"])
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

    def end_turn(self, message):
        env = dict(os.environ, CLAUDE_PLUGIN_DATA=self.data)
        event = {"hook_event_name": "Stop", "stop_hook_active": False, "last_assistant_message": message}
        subprocess.run([NODE, CHECK], input=json.dumps(event), capture_output=True, encoding="utf-8", env=env,
                       check=True)

    # A prompt without a level command gets a 1-line reminder at the default level, full.
    def test_prompt_without_command_reminds_at_full_in_1_line(self):
        output = self.run_hook("prompt", "fix the build")

        self.assertEqual(output["hookEventName"], "UserPromptSubmit")
        self.assertIn("TERSE FULL", output["additionalContext"])
        self.assertNotIn("caveman", output["additionalContext"])
        self.assertLess(len(output["additionalContext"]), 80)

    # After a reply with a hard finding, the next prompt gets the full reminder with the broken rule, then 1 line again.
    def test_hard_finding_brings_back_the_full_reminder_once(self):
        self.end_turn(LONG_GATE)
        full = self.run_hook("prompt", "next task")["additionalContext"]
        short = self.run_hook("prompt", "next task")["additionalContext"]

        self.assertIn("caveman: fragments, no articles, no filler.", full)
        self.assertIn("gate is 19 lines, max 12", full)
        self.assertLess(len(short), 80)

    # A soft finding only goes to the log and keeps the reminder at 1 line.
    def test_soft_finding_keeps_the_short_reminder(self):
        self.end_turn("6 files.\n" + "\n".join(f"- `f{index}.py`" for index in range(6)))

        self.assertLess(len(self.run_hook("prompt", "next task")["additionalContext"]), 80)

    # A level command switches the level for this prompt and every later one.
    def test_level_command_switches_and_sticks(self):
        self.run_hook("prompt", "terse ultra")
        output = self.run_hook("prompt", "next task")

        self.assertIn("TERSE ULTRA", output["additionalContext"])

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
        self.assertIn("`path:l:c`", output["additionalContext"])


if __name__ == "__main__":
    unittest.main()
