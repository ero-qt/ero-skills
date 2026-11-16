# Stage briefs

Each section is the brief of 1 stage agent. The `commit-cycle` workflow starts the plugin's `stage-<section>` agent for each stage, like `work-loop:stage-red`, and that agent reads its section here. The stage agents come with repo-writing and code-comments loaded. Without the workflow, start the same agent for each stage with the inputs below. Paste the section into the prompt only when the plugin's agents aren't there.

## Every stage

The driver gives every stage agent these inputs:

- The commit subject, its size and the loop level.
- The spec: the task in the user's words or the path of the issue or plan it comes from.
- The path of the house brief. Read it before anything else and follow every line of it.
- The commit plan, once the plan stage or the driver has one.
- The CI commands word for word and the base the diff starts from.

Rules for every stage:

- Don't commit, push, tag or delete anything and don't touch a remote.
- Stage only by explicit path. Never `git add -A`, `git add .` or `git commit -a`.
- Run each CI command as given into its own log file and read the log. Don't start any other long process.
- Write repo text by repo-writing and code by code-comments. Run `python3 <skills>/repo-writing/scripts/prose_check.py --staged` after you stage text. `<skills>` is the folder above the `work-loop` folder of this file.
- When the prompt has a resume note, the tree already has part of this stage's work from a run that stopped. Read it, keep what's right and finish the stage.
- Return only the fields the stage asks for. The driver writes the ledger record from them.

## plan

Research the change and plan it before any code exists.

1. Read the spec, the files the change touches, their callers, their tests and the sibling of each touched part.
2. Look for a maintained package, a standard file format or an existing tool that does the job. Give the size in lines of using it and of writing it by hand. Search the official docs and the issue trackers, and papers or talks when the problem is deep. Note the date of each source.
3. Settle the public shape: names, parameters in a sensible order and what each returns.
4. List the failing tests in the order you'd write them, each with the fact it pins.

Return `files`, `publicShape`, `tests` (each with `name` and `pins`), `risks` and `research` (each with `source`, `date` and `finding`). The research list is never empty, and "searched X, didn't find anything" counts as an entry.

## red

Write the failing tests of the plan and nothing else.

1. Write the tests in their own edit. When the code they call doesn't exist yet, add a stub that compiles and does nothing, because a compile error isn't a red test.
2. Run the narrow test command and read the log.
3. A test that passes on its first run doesn't pin anything. Rewrite it until it fails for the reason the plan gives.

Return `command`, `tests` and `assertion`: the failure line from the log, quoted word for word, like `test_parses_empty_file: expected 0 but was 1`. When no test fails for the planned reason, return an empty `assertion` and the commit stops there.

## implement

Write the least code that makes the red tests pass.

1. Change only what the plan lists. Don't add an option, a helper or a check that the plan and the tests don't call for.
2. Run every CI command and read each log.
3. Stage the changed files by path.

Return `green` (true when every command passed), `commands` (each with `command` and `lastLine`) and `staged` (the paths).

## adversarial

Write tests for what's most likely wrong with the staged change. You didn't write the code, so don't trust it.

- Try empty, huge and odd input, order, partial state and every way the code can fail.
- Add a test for each rule of the spec that doesn't have one yet.
- A new test that fails is a bug in the code. Fix the code, not the test, then run the CI commands again.

Return `testsAdded`, `bugsFixed` (each with `test` and `fix`) and `green`.

## simplify

Look at the staged diff for anything that can go.

- A wrapper or helper with 1 caller.
- An option nobody asked for.
- A check for something that can't happen.
- Hand-written code that a package, a standard file or the standard library could replace.

Give the size in lines before and after for each cut. Make the cuts that keep the tests green, run the CI commands and stage by path.

Return `cuts` (each with `what`, `linesBefore` and `linesAfter`), `checked` (what you looked at, even when nothing could go) and `green`.

## style

Bring the staged diff in line with the repo's own style.

1. Run the formatter and the linter with the repo's commands.
2. Go through the house brief line by line and check the diff against each line.
3. Compare each touched part with its sibling: same names, same order, same layout.

Return `format` and `lint` (the exit code of each), `brief` (`passed` and `total`), `siblings` (the files you compared) and `green`.

## docs

Check whether the repo wants docs in the same commit, through its agents file, its contributing rules or an existing changelog. Then go through the changelog, the readme, the agents file and the package metadata, and change what the commit calls for. A change to something not released yet edits the existing `Unreleased` entry.

Return `docs`, 1 entry per file with `file` and either `change` or `none` with the reason.

## review

Review the staged diff and change nothing. Don't edit or stage anything and don't run anything that writes files or takes long. You only get the diff, the spec and the plan, not the chat.

The prompt gives your lens:

- `correctness`: the diff against the spec, with an input that shows each bug. Work through "Claims", "Correctness", "Parity and siblings" and "Verification" of [review-checklist.md](review-checklist.md).
- `design`: work through "Design", "Reuse" and "Shape" of the checklist.
- `prose`: every added comment, name, message, doc line and the commit subject, by repo-writing and code-comments. Work through "Prose" of the checklist.
- `all`: every item of [review-checklist.md](review-checklist.md).

Return `verdict` (1 line) and `findings`, each with `severity` (`bug`, `design`, `prose` or `nit`), `location`, `finding` and `trigger` (the input or line that shows it).

## fix

Go through the review findings above `nit` 1 by 1 and judge each on its merits. Every finding ends up in `fixed` or in `skipped`, also when 2 findings are the same problem.

- A real finding gets fixed, with a test first when it changes behavior.
- A wrong finding gets skipped, with 1 line on why.
- Run the CI commands and the prose check again and stage by path.

Return `fixed` (each with `finding` and `change`), `skipped` (each with `finding` and `why`) and `green`.
