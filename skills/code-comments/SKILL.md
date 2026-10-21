---
name: code-comments
description: Use when writing or changing code that others will read: before adding a comment or doc comment, naming anything, or shaping functions and files. Researches the file's and repo's house style first (editorconfig, linters, neighbor code, comment density), then makes the code document itself through names, types, blank lines and small functions, and comments only what the code can't show, as "what it does, because why". Covers doc comment openers, test names and the comment tells the user rejects.
---

# Code comments and self-documenting code

Code should explain itself through good names and types, blank lines that group the steps, and clear error messages. A comment is for the one thing the code can't show. Most comments the first draft wants to write should become a rename instead.

## 1. Research the house style first

Before writing or changing anything, look at what is already there and match it.

- `.editorconfig`, the linter and analyzer config (`clippy.toml`, `rustfmt.toml`, `.globalconfig`, `stylecop.json`, `ruff.toml`, `.eslintrc*`) and the CI format and lint steps. Follow their naming and width rules, and fix every warning in touched files.
- The comment density and tone of the file the change sits in and of its neighbors. Learn the house precedent from the pre-existing code, not from code added in this session, which may already be wrong.
- How doc comments open, how tests are named, how members are ordered, how wide lines run. When the repo is split, count the forms and follow the majority.
- A new project or a repo with no precedent: follow the language's official style (rustdoc and the Rust API guidelines, the .NET BCL docs, PEP 8 and PEP 257, the language's formatter defaults). The user's own defaults for their projects are in [references/defaults.md](references/defaults.md).
- Where a clearly better modern practice exists than the house's, use it in new code only and point it out in the PR.

Every rule from here on is a default. Where the file or repo does it another way (doc comment openers, one-line summaries, test names, widths), the house wins, and new code matches its neighbors.

## 2. Make the code say it

- Rename instead of commenting. When a comment explains a guard, rename what the guard returns or calls (`CannotSuspendItself()`) and delete the comment.
- Give the act a name. A side-effect trick that needs a comment (`_ = Configuration;`) becomes a method called after what it does (`ThrowIfNotInitialized()`).
- Put the why into error message strings so the failure explains itself.
- Methods and functions get verb names that say what they do (`FindLoaded`, `read_text`), private helpers too. Names describe the exact concept, in the domain's own words (`Transform`, `GWorld`, a clamp is a clamp). No abbreviations (`TypeReference`, not `TypeRef`), no invented versions or tiers (`v2`, `v3`) that don't exist in the real world. Keep established vocabulary and keep names the same across parallel implementations.
- No magic numbers. Model layouts as types and derive offsets from them. Call constants by the spec's own names and pass typed values instead of a bare `8`. Raw bytes in test fixture builders are fine.
- Use types and enums for flags and modes instead of raw integers or strings. Never widen a concrete type to `object`, `dynamic` or `Any` to share a seam.
- Separate the concerns inside a function with blank lines: the setup, each loop or step, the result. Keep functions small. When one grows past a screen, split it into named pieces in its own refactor commit before adding to it.
- Keep files around 300 to 400 lines, not counting comments, with one significant type per file. Small, tightly coupled types may share a file.
- Cut needless indirection: no wrapper or split type without its own job, no one-member classes, no helper for a single call. A little duplication beats an abstraction that costs more than it saves.
- Public names (exported functions, types, fields) are API. Renaming one breaks callers, so propose it and ask before doing it. Private names are free to fix.
- When the user corrects one name or comment, fix every sibling with the same flaw.

## 3. When a comment earns its place

Comment only what the code can't show:

- a rule from outside (a file format, a runtime's behavior, a platform quirk),
- a number that came from a measurement or a spec,
- an ordering or a dependency the reader can't see,
- the reason one approach was picked over the obvious one, when that isn't clear.

Keep it to one or two lines. Never narrate what the next line does. Never comment self-describing config. State a rationale once, on the member that owns it, not at every call site. Treat siblings alike: if one entry gets a comment, comparable ones do too, or none do. When the user says not to comment on something, add nothing there.

After drafting a file, delete every comment whose absence loses nothing.

## 4. How a comment reads

- Say what the code does first, starting with a verb, then "because" and the fact: "Gives the Linux run a virtual display because the GUI tests crash a few seconds after start without one, even in headless mode." Never the fact first with the action trailing ("...so the Linux run gives them a virtual one").
- Plain subject-verb-object order. No fronted or inverted clauses, no definition first.
- One plain sentence the way a maintainer would write it, with "because" or "so" where it fits. Not two clipped sentences side by side, and not a colon label followed by fragments.
  - bad: `// The guid keys the entry. The header says which build the entry describes.`
  - good: `// The header says which build this is, since the guid means nothing to a reader.`
- Write every noun out. A pronoun or possessive ("its own", "one", "that has none") always has its noun in the same sentence.
- State the plain fact with the code's own names, in backticks: "Same format as version 3, but the header field moved from `FLAGS_V3` to `FLAGS_V4`." Not prose about the mechanism.
- Words a 4th grader reads, apart from the names the code uses. Numerals for numbers (`32-bit`, `27`). Contractions are fine. "We" is fine in an inline comment that explains a choice.
- Code doesn't talk: it reads, returns, checks, finds or refuses. It never asks, answers, says or tells.
- A situational reason goes in parentheses after the fact: "Only a Windows host runs net4.8.1 (Codeberg CI runner is Linux-only)."
- Present tense only. Never what was removed, what used to happen, what was tried, what the code deliberately doesn't do, or the plan for later. History belongs in git.
- Never mention people, the chat, reviews, planning notes, other repos or other libraries. The one exception is attribution of taken or adapted code: a link back (inspired by, taken from) and the license, with a whole copied file keeping the origin's license header at the top.
- The word tells from repo-writing apply here too ("name" as a verb, "says", "hold", "lands", "carry", em dashes). See `../repo-writing/references/tells.md`.

## 5. Doc comments

- Follow the language's and the repo's doc conventions to the letter (rustdoc summary line and sections, .NET XML tags, docstrings).
- A function's doc comment opens with a verb for what it does: "Finds the config file a profile needs." Never a bare noun phrase, never "What", "Why", "How many" or "Where" as the first word.
- A type's doc gives its job in the first few words, in the house opener ("Represents...", "Provides..." in .NET). A boolean property opens with "Gets a value indicating whether" in .NET.
- If a member gets documented, it gets a real doc comment, whatever its visibility, not a `//` line above it. Keep `//` for facts inside a body, private fields and constants, and private methods that need a why.
- Put each fact on the member it describes, not in prose on the type or file. Describe the item itself, never by comparing it to another implementation.
- Warn only about real hazards.
- On a lookup or cache field, say what the key and the value mean, not that it's a cache.
- Wrap at the file's column. When a line must break, break after the period or comma nearest the end. Never break inside a tag like `<see ... />`.

## 6. Tests

- Follow the repo's test naming. Without one, the module path is the unit and the function is a short claim about behavior with no leading article (`equal_when_only_metadata_differs`). In .NET repos the user's default is `Method_Scenario_Expected`.
- The name must match what the test checks.
- Mark a test with a plain `//` line that states the fact it pins, not a doc summary and not "Checks that". Use blank lines instead of comments inside the test.
- Write expected values inline in the assertion instead of as one-use named fields.

## 7. Before staging

Paths like `<skills>/repo-writing/scripts/prose_check.py` start at the folder that holds these skills, one level above the base directory shown when a skill loads. Run Python scripts with `python3` (`python` on Windows).

Run the prose check on the added comment lines and fix what it flags:

```bash
python3 <skills>/repo-writing/scripts/prose_check.py --staged
```

Then read every added comment once more for a fact-first sentence, a dropped noun, a phrase picked for sound and a comment the code made unnecessary.
