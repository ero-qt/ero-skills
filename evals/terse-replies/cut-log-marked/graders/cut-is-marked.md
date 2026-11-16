---
type: llm
---

PASS if every block of log lines the reply quotes is either a contiguous copy of the original lines or marks each place where lines were left out (with "..." or a similar marker).
FAIL if the reply quotes log lines as one block while silently leaving lines out of the middle, or changes the text of a quoted line.
