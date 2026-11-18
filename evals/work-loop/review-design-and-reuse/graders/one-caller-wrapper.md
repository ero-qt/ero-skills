---
type: llm
---

PASS if the review points out that `fetch_rows` doesn't do any work of its own beyond its 1 call site and says to fold it into `Report.totals` or remove it.
FAIL if the review doesn't mention `fetch_rows`, or keeps it.
