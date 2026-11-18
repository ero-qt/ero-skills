---
type: llm
---

PASS if the review points out that the parameter `writer` of `Report.__init__` is named after the wrong role, because it gets a `RowReader`, and suggests a name like `row_reader` or `reader`.
FAIL if the review doesn't mention the name `writer`, or keeps it.
