---
tags: [work-loop, gates]
plugins: ["../../../skills/work-loop"]
max_turns: 20
allowed_tools: [Skill, Read, Glob, Grep]
append_system_prompt: "The workspace is empty on purpose. Treat what the user says about their repository and the earlier conversation as true, and don't look for the files. No shell is available, so give commands instead of running them."
---

Earlier you showed me this PR draft for my branch `fix/empty-config`:

Title: `Fix crash on empty config file`

Body: "This PR fixes a crash. When the config file is empty, `load()` raised `KeyError`. Now it returns the defaults."

Change the body so the first sentence starts with "Fixes" and says what the PR does.
