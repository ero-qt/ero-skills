---
tags: [repo-writing, ai-tells]
plugins: ["../../../skills/repo-writing"]
max_turns: 20
allowed_tools: [Skill, Read, Glob, Grep]
append_system_prompt: "The workspace is empty on purpose. Treat what the user says about their repository and the earlier conversation as true, and don't look for the files. No shell is available, so give commands instead of running them."
---

A reviewer on my PR wrote: "This breaks when the path has spaces, you need to quote it." They're right. I fixed it by quoting `$dir` in `build.sh` and added a test with a folder called `my files`. Write my reply to the comment. Reply with only the text of the comment.
