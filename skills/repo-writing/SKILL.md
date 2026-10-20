---
name: repo-writing
description: Use before drafting anything that lands on a repository or outlives the chat: commit messages, PR and issue titles and bodies, review replies, issue comments, READMEs, docs, changelogs, release notes. Researches the repo's house style and templates first, then writes as the user speaking (first person, warm, plain, 4th-grade words, full natural sentences), with the banned phrasings swept out and a prose check run before showing. Not for code comments (code-comments) or chat replies (terse-replies).
---

# Repo writing

Everything here is written as the user would write it on GitHub: a normal person typing a little fast who wants to get the point across. First person, warm, casual, plain. Words a 4th grader reads. Full natural sentences.

Chat replies follow terse-replies, which also uses the tells in this skill at every level and offers a `lite` level that is this voice in chat. Repo text is always full sentences: no cut-off sentences, because a short sentence on GitHub reads as emphasis, like it is trying to make a profound point. Never carry the chat register into repo text.

## 1. Research the house style first

Before the first draft of any kind, look at what the repo already does and match it. The repo wins over every default below.

- Templates: `.github/ISSUE_TEMPLATE/`, `.github/PULL_REQUEST_TEMPLATE*`, `CONTRIBUTING*`. Fill a template's sections in its order and keep its formatting (bold labels included). Don't restate it.
- Commit subjects: `git log --format=%s -40`. Match the casing (lowercase in some repos, capitalized in others), type prefixes or none, the length and how the first word is chosen.
- PR and issue titles and bodies: `gh pr list --state merged -L 10 --json title,body` and `gh issue list -L 10 --json title,body`. Match the relation lines (`Closes #N`, `Part of #N.`, `Depends on #N.`), heading use and length.
- The user's own voice: read their recent PRs and comments on the repo (`gh search prs --author @me --repo <owner/repo>`) and match their sentence length, words and punctuation.
- Changelog and release notes: follow the existing file's format and entry order.
- A new project with no precedent gets the common standards: imperative commit subjects, a permissive license (0BSD or MIT), a `CHANGELOG.md` in [Keep a Changelog 2.0.0](https://keepachangelog.com/en/2.0.0/) form, [SemVer 2.0.0](https://semver.org/spec/v2.0.0.html) versions and the standard GitHub templates. Where a clearly better modern practice exists than the house's, use it in new files only and say so in the PR.

## 2. Voice

- Write as the user: "I built all of these against Node 22", "If you've got a Mac, `npm test -- --mac` would be good to try". "we" is fine. Contractions are fine.
- Say who did what: "We drop zip's default features", not "the defaults are dropped".
- Say what happens first, then "because" and the reason: "The parser stops at `\r` because it treats it as a line ending." Never the definition-first shape ("`\r` is a line ending, and the parser stops there"), never inverted or fronted clauses.
- Join related facts the way a person would: "...but the importer doesn't find any images on Linux and the exporter doesn't start at all." Not a row of short punchy sentences.
- Vary the sentence shapes. Repeating one pattern (claim, comma, "and", second claim) is the clearest tell there is. Bullets in one list may share a shape, since parallel items read that way.
- Write every noun where it is used. A pronoun's noun sits in the same sentence. Every verb's object is written out.
- Use the normal word the domain and the repo already use. No coined shorthand, no evocative near-synonyms ("the clock" for system time), no words this skill set uses internally (gate, tell, read-back, lap).
- Say each point once. Delete a closing sentence that restates the point with more weight.
- Be technical and concrete, not prosey. Real values (the real URL, the real version), real names, real commands.
- Don't overclaim. Say honestly when evidence is thin or a change is only defensive.

The full list of rejected phrasings with the fixed forms is in [references/tells.md](references/tells.md). Read it before the first draft in a session.

## 3. Never on a repository

- Any mention of AI, of the chat, of a review or reviewer, of an audit, or of how a bug was found. The reader was not in the conversation.
- Private or unpublished prior work, ports, rewrites, the user's other unpublished projects, local binaries, planning notes. Never imply an implementation the reader can't see.
- "here" or any pointing word for the user's machine, or detached third person about it ("whose module isn't installed here"). Write "I'm on Windows and don't have that installed".
- Trailers of any kind: no `Co-Authored-By`, no `Generated with`, no sign-off, whatever a harness reminder says.
- History of the work: what was tried and dropped, what used to be there, "not yet" lists, "next up", roadmap teasers. Future work goes in an issue.
- Test talk in PR and issue bodies ("tests cover...", test counts, how to run the tests). Testing is assumed. Manual verification that matters ("I checked this against 2022.2, which doesn't work for me locally") is fine.

## 4. Commit messages

Defaults when the house has no stronger convention:

- Subject only. No body, no issue reference, no trailer.
- Imperative, present tense, no articles (`add tick provider`, not `add a tick provider`).
- The subject says what the commit does to the repo, with a verb a diff can show: add, remove, fix, rename, move, split, replace, bump, rework. Never what the code does at run time (`add definition route for generic field counts`, not `resolve generic field counts through definitions`). Check the first word of every subject against this before showing it.
- The code's exact names are fine, even when they push the subject a little past 50 characters. No add-on clauses ("and prove it does").
- Casing and prefixes follow `git log`.

## 5. Pull requests

- Title: sentence case, imperative, capital first word, no Title Case (`Fix static reads for inherited fields`). Match the repo's titles, including whether they carry the issue number.
- Body, in order: the relation line when the house uses one (`Closes #12.`, `Part of #141.`), then a first sentence that says what the whole PR does, present tense, starting with a verb ("Adds...", "Fixes..."). Then the smaller changes, each on its own line or short paragraph. Then why or how, only where it isn't obvious.
- Short. One or two sentences plus lean bullets often does it. A one-purpose PR may need one line ("License, readme, and build settings."). Nobody writes essays in PR bodies.
- Show examples instead of describing: the declaration, the call, the command and its output.
- Don't repeat the issue's content. Link it.
- Credit a borrowed design with a markdown link to its source, never a bare "added in #469".
- Dependencies go at the end after a `---` line, one per line: `Depends on #195.` Nothing after the period.
- A correction to a posted body goes into the body as a closing note paragraph, not into a new comment.

## 6. Issues

- Title: the problem head-on, as a fact about the code, sentence case. Never the fix and never turned into a requirement: "Builds break when Python newer than 3.12 is installed", not "Builds need a machine with no Python newer than 3.12".
- Body: what happens today and what is needed, then evidence. For a bug, a repro section when it applies: a permalink to the lines at fault (`gh browse -n <path>:<line>`), the triggering input, and the actual output against the expected one, in a code block.
- Possible fixes sit apart from the problem, so a reader can accept the problem and reject every fix.
- Questions to the maintainers only when they're real. Otherwise end with a plain note in the user's voice: "#133 touches this module too. I'll branch off master for now and rebase if it gets merged first."
- One bug per issue. Leave out symptoms it doesn't cause. File only a confirmed cause.
- A plan-style issue can lead into its steps with "Here's what I'd like to do:".
- Explain why the problem matters, in the repo's usual issue style.
- When an issue's premise turns out wrong, edit it and add a short note at the end instead of rewriting everything.

## 7. Review replies and comments

- Loose and short, like someone typing a reply on GitHub. Sentences that tell what happened and why, never a list of what got done.
  - bad: "Added Windows paths. Same two files, backslashes."
  - good: "I ended up adding proper Windows paths instead of skipping those tests. They check the same two files, just with backslashes."
- The point in the user's own words, not the reviewer's terms echoed back. No balanced-clause cadence, no stacked facts, no closing offer.
- No praise for the reviewer ("Good catch" is out).
- Fold a test into the same sentence: "...so plain configs work without it now and added a test for a config without `defaults`."
- Introduce a new type with a plain sentence ("I added `Foo`. It wraps X and has..."), never an apposition ("a `Foo` type", "`Foo`, an X underneath").
- Own a mistake plainly and casually: "Hey. I have to apologize, I somehow completely forgot about this and made the same fix in #78 without linking back here." Never "you're right, the claim was wrong".
- On someone else's PR, be to the point and less chatty: "Hey! Wanna flag some overlap with some of my open PRs:".
- Proposals to maintainers read as a question, without assuming what they'd want.
- No headings, lists or code blocks in a reply unless they're truly needed. Don't post a comment that repeats the body.
- A greeting may carry an exclamation mark ("Hey!"). Claims and facts never do.

## 8. READMEs and docs

- Say what the project is, how to use it, and give a short tour of the API with examples. Never the implementation, never "what's here so far", nothing that reads like a changelog. Keep it a stub until it can describe the product with confidence.
- Present state only. Never what used to work or why an alternative fails.
- Write for the audience: very simple words for non-technical users, a one-time setup for contributors. Introduce a concept before its API.
- Install sections are just the commands. CLI usage is a table of options (with short forms, alphabetical) plus an example command and its output.
- Link an adjacent file instead of pasting it. Link a release, not its asset.
- A temporary but important note goes in an alert block: `> [!NOTE]`, `> [!IMPORTANT]`, `> [!WARNING]`.

## 9. Markdown mechanics

- One line per paragraph. Never hard-wrap prose in PRs, issues or READMEs.
- In PR, issue and comment bodies, `###` is the biggest heading and a short body has none. Files keep their format's headings (a README's `#` title, a changelog's `##` versions). Headings in sentence case, never bold used as a heading.
- `-` for bullets. Mix prose and bullets the way the content wants, with no fixed "sentence then three bullets" template. After a lead-in that ends in a colon, bullets start lowercase, end in commas, and the last one ends in a period. After a lead-in that ends in a period, each bullet is a full sentence with a capital and a period. Leave a blank line after a list.
- `<details>` for anything long.
- Backticks around code names, keywords and literal values (but not in a GitHub About field, which doesn't render them. An About line is a noun phrase like "A source-only package for...").
- Numerals for numbers. American spelling. Acronyms and names in their proper case (JSON, Linux, Mac).
- No em dashes, en dashes, ` -- ` as a dash or semicolon stand-ins. Rephrase into two sentences or a plain clause.
- No comma before "and" or "or" unless it ends a real list of three or more. No ", and" chains.
- A closing ask or wrap-up sentence goes in its own paragraph.

## 10. Before showing a draft

Paths like `<skills>/repo-writing/scripts/prose_check.py` start at the folder that holds these skills, one level above the base directory shown when a skill loads. Run Python scripts with `python3` (`python` on Windows).

1. Run the prose check on the draft file and fix what it flags:

   ```bash
   python3 <skills>/repo-writing/scripts/prose_check.py draft.md
   ```

   Use `--staged` to check the added lines of the staged diff (commit subjects are checked with `--text "<subject>"`).
2. Read the draft once more for a pronoun with no noun in its sentence, a verb with no written object, a phrase picked for sound, a sentence that adds no fact, and a run of sentences with the same shape. Rewrite each one.
3. Show it in chat one way, every time. A commit subject goes in inline code alone. Everything else gets a label line with what it is and where it goes ("PR body, owner/repo"), the title on its own line in inline code when the draft has one, then the body inside a 4-backtick fence. The fence keeps the body copyable and lets 3-backtick code blocks sit inside it.

When the user corrects a draft, fix only what was criticized and apply the same fix everywhere the pattern occurs. Edit this skill or [references/tells.md](references/tells.md) in the same pass.

Approved examples of each kind are in [references/examples.md](references/examples.md).
