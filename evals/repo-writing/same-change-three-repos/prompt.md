---
tags: [repo-writing, ai-tells]
plugins: ["../../../skills/repo-writing"]
max_turns: 20
allowed_tools: [Skill, Read, Glob, Grep]
append_system_prompt: "The workspace is empty on purpose. Treat what the user says about their repository and the earlier conversation as true, and don't look for the files. No shell is available, so give commands instead of running them."
---

I added the same Dependabot config (weekly updates for GitHub Actions, Monday 06:00 UTC) to my 3 repos `alpha`, `beta` and `gamma` today. Write the commit subject and the PR body for `beta`. Reply with only the subject and the body.
