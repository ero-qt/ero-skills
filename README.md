# Skills

Skills for Claude Code that make it work on a repository like a careful contributor and write like a person.

## Install

```
/plugin marketplace add ero-qt/ero-skills
/plugin install repo-writing@ero-qt-skills
/plugin install code-comments@ero-qt-skills
/plugin install terse-replies@ero-qt-skills
/plugin install work-loop@ero-qt-skills
```

Each skill is its own plugin, so you can pick the ones you want.

## Skills

- [`repo-writing`](skills/repo-writing/SKILL.md): Writes commit messages, PR and issue text, review replies and docs. It reads the repo's templates and history first, then writes in plain first person with the usual AI phrasings swept out. A prose check script flags the leftovers.
- [`code-comments`](skills/code-comments/SKILL.md): Makes code explain itself through names, types, blank lines and small functions. A comment stays only for what the code can't show and reads as what the code does, then why.
- [`terse-replies`](skills/terse-replies/SKILL.md): Keeps chat replies caveman-short at 3 levels (lite, full, ultra) with the same AI tells banned as in repo-writing. The answer or the blocker comes first. Steps come with exact commands and clicks, every reply ends on the state and the next step, and decisions go through the question tool. A check at the end of each turn logs the replies that break these rules.
- [`work-loop`](skills/work-loop/SKILL.md): Runs every repo task in one fixed order. It checks open PRs, issues and CI first, plans the commits, writes a failing test before the code, runs the real thing end to end, gets a read-only review and only then opens the PR. The size of each commit decides how many of these steps it needs. Choices like filing issues or the review model are knobs with defaults. A state script does the first check, a workflow runs the steps of a commit through agents and a ledger script writes down the proof of each step. A hook stops commits with a trailer, a dash or a file that must never be staged.

## License

[0BSD](LICENSE)
