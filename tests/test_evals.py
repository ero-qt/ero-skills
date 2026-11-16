"""Tests for the eval cases under evals/<skill>/, run with `python3 -m unittest`."""

import glob
import json
import os
import re
import unittest

ROOT = os.path.join(os.path.dirname(__file__), "..")
EVALS = os.path.join(ROOT, "evals")
SKILLS = sorted(os.path.basename(os.path.dirname(path)) for path in glob.glob(os.path.join(ROOT, "skills", "*", "SKILL.md")))

PROMPT_KEYS = {"schema_version", "name", "description", "tags", "plugins", "runs", "expected_outcome", "model",
               "max_turns", "timeout_seconds", "allowed_tools", "append_system_prompt", "env"}
GRADER_KEYS = {
    "regex": {"pattern", "flags", "match", "target"},
    "tool_used": {"tool", "input_match", "min", "max"},
    "tool_order": {"before", "after"},
    "file_exists": {"path", "exists"},
    "llm": {"criteria", "focus"},
}
REQUIRED_GRADER_KEYS = {"regex": {"pattern"}, "tool_used": {"tool"}, "tool_order": {"before", "after"},
                        "file_exists": {"path"}, "llm": set()}
MISTAKES = ["ai-tells", "process-weight", "design", "reuse", "reply-shape", "conventions", "gates"]


def read(path):
    with open(path, encoding="utf-8") as file:
        return file.read()


def split_frontmatter(text):
    match = re.match(r"---\n(.*?)\n---\n?(.*)", text, re.S)
    if not match:
        return {}, text
    fields = {}
    for line in match.group(1).splitlines():
        key, separator, value = line.partition(":")
        if separator:
            fields[key.strip()] = value.strip()
    return fields, match.group(2).strip()


def scalar(value):
    if value[:1] == "'" and value[-1:] == "'":
        return value[1:-1].replace("''", "'")
    if value[:1] == '"' and value[-1:] == '"':
        return json.loads(value)
    return value


def items(value):
    return [scalar(item.strip()) for item in value.strip("[]").split(",") if item.strip()]


def cases(skill=None):
    pattern = os.path.join(EVALS, skill or "*", "*", "prompt.md")
    return sorted(os.path.dirname(path) for path in glob.glob(pattern))


def skill_of(case):
    return os.path.basename(os.path.dirname(case))


def graders(case):
    return {os.path.basename(path)[:-3]: split_frontmatter(read(path))
            for path in sorted(glob.glob(os.path.join(case, "graders", "*.md")))}


class Suites(unittest.TestCase):
    def test_every_skill_has_at_least_3_cases(self):
        for skill in SKILLS:
            with self.subTest(skill=skill):
                self.assertGreaterEqual(len(cases(skill)), 3)

    def test_every_eval_folder_belongs_to_a_skill(self):
        for folder in glob.glob(os.path.join(EVALS, "*", "")):
            name = os.path.basename(os.path.dirname(folder))
            if name != "results":
                self.assertIn(name, SKILLS)

    def test_every_mistake_has_at_least_2_cases(self):
        tags = [items(split_frontmatter(read(os.path.join(case, "prompt.md")))[0].get("tags", "[]"))
                for case in cases()]
        for name in MISTAKES:
            with self.subTest(tag=name):
                self.assertGreaterEqual(sum(name in case_tags for case_tags in tags), 2)

    def test_marketplace_entry_points_at_its_suite(self):
        with open(os.path.join(ROOT, ".claude-plugin", "marketplace.json"), encoding="utf-8") as file:
            plugins = json.load(file)["plugins"]
        for plugin in plugins:
            with self.subTest(plugin=plugin["name"]):
                self.assertEqual(plugin.get("experimental", {}).get("evals"), f"evals/{plugin['name']}")


class Prompts(unittest.TestCase):
    def test_prompt_keys_are_known(self):
        for case in cases():
            fields, _ = split_frontmatter(read(os.path.join(case, "prompt.md")))
            with self.subTest(case=case):
                self.assertLessEqual(set(fields), PROMPT_KEYS)

    def test_prompt_has_a_body(self):
        for case in cases():
            _, body = split_frontmatter(read(os.path.join(case, "prompt.md")))
            with self.subTest(case=case):
                self.assertTrue(body)

    def test_case_loads_only_its_own_skill(self):
        for case in cases():
            fields, _ = split_frontmatter(read(os.path.join(case, "prompt.md")))
            with self.subTest(case=case):
                self.assertEqual(items(fields.get("plugins", "[]")), [f"../../../skills/{skill_of(case)}"])

    def test_case_is_tagged_with_its_skill_and_a_mistake(self):
        for case in cases():
            tags = items(split_frontmatter(read(os.path.join(case, "prompt.md")))[0].get("tags", "[]"))
            with self.subTest(case=case):
                self.assertIn(skill_of(case), tags)
                self.assertTrue(set(tags) & set(MISTAKES))

    def test_scaffold_script_exists(self):
        for case in cases():
            path = os.path.join(case, "case.yaml")
            if not os.path.exists(path):
                continue
            text = read(path)
            with self.subTest(case=case):
                self.assertIn('schema_version: "1.1"', text)
                self.assertRegex(text, rf"(?m)^name: {re.escape(os.path.basename(case))}$")
                script = re.search(r"scaffold_script: (\S+)", text)
                if script:
                    self.assertTrue(os.path.exists(os.path.join(case, script.group(1))))


class Graders(unittest.TestCase):
    def test_every_case_has_a_grader_on_the_result(self):
        for case in cases():
            kinds = [fields.get("type") for fields, _ in graders(case).values()]
            with self.subTest(case=case):
                self.assertTrue(set(kinds) & {"regex", "llm", "file_exists"})

    def test_every_case_checks_that_its_skill_loaded(self):
        for case in cases():
            fired = [fields for fields, _ in graders(case).values()
                     if fields.get("type") == "tool_used" and fields.get("tool") == "Skill"]
            with self.subTest(case=case):
                self.assertEqual(len(fired), 1)
                self.assertRegex(f'"skill": "{skill_of(case)}"', scalar(fired[0]["input_match"]))
                for other in SKILLS:
                    if other != skill_of(case):
                        self.assertNotRegex(f'"skill": "{other}"', scalar(fired[0]["input_match"]))

    def test_grader_keys_match_its_type(self):
        for case in cases():
            for name, (fields, body) in graders(case).items():
                kind = fields.get("type")
                with self.subTest(case=case, grader=name):
                    self.assertIn(kind, GRADER_KEYS)
                    options = set(fields) - {"type", "weight", "arm"}
                    self.assertLessEqual(options, GRADER_KEYS[kind])
                    self.assertLessEqual(REQUIRED_GRADER_KEYS[kind], options)
                    if kind == "llm":
                        self.assertRegex(body, r"\bPASS\b")
                        self.assertRegex(body, r"\bFAIL\b")

    def test_regex_patterns_compile(self):
        for case in cases():
            for name, (fields, _) in graders(case).items():
                for key in ("pattern", "input_match"):
                    if key in fields:
                        with self.subTest(case=case, grader=name, key=key):
                            re.compile(scalar(fields[key]))


class SharedText(unittest.TestCase):
    def test_no_dash_graders_are_identical(self):
        texts = {case: read(os.path.join(case, "graders", "no-dash.md")) for case in cases()
                 if os.path.exists(os.path.join(case, "graders", "no-dash.md"))}
        self.assertGreater(len(texts), 1)
        self.assertEqual(len(set(texts.values())), 1, sorted(texts))

    def test_no_dash_pattern_flags_only_prose_dashes(self):
        path = glob.glob(os.path.join(EVALS, "*", "*", "graders", "no-dash.md"))[0]
        pattern = re.compile(scalar(split_frontmatter(read(path))[0]["pattern"]))
        samples = [
            ("Run `cargo test parser::reads_trailing_space -- --nocapture`.", False),
            ("Run `git checkout -- src/main.rs` to drop the change.", False),
            ("The build-cache folder is 2-3 MB.", False),
            ("The scan \u2014 which runs first \u2014 finds it.", True),
            ("Versions 3.8\u20133.12 work.", True),
        ]
        for text, flagged in samples:
            with self.subTest(text=text):
                self.assertEqual(bool(pattern.search(text)), flagged)

    def test_cases_share_one_system_prompt(self):
        prompts = {split_frontmatter(read(os.path.join(case, "prompt.md")))[0].get("append_system_prompt")
                   for case in cases()}
        prompts.discard(None)
        self.assertEqual(len(prompts), 1, prompts)


if __name__ == "__main__":
    unittest.main()
