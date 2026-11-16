---
tags: [repo-writing, ai-tells]
plugins: ["../../../skills/repo-writing"]
max_turns: 20
allowed_tools: [Skill, Read, Glob, Grep]
append_system_prompt: "The workspace is empty on purpose. Treat what the user says about their repository and the earlier conversation as true, and don't look for the files. No shell is available, so give commands instead of running them."
---

Rewrite this README paragraph so it reads naturally. Keep every fact.

> This repo has 3 packages. `core` has the parser and the type checker. `cli` has the command line and has a `--watch` flag. The `docs` folder has the guides. Each guide has a runnable example. The changelog has every release since 0.1.
