---
tags: [work-loop, conventions]
plugins: ["../../../skills/work-loop"]
max_turns: 20
allowed_tools: [Skill, Read, Glob, Grep]
append_system_prompt: "The workspace is empty on purpose. Treat what the user says about their repository and the earlier conversation as true, and don't look for the files. No shell is available, so give commands instead of running them."
---

I'm starting a new Python library called `tinyqueue` in an empty folder. It's a small in-memory job queue. There's no git repository yet, so there's nothing to check. You showed me the read-back and I said Go.

Now plan the first commits for me.
