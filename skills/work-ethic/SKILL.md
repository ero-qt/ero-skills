---
name: work-ethic
description: "Use when the user changes or asks about a knob (the loop level, auto mode, docs, issues, progress notes, agent models, worktrees, branch cleanup or the terse level), asks which knobs are in effect or how often the rules got broken, asks which of repo-writing, code-comments, terse-replies and work-loop covers what, or right after a compaction to reload the skills in order. Not for the work itself, which the other 4 skills cover."
---

# Work ethic

This skill ties together repo-writing, code-comments, terse-replies and work-loop. Its plugin runs the hooks of all 4, keeps the knobs and counts how often a rule gets broken.

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

## Hooks

The plugin's hooks run for the whole session, whether this skill is loaded or not.

- At every prompt, `scripts/knobs.js` saves the knob phrases and shows the knobs in 1 line. After a reply that broke a terse rule, it adds the full terse rules once.
- At the start of a session it shows the terse rules and the knobs. After a compaction it also lists the skills to load again. After a compaction, a resume or a fork it gives the house brief and the newest ledger record.
- At the end of each turn, `reply-check.js` of terse-replies writes down the reply rules it finds broken. It never stops the turn.
- Before a `git commit`, `commit-guard.js` of work-loop stops a commit with a trailer, a hard prose finding or a path that must never be staged. It warns when source changed without a doc change.

## Knobs

The user changes a knob by saying its phrase on a line of its own, like `loop strict`. The terse phrases also work inside a sentence. `auto on` only works as the whole message, because a subagent report also comes in as a prompt. The plugin's prompt hook saves the knob and shows all knobs in 1 line, like `knobs: terse full, loop standard, gated`.

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
- `autonomy` only lasts for the session it was said in and never goes in a file. A resumed session starts gated again.
- The rest go in `.git/work-loop/knobs.json` of the repo, which wins over the user's file. Outside a repo they go in the user's file.

When the user asks for a knob in other words, or wants a default for every repo, save it yourself:

```bash
node "${CLAUDE_SKILL_DIR}/scripts/knobs.js" --data "${CLAUDE_PLUGIN_DATA}" set loop strict
node "${CLAUDE_SKILL_DIR}/scripts/knobs.js" --data "${CLAUDE_PLUGIN_DATA}" set review-model opus low --user
node "${CLAUDE_SKILL_DIR}/scripts/knobs.js" --data "${CLAUDE_PLUGIN_DATA}" --session "${CLAUDE_SESSION_ID}" show
```

`set` refuses `autonomy`, because only the user's own words turn auto mode on. When the user asks for auto mode in other words, ask them to send `auto on` as a message of its own.


## Slips

The hooks write every rule they find broken to `${CLAUDE_PLUGIN_DATA}/slips.jsonl`. When the user asks how often the rules get broken, run this and show its lines as they are:

```bash
node "${CLAUDE_SKILL_DIR}/scripts/status.js" --data "${CLAUDE_PLUGIN_DATA}" --days 7
```

A rule that keeps coming back after its text changed needs a check in a script, not more text.
