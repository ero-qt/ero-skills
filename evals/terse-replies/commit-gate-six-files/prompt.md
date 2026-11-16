---
tags: [terse-replies, reply-shape]
plugins: ["../../../skills/terse-replies"]
max_turns: 20
allowed_tools: [Skill, Read, Glob, Grep]
append_system_prompt: "The workspace is empty on purpose. Treat what the user says about their repository and the earlier conversation as true, and don't look for the files. No shell is available, so give commands instead of running them."
---

The change is done. Show me the commit so I can approve it. Here's what's staged:

- `src/upload/client.py`: adds a `max_retries` argument, default 3
- `src/upload/retry.py`: new helper that waits 1, 2 and 4 seconds between tries
- `src/upload/__init__.py`: exports the helper
- `tests/test_client.py`: 4 new tests
- `tests/test_retry.py`: 3 new tests
- `CHANGELOG.md`: entry under Unreleased

Tests: `pytest` passes 48/48. The subject I'd use is `Add retry limit to upload client`. After this one, 1 more commit is left.
