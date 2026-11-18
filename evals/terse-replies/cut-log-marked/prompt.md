---
tags: [terse-replies, reply-shape]
plugins: ["../../../skills/terse-replies"]
max_turns: 20
allowed_tools: [Skill, Read, Glob, Grep]
append_system_prompt: "The workspace is empty on purpose. Treat what the user says about their repository and the earlier conversation as true, and don't look for the files. No shell is available, so give commands instead of running them."
---

Here's the end of the test run. Show me just the part that matters.

```
test parser::reads_empty_file ... ok
test parser::reads_one_line ... ok
test parser::reads_crlf ... ok
test parser::reads_bom ... ok
test parser::reads_tabs ... ok
test parser::reads_unicode ... ok
test parser::reads_long_line ... ok
test parser::rejects_nul ... ok
test parser::reads_trailing_space ... FAILED
test parser::reads_comment ... ok
test parser::reads_quoted ... ok
test parser::reads_escaped ... ok

failures:

---- parser::reads_trailing_space stdout ----
thread 'parser::reads_trailing_space' panicked at src/parser.rs:41:9:
assertion `left == right` failed
  left: None
 right: Some("key")

failures:
    parser::reads_trailing_space

test result: FAILED. 11 passed; 1 failed; 0 ignored; 0 measured; 0 filtered out
```
