# Agent instructions

This repo contains Claude Code skills. Each skill is its own plugin in `.claude-plugin/marketplace.json`. Work in this repo follows its own work-loop, repo-writing and code-comments skills.

## Layout

- `skills/<name>/SKILL.md` is the skill. Its frontmatter has `name` (the folder name) and `description`. The description tells Claude what the skill does and when to load it, because it is all Claude sees before loading.
- `skills/<name>/references/` contains long lists and examples the skill links to. `skills/<name>/scripts/` contains scripts the skill runs.
- `tests/` contains the unit tests for the scripts.
- A skill refers to another skill's files as `<skills>/<other>/...`, which starts at the folder above the skill's base directory.

## Adding or changing a skill

1. Run the work-loop state check: `bash skills/work-loop/scripts/state.sh "<topic>"`.
2. Write the skill text by repo-writing rules, with one fact in one place. Put long lists in `references/`.
3. Add a new skill to `.claude-plugin/marketplace.json` as its own plugin entry and to the skill list in `README.md`.
4. Add a `CHANGELOG.md` entry under `## [Unreleased]` for anything a user of the skills would notice, in [Keep a Changelog 2.0.0](https://keepachangelog.com/en/2.0.0/) form. A change to something not released yet edits the existing entry. Tests and CI get no entry.
5. Run the prose check on the staged diff: `python3 skills/repo-writing/scripts/prose_check.py --staged`. Hard findings block the commit. Check findings need a look, since quoted bad examples in the skills trip them on purpose.

## Testing

- Script changes get a failing unit test first, then the fix. Run the tests with `python3 -m unittest discover -s tests`. Tests must not depend on the machine's git config, so set any identity or setting inside the test.
- Skill text changes get a behavior test. Start a fresh agent with no chat context, have it read the changed skill (and any skill it pairs with) as if loaded, give it a concrete scenario, and have it write the exact reply plus a self-check of rules it was unsure about. Cover normal cases and unusual ones: an angry user, a request that breaks a rule, another language, a repo whose house style differs from the defaults, autonomy with a blocker. Fix every problem the self-checks find and rerun the affected scenarios.
- Check `state.sh` against a real fork PR as well as a repo with no PR, because `gh` only finds fork PRs as `owner:branch`.

## Releases

Versions follow [SemVer 2.0.0](https://semver.org/spec/v2.0.0.html). A release turns `## [Unreleased]` into `## [x.y.z] - YYYY-MM-DD`, adds a new empty `Unreleased` section and updates the compare links at the bottom of the changelog.
