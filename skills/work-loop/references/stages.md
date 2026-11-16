# Stages

The size of a commit picks its stages and the `loop` knob adds or drops some. Each stage ends with a proof. Write that proof to the ledger as 1 line before you move on. The proof column below shows each record as `<stage>: <proof>`, and `ledger.js` takes the stage and the proof as separate arguments:

```bash
node <skills>/work-loop/scripts/ledger.js add red "test_parses_empty_file: expected 0 but was 1"
```

`ledger.js show` prints the records of the commit in progress. The commit guard reads the `docs` records. At `loop strict` a missing docs reason stops the commit. [strict.md](strict.md) has who runs each stage and how a stopped commit goes on.

## Stages per size

`S` means the stage runs only at `loop strict`.

| Stage | trivial | small | medium | large |
|---|---|---|---|---|
| Slice plan (once per branch) | | | S | yes |
| State check | yes | yes | yes | yes |
| Plan and research | | | yes, inline | yes, agent |
| Red test | | yes | yes | yes |
| Implement | yes | yes | yes | yes |
| Adversarial tests | | | S | yes |
| Simplify | | S | yes | yes |
| House style | tools only | yes | yes | yes |
| Docs | yes | yes | yes | yes |
| Review | | S: 1 agent | 1 agent | 3 agents |
| Fix | | if findings | if findings | if findings |
| Driver verify | yes | yes | yes | yes |
| Gate | yes | yes | yes | yes |
| Record | yes | yes | yes | yes |

- `standard` is the table without the `S` cells.
- `strict` is the table with the `S` cells.
- `light` runs the trivial column for trivial and small commits. Medium and large ones get the small column.

## What each stage does

| Stage | What happens | Proof for the ledger |
|---|---|---|
| Slice plan | Write the goal as 1 result someone can see ("the tool reads X and prints Y"), the rules for every commit and the commits in order, each with its size and first failing test. Also write down what's out of scope. For a new repo, suggest a readme, changelog, agents file, license and CI once. [slice-plan.md](slice-plan.md) has the form. The user says Go. | `slice: <path>, 5 commits` |
| State check | Run `state.sh`. The tree doesn't have edits you didn't make. | `state: ok, 0 behind` |
| Plan and research | Read the touched files with their callers, tests and siblings. Look for a maintained package, a standard file format or a tool that already does the job. Give the size of both ways in lines. List the files, the public shape, the failing tests and what each one pins. "Searched X and didn't find anything" counts as research. | `plan: 4 files, 6 tests, 3 sources` |
| Red test | Write the tests in their own edit and run them. A compile error isn't red, so stub the code first. A test that passes on its first run gets rewritten. | `red: <the failure line, word for word>` |
| Implement | Write the least code that passes. Run the commands CI runs, word for word, each into a log file. | `green: <the last line of each command>` |
| Adversarial tests | A fresh agent writes tests for what most likely breaks: empty, huge and odd input, order, partial state, every way to fail and any rule of the spec without a test. A new test that fails is a bug in the code, so fix the code. | `adv: +9 tests, 2 bugs fixed` |
| Simplify | Go over the diff for what can go: a helper with 1 caller, an option nobody asked for, checks for what can't happen, code a package or standard file could replace. Give both sizes for each cut. | `simplify: -41 lines` or `simplify: none` with what you checked |
| House style | Run the repo's formatter and linter. Then check the diff against the house brief line by line and compare each touched part with its sibling: same names, order and layout. | `style: format 0, lint 0, brief 14/14, sibling 3 files` |
| Docs | Check whether the repo wants docs in the same commit, through its agents file, its contributing rules or an existing changelog. Then touch the changelog, readme, agents file and package metadata as needed. | `docs: changelog +1` or `docs: none: <reason>` |
| Review | Read-only agents with no chat context. 1 agent works through the checklist. 3 agents split it into correctness against the spec, design (reuse, smaller ways, API shape, parameter names and order) and prose. Pass the model by name. | `review: 7 findings, 4 above nit`, or `review: inline, 7 findings` without agents |
| Fix | Judge each finding on its merits. Fix a real one, with a test when behavior changes. Skip a wrong one with 1 line on why. Run CI's commands and the prose check again. | `fix: 3 fixed, 1 skipped` or `fix: none, 0 findings above nit` |
| Driver verify | Do this yourself. The staged paths match the plan, nothing foreign is staged, CI's commands pass and the end-to-end run works on the real thing. | `verify: <the last line of each command>` |
| Gate | Show the commit in the gate shape of SKILL.md. At `autonomy: auto`, commit without asking. | `gate: approved` or `gate: auto` |
| Record | Commit and tick the commit in the plan. | `commit: a1b2c3d` |

## Research

- Read the code the change touches and its tests. Read the actual code of any reference implementation before describing or planning a mechanism, even in a one-line answer. If what you would write doesn't have a counterpart in the code, ask instead of inventing it.
- Look for an existing API, base type or helper before adding one (`rg` for the concept, the repo's own base classes, the user's reference repos).
- Read the house style: `CONTRIBUTING*`, `.github/ISSUE_TEMPLATE/`, `.github/PULL_REQUEST_TEMPLATE*`, `.editorconfig`, linter and analyzer config, the CI workflow files (for the exact commands CI runs), `git log --format=%s -30`, recent merged PR titles and bodies. A new project with no precedent follows the language's or the industry's standard.
- Read the repo's planning or agent docs (`AGENTS.md`, `CLAUDE.md`, decision logs) alongside the code, never instead of it. Notes written down from the user's offhand comments are context, not law. The user's current words win.
- Measure instead of guessing. One quick test settles a suspected cause faster than reading. Before filing a bug from a symptom, trace the symptom back to its first wrong value. Before claiming something is missing, check whether the code, the disk or the reference already has it.
- Verify every factual claim (what is merged, released, built, what an API does) before stating it.

## End of the branch

The review of SKILL.md §7 also gets the slice plan. It finds what a review of 1 commit can't: siblings that drifted apart, a type that lost its user, docs that match commit 2 but not commit 5.

## A stretch on auto

`autonomy: auto` skips the commit gate, `Review?` and the yes before the review agents. The review itself still runs. Everything else stays: the commit style, staging by path, the end-to-end check and the CI watch. Never push the default branch.

- The permissions and safety rules of SKILL.md still apply: no downloads, installs, deletes, force pushes or posts in the user's name without a yes.
- A design fork, an unreadable failure or a reserved decision stops only that item. Write it in the plan file for the user and go on with independent work. A public API break counts as a design fork.
- Rebasing your own unpushed commits onto a branch a maintainer updated is fine, since the push stays a fast-forward.
- When signing needs a passphrase and the user is away, commit nothing more and report it.
- Watch CI for up to 30 minutes. Still pending after that: report it as pending.
- End the stretch with one report: what was done and pushed, what waits and why, then one question tool call with every queued decision.

## Changelog and releases

- A repo with a changelog but no house form for it follows [Keep a Changelog 2.0.0](https://keepachangelog.com/en/2.0.0/). The types are `Added`, `Changed`, `Deprecated`, `Removed`, `Fixed` and `Security`, in that order. A breaking entry starts with `**Breaking:**`.
- A release bumps the version by [SemVer 2.0.0](https://semver.org/spec/v2.0.0.html): major for a break, minor for a feature, patch for a fix. It turns `## [Unreleased]` into `## [x.y.z] - YYYY-MM-DD`, adds a new empty `Unreleased` above it and updates the compare links at the bottom of the changelog. Tags follow the repo's form.

## Running tests and builds

- Never pipe a test, build or sweep run through `grep`, `head` or `tail`. Redirect the whole run to a log file in the scratchpad, then read the file: `cargo test --offline > "$SP/test-<what>.log" 2>&1; echo "exit $?"`.
- Never start a run while another run of the same project is alive. Never edit or build a project while its run is in flight.
- Never rerun the full suite after a narrow fix that the narrow run already verified. Never retry a long command unchanged. Change something or report.
- Reuse finished artifacts and measurements instead of rebuilding them.
- Make long runs print progress and run headless, with no windows or prompts stealing focus. Give the user a command to watch them.
