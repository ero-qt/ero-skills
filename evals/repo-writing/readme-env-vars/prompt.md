---
tags: [repo-writing, ai-tells]
plugins: ["../../../skills/repo-writing"]
max_turns: 20
allowed_tools: [Skill, Read, Glob, Grep]
append_system_prompt: "The workspace is empty on purpose. Treat what the user says about their repository and the earlier conversation as true, and don't look for the files. No shell is available, so give commands instead of running them."
---

Write the usage section of the README for my CLI `logtrim`, which deletes old lines from log files. It reads 3 environment variables:

- `LOGTRIM_MAX_LINES`: how many lines to keep per file, default 1000
- `LOGTRIM_DIR`: the folder with the logs, default `./logs`
- `LOGTRIM_DRY_RUN`: when it's `1`, it prints the files it would trim and doesn't change them

An unset variable uses its default. A `LOGTRIM_DIR` that doesn't exist makes it exit with code 2 and print `logtrim: no such directory`. A `LOGTRIM_MAX_LINES` that isn't a number is treated as unset.

Reply with only the section.
