"""Tests for skills/work-loop/scripts/commit-guard.js, run with `python3 -m unittest`."""

import json
import os
import shutil
import subprocess
import tempfile
import unittest

SCRIPTS = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "skills", "work-loop", "scripts"))
GUARD = os.path.join(SCRIPTS, "commit-guard.js")
LEDGER = os.path.join(SCRIPTS, "ledger.js")
NODE = shutil.which("node") or "node"

# Keeps the tests away from the machine's git config.
GIT_ENV = {
    "GIT_CONFIG_GLOBAL": os.devnull,
    "GIT_CONFIG_NOSYSTEM": "1",
    "GIT_AUTHOR_NAME": "Test",
    "GIT_AUTHOR_EMAIL": "test@example.com",
    "GIT_COMMITTER_NAME": "Test",
    "GIT_COMMITTER_EMAIL": "test@example.com",
}

TRAILER = "Co-Authored-By: Someone <someone@example.com>"
DASH = "—"


@unittest.skipIf(shutil.which("node") is None, "node is not installed")
class CommitGuard(unittest.TestCase):
    def setUp(self):
        self.repo = tempfile.mkdtemp()
        self.data = tempfile.mkdtemp()
        self.env = dict(os.environ, CLAUDE_PLUGIN_DATA=self.data, **GIT_ENV)
        self.git("init", "-q", "-b", "main")
        self.write("README.md", "# Demo\n")
        self.git("add", "README.md")
        self.git("commit", "-q", "-m", "Add readme")

    def tearDown(self):
        shutil.rmtree(self.repo, ignore_errors=True)
        shutil.rmtree(self.data, ignore_errors=True)

    def git(self, *args):
        return subprocess.run(["git", *args], cwd=self.repo, env=self.env, check=True, capture_output=True,
                              encoding="utf-8").stdout

    def write(self, name, text):
        path = os.path.join(self.repo, name)
        os.makedirs(os.path.dirname(path), exist_ok=True)
        with open(path, "w", encoding="utf-8", newline="\n") as file:
            file.write(text)

    def stage(self, name, text):
        self.write(name, text)
        self.git("add", name)

    def set_knobs(self, **knobs):
        folder = os.path.join(self.repo, ".git", "work-loop")
        os.makedirs(folder, exist_ok=True)
        with open(os.path.join(folder, "knobs.json"), "w", encoding="utf-8") as file:
            json.dump(knobs, file)

    def guard(self, command='git commit -m "Add parser"', tool="Bash", cwd=None, raw=None):
        event = {"hook_event_name": "PreToolUse", "cwd": cwd or self.repo, "tool_name": tool,
                 "tool_input": {"command": command}}
        result = subprocess.run([NODE, GUARD], input=raw if raw is not None else json.dumps(event),
                                capture_output=True, encoding="utf-8", env=self.env)
        self.assertEqual(result.returncode, 0, result.stderr)
        return json.loads(result.stdout)["hookSpecificOutput"] if result.stdout.strip() else None

    def assert_denied(self, output, *words):
        self.assertIsNotNone(output, "the commit went through")
        self.assertEqual(output["permissionDecision"], "deny")
        for word in words:
            self.assertIn(word, output["permissionDecisionReason"])

    def slips(self):
        path = os.path.join(self.data, "slips.jsonl")
        if not os.path.exists(path):
            return []
        with open(path, encoding="utf-8") as file:
            return [json.loads(line) for line in file if line.strip()]

    # A clean commit gets no output and goes through the normal permission prompt.
    def test_clean_commit_passes(self):
        self.stage("parser.py", "def parse(text):\n    return text.split()\n")

        self.assertIsNone(self.guard())

    # Commands that don't commit are never checked.
    def test_other_commands_pass(self):
        self.stage("notes.md", f"A {DASH} B\n")

        for command in ["git status", "git log --grep commit", "echo git commit", "npm test"]:
            with self.subTest(command=command):
                self.assertIsNone(self.guard(command))

    def test_trailer_in_the_message_is_denied(self):
        self.stage("parser.py", "x = 1\n")

        self.assert_denied(self.guard(f'git commit -m "Add parser" -m "{TRAILER}"'), "trailer")

    def test_trailer_in_a_heredoc_message_is_denied(self):
        self.stage("parser.py", "x = 1\n")
        command = f"git commit -F - <<'EOF'\nAdd parser\n\n{TRAILER}\nEOF"

        self.assert_denied(self.guard(command), "trailer")

    def test_trailer_in_a_message_file_is_denied(self):
        self.stage("parser.py", "x = 1\n")
        message = os.path.join(self.data, "message.txt")
        with open(message, "w", encoding="utf-8") as file:
            file.write(f"Add parser\n\n{TRAILER}\n")

        self.assert_denied(self.guard(f'git commit -F "{message}"'), "trailer")

    # A hard finding of the prose check in the staged lines denies the commit.
    def test_hard_prose_finding_in_staged_lines_is_denied(self):
        self.stage("notes.md", f"The parser stops {DASH} it reads 1 line.\n")

        self.assert_denied(self.guard(), "prose check", "notes.md")

    # A check finding only needs a look, so it doesn't deny.
    def test_check_prose_finding_passes(self):
        self.stage("notes.md", "Note that the parser reads 1 line.\n")

        self.assertIsNone(self.guard())

    def test_dash_in_the_subject_is_denied(self):
        self.stage("parser.py", "x = 1\n")

        self.assert_denied(self.guard(f'git commit -m "Add parser {DASH} with tests"'), "prose check", "message")

    # Short flags can come together, like `-am` or `-sm`.
    def test_dash_in_a_message_after_joined_flags_is_denied(self):
        self.stage("parser.py", "x = 1\n")

        self.assert_denied(self.guard(f'git commit -am "Add parser {DASH} with tests"'), "prose check", "message")

    def test_default_never_stage_path_is_denied(self):
        self.stage(".env", "TOKEN=1\n")

        self.assert_denied(self.guard(), ".env")

    # The repo adds its own paths in .git/work-loop/never-stage, 1 pattern per line.
    def test_repo_never_stage_pattern_is_denied(self):
        os.makedirs(os.path.join(self.repo, ".git", "work-loop"), exist_ok=True)
        self.write(".git/work-loop/never-stage", "# local files\n.scratch/\n*.local.json\n")

        for name in [".scratch/plan.md", "config/app.local.json"]:
            with self.subTest(name=name):
                self.git("reset", "-q")
                self.stage(name, "x\n")
                self.assert_denied(self.guard(), name)

    def test_path_outside_the_patterns_passes(self):
        os.makedirs(os.path.join(self.repo, ".git", "work-loop"), exist_ok=True)
        self.write(".git/work-loop/never-stage", ".scratch/\n")
        self.stage("src/scratch.py", "x = 1\n")

        self.assertIsNone(self.guard())

    # At loop strict with docs on, source without a doc change is denied.
    def test_source_without_docs_is_denied_at_strict(self):
        self.set_knobs(docs="on", loop="strict")
        self.stage("parser.py", "x = 1\n")

        self.assert_denied(self.guard(), "docs", "ledger.js")

    # Below strict the same commit goes through with a warning for Claude.
    def test_source_without_docs_warns_below_strict(self):
        self.set_knobs(docs="on", loop="standard")
        self.stage("parser.py", "x = 1\n")

        output = self.guard()

        self.assertIsNotNone(output)
        self.assertNotIn("permissionDecision", output)
        self.assertIn("docs", output["additionalContext"])

    def test_ledger_reason_clears_the_docs_check(self):
        self.set_knobs(docs="on", loop="strict")
        self.stage("parser.py", "x = 1\n")
        subprocess.run([NODE, LEDGER, "add", "docs", "none: internal refactor"], cwd=self.repo, env=self.env,
                       check=True, capture_output=True)

        self.assertIsNone(self.guard())

    # A ledger record from before the last commit doesn't count for this one.
    def test_ledger_reason_of_an_earlier_commit_doesnt_count(self):
        self.set_knobs(docs="on", loop="strict")
        subprocess.run([NODE, LEDGER, "add", "docs", "none: internal refactor"], cwd=self.repo, env=self.env,
                       check=True, capture_output=True)
        self.stage("a.md", "A\n")
        self.git("commit", "-q", "-m", "Add a")
        self.stage("parser.py", "x = 1\n")

        self.assert_denied(self.guard(), "docs")

    def test_ledger_record_without_a_reason_doesnt_count(self):
        self.set_knobs(docs="on", loop="strict")
        self.stage("parser.py", "x = 1\n")
        subprocess.run([NODE, LEDGER, "add", "docs", "none:"], cwd=self.repo, env=self.env, capture_output=True)

        self.assert_denied(self.guard(), "docs")

    def test_source_with_a_doc_change_passes(self):
        self.set_knobs(docs="on", loop="strict")
        self.stage("parser.py", "x = 1\n")
        self.stage("CHANGELOG.md", "# Changelog\n\n- Add parser.\n")

        self.assertIsNone(self.guard())

    # Test-only and CI-only commits don't need docs.
    def test_test_and_ci_only_commits_pass(self):
        self.set_knobs(docs="on", loop="strict")

        for name in ["tests/test_parser.py", "src/parser.test.ts", "Parser.Tests/ParserTests.cs",
                     ".github/workflows/ci.yml"]:
            with self.subTest(name=name):
                self.git("reset", "-q")
                self.stage(name, "x\n")
                self.assertIsNone(self.guard())

    # The default docs value `repo` turns the check on when the repo keeps a changelog.
    def test_docs_repo_is_on_with_a_changelog(self):
        self.set_knobs(loop="strict")
        self.stage("CHANGELOG.md", "# Changelog\n")
        self.git("commit", "-q", "-m", "Add changelog")
        self.stage("parser.py", "x = 1\n")

        self.assert_denied(self.guard(), "docs")

    def test_docs_repo_is_off_without_a_changelog(self):
        self.set_knobs(loop="strict")
        self.stage("parser.py", "x = 1\n")

        self.assertIsNone(self.guard())

    def test_docs_off_skips_the_check(self):
        self.set_knobs(docs="off", loop="strict")
        self.stage("parser.py", "x = 1\n")

        self.assertIsNone(self.guard())

    # The repo's knobs win over the user's defaults in the plugin data folder.
    def test_repo_knobs_win_over_user_knobs(self):
        with open(os.path.join(self.data, "knobs.json"), "w", encoding="utf-8") as file:
            json.dump({"docs": "on", "loop": "strict"}, file)
        self.stage("parser.py", "x = 1\n")

        self.assert_denied(self.guard(), "docs")
        self.set_knobs(loop="standard")
        self.assertNotIn("permissionDecision", self.guard())

    # Every finding goes to the slip log, hard when it denies and soft when it warns.
    def test_findings_go_to_the_slip_log(self):
        self.set_knobs(docs="on", loop="standard")
        self.stage("parser.py", "x = 1\n")
        self.stage(".env", "TOKEN=1\n")

        self.guard()

        kinds = sorted((slip["rule"], slip["kind"]) for slip in self.slips())
        self.assertEqual(kinds, [("docs", "soft"), ("never-stage", "hard")])
        self.assertTrue(all(slip["check"] == "commit" and "time" in slip for slip in self.slips()))

    # `git -C <repo>` and a leading `cd <repo> &&` check that repo, wherever the session is.
    def test_commit_in_another_folder_checks_that_repo(self):
        self.stage(".env", "TOKEN=1\n")
        elsewhere = self.data

        self.assert_denied(self.guard(f'git -C "{self.repo}" commit -m "Add env"', cwd=elsewhere), ".env")
        self.assert_denied(self.guard(f'cd "{self.repo}" && git commit -m "Add env"', cwd=elsewhere), ".env")

    def test_powershell_commit_is_checked(self):
        self.stage(".env", "TOKEN=1\n")

        self.assert_denied(self.guard(tool="PowerShell"), ".env")

    def test_other_tools_pass(self):
        self.stage(".env", "TOKEN=1\n")

        self.assertIsNone(self.guard(tool="Write"))

    def test_bad_input_is_ignored(self):
        self.assertIsNone(self.guard(raw="not json"))
        self.assertIsNone(self.guard(raw=json.dumps({"tool_name": "Bash"})))

    def test_folder_outside_a_repo_passes(self):
        self.assertIsNone(self.guard(cwd=self.data))


if __name__ == "__main__":
    unittest.main()
