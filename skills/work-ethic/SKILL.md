---
name: work-ethic
description: "Use when the user changes or asks about a knob (the loop level, auto mode, docs, issues, progress notes, agent models, worktrees, branch cleanup or the terse level), asks which knobs are in effect or how often the rules got broken, asks which of repo-writing, code-comments, terse-replies and work-loop covers what, or right after a compaction to reload the skills in order. Not for the work itself, which the other 4 skills cover."
---

# Work ethic

This skill ties together repo-writing, code-comments, terse-replies and work-loop. It keeps the knobs.

Paths like `<skills>/work-loop/...` start at the folder above this skill's base directory.

## Which skill does what

| Work | Skill |
|---|---|
| Chat replies | terse-replies |
| Commits, PRs, issues, review replies, readmes, changelogs | repo-writing |
| Code, names, comments, log lines, error messages | code-comments |
| The order of a repo task, its gates and its commits | work-loop |

Most tasks need more than 1. A commit follows work-loop for the steps, code-comments for the code and repo-writing for the subject. The reply that shows it follows terse-replies.

## After a compaction

Load the skills again in this order: terse-replies, repo-writing, code-comments, work-loop. Then read the house brief `.git/work-loop/house.md` if the repo has one. Read the newest ledger record with `node <skills>/work-loop/scripts/ledger.js last`. Do this before the next action and before you ask the user anything these files answer.

## Subagents

A subagent starts without the skills or the chat. When it writes code or repo text, put the path of the house brief in its prompt and tell it that repo text follows `<skills>/repo-writing/references/tells.md`. The work-loop stage agents already load repo-writing and code-comments.

## Knobs

The user changes a knob by saying its phrase on a line of its own, like `loop strict`. The terse phrases also work inside a sentence. The plugin's prompt hook saves the knob and shows all knobs in 1 line, like `knobs: terse full, loop standard, gated`.

| Knob | Phrase | Default | Skill |
|---|---|---|---|
| `terse` | `terse lite`, `terse full`, `terse ultra`, `normal replies` | `full` | terse-replies |
| `loop` | `loop light`, `loop standard`, `loop strict` | `standard` | work-loop |
| `autonomy` | `auto on`, `auto off` | `gated` | work-loop |
| `docs` | `docs repo`, `docs on`, `docs off` | `repo` | work-loop |
| `issues` | `issues house`, `issues after-code`, `issues never` | `house` | work-loop |
| `narrate` | `narrate silent`, `narrate milestones` | `silent` | work-loop |
| `review-model`, `plan-model`, `impl-model` | `review-model <model> [effort]` | the session model | work-loop |
| `worktrees` | `worktrees off`, `worktrees parallel` | `off` | work-loop |
| `cleanup` | `cleanup ask`, `cleanup auto` | `ask` | work-loop |

The Knobs section of work-loop and the Levels table of terse-replies say what each value does.

- `terse` goes in `${CLAUDE_PLUGIN_DATA}/knobs.json`, the user's file, so it stays the same in every repo and session.
- `autonomy` only lasts for the session it was said in and never goes in a file.
- The rest go in `.git/work-loop/knobs.json` of the repo, which wins over the user's file. Outside a repo they go in the user's file.

When the user asks for a knob in other words, or wants a default for every repo, save it yourself:

```bash
node "${CLAUDE_SKILL_DIR}/scripts/knobs.js" --data "${CLAUDE_PLUGIN_DATA}" set loop strict
node "${CLAUDE_SKILL_DIR}/scripts/knobs.js" --data "${CLAUDE_PLUGIN_DATA}" set review-model opus low --user
node "${CLAUDE_SKILL_DIR}/scripts/knobs.js" --data "${CLAUDE_PLUGIN_DATA}" --session "${CLAUDE_SESSION_ID}" show
```

`set` doesn't change `autonomy`, because only the user's own words turn auto mode on.

