"""Tests for skills/terse-replies/scripts/reply-check.js, run with `python3 -m unittest`."""

import json
import os
import shutil
import subprocess
import tempfile
import unittest

SCRIPTS = os.path.join(os.path.dirname(__file__), "..", "skills", "terse-replies", "scripts")
CHECK = os.path.join(SCRIPTS, "reply-check.js")
KNOBS = os.path.abspath(os.path.join(SCRIPTS, "..", "..", "work-ethic", "scripts", "knobs.js"))
NODE = shutil.which("node") or "node"

LONG_REPORT = "\n".join([
    "Build fixed.",
    "Cache folder missing on runner.",
    "Cleanup step removed it.",
    "Step skips it now.",
])

TOOL_TURN = [
    {"type": "user", "message": {"role": "user", "content": "fix the build"}},
    {"type": "assistant", "message": {"role": "assistant", "content": [
        {"type": "tool_use", "id": "t1", "name": "Bash", "input": {"command": "make"}}]}},
    {"type": "user", "message": {"role": "user", "content": [
        {"type": "tool_result", "tool_use_id": "t1", "content": "ok"}]}},
]

GATE_OK = "\n".join([
    "Commit staged, 6 files.",
    "Tests pass, 48/48.",
    "",
    "- `client.py`: `max_retries`, default 3",
    "- `retry.py`: waits 1, 2, 4 s",
    "- 7 new tests",
    "",
    "`Add retry limit to upload client`",
    "Approve? Next: docs commit (2/2).",
])


def gate_of(lines):
    body = [f"`file{index}.py`: change {index}" for index in range(lines - 2)]
    return "\n".join(body + ["`Add retry limit to upload client`", "Approve?"])


@unittest.skipIf(shutil.which("node") is None, "node is not installed")
class ReplyCheck(unittest.TestCase):
    def setUp(self):
        self.data = tempfile.mkdtemp()
        self.env = dict(os.environ, CLAUDE_PLUGIN_DATA=self.data)
        self.set_level("full")

    def tearDown(self):
        shutil.rmtree(self.data, ignore_errors=True)

    def set_level(self, level):
        with open(os.path.join(self.data, "knobs.json"), "w", encoding="utf-8") as file:
            json.dump({"terse": level}, file)

    def prompt(self, text, session=None):
        event = {"prompt": text, "cwd": self.data, "session_id": session}
        subprocess.run([NODE, KNOBS, "prompt"], input=json.dumps(event), capture_output=True, encoding="utf-8",
                       env=self.env, cwd=self.data, check=True)

    def check(self, message, stop_hook_active=False, transcript_path=None, raw=None, session=None):
        event = {"hook_event_name": "Stop", "stop_hook_active": stop_hook_active, "last_assistant_message": message,
                 "cwd": self.data, "session_id": session}
        if transcript_path:
            event["transcript_path"] = transcript_path
        result = subprocess.run([NODE, CHECK], input=raw if raw is not None else json.dumps(event),
                                capture_output=True, encoding="utf-8", env=self.env, cwd=self.data)
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(result.stdout, "", "the check only logs and never answers the hook")
        return self.slips()

    def slips(self):
        path = os.path.join(self.data, "slips.jsonl")
        if not os.path.exists(path):
            return []
        with open(path, encoding="utf-8") as file:
            return [json.loads(line) for line in file if line.strip()]

    def rules(self, slips, kind=None):
        return sorted(slip["rule"] for slip in slips if kind is None or slip["kind"] == kind)

    def write_transcript(self, entries):
        path = os.path.join(self.data, "transcript.jsonl")
        with open(path, "w", encoding="utf-8") as file:
            file.writelines(json.dumps(entry) + "\n" for entry in entries)
        return path

    # A commit gate of 11 lines with the subject right above the gate line passes.
    def test_gate_of_11_lines_passes(self):
        self.assertEqual(self.check(gate_of(11)), [])

    # A commit gate of 19 lines is a hard finding with both counts in the detail.
    def test_gate_of_19_lines_logs_a_hard_finding(self):
        slips = self.check(gate_of(19))

        self.assertEqual(self.rules(slips, "hard"), ["gate-length"])
        self.assertIn("19", slips[0]["detail"])
        self.assertIn("12", slips[0]["detail"])
        self.assertEqual(slips[0]["check"], "reply")
        self.assertIn("time", slips[0])

    # Lines inside a fence don't count toward the gate, so a long PR draft can sit above it.
    def test_fenced_draft_doesnt_count_toward_the_gate(self):
        draft = "\n".join(f"Line {index} of the PR body." for index in range(30))
        message = f"PR, owner/repo\n`Add retry limit`\n\n````\n{draft}\n````\nApprove?"

        self.assertEqual(self.check(message), [])

    # The line above the gate has to be the subject in inline code.
    def test_gate_without_subject_above_logs_a_hard_finding(self):
        message = "Commit staged, 6 files.\nSubject is `Add retry limit`.\nTests pass.\nApprove?"

        self.assertEqual(self.rules(self.check(message), "hard"), ["gate-subject"])

    def test_gate_with_subject_above_passes(self):
        self.assertEqual(self.check(GATE_OK), [])

    # Em dashes, en dashes and ` -- ` outside code are hard findings, inside code they're fine.
    def test_dash_outside_code_logs_a_hard_finding(self):
        for message in ["3/120 fail — all parser.", "Range 1–3.", "Build passes -- tests don't."]:
            with self.subTest(message=message):
                self.assertIn("dash", self.rules(self.check(message), "hard"))
                os.remove(os.path.join(self.data, "slips.jsonl"))

    def test_dash_inside_code_passes(self):
        message = "Run `git log -- src`.\n\n```\nfoo — bar\n```"

        self.assertEqual(self.check(message), [])

    # A title in double quotes is text from somewhere else, so its dash stays. A dash next to the quote still counts.
    def test_dash_inside_double_quotes_passes(self):
        self.assertEqual(self.check('Issue title: "Fix parser – trailing space".'), [])
        self.assertEqual(self.check("Titel: „Parser – Leerzeichen“, “Fix – space”."), [])
        self.assertEqual(self.rules(self.check('"Fix parser" – done.')), ["dash"])

    # A first line with validation, an apology or an announcement is a hard finding.
    def test_validating_opener_logs_a_hard_finding(self):
        for opener in ["You're right, cache was stale.", "Sorry, wrong file.", "I'll fix the test.", "Let me check."]:
            with self.subTest(opener=opener):
                self.assertEqual(self.rules(self.check(opener + "\nFixed."), "hard"), ["opener"])
                os.remove(os.path.join(self.data, "slips.jsonl"))

    # A closing offer at the end is a hard finding.
    def test_closing_offer_logs_a_hard_finding(self):
        for closing in ["Let me know if it breaks.", "Happy to add more tests.", "Want me to push it?"]:
            with self.subTest(closing=closing):
                self.assertEqual(self.rules(self.check("Tests pass, 48/48.\n" + closing), "hard"), ["closing-offer"])
                os.remove(os.path.join(self.data, "slips.jsonl"))

    # An offer phrase inside inline code or double quotes is a quote and not an offer.
    def test_quoted_closing_offer_passes(self):
        self.assertEqual(self.check("Tells updated.\nNext: add `let me know` to tells."), [])
        self.assertEqual(self.check('Tells updated.\nNext: add "happy to" to tells.'), [])

    # The check prints nothing and only logs when stop_hook_active is true.
    def test_stop_hook_active_still_never_answers(self):
        slips = self.check(gate_of(19), stop_hook_active=True)

        self.assertEqual(self.rules(slips, "hard"), ["gate-length"])

    # Length rules don't apply after an "explain" prompt, but wording rules still do.
    def test_explain_prompt_skips_length_rules(self):
        self.prompt("terse full. explain why rebase changes hashes")
        long_reply = "\n".join(f"- point {index} with a few more words in it than usual for a line" for index in range(14))

        self.assertEqual(self.check(long_reply), [])
        self.assertEqual(self.rules(self.check("Sure — here it is.")), ["dash"])

    # The next prompt without an explanation request turns the length rules back on.
    def test_explain_flag_resets_on_the_next_prompt(self):
        self.prompt("explain the cache")
        self.prompt("fix the build")

        self.assertEqual(self.rules(self.check(gate_of(19)), "hard"), ["gate-length"])

    # Each session has its own explain flag, so an "explain" prompt in 1 session leaves the others alone.
    def test_explain_prompt_of_another_session_doesnt_count(self):
        self.prompt("explain the cache", session="a/1")

        self.assertEqual(self.check(gate_of(19), session="a/1"), [])
        self.assertEqual(self.rules(self.check(gate_of(19), session="b"), "hard"), ["gate-length"])

    # Each record gives the session and the folder, so the log shows where a rule got broken.
    def test_record_has_the_session_and_the_folder(self):
        slip = self.check("A — B.", session="a")[0]

        self.assertEqual(slip["session_id"], "a")
        self.assertEqual(slip["cwd"], self.data)

    # At lite or with terse off, the check doesn't log anything.
    def test_lite_and_off_skip_the_check(self):
        for level in ["lite", "off"]:
            with self.subTest(level=level):
                self.set_level(level)
                self.assertEqual(self.check(gate_of(19) + "\nSorry — let me know."), [])

    # The check uses the default level, full, when no level is saved.
    def test_missing_knobs_file_checks_at_full(self):
        os.remove(os.path.join(self.data, "knobs.json"))

        self.assertEqual(self.rules(self.check("A — B.")), ["dash"])

    # More than 5 bullets is a soft finding.
    def test_more_than_5_bullets_logs_a_soft_finding(self):
        message = "6 files changed.\n" + "\n".join(f"- `f{index}.py`" for index in range(6))

        self.assertEqual(self.rules(self.check(message), "soft"), ["bullets"])

    def test_5_bullets_pass(self):
        message = "5 files changed.\n" + "\n".join(f"- `f{index}.py`" for index in range(5))

        self.assertEqual(self.check(message), [])

    # The skill splits a long list into "now" and "later", so each part has its own count.
    def test_bullets_count_per_part_of_a_split_list(self):
        now = "\n".join(f"- `f{index}.py`" for index in range(4))
        later = "\n".join(f"- `g{index}.py`" for index in range(4))

        self.assertEqual(self.check(f"8 files changed.\n\nNow:\n{now}\n\nLater:\n{later}"), [])

    # A blank line alone doesn't split a list.
    def test_blank_line_doesnt_split_a_list(self):
        first = "\n".join(f"- `f{index}.py`" for index in range(3))
        second = "\n".join(f"- `g{index}.py`" for index in range(3))

        self.assertEqual(self.rules(self.check(f"6 files changed.\n{first}\n\n{second}"), "soft"), ["bullets"])

    # At ultra, lines that average more than 12 words are a soft finding. Inline code doesn't count as words.
    def test_long_lines_at_ultra_log_a_soft_finding(self):
        self.set_level("ultra")
        message = "The build failed because the cache folder was missing on the runner after the cleanup step ran."

        self.assertEqual(self.rules(self.check(message), "soft"), ["line-words"])

    def test_long_lines_at_full_pass(self):
        message = "The build failed because the cache folder was missing on the runner after the cleanup step ran."

        self.assertEqual(self.check(message), [])

    def test_inline_code_doesnt_count_as_words(self):
        self.set_level("ultra")
        message = "Fails: `error: could not find the file named config dot toml in any of the parent folders`"

        self.assertEqual(self.check(message), [])

    # A report after a turn that used tools has to close on State and Next.
    def test_tool_turn_without_close_logs_a_soft_finding(self):
        transcript = self.write_transcript(TOOL_TURN)

        self.assertEqual(self.rules(self.check(LONG_REPORT, transcript_path=transcript), "soft"), ["close"])
        os.remove(os.path.join(self.data, "slips.jsonl"))
        self.assertEqual(self.check(LONG_REPORT + "\n\nState: done.\nNext: push.", transcript_path=transcript), [])
        self.assertEqual(self.check(LONG_REPORT + "\n\nStand: fertig.\nWeiter: push.", transcript_path=transcript), [])
        self.assertEqual(self.check(GATE_OK, transcript_path=transcript), [])

    # A close with bold labels is still a close.
    def test_close_with_bold_labels_passes(self):
        transcript = self.write_transcript(TOOL_TURN)

        for close in ["**State:** done.\n**Next:** push.", "**Stand**: fertig.\n**Weiter**: push."]:
            with self.subTest(close=close):
                self.assertEqual(self.check(f"{LONG_REPORT}\n\n{close}", transcript_path=transcript), [])

    # A read-back or a plan ends on a bare `Go?`, which takes the place of the close.
    def test_go_gate_takes_the_place_of_the_close(self):
        transcript = self.write_transcript(TOOL_TURN)

        self.assertEqual(self.check(LONG_REPORT + "\n\nGo?", transcript_path=transcript), [])
        self.assertEqual(self.rules(self.check(LONG_REPORT + "\nGo? Or wait.\nMore text.", transcript_path=transcript)),
                         ["close"])

    # A reply of at most 3 lines without a list counts as a pure answer, so a missing close isn't logged for it.
    def test_short_answer_after_tools_needs_no_close(self):
        transcript = self.write_transcript(TOOL_TURN)

        self.assertEqual(self.check("Yes.", transcript_path=transcript), [])
        self.assertEqual(self.check("No.\n\n3 callers left.\nAll in `src/io`.", transcript_path=transcript), [])
        steps = "Blocked.\n1. Run `gh auth login`\n2. Approve"
        self.assertEqual(self.rules(self.check(steps, transcript_path=transcript)), ["close"])

    # Tools from an earlier turn don't count, because the turn starts at the last typed prompt.
    def test_tools_before_the_last_prompt_dont_count(self):
        transcript = self.write_transcript([
            {"type": "user", "message": {"role": "user", "content": "fix the build"}},
            {"type": "assistant", "message": {"role": "assistant", "content": [
                {"type": "tool_use", "id": "t1", "name": "Bash", "input": {"command": "make"}}]}},
            {"type": "user", "message": {"role": "user", "content": [
                {"type": "tool_result", "tool_use_id": "t1", "content": "ok"}]}},
            {"type": "assistant", "message": {"role": "assistant", "content": [{"type": "text", "text": "Fixed."}]}},
            {"type": "user", "message": {"role": "user", "content": [{"type": "text", "text": "what was it?"}]}},
        ])

        self.assertEqual(self.check("Stale cache.", transcript_path=transcript), [])

    # A missing or broken transcript skips the close rule instead of guessing.
    def test_missing_transcript_skips_the_close_rule(self):
        missing = os.path.join(self.data, "missing.jsonl")

        self.assertEqual(self.check("Build fixed.", transcript_path=missing), [])

    # A count like 1/2 needs every other part on screen too.
    def test_count_without_other_half_logs_a_soft_finding(self):
        self.assertEqual(self.rules(self.check("Part 1/2: parser fixed."), "soft"), ["count-half"])

    def test_count_with_every_part_passes(self):
        self.assertEqual(self.check("1/2: parser fixed.\n2/2: tests added."), [])

    # Progress counts inside a line aren't part labels.
    def test_progress_count_passes(self):
        self.assertEqual(self.check("3/120 fail.\n\nState: commit 2/4 done.\nNext: commit 3/4."), [])

    # The hook doesn't fail on input that isn't JSON or doesn't have a message.
    def test_bad_input_is_ignored(self):
        self.assertEqual(self.check("", raw="not json"), [])
        self.assertEqual(self.check("", raw=json.dumps({"stop_hook_active": False})), [])


if __name__ == "__main__":
    unittest.main()
