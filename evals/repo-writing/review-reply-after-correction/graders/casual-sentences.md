---
type: llm
---

PASS if the reply reads like a short GitHub comment in first person that says what was changed and folds the test into the same or the next sentence (for example "I quoted `$dir` in `build.sh` and added a test with a folder called `my files`.").
FAIL if it is a list of what got done, clipped fragments, praise for the reviewer, or longer than 3 sentences.
Judge only the draft, not any notes around it.
