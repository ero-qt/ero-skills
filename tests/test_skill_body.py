"""Tests for the size of every skills/<name>/SKILL.md body, run with `python3 -m unittest`.

After a compaction Claude Code keeps the first 5,000 tokens of each skill it loaded. The count here is
characters divided by 4, which needs no tokenizer. It's only an estimate: code, paths and tables take more
tokens per character than plain English, so check the real count with a tokenizer before a release.
"""

import glob
import math
import os
import re
import unittest

SKILLS = os.path.join(os.path.dirname(__file__), "..", "skills")
COMPACTION_TOKENS = 5000
LIMITS = {"work-loop": 4500}


def body_tokens(path):
    with open(path, encoding="utf-8") as file:
        text = file.read()
    body = re.sub(r"\A---\n.*?\n---\n", "", text, flags=re.S)
    return math.ceil(len(body) / 4)


class Body(unittest.TestCase):
    def test_every_body_fits_what_compaction_keeps(self):
        paths = glob.glob(os.path.join(SKILLS, "*", "SKILL.md"))
        self.assertIn("work-loop", [os.path.basename(os.path.dirname(path)) for path in paths])
        for path in paths:
            name = os.path.basename(os.path.dirname(path))
            with self.subTest(skill=name):
                self.assertLessEqual(body_tokens(path), LIMITS.get(name, COMPACTION_TOKENS))


if __name__ == "__main__":
    unittest.main()
