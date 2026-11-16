# Stages

The size of a commit picks its stages and the `loop` knob adds or drops some. Each stage ends with a proof. Write that proof to the ledger as 1 line before you move on:

```bash
node <skills>/work-loop/scripts/ledger.js add red "test_parses_empty_file: expected 0 but was 1"
```

`ledger.js show` prints the records of the commit in progress. The commit guard reads the `docs` records. At `loop strict` a missing docs reason stops the commit.

## Stages per size

`S` means the stage runs only at `loop strict`.

| Stage | trivial | small | medium | large |
|---|---|---|---|---|
| Slice plan (once per branch) | | | S | yes |
| State check | yes | yes | yes | yes |
| Plan and research | | | yes, inline | yes, agent |
| Red test | | yes | yes | yes |
| Implement and CI commands | yes | yes | yes | yes |
| Adversarial tests | | | S | yes |
| Simplify | | S | yes | yes |
| House style | tools only | yes | yes | yes |
| Docs | yes | yes | yes | yes |
| Review | | S: 1 agent | 1 agent | 3 agents |
| Fix | | if findings | if findings | if findings |
| Driver verify | yes | yes | yes | yes |
| Gate | yes | yes | yes | yes |
| Record | yes | yes | yes | yes |

- `standard` is the table without the `S` cells. It's the default.
- `strict` is the table with the `S` cells.
- `light` runs the trivial column for trivial and small commits. Medium and large ones get the small column.

## What each stage does

| Stage | What happens | Proof for the ledger |
|---|---|---|
| Slice plan | Write the goal as 1 result someone can see ("the tool reads X and prints Y"), the rules for every commit and the commits in order, each with its size and first failing test. Also write down what's out of scope. For a new repo, suggest a readme, changelog, agents file, license and CI once. The user says Go. | `plan: <path>, 5 commits` |
| State check | Run `state.sh`. The tree doesn't have edits you didn't make. | `state: ok, 0 behind` |
| Plan and research | Read the touched files with their callers, tests and siblings. Look for a maintained package, a standard file format or a tool that already does the job, and give the size of both ways in lines. List the files, the public shape, the failing tests and what each one pins. "Searched X and didn't find anything" counts as research. | `plan: 4 files, 6 tests, 3 sources` |
| Red test | Write the tests in their own edit and run them. A compile error isn't red, so stub the code first. A test that passes on its first run gets rewritten. | the failing assertion, quoted |
| Implement | Write the least code that passes. Run the commands CI runs, word for word, each into a log file. | the last line of each command |
| Adversarial tests | A fresh agent writes tests for what most likely breaks: empty, huge and odd input, order, partial state, every way to fail and any rule of the spec without a test. A new test that fails is a bug in the code, so fix the code. | `adv: +9 tests, 2 bugs fixed` |
| Simplify | Go over the diff for what can go: a helper with 1 caller, an option nobody asked for, checks for what can't happen, code a package or standard file could replace. Give both sizes for each cut. | `simplify: -41 lines` or `simplify: none` with what you checked |
| House style | Run the repo's formatter and linter. Then compare each touched part with its sibling: same names, order and layout. | `style: format 0, sibling 3 files` |
| Docs | Check whether the repo wants docs in the same commit, through its agents file, its contributing rules or an existing changelog. Then touch the changelog, readme, agents file and package metadata as needed. | `docs: changelog +1` or `docs: none: <reason>` |
| Review | Read-only agents with no chat context. 1 agent works through the checklist. 3 agents split it into correctness against the spec, design (reuse, smaller ways, API shape, parameter names and order) and prose. Pass the model by name. | `review: 7 findings, 4 above nit` |
| Fix | Judge each finding on its merits. Fix a real one, with a test when behavior changes. Skip a wrong one with 1 line on why. Run CI's commands and the prose check again. | `fix: 3 fixed, 1 skipped` |
| Driver verify | You, not an agent: the staged paths match the plan, nothing foreign is staged, CI's commands pass and the end-to-end run works on the real thing. | the last lines of the commands |
| Gate | Show the commit in the gate shape of SKILL.md. In autonomous mode, commit without asking. | `gate: approved` or `gate: auto` |
| Record | Commit and tick the commit in the plan. | `commit: a1b2c3d` |

## End of the branch

- Before the PR, 1 read-only agent reviews the whole diff against the base with the checklist and the slice plan. It finds what a review of 1 commit can't: siblings that drifted apart, a type that lost its user, docs that match commit 2 but not commit 5. Its findings go back through the loop. A branch with only trivial commits skips it.
- Then the PR gate and the report, as in SKILL.md.

## Changelog and releases

- A repo with a changelog but no house form for it follows [Keep a Changelog 2.0.0](https://keepachangelog.com/en/2.0.0/). The types are `Added`, `Changed`, `Deprecated`, `Removed`, `Fixed` and `Security`, in that order. A breaking entry starts with `**Breaking:**`.
- A release bumps the version by [SemVer 2.0.0](https://semver.org/spec/v2.0.0.html): major for a break, minor for a feature, patch for a fix. It turns `## [Unreleased]` into `## [x.y.z] - YYYY-MM-DD`, adds a new empty `Unreleased` above it and updates the compare links at the bottom of the changelog. Tags follow the repo's form.

## Running tests and builds

- Never pipe a test, build or sweep run through `grep`, `head` or `tail`. Redirect the whole run to a log file in the scratchpad, then read the file: `cargo test --offline > "$SP/test-<what>.log" 2>&1; echo "exit $?"`.
- Never start a run while another run of the same project is alive. Never edit or build a project while its run is in flight.
- Never rerun the full suite after a narrow fix that the narrow run already verified. Never retry a long command unchanged. Change something or report.
- Reuse finished artifacts and measurements instead of rebuilding them.
- Make long runs print progress and run headless, with no windows or prompts stealing focus. Give the user a command to watch them.
