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

    def ledger(self, stage, proof):
        subprocess.run([NODE, LEDGER, "add", stage, proof], cwd=self.repo, env=self.env, check=True,
                       capture_output=True)

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

    # Only a trailer line of the message counts, not other commands or a subject that talks about trailers.
    def test_trailer_words_outside_a_trailer_line_pass(self):
        self.stage("parser.py", "x = 1\n")

        for command in ['git commit -m "Add parser" && gh pr create --body "Generated with [Claude Code](x)"',
                        'git commit -m "Deny a Signed-off-by: line in the guard"']:
            with self.subTest(command=command):
                self.assertIsNone(self.guard(command))

    def test_trailer_is_reported_once(self):
        self.stage("parser.py", "x = 1\n")

        self.guard(f'git commit -m "Add parser" -m "{TRAILER}"')

        self.assertEqual([slip["rule"] for slip in self.slips()], ["trailer"])

    # `--signoff` adds a Signed-off-by line to the message.
    def test_signoff_is_denied(self):
        self.stage("parser.py", "x = 1\n")

        for command in ['git commit -s -m "Add parser"', 'git commit --signoff -m "Add parser"',
                        'git commit -sm "Add parser"']:
            with self.subTest(command=command):
                self.assert_denied(self.guard(command), "trailer")

    # A hard finding of the prose check in the staged lines denies the commit.
    def test_hard_prose_finding_in_staged_lines_is_denied(self):
        self.stage("notes.md", f"The parser stops {DASH} it reads 1 line.\n")

        self.assert_denied(self.guard(), "prose check", "notes.md")

    # Text that belongs to someone else, like a license or a house style with dashes, can stay with a ledger reason.
    def test_ledger_reason_keeps_staged_prose(self):
        self.stage("LICENSE.txt", "Copyright 2019–2024 “The Authors”\n")

        self.assert_denied(self.guard(), "prose check", 'add prose "keep:')
        self.ledger("prose", "keep: license text")
        output = self.guard()

        self.assertIsNotNone(output)
        self.assertNotIn("permissionDecision", output)
        self.assertIn("LICENSE.txt", output["additionalContext"])
        self.assertIn(("prose check", "soft"), [(slip["rule"], slip["kind"]) for slip in self.slips()])

    # The reason keeps text in staged files only. The commit message is always new text.
    def test_ledger_reason_doesnt_keep_the_message(self):
        self.stage("parser.py", "x = 1\n")
        self.ledger("prose", "keep: license text")

        self.assert_denied(self.guard(f'git commit -m "Add parser {DASH} now"'), "message")

    # A check finding only needs a look, so it doesn't deny.
    def test_check_prose_finding_passes(self):
        self.stage("notes.md", "Note that the parser reads 1 line.\n")

        self.assertIsNone(self.guard())

    def test_dash_in_the_subject_is_denied(self):
        self.stage("parser.py", "x = 1\n")

        self.assert_denied(self.guard(f'git commit -m "Add parser {DASH} with tests"'), "prose check", "message")

    # Short flags can come together, like `-qm` or `-vm`.
    def test_dash_in_a_message_after_joined_flags_is_denied(self):
        self.stage("parser.py", "x = 1\n")

        self.assert_denied(self.guard(f'git commit -qm "Add parser {DASH} with tests"'), "prose check", "message")

    # The guard reads the index before the command runs, so it can't see what the same command stages.
    def test_staging_in_the_commit_command_is_denied(self):
        self.write("notes.md", f"A {DASH} B\n")

        for command in ['git add -A && git commit -m "Add notes"', 'git add .\ngit commit -m "Add notes"',
                        'git rm -q old.py; git commit -m "Remove old"', 'git stage notes.md && git commit -m "Add"',
                        'git mv a.py b.py && git commit -m "Rename"']:
            with self.subTest(command=command):
                self.assert_denied(self.guard(command), "Stage by path first")

    def test_commit_flags_that_stage_are_denied(self):
        self.stage("parser.py", "x = 1\n")

        for command in ['git commit -a -m "Add parser"', 'git commit --all -m "Add parser"',
                        'git commit -qam "Add parser"', 'git commit -i parser.py -m "Add parser"',
                        'git commit --only -m "Add parser" parser.py', 'git commit -m "Add parser" README.md',
                        'git commit -m "Add parser" -- README.md']:
            with self.subTest(command=command):
                self.assert_denied(self.guard(command), "Stage by path first")

    # Flags that take a value, like --author or -C, aren't mistaken for a path.
    def test_commit_flag_values_are_not_paths(self):
        self.stage("parser.py", "x = 1\n")

        for command in ['git commit --author "Test <test@example.com>" -m "Add parser"',
                        'git commit -C HEAD --reset-author', 'git commit --amend --no-edit',
                        'git commit --cleanup strip -m "Add parser"', 'git add parser.py']:
            with self.subTest(command=command):
                self.assertIsNone(self.guard(command))

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

    # The commit-cycle workflow writes the docs record, so its form has to clear this check.
    def test_docs_record_of_the_commit_cycle_clears_the_docs_check(self):
        from test_commit_cycle import proof, replies_with, run

        self.set_knobs(docs="on", loop="strict")
        self.stage("parser.py", "x = 1\n")
        replies = replies_with(docs={"docs": [{"file": "CHANGELOG.md", "none": "internal refactor"}]})
        self.ledger("docs", proof(run(replies=replies), "docs"))

        self.assertIsNone(self.guard())

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

    # Lock files, dotfile config and license files never need a doc change, so they aren't logged as slips either.
    def test_lock_dotfile_and_license_commits_pass(self):
        self.set_knobs(docs="on", loop="standard")

        for name in [".gitignore", "package-lock.json", ".editorconfig", "LICENSE", "web/yarn.lock"]:
            with self.subTest(name=name):
                self.git("reset", "-q")
                self.stage(name, "x\n")
                self.assertIsNone(self.guard())
        self.assertEqual(self.slips(), [])

    # The default docs value `repo` turns the check on when the repo keeps a changelog.
    def test_docs_repo_is_on_with_a_changelog(self):
        self.set_knobs(loop="strict")
        self.stage("CHANGELOG.md", "# Changelog\n")
        self.git("commit", "-q", "-m", "Add changelog")
        self.stage("parser.py", "x = 1\n")

        self.assert_denied(self.guard(), "docs")

    def test_docs_repo_finds_the_changelog_from_a_subfolder(self):
        self.set_knobs(loop="strict")
        self.stage("CHANGELOG.md", "# Changelog\n")
        self.git("commit", "-q", "-m", "Add changelog")
        self.stage("src/parser.py", "x = 1\n")

        self.assert_denied(self.guard(cwd=os.path.join(self.repo, "src")), "docs")

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

    # A PowerShell here-string ends only at `'@` on its own line, so an apostrophe inside doesn't end it.
    def test_powershell_here_string_message_is_checked(self):
        self.stage("parser.py", "x = 1\n")

        dash = self.guard(f"git commit -m @'\nAdd parser that doesn't stop {DASH} now\n'@", tool="PowerShell")
        trailer = self.guard(f"git commit -m @\"\nAdd parser that doesn't stop\n\n{TRAILER}\n\"@", tool="PowerShell")
        clean = self.guard("git commit -m @'\nAdd parser that doesn't stop\n'@", tool="PowerShell")

        self.assert_denied(dash, "prose check", "message")
        self.assert_denied(trailer, "trailer")
        self.assertIsNone(clean)

    # PowerShell doubles a quote to escape it and keeps backslashes as they are.
    def test_powershell_quotes_and_paths(self):
        self.stage(".env", "TOKEN=1\n")
        elsewhere = self.data

        self.assert_denied(self.guard(f"git commit -m 'It''s fine {DASH} really'", tool="PowerShell"), "message")
        self.assert_denied(self.guard(f"git -C {self.repo} commit -m 'Add env'", tool="PowerShell", cwd=elsewhere),
                           ".env")

    # Claude Code writes Bash commit messages as a heredoc inside `$(cat ...)`.
    def test_cat_heredoc_message_is_checked(self):
        self.stage("parser.py", "x = 1\n")
        form = "git commit -m \"$(cat <<'EOF'\n{}\nEOF\n)\""

        self.assertIsNone(self.guard(form.format("Add parser\n\nIt reads 1 line.")))
        self.assert_denied(self.guard(form.format(f"Add parser {DASH} now")), "prose check", "message")
        self.assert_denied(self.guard(form.format(f"Add parser\n\n{TRAILER}")), "trailer")

    # A heredoc that writes a file isn't a command, also without a space before `<<`.
    def test_heredoc_body_is_not_a_command(self):
        self.stage("parser.py", "x = 1\n")

        for start in ["cat <<'EOF' > run.sh", "cat<<'EOF' > run.sh"]:
            with self.subTest(start=start):
                self.assertIsNone(self.guard(f'{start}\ngit commit -m "x {DASH} y"\nEOF'))

    # Subshells, groups, conditions, wrappers and git's own options still lead to the commit.
    def test_wrapped_commits_are_checked(self):
        self.stage(".env", "TOKEN=1\n")

        for command in ['(git commit -m "Add env")', '{ git commit -m "Add env"; }',
                        'if true; then git commit -m "Add env"; fi', 'env GIT_TRACE=0 git commit -m "Add env"',
                        'GIT_TRACE=0 git commit -m "Add env"', 'command git commit -m "Add env"',
                        'git --git-dir .git commit -m "Add env"', 'git -c user.name=Test commit -m "Add env"']:
            with self.subTest(command=command):
                self.assert_denied(self.guard(command), ".env")

    # Without the prose check script the other checks still run.
    def test_missing_prose_check_skips_only_the_prose_check(self):
        skills = os.path.dirname(os.path.dirname(SCRIPTS))
        copy = os.path.join(self.data, "skills", "work-loop", "scripts")
        for skill, name in [("work-loop", "commit-guard.js"), ("work-loop", "ledger.js"), ("work-ethic", "knobs.js"),
                            ("terse-replies", "terse-reminder.js")]:
            folder = os.path.join(self.data, "skills", skill, "scripts")
            os.makedirs(folder, exist_ok=True)
            shutil.copy(os.path.join(skills, skill, "scripts", name), folder)
        self.stage("notes.md", f"A {DASH} B\n")
        self.stage(".env", "TOKEN=1\n")
        event = {"cwd": self.repo, "tool_name": "Bash", "tool_input": {"command": 'git commit -m "Add notes"'}}

        result = subprocess.run([NODE, os.path.join(copy, "commit-guard.js")], input=json.dumps(event),
                                capture_output=True, encoding="utf-8", env=self.env)

        reason = json.loads(result.stdout)["hookSpecificOutput"]["permissionDecisionReason"]
        self.assertIn(".env", reason)
        self.assertNotIn("prose check", reason)

    # Without Python on the path the other checks still run.
    def test_missing_python_skips_only_the_prose_check(self):
        folders = {os.path.dirname(shutil.which(name)) for name in ["node", "git"]}
        if any(shutil.which(name, path=os.pathsep.join(folders)) for name in ["python", "python3"]):
            self.skipTest("python sits next to node or git")
        self.stage("notes.md", f"A {DASH} B\n")
        self.stage(".env", "TOKEN=1\n")
        self.env["PATH"] = os.pathsep.join(folders)

        output = self.guard()

        self.assert_denied(output, ".env")
        self.assertNotIn("prose check", output["permissionDecisionReason"])

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
