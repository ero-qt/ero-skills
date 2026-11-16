---
tags: [work-loop, conventions]
plugins: ["../../../skills/work-loop"]
max_turns: 20
allowed_tools: [Skill, Read, Glob, Grep]
append_system_prompt: "The workspace is empty on purpose. Treat what the user says about their repository and the earlier conversation as true, and don't look for the files. No shell is available, so give commands instead of running them."
---

This conversation was compacted. Summary: you're on branch `fix/timeout` in a Python repo, fixing a request timeout that ignores the `timeout` setting. The plan had 3 commits and commit 1 is done. Commit 2 (pass `timeout` through to the HTTP session) is staged and waits for my approval. Continue.
