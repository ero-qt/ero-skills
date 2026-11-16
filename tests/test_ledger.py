"""Tests for skills/work-loop/scripts/ledger.js, run with `python3 -m unittest`."""

import json
import os
import shutil
import subprocess
import tempfile
import unittest

LEDGER = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "skills", "work-loop", "scripts", "ledger.js"))
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


def git(repo, *args):
    env = dict(os.environ, **GIT_ENV)
    return subprocess.run(["git", *args], cwd=repo, env=env, check=True, capture_output=True, encoding="utf-8").stdout


def make_repo():
    repo = tempfile.mkdtemp()
    git(repo, "init", "-q", "-b", "main")
    return repo


def commit(repo, name):
    with open(os.path.join(repo, name), "w", encoding="utf-8") as file:
        file.write(name + "\n")
    git(repo, "add", name)
    git(repo, "commit", "-q", "-m", f"Add {name}")


@unittest.skipIf(shutil.which("node") is None, "node is not installed")
class Ledger(unittest.TestCase):
    def setUp(self):
        self.repo = make_repo()

    def tearDown(self):
        shutil.rmtree(self.repo, ignore_errors=True)

    def run_ledger(self, *args, cwd=None):
        return subprocess.run([NODE, LEDGER, *args], cwd=cwd or self.repo, capture_output=True, encoding="utf-8",
                              env=dict(os.environ, **GIT_ENV))

    def records(self):
        path = os.path.join(self.repo, ".git", "work-loop", "ledger.jsonl")
        with open(path, encoding="utf-8") as file:
            return [json.loads(line) for line in file if line.strip()]

    # A record goes to .git/work-loop/ledger.jsonl with the stage, the proof, the time and the commit it builds on.
    def test_add_writes_a_record_under_git(self):
        commit(self.repo, "a.txt")
        result = self.run_ledger("add", "docs", "none:", "internal", "refactor")

        self.assertEqual(result.returncode, 0, result.stderr)
        records = self.records()
        self.assertEqual(len(records), 1)
        self.assertEqual(records[0]["stage"], "docs")
        self.assertEqual(records[0]["proof"], "none: internal refactor")
        self.assertEqual(records[0]["head"], git(self.repo, "rev-parse", "HEAD").strip())
        self.assertIn("time", records[0])

    # The ledger lives under .git, so it never shows up as a change to stage.
    def test_ledger_doesnt_show_in_status(self):
        commit(self.repo, "a.txt")
        self.run_ledger("add", "red", "test_parse: expected 3 but was 0")

        self.assertEqual(git(self.repo, "status", "--porcelain"), "")

    # A repo without a commit yet records an empty head.
    def test_add_before_the_first_commit_records_an_empty_head(self):
        result = self.run_ledger("add", "plan", "4 files, 6 tests")

        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(self.records()[0]["head"], "")

    # `show` prints the records of the commit in progress and leaves out the ones from before the last commit.
    def test_show_prints_only_the_commit_in_progress(self):
        commit(self.repo, "a.txt")
        self.run_ledger("add", "red", "old proof")
        commit(self.repo, "b.txt")
        self.run_ledger("add", "red", "test_b: expected 1 but was 0")
        self.run_ledger("add", "green", "12/12")

        result = self.run_ledger("show")

        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(result.stdout.splitlines(), ["red: test_b: expected 1 but was 0", "green: 12/12"])

    def test_show_without_a_ledger_prints_nothing(self):
        result = self.run_ledger("show")

        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(result.stdout, "")

    # `last` prints the newest record with the short hash of the commit it builds on.
    def test_last_prints_the_newest_record(self):
        commit(self.repo, "a.txt")
        self.run_ledger("add", "red", "first")
        self.run_ledger("add", "green", "12/12")

        result = self.run_ledger("last")

        short = git(self.repo, "rev-parse", "--short=7", "HEAD").strip()
        self.assertEqual(result.stdout.strip(), f"{short} green: 12/12")

    # A worktree writes to the ledger of the main repo, because .git in a worktree is a file.
    def test_worktree_uses_the_common_git_folder(self):
        commit(self.repo, "a.txt")
        worktree = tempfile.mkdtemp()
        shutil.rmtree(worktree)
        git(self.repo, "worktree", "add", "-q", worktree)
        try:
            result = self.run_ledger("add", "state", "ok", cwd=worktree)

            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertEqual(self.records()[0]["stage"], "state")
        finally:
            git(self.repo, "worktree", "remove", "--force", worktree)

    def test_add_without_a_proof_fails(self):
        result = self.run_ledger("add", "docs")

        self.assertEqual(result.returncode, 1)
        self.assertIn("Usage", result.stdout + result.stderr)

    def test_unknown_command_fails(self):
        self.assertEqual(self.run_ledger("drop").returncode, 1)
        self.assertEqual(self.run_ledger().returncode, 1)

    def test_outside_a_repo_fails(self):
        folder = tempfile.mkdtemp()
        try:
            result = self.run_ledger("add", "docs", "none: x", cwd=folder)
        finally:
            shutil.rmtree(folder, ignore_errors=True)

        self.assertEqual(result.returncode, 1)
        self.assertIn("isn't a git repository", result.stderr)


if __name__ == "__main__":
    unittest.main()
