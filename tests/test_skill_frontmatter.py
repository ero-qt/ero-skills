"""Tests for the frontmatter of every skills/<name>/SKILL.md, run with `python3 -m unittest`."""

import glob
import os
import re
import unittest

SKILLS = os.path.join(os.path.dirname(__file__), "..", "skills")


def frontmatter(path):
    with open(path, encoding="utf-8") as file:
        text = file.read()
    match = re.match(r"---\n(.*?)\n---\n", text, re.S)
    return dict(line.split(": ", 1) for line in match.group(1).splitlines()) if match else {}


class Frontmatter(unittest.TestCase):
    def test_every_skill_has_its_folder_name(self):
        for path in glob.glob(os.path.join(SKILLS, "*", "SKILL.md")):
            with self.subTest(path=path):
                self.assertEqual(frontmatter(path).get("name"), os.path.basename(os.path.dirname(path)))

    def test_plain_description_has_no_yaml_mapping_or_comment_mark(self):
        # A YAML plain scalar ends at ": " or " #", so strict parsers reject or cut the description.
        for path in glob.glob(os.path.join(SKILLS, "*", "SKILL.md")):
            description = frontmatter(path)["description"]
            if description.startswith('"'):
                continue
            with self.subTest(path=path):
                self.assertNotIn(": ", description)
                self.assertNotIn(" #", description)


if __name__ == "__main__":
    unittest.main()
