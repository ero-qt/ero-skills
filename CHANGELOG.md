# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/2.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Added

- `repo-writing` skill, which writes commits, PRs, issues, review replies and docs the way a person on GitHub would, after it reads the repo's own style. It starts from how natural text reads, with 3 tests to run on every draft. Its list of AI tells goes from single words up to the stance of a whole text. The prose check flags most of them, reads whole paragraphs for rhythm and prints how many tells it found per 100 words. `--explain` prints why a rule flags a sentence and how to fix it.
- `code-comments` skill, which makes code explain itself and keeps comments to the facts that the code can't show.
- `terse-replies` skill, which keeps chat replies caveman-short at 3 levels, with the answer first, exact steps and the state and next step at the end. Its plugin also sets a Terse output style, and a hook that reminds Claude of the level in 1 line at every prompt, so the style stays on for the whole session. The full rules come back after a compaction and at the prompt after a reply that broke one of them. The level is kept between sessions. At the end of each turn a check reads the reply and writes every broken rule to `slips.jsonl` in the plugin's data folder, like a commit gate longer than 12 lines, a dash or a closing offer. It never stops the turn.
- `work-loop` skill, which runs repo tasks in one fixed order, from checking open PRs and issues to the review and the PR. Its `ledger.js` script writes the proof of each step of a commit to `.git/work-loop/ledger.jsonl`, where it can't be staged by mistake.

[Unreleased]: https://github.com/ero-qt/ero-skills/commits/main/
