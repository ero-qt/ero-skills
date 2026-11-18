"""Tests for the stage briefs and the links of the work-loop skill, run with `python3 -m unittest`."""

import glob
import os
import re
import unittest

WORK_LOOP = os.path.join(os.path.dirname(__file__), "..", "skills", "work-loop")
REFERENCES = os.path.join(WORK_LOOP, "references")

# Rows of the stage table in stages.md, mapped to the brief that runs them. The driver runs the rows mapped to None.
STAGES = {
    "Slice plan": None,
    "State check": None,
    "Plan and research": "plan",
    "Red test": "red",
    "Implement": "implement",
    "Adversarial tests": "adversarial",
    "Simplify": "simplify",
    "House style": "style",
    "Docs": "docs",
    "Review": "review",
    "Fix": "fix",
    "Driver verify": None,
    "Gate": None,
    "Record": None,
}


def read(path):
    with open(path, encoding="utf-8") as file:
        return file.read()


# Drops fenced blocks, because their links are examples.
def prose(text):
    return re.sub(r"^(`{3,}).*?^\1$", "", text, flags=re.S | re.M)


def table_rows(text, heading):
    section = text.split(f"## {heading}\n", 1)[1].split("\n## ", 1)[0]
    rows = [line for line in section.splitlines() if line.startswith("| ") and not line.startswith("| Stage")]
    return [re.sub(r" \(.*\)$", "", row.split("|")[1].strip()) for row in rows]


class StageBriefs(unittest.TestCase):
    def test_every_stage_of_the_table_is_known(self):
        stages = read(os.path.join(REFERENCES, "stages.md"))
        self.assertEqual(table_rows(stages, "Stages per size"), list(STAGES))
        self.assertEqual(table_rows(stages, "What each stage does"), list(STAGES))

    def test_every_agent_stage_has_a_brief(self):
        briefs = read(os.path.join(REFERENCES, "stage-briefs.md"))
        sections = re.findall(r"^## (\S+)$", briefs, re.M)
        self.assertEqual(sections, [brief for brief in STAGES.values() if brief])

    # A lens reads its items from the checklist, so every section it lists has to exist there. A review with only these 3 lenses skips a section that none of them lists.
    def test_every_review_lens_names_sections_of_the_checklist(self):
        review = read(os.path.join(REFERENCES, "stage-briefs.md")).split("## review\n", 1)[1].split("\n## ", 1)[0]
        checklist = re.findall(r"^## (.+)$", read(os.path.join(REFERENCES, "review-checklist.md")), re.M)
        lenses = dict(re.findall(r"^- `(\w+)`: (.+)$", review, re.M))
        self.assertEqual(list(lenses), ["correctness", "design", "prose", "all"])
        covered = set()
        for lens in ["correctness", "design", "prose"]:
            with self.subTest(lens=lens):
                named = re.findall(r'"([^"]+)"', lenses[lens])
                self.assertTrue(named)
                self.assertLessEqual(set(named), set(checklist))
                covered |= set(named)
        self.assertEqual(covered, set(checklist))


class Links(unittest.TestCase):
    # A link to a file that doesn't exist sends Claude to read nothing.
    def test_every_relative_link_points_to_a_file(self):
        for path in glob.glob(os.path.join(WORK_LOOP, "**", "*.md"), recursive=True):
            for target in re.findall(r"\]\(([^)#]+)\)", prose(read(path))):
                if "://" in target:
                    continue
                with self.subTest(file=os.path.relpath(path, WORK_LOOP), link=target):
                    self.assertTrue(os.path.exists(os.path.join(os.path.dirname(path), target)))


if __name__ == "__main__":
    unittest.main()
