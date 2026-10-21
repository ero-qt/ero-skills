"""Tests for skills/repo-writing/scripts/prose_check.py, run with `python3 -m unittest`."""

import os
import subprocess
import sys
import tempfile
import unittest

SCRIPT = os.path.join(os.path.dirname(__file__), "..", "skills", "repo-writing", "scripts", "prose_check.py")


def run(*args, stdin=None, cwd=None):
    result = subprocess.run([sys.executable, "-I", SCRIPT, *args], input=stdin, capture_output=True,
                            cwd=cwd, encoding="utf-8")
    return result.returncode, result.stdout


def git(cwd, *args):
    # Sets an identity because CI runners have no git user configured.
    subprocess.run(["git", "-c", "commit.gpgsign=false", "-c", "core.autocrlf=false", "-c", "user.name=test",
                    "-c", "user.email=test@example.com", *args],
                   cwd=cwd, check=True, capture_output=True)


class HardRules(unittest.TestCase):
    def test_em_dash_fails(self):
        code, out = run("--text", "the scan — then it stops")
        self.assertEqual(code, 1)
        self.assertIn("em or en dash", out)

    def test_curly_quote_on_stdin_fails(self):
        code, out = run(stdin="it’s fine\n")
        self.assertEqual(code, 1)
        self.assertIn("curly quote", out)

    def test_trailer_line_fails(self):
        code, out = run("--text", "Co-Authored-By: someone <a@b.c>")
        self.assertEqual(code, 1)
        self.assertIn("trailer", out)

    def test_generated_with_in_prose_passes(self):
        code, out = run("--text", "the bindings are generated with bindgen")
        self.assertEqual(code, 0)
        self.assertIn("0 hard, 0 to check", out)

    def test_clean_subject_passes(self):
        self.assertEqual(run("--text", "add tick provider"), (0, "0 hard, 0 to check\n"))


class CheckRules(unittest.TestCase):
    def test_banned_verbs_are_flagged(self):
        _, out = run("--text", "every match names one global and the walk lands there")
        self.assertIn("'name' as a verb", out)
        self.assertIn("'lands'", out)

    def test_british_spelling_after_an_allowed_word_is_flagged(self):
        _, out = run("--text", "otherwise we initialise it")
        self.assertIn("British spelling", out)

    def test_american_spelling_passes(self):
        self.assertEqual(run("--text", "in favor of the color behavior")[1], "0 hard, 0 to check\n")

    def test_allowed_ise_words_pass(self):
        self.assertEqual(run("--text", "a surprising and promising result, the cruise ends")[1], "0 hard, 0 to check\n")

    def test_greeting_exclamation_passes(self):
        self.assertEqual(run("--text", "Hey! I closed mine in favor of yours.")[1], "0 hard, 0 to check\n")

    def test_claim_exclamation_is_flagged(self):
        self.assertIn("exclamation mark", run("--text", "This makes it much faster!")[1])

    def test_help_prints_usage(self):
        code, out = run("--help")
        self.assertEqual(code, 0)
        self.assertIn("Usage:", out)

    def test_code_spans_are_skipped(self):
        self.assertEqual(run("--text", "rename `names_lookup` to something")[1], "0 hard, 0 to check\n")


class Fences(unittest.TestCase):
    def test_inner_fence_does_not_end_outer_code_fence(self):
        draft = "````markdown\n```rust\nlet a = 1; // name the thing\n```\nthe walk lands — here\n````\n"
        with tempfile.NamedTemporaryFile("w", suffix=".md", delete=False, encoding="utf-8") as file:
            file.write(draft)
        try:
            self.assertEqual(run(file.name), (0, "0 hard, 0 to check\n"))
        finally:
            os.unlink(file.name)

    def test_draft_wrapper_fence_is_checked_as_prose(self):
        draft = "````\nthe walk lands — here\n```rust\nlet a = 1; // name it\n```\n````\n"
        with tempfile.NamedTemporaryFile("w", suffix=".md", delete=False, encoding="utf-8") as file:
            file.write(draft)
        try:
            code, out = run(file.name)
            self.assertEqual(code, 1)
            self.assertIn(":2: hard: em or en dash", out)
            self.assertNotIn(":4:", out)
        finally:
            os.unlink(file.name)

    def test_staged_line_inside_existing_fence_is_skipped(self):
        with tempfile.TemporaryDirectory() as repo:
            git(repo, "init", "-q")
            path = os.path.join(repo, "a.md")
            with open(path, "w", encoding="utf-8", newline="\n") as file:
                file.write("# a\n\n```\ncode one\n```\n")
            git(repo, "add", "a.md")
            git(repo, "commit", "-qm", "x")
            with open(path, "w", encoding="utf-8", newline="\n") as file:
                file.write("# a\n\n```\ncode one\ncode two -- added\n```\nthe scan — then\n")
            git(repo, "add", "a.md")

            code, out = run("--staged", cwd=repo)

            self.assertEqual(code, 1)
            self.assertNotIn("a.md:5:", out)
            self.assertIn("a.md:7: hard: em or en dash", out)


if __name__ == "__main__":
    unittest.main()
