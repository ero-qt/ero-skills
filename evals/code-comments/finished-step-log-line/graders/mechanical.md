---
type: llm
---

PASS if the template is label: value pairs (such as "Copied package: {PackageId}, files: {FileCount}, elapsed: {ElapsedMs} ms") and not a full sentence.
FAIL if the template is a prose sentence such as "Finished copying {FileCount} files for {PackageId} in {ElapsedMs} ms." or has a trailing period or exclamation mark.
