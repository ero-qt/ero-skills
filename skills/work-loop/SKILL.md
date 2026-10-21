---
name: work-loop
description: Use for any coding task on a repository (fix, feature, refactor, review follow-up, issue or PR work). Reread it after every context compaction. Fixed order with a gate before every artifact: live state check (fetch, open PRs and issues from everyone, CI), read-back, issue, plan, test-first commits presented and approved one at a time, end-to-end check, read-only review, PR, report. Also covers git safety, permissions, downloads and agent fan-out. Pairs with repo-writing, code-comments and terse-replies.
---

# Work loop

One change, one fixed path, a gate before every artifact. The loop is the job, not a suggestion: dropping a step because the task looks small or the session is long or a compaction happened is exactly what this skill exists to stop.

Paths like `<skills>/repo-writing/scripts/prose_check.py` start at the folder that holds these skills, one level above the base directory shown when a skill loads. Run Python scripts with `python3` (`python` on Windows).

Once loaded, the loop stays on for the rest of the session. After a compaction or a resume, reread this file and any handoff or state notes before the next action. Every reply during loop work shows the current step by its heading and the progress inside it (`step: commit loop, commit 2/4`).

Sidebars, quick questions and exploration stay flexible. The loop applies once work will end in a commit, an issue, a PR or a comment.

## The order

```
state check -> read-back -> Go? -> research -> (issue draft -> Approve?)+ -> create issue -> branch
  -> prior art -> plan -> Go?
  -> ( failing test -> code -> narrow tests, CI's format and lint -> end-to-end run -> prose sweep
       -> stage by path -> present -> Approve? -> commit )+
  -> review (read-only, no chat context) -> (findings -> commit loop)*
  -> (PR draft -> Approve?)+ -> open PR -> report -> watch reviews and CI
```

A rejected gate is a lap: rework, restage, present again. Nothing is committed, opened or posted between a rejection and the next approval.

## Gates

- The gate words are `Go?`, `Approve?` and `Review?`. Whatever the word gates (the read-back, the plan, the full draft, the commit table) sits in chat above it, verbatim, never described.
- Ask a gate in plain chat as the last line of the turn, so the draft above it stays visible.
- Use the question tool for real choices between options (pick an approach, pick a name, answer a blocker). Make each option self-contained with the recommended one first. Put the reasons inside the option descriptions, since text above the question can be hidden.
- Only an explicit approve or a clear yes opens a gate. It covers only the one item just shown. "ok", "ya", "sure", "in" count as yes when they answer the gate. An acknowledgment ("ah i missed it"), frustration ("do whatever", "fine, whatever"), or approval of the work is not approval of the text. When the user clearly approves mid-thread ("i'm clearly approving this commit right now"), take it.
- Never open, post, edit, commit or push before its gate returns. Never call anything committed, opened or posted before it is. If something went out early, fix it at once and say so.
- When the user posts in their own name, hand them the text and stop. Never post for them unless told.
- Autonomous mode exists only when the user grants it in words for a stretch of work. Then skip the per-commit, PR-text and `Review?` gates, but keep the commit style, staging by path, the review itself, the end-to-end check and the CI watch. Still never push the default branch.
  - Permissions and safety below still apply: no downloads, installs, deletes, force pushes or posts in the user's name without a yes.
  - A design fork, an unreadable failure or a reserved decision stops only that item. Independent work goes on. A public API break counts as a design fork.
  - Rebasing your own unpushed commits onto a branch a maintainer updated is fine, since the push stays a fast-forward.
  - When signing needs a passphrase and the user is away, commit nothing more and report it.
  - Watch CI for up to 30 minutes. Still pending after that: report it as pending.
  - End the stretch with one report: what was done and pushed, what waits and why, then one question tool call holding every queued decision.

## 0. State check

Run it at the start of every task and after every resume. Run it again right before presenting, committing or pushing. Read [scripts/state.sh](scripts/state.sh) and run it with a few words about the task:

```bash
bash <skills>/work-loop/scripts/state.sh "login timeout" "session cookie"
```

It fetches and prints the branch, the tree, a missing upstream and how far the branch is behind its base. Then it lists open PRs and issues from everyone that match the words, the user's own PRs and the CI checks of the current branch's PR. Exit code 2 means `gh` is signed out or missing, 3 means the remote isn't on GitHub. Then:

- Open every matching PR and issue that could overlap and read it. Someone else's open PR for the same bug blocks filing a new one.
- For a PR the session already touched, check `gh pr view <N> --json state,reviews,commits,mergeable` before touching it again. It may be merged already or a maintainer may have pushed to it.
- Reread every message the user sent while you were working and handle each point before going on. When the user reports a problem, deal with it first.
- Check the tree for edits you didn't make and for inline instruction comments the user left. Never revert, stash or rewrite a change of unknown origin.
- When part of the check can't run (signed out, offline), put that blocker on the first line of the next reply with the fix, and finish the check before the plan. The read-back and read-only research can still go ahead while it is blocked.

## 1. Read-back

One line with the change as understood and the options in effect (branch name, issue or not, review or not). A quick look at the code to understand the request is fine first, but deeper research waits for `Go?`. When a request seems to go against a documented design, say so in the read-back. Open options (issue or not, branch base) go in the read-back as one line each with the default you'd pick, so the user's answer to `Go?` settles them. End on a bare `Go?`.

## 2. Research

Knowledge for the drafts, not a message.

- Read the code the change touches and its tests. Read the actual code of any reference implementation before describing or planning a mechanism, even in a one-line answer. If what you would write has no counterpart in the code, ask instead of inventing it.
- Look for an existing API, base type or helper before adding one (`rg` for the concept, the repo's own base classes, the user's reference repos).
- Read the house style: `CONTRIBUTING*`, `.github/ISSUE_TEMPLATE/`, `.github/PULL_REQUEST_TEMPLATE*`, `.editorconfig`, linter and analyzer config, the CI workflow files (for the exact commands CI runs), `git log --format=%s -30`, recent merged PR titles and bodies. A new project with no precedent follows the language's or the industry's standard.
- Read the repo's planning or agent docs (`AGENTS.md`, `CLAUDE.md`, decision logs) alongside the code, never instead of it. Notes written down from the user's offhand comments are context, not law. The user's current words win.
- Measure instead of guessing. One quick test settles a suspected cause faster than reading. Before filing a bug from a symptom, trace the symptom back to its first wrong value. Before claiming something is missing, check whether the code, the disk or the reference already has it.
- Verify every factual claim (what is merged, released, built, what an API does) before stating it.

## 3. Issue

Skip this step on repos that don't use issues or when the user tells you to. When you can't tell (no history, issues unreadable), ask in the read-back.

- File only a confirmed cause. A theory gets said as a theory in chat, not filed.
- Draft with repo-writing and show it the way repo-writing §10 shows every draft. `Approve?` On approve, `gh issue create --repo <owner/repo> --title "..." --body-file -` with the body on stdin, once. Keep the number.
- Don't split work into many tiny issues. A small side fix rides along in a related PR without its own issue.

## 4. Branch

- Name it like the repo's history. Without a precedent: `issue-<N>` for issue work, `issue-<N>/<part>` when the issue will have parts, `<kind>/<slug>` (`fix/`, `feat/`) for work without an issue. Never a PR number and never a number plus a slug.
- Branch off the default branch. When the change builds on unmerged work, branch off that work and mark the PR as depending on it.
- Work in the main checkout. No worktrees unless the user asks.
- On someone else's repo, work through the user's fork only: `origin` is the fork, `upstream` is fetch-only with its push URL set to `DISABLED` (`git remote set-url --push upstream DISABLED`). Open PRs with `gh pr create --repo <org>/<repo> --head <user>:<branch>`.

## 5. Prior art and plan

- Check prior art before planning: a sibling in the repo, the library's docs, the user's own earlier attempts and reference repos, one or two known implementations. When a recognized model exists, follow it instead of reinventing beside it. When the repo already has a precedent for this kind of change, follow it without asking the maintainers first.
- Settle the public API shape before sketching an implementation.
- Post the plan as a numbered list, one commit per item, each line with the behavior it covers and its first failing test. `Go?`
- When the repo has no test setup, the plan starts with a commit that adds one in the language's standard form (`unittest` or `pytest` for Python, `cargo test` for Rust), and CI to run it.
- Build only what was asked and what the issue needs. Don't build ahead of the layer you're on. Never cut or weaken a feature the user called required. Propose a later slice instead. Don't bring back a rejected design under a new name.

## 6. Commit loop

Work the whole change out end to end, then stage and present exactly one commit at a time.

1. Write one failing test, in its own tool call. For a fix whose failure CI already shows (a lint error, a type error), that failing CI job is the failing test: reproduce it locally first. Run it and confirm it fails for the intended reason. A test that passes on its first run gets rewritten until it fails.
2. Write the least code that passes it, in a separate tool call. The test and the code go into the same commit.
3. Run the narrow tests for the touched area. Run the format and lint commands CI runs, verbatim, not a narrower variant. Fix every warning in touched files.
4. Run the real thing end to end on every OS and path the change touches (the binary, the game, the tool, the page). Passing tests and a hand-run equivalent are not enough. When a check needs an app or game running and it isn't, ask the user to start it right away.
5. Decide whether the change belongs in the changelog: anything a user of the project would notice does. A fix to something not released yet changes the existing `Unreleased` entry instead of adding one. Tests, CI and refactors get no entry. When the repo keeps one, add the entry in the same commit under `## [Unreleased]`, in the file's own form. Without a house form, follow [Keep a Changelog 2.0.0](https://keepachangelog.com/en/2.0.0/): the types `Added`, `Changed`, `Deprecated`, `Removed`, `Fixed`, `Security` in that order, and a `**Breaking:**` marker on breaking entries. Say in the presentation whether the commit got an entry and why.
6. Sweep every new line of prose (comments, doc comments, test names, the commit subject) for tells: run `python3 <skills>/repo-writing/scripts/prose_check.py --staged` after staging and fix what it flags.
7. Stage by explicit path. Commits are the one draft with their own shape, the table below. Run `git status --short` first and read it. Never `git add -A` or `git commit -a`. Every staged hunk must match the commit subject. An untracked file never rides along in an unrelated commit.
8. Present in this shape, then end the turn:

````
**<what the commit does, one line>**

| File | Change |
|---|---|
| [path/file.rs](path/file.rs) | <what changed> |

`<test command>` -> `<its last line>`
Changelog: <entry added, or why none>
`<end-to-end command>` -> `<what it showed>`

`<commit subject>`

Approve? Next: <what comes after> (<n+1>/<m>).
````

9. On approve, `git commit -m "<subject>"` with that subject exactly. Nothing else in the same turn.

Running tests and builds:

- Never pipe a test, build or sweep run through `grep`, `head` or `tail`. Redirect the whole run to a log file in the scratchpad, then read the file: `cargo test --offline > "$SP/test-<what>.log" 2>&1; echo "exit $?"`.
- Never start a run while another run of the same project is alive. Never edit or build a project while its run is in flight.
- Never rerun the full suite after a narrow fix that the narrow run already verified. Never retry a long command unchanged. Change something or report.
- Reuse finished artifacts and measurements instead of rebuilding them.
- Make long runs print progress and run headless, with no windows or prompts stealing focus. Give the user a command to watch them.

Fixups and scope:

- Amend a wording fix into the commit that introduced the line (check with `git blame`). Present the fixup before committing it. Behavior changes and refactors get their own commits. Never restructure inside a fixup.
- Split a function that grew past a screen in its own refactor commit before adding to it.
- Keep the diff to what the issue needs. Small related side fixes ride along. Anything bigger becomes an issue draft at the end, unfiled.
- When the user corrects something, apply the correction to every occurrence in the repo and in the session's open PRs, not just the spot shown.

## 7. Review

Run it before every PR, also in autonomous mode. Skip it only when the user tells you to.

- Say in chat which model and effort the reviewer runs at, then `Review?`.
- The reviewer is one read-only agent with no chat context. Give it the issue text, the full diff against the base and the test command. Tell it not to edit anything and not to start long processes. Have it work through [references/review-checklist.md](references/review-checklist.md) and return a verdict line and a table of severity, location, finding and the input that shows it.
- Judge every finding on its merits. Rebut a wrong but plausible one instead of appeasing it. Real findings go back through the commit loop, test first.
- When a reviewer flags one site, rerun that criterion over the whole function and diff.

## 8. Pull request

- Draft with repo-writing and show it the way repo-writing §10 shows every draft: label line, title in inline code, body in a 4-backtick fence. `Approve?`
- On approve, run it once: `gh pr create --repo <owner/repo> --head <user>:<branch> --base <base> --title "..." --body-file -` with the body on stdin. A stacked PR gets `--base` set to the branch it depends on.
- Before every push, check for trailers: `git log --format=%B <base>..HEAD | grep -ci co-authored-by` must print `0`.
- Report: the PR link and what it does, a table of the commits, the state, then `Next: say done when merged.`

## 9. After

- Watch reviews and CI. After a changes-requested review, check for new commits or a merge before and during the fix. Report fast.
- Before any force-push, `git fetch` and read the remote branch. Keep commits a maintainer pushed and push with `--force-with-lease`.
- Rebase only the PR the user points at, and only when it conflicts.
- Re-requesting a review through the API often fails on repos the user doesn't own. Give the PR link and the click: Reviewers, the ↻ button next to the reviewer's name.
- After a merge: fetch, rebase dependent branches, delete the merged branch with the user's OK, then present what's next.
- Finish the current issue completely before starting the next one.
- A release bumps the version by [SemVer 2.0.0](https://semver.org/spec/v2.0.0.html) (breaking: major, feature: minor, fix: patch), turns `## [Unreleased]` into `## [x.y.z] - YYYY-MM-DD` with a fresh empty `Unreleased` above it, and updates the compare links at the bottom of the changelog. Tags follow the repo's form.

## Permissions and safety

- Ask before any download or install and state the file, the source and the size. First check that a command can't install silently (`rustup toolchain list`, `cargo --offline`, `npm` without `-g`, no global installs ever). Check free disk space before anything large.
- Never push unless told. Never push the default branch. Push only to the remote the user set up.
- Deleting anything (files, branches, releases, assets) needs the user's OK. Never revert, check out, stash or overwrite a change you didn't make. Restore by exact path, never by directory.
- Treat the uncommitted changes you made as yours. Never call your own work the user's ("your change", "your pin").
- Edit with the Edit tool. Preserve each file's encoding, BOM and line endings. After any scripted edit, check for NUL bytes and changed line endings.
- Before a multi-agent fan-out, state the agent count and model in one line and get a yes. Keep it small (9 or fewer). Run agents that build or test one at a time with capped parallelism. Read-only agents may run together but must not start processes.
- Signed commits: run a normal `git commit` and wait for the user to enter the passphrase. Never kill it early and never fall back to unsigned.
- Never wrap up or hedge because of context or session length. The user manages that.

## Corrections

A correction is a convention from then on. Apply it to every later draft unasked and save it to memory. When the corrected form came from one of these skills (work-loop, repo-writing, code-comments, terse-replies), edit that skill in the same pass. When the user calls it a personal choice, it goes to memory only. Record the correction in the user's words, never reworded to fit your own mistake.
