"""Tests for skills/repo-writing/scripts/prose_check.py, run with `python3 -m unittest`."""

import importlib.util
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
    # Sets an identity because CI runners don't have a git user configured.
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

    def test_clipped_negation_is_flagged(self):
        for text in ("the repo has no samples folder", "the tests have no fixtures", "the old build had no cache",
                     "shares its config with no other service", "the search finds nothing", "it allocates nothing"):
            with self.subTest(text=text):
                self.assertIn("clipped negation", run("--text", text)[1])

    def test_negation_with_doesnt_passes(self):
        self.assertEqual(run("--text", "the repo doesn't have a samples folder")[1], "0 hard, 0 to check\n")

    def test_help_prints_usage(self):
        code, out = run("--help")
        self.assertEqual(code, 0)
        self.assertIn("Usage:", out)

    def test_code_spans_are_skipped(self):
        self.assertEqual(run("--text", "rename `names_lookup` to something")[1], "0 hard, 0 to check\n")


def run_file(text, name="draft.md"):
    with tempfile.TemporaryDirectory() as folder:
        path = os.path.join(folder, name)
        with open(path, "w", encoding="utf-8", newline="\n") as file:
            file.write(text)
        return run(path)


class SpecRules(unittest.TestCase):
    # Each rule gets 1 text it flags and 1 close text it lets through.
    CASES = {
        "copula dodge": ("`Cache` serves as a store for parsed files", "`Cache` keeps the parsed files"),
        "participle tail": ("It retries, ensuring delivery.", "It retries until the server answers."),
        "contrast frame": ("This isn't a cache, it's a ledger.", "This is a ledger of every write."),
        "triad": ("The parser is fast, safe and correct.", "It runs on Linux, Mac and Windows."),
        "fronted clause": ("Since the tests crash without a display, the run gets one.",
                           "The run gets a display because the tests crash without one."),
        "colon setup": ("The result: faster builds.", "Usage: run the script with a path."),
        "nominalization": ("It performs validation of the input.", "It checks the input."),
        "formal connective": ("Additionally, it caches the result.", "It also caches the result."),
        "significance claim": ("Retries play a key role in the client.", "The client retries 3 times."),
        "announcing intro": ("This section covers the config file.", "The config file is TOML."),
        "teaching tone": ("Please ensure that the path exists.", "The path doesn't exist."),
    }

    def test_each_rule_flags_its_tell_and_passes_the_plain_form(self):
        for rule, (bad, good) in self.CASES.items():
            with self.subTest(rule=rule):
                self.assertIn(rule, run("--text", bad)[1])
                self.assertNotIn(rule, run("--text", good)[1])

    def test_list_of_longer_items_is_not_a_triad(self):
        self.assertNotIn("triad", run("--text", "a table of severity, location, finding and the input")[1])

    def test_could_not_in_a_quoted_error_is_not_a_hedge(self):
        self.assertNotIn("hedge stack", run_file('It prints "could not start" when the file may be gone.\n')[1])

    def test_talking_code_is_flagged_in_comments_only(self):
        with tempfile.TemporaryDirectory() as repo:
            git(repo, "init", "-q")
            with open(os.path.join(repo, "a.py"), "w", encoding="utf-8", newline="\n") as file:
                file.write("# The parser knows the width now.\nx = 1\n")
            with open(os.path.join(repo, "a.md"), "w", encoding="utf-8", newline="\n") as file:
                file.write("I know the width now.\n")
            git(repo, "add", "a.py", "a.md")

            _, out = run("--staged", cwd=repo)

            self.assertIn("a.py:1: check: code that talks or thinks", out)
            self.assertIn("a.py:1: check: 'now' in a comment", out)
            self.assertNotIn("a.md:1: check: code that talks", out)
            self.assertNotIn("a.md:1: check: 'now'", out)

    def test_skill_and_tells_files_get_only_the_hard_rules(self):
        text = "The build is robust and caches the restore step — every time.\n"
        for name in ("SKILL.md", "tells.md"):
            with self.subTest(name=name):
                code, out = run_file(text, name)
                self.assertEqual(code, 1)
                self.assertIn("hard: em or en dash", out)
                self.assertNotIn("jargon or sales word", out)


class Explain(unittest.TestCase):
    def load(self):
        spec = importlib.util.spec_from_file_location("prose_check", SCRIPT)
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        return module

    def test_explain_prints_the_row_of_the_rule(self):
        code, out = run("--explain", "participle tail")
        self.assertEqual(code, 0)
        self.assertIn("Level: Sentence", out)
        self.assertIn("Bad: ", out)
        self.assertIn("Good: ", out)

    def test_explain_of_an_unknown_rule_fails(self):
        code, out = run("--explain", "no such rule")
        self.assertEqual(code, 1)
        self.assertIn("no such rule", out)

    def test_every_rule_has_a_row_in_tells(self):
        module = self.load()
        rules = [rule for rule, _ in module.HARD + module.CHECK + module.MARKDOWN + module.COMMENT_ONLY]
        rules += ["NUL byte in a text file", "dramatic short sentence", "decision packed into 1 sentence",
                  "hedge stack", "same skeleton in a row", "closing restatement", "flat sentence length",
                  "same verb in many sentences"]
        for rule in rules:
            with self.subTest(rule=rule):
                self.assertIsNotNone(module.explain(rule))


class ParagraphChecks(unittest.TestCase):
    def test_short_sentence_after_a_long_one_is_flagged(self):
        text = "The importer reads every image in the folder and writes a thumbnail for each one on Linux. It stops.\n"
        self.assertIn("dramatic short sentence", run_file(text)[1])

    def test_short_sentence_with_code_passes(self):
        text = "The importer reads every image in the folder and writes a thumbnail for each one on Linux. Run `make`.\n"
        self.assertNotIn("dramatic short sentence", run_file(text)[1])

    def test_decision_in_one_breath_is_flagged(self):
        text = ("Reads now format their message lazily, because failed reads are common in the scan loop and "
                "formatting the message is slow, which made every scan of a large file take twice as long.\n")
        self.assertIn("decision packed into 1 sentence", run_file(text)[1])

    def test_long_sentence_with_one_reason_passes(self):
        text = ("Failed reads don't format their message unless you ask for it, because formatting it made every "
                "scan of a large file in the loop about 100 nanoseconds slower than before.\n")
        self.assertNotIn("decision packed into 1 sentence", run_file(text)[1])

    def test_flat_sentence_length_is_flagged(self):
        text = ("The parser reads the header first and checks the magic bytes. "
                "Then it reads the table of contents into a small list. "
                "Each entry points at one block of data in the file. "
                "The reader skips any block whose type it doesn't know.\n")
        self.assertIn("flat sentence length", run_file(text)[1])

    def test_uneven_sentence_length_passes(self):
        text = ("The parser reads the header first. "
                "Then it reads the table of contents, which points at every block of data in the file. "
                "Each entry is 16 bytes. "
                "The reader skips any block whose type it doesn't know and logs the offset so you can find it.\n")
        self.assertNotIn("flat sentence length", run_file(text)[1])

    def test_same_first_word_three_times_is_flagged(self):
        text = "The cache keeps 10 entries. The reader checks it first. The writer clears it on save.\n"
        self.assertIn("same skeleton in a row", run_file(text)[1])

    def test_varied_openers_pass(self):
        text = "The cache keeps 10 entries. A read checks it first and the writer clears it on save.\n"
        self.assertNotIn("same skeleton in a row", run_file(text)[1])

    def test_same_verb_in_many_sentences_is_flagged(self):
        text = ("This repo has 3 packages. `core` has the parser. `cli` has the command line.\n\n"
                "The docs folder has the guides.\n")
        _, out = run_file(text)
        self.assertIn("same verb in many sentences: 'has' 4 times", out)

    def test_varied_verbs_pass(self):
        text = ("This repo has 3 packages. `core` contains the parser. `cli` is the command line.\n\n"
                "The guides are in the docs folder.\n")
        self.assertNotIn("same verb in many sentences", run_file(text)[1])

    def test_closing_restatement_is_flagged(self):
        text = "The build caches the restore step. This keeps the build fast.\n"
        self.assertIn("closing restatement", run_file(text)[1])

    def test_last_sentence_with_a_new_fact_passes(self):
        text = "The build caches the restore step. A clean build takes 4 minutes.\n"
        self.assertNotIn("closing restatement", run_file(text)[1])

    def test_hedge_stack_is_flagged(self):
        self.assertIn("hedge stack", run_file("This may potentially help in some setups.\n")[1])

    def test_one_hedge_passes(self):
        self.assertNotIn("hedge stack", run_file("This may help when the cache is cold.\n")[1])

    def test_sentences_in_a_list_or_table_are_not_joined(self):
        text = ("- The parser reads the header first and checks the magic bytes in it.\n"
                "- Stops.\n\n"
                "| a | b |\n|---|---|\n| The parser reads the header and checks the magic bytes in it. | It stops. |\n")
        self.assertNotIn("dramatic short sentence", run_file(text)[1])

    def test_skill_and_tells_files_skip_the_paragraph_checks(self):
        text = "The build caches the restore step. This keeps the build fast.\n"
        for name in ("SKILL.md", "tells.md"):
            with self.subTest(name=name):
                self.assertNotIn("closing restatement", run_file(text, name)[1])

    def test_commit_subject_gets_the_paragraph_checks(self):
        self.assertIn("hedge stack", run("--text", "possibly fix what might break")[1])


class Density(unittest.TestCase):
    def test_file_gets_a_density_line(self):
        _, out = run_file("The build is robust. It caches the restore step and the test step.\n")
        self.assertIn("tells: 1 in 13 words, 7.7 per 100", out)

    def test_clean_file_gets_a_density_line(self):
        _, out = run_file("The build caches the restore step.\n")
        self.assertIn("tells: 0 in 6 words, 0.0 per 100", out)

    def test_commit_subject_gets_no_density_line(self):
        self.assertNotIn("tells:", run("--text", "add a robust cache")[1])

    def test_staged_density_counts_added_lines_only(self):
        with tempfile.TemporaryDirectory() as repo:
            git(repo, "init", "-q")
            path = os.path.join(repo, "a.md")
            with open(path, "w", encoding="utf-8", newline="\n") as file:
                file.write("A robust and seamless intro line.\n")
            git(repo, "add", "a.md")
            git(repo, "commit", "-qm", "x")
            with open(path, "a", encoding="utf-8", newline="\n") as file:
                file.write("\nThe build caches the restore step. This keeps the build fast.\n")
            git(repo, "add", "a.md")

            _, out = run("--staged", cwd=repo)

            self.assertIn("a.md:3: check: closing restatement", out)
            self.assertIn("a.md: tells: 1 in 11 words", out)
            self.assertNotIn("a.md:1:", out)


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
