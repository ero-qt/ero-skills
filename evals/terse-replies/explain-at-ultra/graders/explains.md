---
type: llm
---

PASS if the reply explains that a commit hash covers the parent commit (and metadata such as the committer date), so a new parent gives a new hash, and it starts with that answer instead of a preamble.
FAIL if the explanation is wrong or missing, or the reply opens with a preamble such as "Great question" or "Let me explain".
