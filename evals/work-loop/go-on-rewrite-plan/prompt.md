---
tags: [work-loop, gates]
plugins: ["../../../skills/work-loop"]
max_turns: 20
allowed_tools: [Skill, Read, Glob, Grep]
append_system_prompt: "The workspace is empty on purpose. Treat what the user says about their repository and the earlier conversation as true, and don't look for the files. No shell is available, so give commands instead of running them."
---

Earlier you proposed: "Squash the 3 unpushed commits on `feature/export` into 1 commit with the subject `Add export command`." Go.
