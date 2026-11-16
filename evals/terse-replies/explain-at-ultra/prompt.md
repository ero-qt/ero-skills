---
tags: [terse-replies, reply-shape]
plugins: ["../../../skills/terse-replies"]
max_turns: 20
allowed_tools: [Skill, Read, Glob, Grep]
append_system_prompt: "The workspace is empty on purpose. Treat what the user says about their repository and the earlier conversation as true, and don't look for the files. No shell is available, so give commands instead of running them."
---

terse ultra

Explain why `git rebase` gives my commits new hashes even when the code in them doesn't change.
