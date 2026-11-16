"""Tests for the stage agents in skills/work-loop/agents, run with `python3 -m unittest`."""

import glob
import json
import os
import re
import unittest

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
WORK_LOOP = os.path.join(ROOT, "skills", "work-loop")
AGENTS = os.path.join(WORK_LOOP, "agents")
BRIEFS = os.path.join(WORK_LOOP, "references", "stage-briefs.md")
WORKFLOW = os.path.join(WORK_LOOP, "workflows", "commit-cycle.js")

# Skills that write or judge repo text and code. Plugin skills are named <plugin>:<skill>.
PRELOADED = ["repo-writing:repo-writing", "code-comments:code-comments"]
READ_ONLY_TOOLS = {"Read", "Grep", "Glob", "Bash"}


def read(path):
    with open(path, encoding="utf-8") as file:
        return file.read()


def frontmatter(text):
    match = re.match(r"---\n(.*?)\n---\n(.*)", text, re.S)
    fields, key = {}, None
    for line in match.group(1).splitlines():
        if line.startswith("  - ") and key:
            fields[key].append(line[4:].strip())
            continue
        key, _, value = line.partition(":")
        fields[key] = value.strip() or []
    return fields, match.group(2)


def briefs():
    return re.findall(r"^## (\S+)$", read(BRIEFS), re.M)


def agent_files():
    return sorted(glob.glob(os.path.join(AGENTS, "*.md")))


class StageAgents(unittest.TestCase):
    def test_every_brief_has_an_agent(self):
        names = [os.path.basename(path)[:-3] for path in agent_files()]
        self.assertEqual(sorted(names), sorted(f"stage-{brief}" for brief in briefs()))

    def test_frontmatter_names_the_file_and_preloads_the_writing_skills(self):
        for path in agent_files():
            fields, _ = frontmatter(read(path))
            with self.subTest(agent=os.path.basename(path)):
                self.assertEqual(fields["name"], os.path.basename(path)[:-3])
                self.assertTrue(fields["description"])
                self.assertNotIn(":", fields["name"])
                self.assertEqual(fields["skills"], PRELOADED)

    # The body points at its section of the briefs, so a brief lives in 1 place.
    def test_body_points_at_its_brief(self):
        for path in agent_files():
            fields, body = frontmatter(read(path))
            stage = fields["name"].removeprefix("stage-")
            with self.subTest(agent=fields["name"]):
                self.assertIn("${CLAUDE_PLUGIN_ROOT}/skills/work-loop/references/stage-briefs.md", body)
                self.assertIn(f'"{stage}"', body)
                self.assertIn('"Every stage"', body)

    # A reviewer that can edit files isn't read-only.
    def test_reviewer_only_gets_read_tools(self):
        fields, _ = frontmatter(read(os.path.join(AGENTS, "stage-review.md")))
        tools = {tool.strip() for tool in fields["tools"].split(",")}

        self.assertEqual(tools, READ_ONLY_TOOLS)


class Wiring(unittest.TestCase):
    def test_workflow_runs_each_stage_as_its_agent(self):
        script = read(WORKFLOW)

        self.assertIn("work-loop:stage-", script)
        for stage in re.findall(r"^  (\w+): \[", script.split("const TABLE = {", 1)[1].split("}", 1)[0], re.M):
            with self.subTest(stage=stage):
                self.assertTrue(os.path.exists(os.path.join(AGENTS, f"stage-{stage}.md")))

    # The plugin's source is the repo root, so only the work-loop entry lists the agent files.
    def test_work_loop_entry_lists_every_agent(self):
        plugins = {plugin["name"]: plugin for plugin in json.loads(read(os.path.join(ROOT, ".claude-plugin", "marketplace.json")))["plugins"]}

        listed = sorted(os.path.normpath(os.path.join(ROOT, path)) for path in plugins["work-loop"]["agents"])
        self.assertEqual(listed, [os.path.normpath(path) for path in agent_files()])
        for name, plugin in plugins.items():
            if name != "work-loop":
                with self.subTest(plugin=name):
                    self.assertNotIn("agents", plugin)
        self.assertFalse(os.path.exists(os.path.join(ROOT, "agents")))


if __name__ == "__main__":
    unittest.main()
