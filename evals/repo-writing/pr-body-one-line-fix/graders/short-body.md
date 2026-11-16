---
type: llm
---

PASS if the PR body (not counting the title and any label line) is 1 or 2 sentences, starts with a verb such as "Fixes" or "Makes", and mentions the Windows path case.
FAIL if the body runs longer than 2 sentences, has headings or a list, or talks about tests or how the bug was found.
Judge only the draft, not any notes around it.
