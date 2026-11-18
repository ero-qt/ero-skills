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
    if not match:
        return {}
    fields = {}
    for line in match.group(1).splitlines():
        key, separator, value = line.partition(": ")
        if separator:
            fields[key] = value
    return fields


class Frontmatter(unittest.TestCase):
    def test_every_skill_has_its_folder_name(self):
        for path in glob.glob(os.path.join(SKILLS, "*", "SKILL.md")):
            with self.subTest(path=path):
                self.assertEqual(frontmatter(path).get("name"), os.path.basename(os.path.dirname(path)))

    def test_description_is_a_valid_yaml_scalar(self):
        for path in glob.glob(os.path.join(SKILLS, "*", "SKILL.md")):
            description = frontmatter(path)["description"]
            with self.subTest(path=path):
                if description[:1] == "'":
                    continue
                if description[:1] == '"':
                    # A bare " inside ends the double-quoted scalar early.
                    self.assertNotRegex(description[1:-1], r'(?<!\\)"')
                    continue
                # A YAML plain scalar ends at ": " or " #", so strict parsers reject or cut the description.
                self.assertNotIn(": ", description)
                self.assertNotIn(" #", description)


if __name__ == "__main__":
    unittest.main()
