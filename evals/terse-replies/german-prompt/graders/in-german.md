---
type: llm
---

PASS if the reply is in German, gives the fix for the long line in `src/save.py:88` with an exact step, and any closing labels are German (such as "Stand:" and "Weiter:").
FAIL if the reply is in English, or uses English labels such as "State:" or "Next:".
