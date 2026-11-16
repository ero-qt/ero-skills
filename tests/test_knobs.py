"""Tests for skills/work-ethic/scripts/knobs.js, run with `python3 -m unittest`."""

import json
import os
import shutil
import subprocess
import tempfile
import unittest

SCRIPT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "skills", "work-ethic", "scripts", "knobs.js"))
NODE = shutil.which("node") or "node"

# Keeps the tests away from the machine's git config.
GIT_ENV = {"GIT_CONFIG_GLOBAL": os.devnull, "GIT_CONFIG_NOSYSTEM": "1"}

PHRASES = [
    ("terse ultra", "terse", "ultra"),
    ("terse lite", "terse", "lite"),
    ("normal replies", "terse", "off"),
    ("stop terse", "terse", "off"),
    ("loop strict", "loop", "strict"),
    ("loop light", "loop", "light"),
    ("auto on", "autonomy", "auto"),
    ("docs off", "docs", "off"),
    ("issues after-code", "issues", "after-code"),
    ("issues never", "issues", "never"),
    ("narrate milestones", "narrate", "milestones"),
    ("worktrees parallel", "worktrees", "parallel"),
    ("cleanup auto", "cleanup", "auto"),
    ("review-model opus low", "review-model", "opus low"),
    ("plan model haiku", "plan-model", "haiku"),
    ("impl-model sonnet high", "impl-model", "sonnet high"),
]


@unittest.skipIf(shutil.which("node") is None, "node is not installed")
class Knobs(unittest.TestCase):
    def setUp(self):
        self.repo = tempfile.mkdtemp()
        self.data = tempfile.mkdtemp()
        self.outside = tempfile.mkdtemp()
        self.env = dict(os.environ, CLAUDE_PLUGIN_DATA=self.data, **GIT_ENV)
        subprocess.run(["git", "init", "-q"], cwd=self.repo, env=self.env, check=True)

    def tearDown(self):
        for folder in (self.repo, self.data, self.outside):
            shutil.rmtree(folder, ignore_errors=True)

    def run_script(self, *args, cwd=None, stdin=""):
        return subprocess.run([NODE, SCRIPT, *args], cwd=cwd or self.repo, input=stdin, capture_output=True,
                              encoding="utf-8", env=self.env)

    def prompt(self, text, session="one", cwd=None):
        event = {"hook_event_name": "UserPromptSubmit", "session_id": session, "cwd": cwd or self.repo,
                 "prompt": text}
        result = self.run_script("prompt", cwd=cwd, stdin=json.dumps(event))
        self.assertEqual(result.returncode, 0, result.stderr)
        output = json.loads(result.stdout)["hookSpecificOutput"]
        self.assertEqual(output["hookEventName"], "UserPromptSubmit")
        return output["additionalContext"]

    def show(self, *args, cwd=None):
        result = self.run_script("show", *args, cwd=cwd)
        self.assertEqual(result.returncode, 0, result.stderr)
        return result.stdout.strip()

    def repo_file(self):
        return os.path.join(self.repo, ".git", "work-loop", "knobs.json")

    def user_file(self):
        return os.path.join(self.data, "knobs.json")

    def read_json(self, path):
        with open(path, encoding="utf-8") as file:
            return json.load(file)

    def write_json(self, path, value):
        os.makedirs(os.path.dirname(path), exist_ok=True)
        with open(path, "w", encoding="utf-8") as file:
            json.dump(value, file)

    def test_line_at_defaults_is_short(self):
        line = self.prompt("fix the build")

        self.assertIn("terse full, loop standard, gated", line)
        self.assertLess(len(line), 80)

    def test_each_phrase_sets_its_value(self):
        for phrase, knob, value in PHRASES:
            with self.subTest(phrase=phrase):
                self.prompt(phrase)
                self.assertIn(f'"{knob}": "{value}"', self.show("--json", "--session", "one"))

    def test_phrase_on_its_own_line_of_a_longer_prompt_counts(self):
        self.prompt("loop strict\nthen add the parser")

        self.assertIn("loop strict", self.show())

    # Only the terse phrases count inside a sentence. "the docs on the site" mustn't turn the docs knob on.
    def test_knob_phrase_inside_a_sentence_changes_nothing(self):
        self.prompt("update the docs on the site and keep the loop strict for now")

        self.assertEqual(self.show(), "knobs: terse full, loop standard, gated")

    def test_terse_phrase_inside_a_sentence_counts(self):
        self.prompt("terse ultra from now on please")

        self.assertIn("terse ultra", self.show())

    def test_repo_knobs_go_to_the_repo_file_and_terse_to_the_user_file(self):
        self.prompt("loop strict")
        self.prompt("terse ultra")

        self.assertEqual(self.read_json(self.repo_file()), {"loop": "strict"})
        self.assertEqual(self.read_json(self.user_file()), {"terse": "ultra"})

    def test_repo_file_wins_over_user_file(self):
        self.write_json(self.user_file(), {"loop": "light", "docs": "off"})
        self.write_json(self.repo_file(), {"loop": "strict"})

        self.assertEqual(self.show(), "knobs: terse full, loop strict, gated, docs off")

    def test_outside_a_repo_the_user_file_gets_the_knob(self):
        self.prompt("loop strict", cwd=self.outside)

        self.assertEqual(self.read_json(self.user_file()), {"loop": "strict"})

    # Autonomy lasts for 1 session and never goes in a knobs file.
    def test_auto_on_lasts_for_its_session_only(self):
        self.assertIn("auto", self.prompt("auto on", session="one"))
        self.assertIn("gated", self.prompt("fix the build", session="two"))
        self.assertFalse(os.path.exists(self.repo_file()))
        self.assertFalse(os.path.exists(self.user_file()))

    def test_auto_off_ends_auto(self):
        self.prompt("auto on")

        self.assertIn("gated", self.prompt("auto off"))

    def test_set_writes_the_repo_file(self):
        result = self.run_script("set", "loop", "strict")

        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(self.read_json(self.repo_file()), {"loop": "strict"})

    def test_set_with_user_flag_writes_the_user_file(self):
        self.run_script("set", "docs", "on", "--user")

        self.assertEqual(self.read_json(self.user_file()), {"docs": "on"})
        self.assertFalse(os.path.exists(self.repo_file()))

    def test_set_takes_a_model_and_an_effort(self):
        self.run_script("set", "review-model", "opus", "low")

        self.assertEqual(self.read_json(self.repo_file()), {"review-model": "opus low"})

    def test_set_refuses_an_unknown_knob_or_value(self):
        for args in (["colour", "blue"], ["loop", "fast"], ["review-model"]):
            with self.subTest(args=args):
                result = self.run_script("set", *args)
                self.assertEqual(result.returncode, 1)
                self.assertTrue(result.stderr.strip())
        self.assertFalse(os.path.exists(self.repo_file()))

    def test_set_refuses_autonomy(self):
        result = self.run_script("set", "autonomy", "auto")

        self.assertEqual(result.returncode, 1)
        self.assertIn("autonomy", result.stderr)

    def test_data_flag_wins_over_the_environment(self):
        other = tempfile.mkdtemp()
        self.addCleanup(shutil.rmtree, other, True)
        self.run_script("--data", other, "set", "docs", "on", "--user")

        self.assertEqual(self.read_json(os.path.join(other, "knobs.json")), {"docs": "on"})

    def test_broken_files_and_events_fall_back_to_defaults(self):
        os.makedirs(os.path.dirname(self.repo_file()))
        with open(self.repo_file(), "w", encoding="utf-8") as file:
            file.write("{not json")

        self.assertEqual(self.show(), "knobs: terse full, loop standard, gated")
        result = self.run_script("prompt", stdin="not json")
        self.assertEqual(result.returncode, 0, result.stderr)


if __name__ == "__main__":
    unittest.main()
