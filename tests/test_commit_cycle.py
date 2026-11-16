"""Tests for skills/work-loop/workflows/commit-cycle.js, run with `python3 -m unittest`.

The script runs in tests/workflow_harness.js, which stands in for the workflow runtime and returns a set reply for
each agent label.
"""

import json
import os
import shutil
import subprocess
import unittest

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
SCRIPT = os.path.join(ROOT, "skills", "work-loop", "workflows", "commit-cycle.js")
HARNESS = os.path.join(ROOT, "tests", "workflow_harness.js")
NODE = shutil.which("node") or "node"

ARGS = {
    "subject": "Add a parser for config files",
    "size": "large",
    "loop": "standard",
    "spec": "The tool reads a config file and prints the merged settings.",
    "houseBrief": "/repo/.git/work-loop/house.md",
    "briefs": "/skills/work-loop/references/stage-briefs.md",
    "ci": ["python3 -m unittest", "ruff check ."],
    "base": "main",
    "models": {
        "plan": {"model": "plan-model", "effort": "low"},
        "review": {"model": "review-model", "effort": "low"},
        "impl": {"model": "impl-model"},
    },
}

PLAN = {
    "files": ["config.py", "tests/test_config.py"],
    "publicShape": "parse(text) -> dict",
    "tests": [{"name": "test_empty_file", "pins": "an empty file gives no settings"}],
    "risks": [],
    "research": [{"source": "https://docs.python.org/3/library/tomllib.html", "date": "2026-11-16",
                  "finding": "tomllib parses TOML, 0 lines by hand"}],
}

REPLIES = {
    "plan": PLAN,
    "red": {"command": "python3 -m unittest tests.test_config", "tests": ["test_empty_file"],
            "assertion": "test_empty_file: expected {} but was None"},
    "implement": {"green": True, "staged": ["config.py", "tests/test_config.py"],
                  "commands": [{"command": "python3 -m unittest", "lastLine": "OK"},
                               {"command": "ruff check .", "lastLine": "All checks passed!"}]},
    "adversarial": {"testsAdded": 4, "bugsFixed": [{"test": "test_bom", "fix": "strip the BOM"}], "green": True},
    "simplify": {"cuts": [{"what": "inlined read_text helper", "linesBefore": 12, "linesAfter": 3}],
                 "checked": "helpers, options, checks", "green": True},
    "style": {"format": 0, "lint": 0, "brief": {"passed": 12, "total": 12}, "siblings": ["env.py"], "green": True},
    "docs": {"docs": [{"file": "CHANGELOG.md", "change": "+1"}, {"file": "README.md", "none": "internal"}]},
    "review:all": {"verdict": "1 finding", "findings": [
        {"severity": "bug", "location": "config.py:4", "finding": "crashes on a BOM", "trigger": "\\ufeffa=1"}]},
    "review:correctness": {"verdict": "1 bug", "findings": [
        {"severity": "bug", "location": "config.py:4", "finding": "crashes on a BOM", "trigger": "\\ufeffa=1"}]},
    "review:design": {"verdict": "clean", "findings": [
        {"severity": "nit", "location": "config.py:1", "finding": "import order", "trigger": "line 1"}]},
    "review:prose": {"verdict": "1 prose", "findings": [
        {"severity": "prose", "location": "config.py:2", "finding": "comment says 'knows'", "trigger": "line 2"}]},
    "fix": {"fixed": [{"finding": "crashes on a BOM", "change": "strip the BOM"}],
            "skipped": [{"finding": "comment says 'knows'", "why": "the line is a quote"}], "green": True},
}


def run(args=None, replies=None, **changes):
    payload = {"script": SCRIPT, "args": dict(args or ARGS, **changes), "replies": REPLIES if replies is None else replies}
    process = subprocess.run([NODE, HARNESS], input=json.dumps(payload), capture_output=True, encoding="utf-8")
    if process.returncode != 0:
        raise AssertionError(process.stderr)
    return json.loads(process.stdout)


def labels(output):
    return [call["label"] for call in output["calls"]]


def stages(output):
    return [record["stage"] for record in output["result"]["records"]]


def proof(output, stage):
    return next(record["proof"] for record in output["result"]["records"] if record["stage"] == stage)


def call(output, label):
    return next(item for item in output["calls"] if item["label"] == label)


def replies_with(**changes):
    replies = dict(REPLIES)
    replies.update(changes)
    return replies


@unittest.skipIf(shutil.which("node") is None, "node is not installed")
class Stages(unittest.TestCase):
    # A large commit runs every agent stage, with 3 review lenses at the same time and a fix round for the findings.
    def test_large_runs_every_agent_stage_in_order(self):
        output = run()

        self.assertIsNone(output["error"])
        self.assertEqual(output["result"]["status"], "done")
        self.assertEqual(labels(output), ["plan", "red", "implement", "adversarial", "simplify", "style", "docs",
                                          "review:correctness", "review:design", "review:prose", "fix"])
        self.assertEqual(stages(output), ["plan", "red", "green", "adv", "simplify", "style", "docs", "review", "fix"])

    def test_trivial_runs_implement_style_and_docs(self):
        output = run(size="trivial")

        self.assertEqual(labels(output), ["implement", "style", "docs"])
        self.assertIn("tools only", call(output, "style")["prompt"])

    def test_small_at_standard_skips_simplify_and_review(self):
        self.assertEqual(labels(run(size="small")), ["red", "implement", "style", "docs"])

    def test_small_at_strict_adds_simplify_and_1_review(self):
        self.assertEqual(labels(run(size="small", loop="strict")),
                         ["red", "implement", "simplify", "style", "docs", "review:all", "fix"])

    # A medium commit gets its plan from the driver, so no plan agent runs.
    def test_medium_at_standard_has_no_plan_agent_and_no_adversarial(self):
        self.assertEqual(labels(run(size="medium", plan="driver plan")),
                         ["red", "implement", "simplify", "style", "docs", "review:all", "fix"])

    def test_medium_at_strict_adds_adversarial(self):
        self.assertEqual(labels(run(size="medium", loop="strict", plan="driver plan")),
                         ["red", "implement", "adversarial", "simplify", "style", "docs", "review:all", "fix"])

    def test_light_runs_the_small_column_for_a_large_commit(self):
        self.assertEqual(labels(run(loop="light")), ["red", "implement", "style", "docs"])

    def test_light_runs_the_trivial_column_for_a_small_commit(self):
        self.assertEqual(labels(run(size="small", loop="light")), ["implement", "style", "docs"])

    def test_no_fix_round_without_findings_above_nit(self):
        replies = replies_with(**{
            "review:correctness": {"verdict": "clean", "findings": []},
            "review:prose": {"verdict": "clean", "findings": []},
        })
        output = run(replies=replies)

        self.assertNotIn("fix", labels(output))
        self.assertEqual(proof(output, "fix"), "none, 0 findings above nit")

    # The fix agent gets the findings it has to judge and not the nits.
    def test_fix_gets_the_findings_above_nit(self):
        prompt = call(run(), "fix")["prompt"]

        self.assertIn("crashes on a BOM", prompt)
        self.assertIn("comment says 'knows'", prompt)
        self.assertNotIn("import order", prompt)


@unittest.skipIf(shutil.which("node") is None, "node is not installed")
class Records(unittest.TestCase):
    def test_red_record_is_the_failure_line_word_for_word(self):
        self.assertEqual(proof(run(), "red"), "test_empty_file: expected {} but was None")

    def test_records_follow_the_proof_forms(self):
        output = run()

        self.assertEqual(proof(output, "plan"), "2 files, 1 tests, 1 sources")
        self.assertEqual(proof(output, "green"), "OK; All checks passed!")
        self.assertEqual(proof(output, "adv"), "+4 tests, 1 bugs fixed")
        self.assertEqual(proof(output, "simplify"), "-9 lines, 1 cuts")
        self.assertEqual(proof(output, "style"), "format 0, lint 0, brief 12/12, sibling 1 files")
        self.assertEqual(proof(output, "docs"), "CHANGELOG.md +1, README.md none: internal")
        self.assertEqual(proof(output, "review"), "3 findings, 2 above nit")
        self.assertEqual(proof(output, "fix"), "1 fixed, 1 skipped")

    def test_simplify_without_cuts_records_what_it_checked(self):
        replies = replies_with(simplify={"cuts": [], "checked": "helpers and options", "green": True})

        self.assertEqual(proof(run(replies=replies), "simplify"), "none, checked helpers and options")

    def test_docs_without_changes_records_the_reason(self):
        replies = replies_with(docs={"docs": [{"file": "CHANGELOG.md", "none": "test only"}]})

        self.assertEqual(proof(run(replies=replies), "docs"), "CHANGELOG.md none: test only")


@unittest.skipIf(shutil.which("node") is None, "node is not installed")
class Stops(unittest.TestCase):
    def test_red_without_a_failure_stops_before_implement(self):
        replies = replies_with(red={"command": "python3 -m unittest", "tests": ["test_empty_file"], "assertion": " "})
        output = run(replies=replies)

        self.assertEqual(output["result"]["status"], "stopped")
        self.assertEqual(output["result"]["stage"], "red")
        self.assertEqual(labels(output), ["plan", "red"])
        self.assertEqual(stages(output), ["plan"])

    def test_implement_that_isnt_green_stops_with_the_last_lines(self):
        replies = replies_with(implement={"green": False, "staged": [],
                                          "commands": [{"command": "python3 -m unittest", "lastLine": "FAILED (failures=1)"}]})
        output = run(replies=replies)

        self.assertEqual(output["result"]["stage"], "implement")
        self.assertIn("FAILED (failures=1)", output["result"]["reason"])
        self.assertNotIn("adversarial", labels(output))

    def test_fix_that_isnt_green_stops(self):
        replies = replies_with(fix={"fixed": [], "skipped": [], "green": False})
        output = run(replies=replies)

        self.assertEqual(output["result"]["status"], "stopped")
        self.assertEqual(output["result"]["stage"], "fix")

    # Every finding above nit comes back as fixed or skipped, so none of them gets lost.
    def test_fix_that_leaves_out_a_finding_stops(self):
        replies = replies_with(fix={"fixed": [{"finding": "crashes on a BOM", "change": "strip the BOM"}],
                                    "skipped": [], "green": True})
        output = run(replies=replies)

        self.assertEqual(output["result"]["stage"], "fix")
        self.assertIn("1 of 2 findings", output["result"]["reason"])
        self.assertNotIn("fix", stages(output))

    def test_agent_that_doesnt_return_stops(self):
        output = run(replies=replies_with(simplify=None))

        self.assertEqual(output["result"]["stage"], "simplify")
        self.assertNotIn("style", labels(output))

    def test_review_lens_that_doesnt_return_stops_before_fix(self):
        output = run(replies=replies_with(**{"review:design": None}))

        self.assertEqual(output["result"]["stage"], "review")
        self.assertNotIn("fix", labels(output))

    # Review agents always get their model by name, so a missing review model stops before any agent starts.
    def test_missing_review_model_stops_before_any_agent(self):
        output = run(models={"impl": {"model": "impl-model"}})

        self.assertEqual(output["result"]["status"], "stopped")
        self.assertIn("review model", output["result"]["reason"])
        self.assertEqual(output["calls"], [])

    def test_missing_review_model_is_fine_without_a_review(self):
        output = run(size="small", models={})

        self.assertEqual(output["result"]["status"], "done")

    def test_unknown_size_stops_before_any_agent(self):
        output = run(size="huge")

        self.assertEqual(output["result"]["status"], "stopped")
        self.assertIn("huge", output["result"]["reason"])
        self.assertEqual(output["calls"], [])

    def test_unknown_loop_level_stops_before_any_agent(self):
        output = run(loop="max")

        self.assertIn("max", output["result"]["reason"])
        self.assertEqual(output["calls"], [])

    def test_missing_ci_commands_stop_before_any_agent(self):
        output = run(ci=[])

        self.assertEqual(output["result"]["status"], "stopped")
        self.assertEqual(output["calls"], [])


@unittest.skipIf(shutil.which("node") is None, "node is not installed")
class Agents(unittest.TestCase):
    def test_each_agent_gets_its_model_by_name(self):
        output = run()

        self.assertEqual(call(output, "plan")["model"], "plan-model")
        self.assertEqual(call(output, "plan")["effort"], "low")
        for label in ["review:correctness", "review:design", "review:prose"]:
            self.assertEqual(call(output, label)["model"], "review-model")
        for label in ["red", "implement", "adversarial", "simplify", "style", "docs", "fix"]:
            self.assertEqual(call(output, label)["model"], "impl-model")
            self.assertNotIn("effort", call(output, label))

    def test_each_stage_runs_as_its_plugin_agent(self):
        for item in run()["calls"]:
            stage = item["label"].split(":")[0]
            with self.subTest(label=item["label"]):
                self.assertEqual(item["agentType"], f"work-loop:stage-{stage}")

    def test_every_prompt_has_the_inputs_of_every_stage(self):
        for item in run()["calls"]:
            with self.subTest(label=item["label"]):
                for text in [ARGS["subject"], ARGS["spec"], ARGS["houseBrief"], ARGS["briefs"], "ruff check .",
                             "large", "standard", "main"]:
                    self.assertIn(text, item["prompt"])

    def test_later_stages_get_the_plan_of_the_plan_stage(self):
        self.assertIn("test_empty_file", call(run(), "red")["prompt"])

    def test_review_lenses_name_their_lens(self):
        output = run()

        for lens in ["correctness", "design", "prose"]:
            self.assertIn(f"Lens: {lens}", call(output, f"review:{lens}")["prompt"])

    def test_agents_run_in_their_phases(self):
        output = run()

        self.assertEqual(output["phases"], [phase["title"] for phase in output["meta"]["phases"]])
        self.assertEqual(call(output, "plan")["phase"], "Plan")
        self.assertEqual(call(output, "review:design")["phase"], "Review")


@unittest.skipIf(shutil.which("node") is None, "node is not installed")
class Resume(unittest.TestCase):
    # A relaunch with the same arguments sends the same prompts, so the runtime returns the saved results.
    def test_same_arguments_send_the_same_prompts(self):
        self.assertEqual(run()["calls"], run()["calls"])

    # The note goes only to the stage that stopped, so the stages before it keep their saved results.
    def test_resume_note_goes_only_to_its_stage(self):
        plain = run()["calls"]
        resumed = run(resumeNote={"stage": "simplify", "note": "the helper is already inlined"})["calls"]

        for before, after in zip(plain, resumed):
            if after["label"] == "simplify":
                self.assertNotEqual(before["prompt"], after["prompt"])
                self.assertIn("the helper is already inlined", after["prompt"])
            else:
                self.assertEqual(before["prompt"], after["prompt"])

    def test_meta_is_named_and_described(self):
        meta = run()["meta"]

        self.assertEqual(meta["name"], "commit-cycle")
        self.assertTrue(meta["description"])


class Marketplace(unittest.TestCase):
    # The plugin's source is the repo root, so the work-loop entry points at its own workflows folder.
    def test_work_loop_ships_the_workflow(self):
        with open(os.path.join(ROOT, ".claude-plugin", "marketplace.json"), encoding="utf-8") as file:
            plugins = {plugin["name"]: plugin for plugin in json.load(file)["plugins"]}

        folder = os.path.join(ROOT, plugins["work-loop"]["workflows"])
        self.assertEqual(os.path.normpath(os.path.join(folder, "commit-cycle.js")), os.path.normpath(SCRIPT))
        for name, plugin in plugins.items():
            if name != "work-loop":
                with self.subTest(plugin=name):
                    self.assertNotIn("workflows", plugin)
                    self.assertFalse(os.path.exists(os.path.join(ROOT, "workflows")))


if __name__ == "__main__":
    unittest.main()
