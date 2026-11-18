---
tags: [repo-writing, ai-tells]
plugins: ["../../../skills/repo-writing"]
max_turns: 20
allowed_tools: [Skill, Read, Glob, Grep]
append_system_prompt: "The workspace is empty on purpose. Treat what the user says about their repository and the earlier conversation as true, and don't look for the files. No shell is available, so give commands instead of running them."
---

Write the PR title and body for a fix I'm sending to an open source project I don't maintain. In `src/config.rs` I changed `value.split(':')` to `value.splitn(2, ':')`, so `--out` now works with Windows paths like `C:\logs\out.txt`. Before, everything after the drive letter got dropped. It's a 1-line change. Reply with only the title and the body.
