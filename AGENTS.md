# Agent instructions

This repo contains Claude Code skills. Each skill is its own plugin in `.claude-plugin/marketplace.json`. Work in this repo follows its own work-loop, repo-writing and code-comments skills.

## Layout

- `skills/<name>/SKILL.md` is the skill. Its frontmatter has `name` (the folder name) and `description`. The description tells Claude what the skill does and when to load it, because it is all Claude sees before loading.
- `skills/<name>/references/` contains long lists and examples the skill links to. `skills/<name>/scripts/` contains scripts the skill runs.
- `tests/` contains the unit tests for the scripts.
- `evals/<skill>/<case>/` contains the eval cases that `claude plugin eval` runs. A case has a `prompt.md` with the prompt and its run settings. Each grader is 1 file in `graders/`. A case that needs files in its workspace also gets a `case.yaml` and a `setup.sh` that creates them.
- A skill refers to another skill's files as `<skills>/<other>/...`, which starts at the folder above the skill's base directory.

## Adding or changing a skill

1. Run the work-loop state check: `bash skills/work-loop/scripts/state.sh "<topic>"`.
2. Write the skill text by repo-writing rules, with one fact in one place. Put long lists in `references/`.
3. Add a new skill to `.claude-plugin/marketplace.json` as its own plugin entry and to the skill list in `README.md`.
4. Add a `CHANGELOG.md` entry under `## [Unreleased]` for anything a user of the skills would notice, in [Keep a Changelog 2.0.0](https://keepachangelog.com/en/2.0.0/) form. A change to something not released yet edits the existing entry. Tests and CI get no entry.
5. Run the prose check on the staged diff: `python3 skills/repo-writing/scripts/prose_check.py --staged`. Hard findings block the commit. Check findings need a look. Files named `SKILL.md` or `tells.md` only get the hard rules because they quote bad examples on purpose. To run every rule on a skill file, pipe it in with `python3 skills/repo-writing/scripts/prose_check.py < skills/<name>/SKILL.md`. A new rule in the script gets a row in `skills/repo-writing/references/tells.md` with the rule's name in the Check column, so `--explain` finds it.

## Testing

- Script changes get a failing unit test first, then the fix. Run the tests with `python3 -m unittest discover -s tests`. Tests must not depend on the machine's git config, so set any identity or setting inside the test.
- Skill text changes get a behavior test. Start a fresh agent with no chat context, have it read the changed skill (and any skill it pairs with) as if loaded, give it a concrete scenario, and have it write the exact reply plus a self-check of rules it was unsure about. Cover normal cases and unusual ones: an angry user, a request that breaks a rule, another language, a repo whose house style differs from the defaults, autonomy with a blocker. Fix every problem the self-checks find and rerun the affected scenarios.
- Skill text changes also get an eval run before and after the change. Run `claude plugin eval . --scaffold --allow-tools Write Edit --threshold 0 --no-publish --tag <skill>` from the repo root. It runs each case of the skill 3 times with the skill and 3 times without it and prints both scores. `--threshold 0` keeps the exit code at 0 when a case scores below 1. `--no-publish` keeps the report on your machine. Add `-j 6` to run 6 cases at once. Leave out `--tag` to run every case. Put the scores of both runs in the PR. While you work on 1 case, `--case <name> --runs 1 --ablation none` runs it once.
- Each case loads only its own skill folder through `plugins` in its `prompt.md`. The terse-replies hooks and output style live in the marketplace entry, so they don't run in the evals.
- Every case checks that its skill loaded and has at least 1 grader on the reply or a file. Use `regex` and `tool_used` graders where they work. An `llm` grader is only for what a pattern can't check. Its rubric has a PASS line and a FAIL line.
- Tags give the skill and the kind of mistake the case catches: `ai-tells` (wording people don't use), `process-weight` (too much or too little process for the change), `design` (parameter order and API shape), `reuse` (hand-written code where a package or standard format exists), `reply-shape` (chat replies), `conventions` (docs and repo rules) and `gates` (acting without approval or asking twice). Each kind has at least 2 cases. When a skill changes because it missed a mistake, the same PR adds a case for that mistake.
- Check `state.sh` against a real fork PR as well as a repo with no PR, because `gh` only finds fork PRs as `owner:branch`.

## Releases

Versions follow [SemVer 2.0.0](https://semver.org/spec/v2.0.0.html). A release turns `## [Unreleased]` into `## [x.y.z] - YYYY-MM-DD`, adds a new empty `Unreleased` section and updates the compare links at the bottom of the changelog.
