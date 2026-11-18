---
tags: [code-comments, ai-tells]
plugins: ["../../../skills/code-comments"]
max_turns: 20
allowed_tools: [Skill, Read, Glob, Grep]
append_system_prompt: "The workspace is empty on purpose. Treat what the user says about their repository and the earlier conversation as true, and don't look for the files. No shell is available, so give commands instead of running them."
---

Add a comment above the first line of this Python function. It needs to explain that `init_logging()` must run before `load_config()`, because `load_config()` logs a warning for every unknown key and those warnings get dropped while logging isn't set up. Show me the function with the comment.

```python
def main():
    init_logging()
    config = load_config()
    run(config)
```
