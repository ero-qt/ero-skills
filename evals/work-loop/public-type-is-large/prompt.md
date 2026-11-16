---
tags: [work-loop, process-weight]
plugins: ["../../../skills/work-loop"]
max_turns: 20
allowed_tools: [Skill, Read, Glob, Grep]
append_system_prompt: "The workspace is empty on purpose. Treat what the user says about their repository and the earlier conversation as true, and don't look for the files. No shell is available, so give commands instead of running them."
---

The state check is done: the tree is clean, CI is green and there are no open PRs or issues. This repo doesn't use issues. You showed me the read-back and I said Go.

The task: add a public `RateLimiter` class to my HTTP client library. It should let callers cap requests per second per host. Now tell me how you'll approach it, before writing any code.
