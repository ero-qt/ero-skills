# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/2.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Added

- `repo-writing` skill, which writes commits, PRs, issues, review replies and docs the way a person on GitHub would, after it reads the repo's own style.
- `code-comments` skill, which makes code explain itself and keeps comments to the facts that the code can't show.
- `terse-replies` skill, which keeps chat replies caveman-short at 3 levels, with the answer first, exact steps and the state and next step at the end. Its plugin also sets a Terse output style, and a hook that reminds Claude of the level at every prompt, so the style stays on for the whole session. The level is kept between sessions.
- `work-loop` skill, which runs repo tasks in one fixed order, from checking open PRs and issues to the review and the PR.

[Unreleased]: https://github.com/ero-qt/skills/commits/main/
