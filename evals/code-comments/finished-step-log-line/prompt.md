---
tags: [code-comments, ai-tells]
plugins: ["../../../skills/code-comments"]
max_turns: 20
allowed_tools: [Skill, Read, Glob, Grep]
append_system_prompt: "The workspace is empty on purpose. Treat what the user says about their repository and the earlier conversation as true, and don't look for the files. No shell is available, so give commands instead of running them."
---

Write the log message template my C# build tool logs at Information level when it finishes copying the files of one package. It has the package id, the number of files and the time in milliseconds. Just the template string.
