---
tags: [code-comments, ai-tells]
plugins: ["../../../skills/code-comments"]
max_turns: 20
allowed_tools: [Skill, Read, Glob, Grep]
append_system_prompt: "The workspace is empty on purpose. Treat what the user says about their repository and the earlier conversation as true, and don't look for the files. No shell is available, so give commands instead of running them."
---

Write a generic `retry(action, attempts)` helper in Python that calls `action` until it doesn't raise or the attempts run out, then raises the last error. Add 2 `unittest` tests for it.
