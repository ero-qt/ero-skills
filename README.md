# Skills

Skills for Claude Code that make it work on a repository like a careful contributor and write like a person.

## Install

```
/plugin marketplace add ero-qt/skills
/plugin install repo-writing@ero-qt-skills
/plugin install code-comments@ero-qt-skills
/plugin install terse-replies@ero-qt-skills
```

Each skill is its own plugin, so you can pick the ones you want.

## Skills

- [`repo-writing`](skills/repo-writing/SKILL.md): Writes commit messages, PR and issue text, review replies and docs. It reads the repo's templates and history first, then writes in plain first person with the usual AI phrasings swept out. A prose check script flags the leftovers.
- [`code-comments`](skills/code-comments/SKILL.md): Makes code explain itself through names, types, blank lines and small functions. A comment stays only for what the code can't show and reads as what the code does, then why.
- [`terse-replies`](skills/terse-replies/SKILL.md): Keeps chat replies caveman-short at 3 levels (lite, full, ultra) with the same AI tells banned as in repo-writing. The answer or the blocker comes first. Steps come with exact commands and clicks, every reply ends on the state and the next step, and decisions go through the question tool.

## License

[0BSD](LICENSE)
