---
type: llm
---

PASS if `retryDelay` sits with the retry and time settings (next to `retryCount` or `timeout`). Every other parameter keeps its name and its group.
FAIL if `retryDelay` goes at the end, among the services or among the output settings. It also fails when a name changes or a parameter is missing.
