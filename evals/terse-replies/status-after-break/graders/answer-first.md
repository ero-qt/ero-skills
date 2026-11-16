---
type: llm
---

PASS if the first line of the reply states the status (the fix is done and staged, or tests pass) with no greeting, preamble or restated question before it.
FAIL if the first line is a greeting, an announcement such as "Here's where we are", or anything other than the status itself.
