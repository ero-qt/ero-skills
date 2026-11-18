# Slice plan

A slice plan comes before the first commit of a large change. At `loop strict` a medium change gets one too. Show it to the user and wait for `Go?`. At `autonomy: auto`, write `gate: auto` in the ledger instead. Keep the plan in a file when the work runs long or the user is away, in the place where the user keeps plans, and write its path in the `slice` record. When there isn't a place yet, ask in the read-back. Don't put it under `.git`, because Claude Code asks before it writes a file there and the question stops a run while the user is away.

## Form

```markdown
# <branch>: <goal in a few words>

Resume: read this file, then `git log -15`, and go on at the first open item.

## Goal

<1 result someone can see, like "the tool reads a config file and prints the merged settings">

## Rules for every commit

- <from the house brief and the user's words for this work>

## Commits

- [ ] 1. `<subject>` (<size>). First failing test: <test and the fact it pins>
- [ ] 2. ...

## Out of scope

- <what this branch won't do, and where it goes instead>

## Open decisions

- <a question for the user, with the default you'd pick>

## Log

- <date>: <what happened, what got deleted>
```

## How to fill it

- The goal is 1 result a person can check by running something, not a list of parts.
- Every commit gets its size and its first failing test. A commit without a test it can fail is a refactor or docs commit, so say which.
- Put every commit that builds a part before the commit that first uses it. Don't plan a type with no user in the same branch.
- For a new repo, suggest a readme, a changelog, an agents file, a license and CI once, as the first commit.
- Tick a commit when it's made and add its hash. Add a log line for anything deleted, so the user can get it back.
- A design fork at `autonomy: auto` goes under open decisions and work goes on with the commits that don't depend on it.
