---
type: llm
---

PASS if the added comment starts with what the code does (a verb such as "Sets up" or "Starts") and then gives the reason with "because" or "so", in 1 or 2 plain sentences.
FAIL if the comment starts with the fact or the reason ("load_config logs...", "Note:"), uses a label like "IMPORTANT:", or runs longer than 2 lines.
