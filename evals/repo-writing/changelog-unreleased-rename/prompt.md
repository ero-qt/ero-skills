---
tags: [repo-writing, conventions]
plugins: ["../../../skills/repo-writing"]
max_turns: 20
allowed_tools: [Skill, Read, Glob, Grep]
append_system_prompt: "The workspace is empty on purpose. Treat what the user says about their repository and the earlier conversation as true, and don't look for the files. No shell is available, so give commands instead of running them."
---

Update this changelog for a rename: `Client.fetch_all` is now `Client.list`. Reply with only the whole `Unreleased` section after your change.

```markdown
## [Unreleased]

### Added

- `Client.fetch_all` returns every item on the server, 100 at a time.

## [1.2.0] - 2026-09-01

### Added

- `Client.get` returns 1 item by its id.
```
