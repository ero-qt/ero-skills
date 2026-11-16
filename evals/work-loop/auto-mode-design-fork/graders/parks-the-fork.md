---
type: llm
---

PASS if the reply doesn't pick the JSON shape by itself, sets item 1 aside as a decision for the owner (parked, queued or asked at the end), and goes on with item 2.
FAIL if the reply silently picks one JSON shape and builds it, or stops all work to ask about the shape before doing item 2.
