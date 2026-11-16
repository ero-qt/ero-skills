# Tells

## How natural text reads

Write it the way you'd say it to someone who works on the same code.

- Start with who does what. Then "because" and the reason, if the reason isn't obvious.
- Use the verb you'd say out loud. If the same verb came out 4 times, read the sentences again one by one. Don't swap the word everywhere.
- Use the real thing: the value, the number, the name. A category ("a hot path", "some cases") is a sign you didn't look it up.
- Join facts with and, but, so and because. Use contractions. Negate with "doesn't" and "isn't".
- Let sentences come out uneven. A long one next to a short one is fine. Don't polish toward a rhythm.
- Say each thing once and stop. Don't write an intro about what's coming or a last line about what it meant.
- Leave out what the reader knows or can see. Cover normal use and what they must act on.
- Commit. If you checked it, say it flat. If you didn't, say "untested" once.
- Write only what belongs to this text. If a sentence is about your day, like what else you did or what you tried first, cut it.

Run 3 tests before you show the text:

1. Read it aloud. Rewrite any sentence you wouldn't say as the one you would.
2. Cover a sentence. If nothing is lost, delete it.
3. Ask whether the sentence would be here if this were the only thing done today.

## What a tell is

A tell is a habit of generated text that shows up more often than a person would write it. One flagged word doesn't prove anything. A text full of them reads as written by a model, even when every fact in it is right.

- Fix the sentence, not the word. Swapping a flagged word for its neighbor only moves the tell. Banning words one by one makes the text worse. Say the sentence out loud and write the one you'd say.
- `prose_check.py` counts and points. A person reads the text and decides. A clean check doesn't mean the text is good.

Tells change with each model generation, so the word lists stay short and most rows are about how a sentence or paragraph is built.

The Check column lists the rules of `scripts/prose_check.py` that flag a row. `prose_check.py --explain "<rule>"` prints the row for a rule. "reader" means only a person catches it.

## Word

| Tell | Why it reads wrong | Bad | Good | Check |
|---|---|---|---|---|
| Style and insider words | They're picked for how they sound or come from the writer's own notes. Nobody says them to a coworker. | "a robust retry", "leverage the cache", "the older lineage", "vendored", "corpus" | "retries 3 times", "use the cache", "libfoo.so.2", "copied into the repo", the plain word | `jargon or sales word` |
| Filler | The sentence says the same without it. | "simply run", "basically", "actually", "obviously" | delete ("just" and "honestly" are fine in a casual voice, as in "I can just remove it") | `filler word` |
| Copula dodge | A plain "is" or "has" got dressed up. | "`Cache` serves as a store for parsed files", "boasts 3 modes" | "`Cache` keeps the parsed files", "has 3 modes" | `copula dodge` |
| Code that talks or thinks | Code reads, returns, checks, finds and throws. It doesn't know, want or say anything. | "the parser knows the width", "stops and says so", "the header tells it the size" | "the parser reads the width from the header", "stops and prints an error", "reads the size from the header" | `code that talks or thinks`, `'says' for code or output` |
| Verbs picked for sound | Each one is a near-synonym of a plain verb. | "every match must name one file", "what a build holds", "releases carried the manifest", "lands on the default settings" | "point at the same file", "what a build contains", "releases came with the manifest", "uses the default settings" | `'name' as a verb`, `'hold' or 'held'`, `'carry'`, `'lands'` |
| Metaphor nouns | The concrete thing is missing. | "owns the seam", "the root", "a hole in the scan", "stands on the loader" | "the plugin list and the symbol table", the real name | `'told by' or 'stands on'` |
| Same verb in every sentence | A verb that repeats in sentence after sentence reads as generated. It's most often "has", but "has" is still fine where you'd say it. | "This repo has 3 packages. `core` has the parser. `cli` has the command line." | the verb you'd say for each sentence: "This repo contains 3 packages. `core` is the parser and `cli` has the command line." | `same verb in many sentences` |
| Spelling and case | Numbers, names and spelling that a person in the field writes another way. | "thirty two bit", "favour", "json", "linux" | "32-bit", "favor", "JSON", "Linux" | `spelled-out number`, `British spelling` |
| "here" for the user's machine | The reader isn't on your machine. | "it works here", "on this machine" | "it works on my machine", "I'm on Windows" | `'here' for the user's machine` |

## Phrase

| Tell | Why it reads wrong | Bad | Good | Check |
|---|---|---|---|---|
| Clipped negation | It's written register. In speech people say "doesn't ... any". | "the repo has no `samples/` folder", "the search finds nothing", "shares its config with no other service" | "the repo doesn't have a `samples/` folder", "the search doesn't find anything", "doesn't share its config with any other service" | `clipped negation` |
| Formal connective at the start | People join sentences with and, but, so and also. | "Additionally, it caches the result." | "It also caches the result." | `formal connective` |
| Framing | It announces a fact instead of stating it. | "Note that the port is fixed.", "one trap worth knowing", "it's important to" | "The port is fixed." | `framing phrase` |
| Significance claim | A general truth stands where the concrete fact belongs. | "a common pain point", "plays a key role", "every plugin hand-rolls this" | what the code did or lacked: "broke 2 releases", or cut it | `significance claim` |

## Sentence

| Tell | Why it reads wrong | Bad | Good | Check |
|---|---|---|---|---|
| Participle tail | A 2nd claim gets glued on with no subject of its own. | "It retries, ensuring delivery." | "It retries until the server answers." | `participle tail` |
| Contrast frame | It knocks down a claim nobody made. | "This isn't a cache, it's a ledger.", "not just fast but safe" | "This is a ledger." | `contrast frame` |
| Triad | 3 items because 3 sounds complete. | "fast, safe and correct" | the 1 item that matters, or a real list of names | `triad` |
| Fact first, action last | The reader waits for the point. Speech starts with who does what. | "Since the tests crash without a display, the Linux run gets one.", "`\r` is a line ending and the parser stops there" | "The Linux run gets a display because the tests crash without one.", "The parser stops at `\r` because it treats it as a line ending." | `fronted clause` |
| Decision packed into 1 breath | "X, because A and B" reads like the summary of a design. | "Reads now format lazily, because failures are common and formatting is slow." | "Failed reads don't format their message unless you ask. Formatting made them about 100 ns slower." | `decision packed into 1 sentence` |
| Dramatic short sentence | A short sentence after a long one reads as emphasis in repo text. | "...doesn't find any images on Linux. The exporter doesn't start." | "...doesn't find any images on Linux and the exporter doesn't start at all." | `dramatic short sentence` |
| Colon setup | It builds up to a reveal. | "The result: faster builds." | "Builds got faster." | `colon setup` |
| Hidden verb | The action hides in a noun. | "performs validation of the input", "provides support for TOML" | "checks the input", "supports TOML" | `nominalization` |
| ", and" chain | Clauses get stacked with a comma before each "and". | "Everything is merged, and #172 fixed X" | "Everything is merged and #172 fixed X" | `comma before 'and' or 'or'` |
| Dropped noun, bare pronoun, missing object | It's compressed past what a reader can follow. | "with it cleared", "to find the manager", "and its tool says" | "after the cache is cleared", "to find the session manager", the full clause | reader |
| Passive with no actor | Nobody does anything. | "the defaults are dropped" | "We drop zip's default features." | reader |
| Apposition for a type | It introduces a name with a label. | "a `ManagedString<N>` type", "`Foo`, an X underneath" | "`ManagedString<N>`", "I added `Foo`. It wraps X." | reader |
| Lead-in colon or a tail after a range | Extra detail hangs off a sentence that was done. | "any 3.8 to 3.12 build, Linux or Windows, CPython or PyPy" | "any 3.8 to 3.12 build" | reader |

## Rhythm

| Tell | Why it reads wrong | Bad | Good | Check |
|---|---|---|---|---|
| Flat sentence length | Sentences a person writes vary a lot more in length. | 4 sentences of 14 to 16 words each | join 2 of them and leave 1 short | `flat sentence length` |
| Same skeleton in a row | The same template over and over: claim, comma, "and", claim, or the same first word. | "The cache keeps 10 entries. The reader checks it first. The writer clears it on save." | change the shape of every 2nd sentence | `same skeleton in a row` |
| Uniform blocks | Layout by template: every paragraph 2 sentences, every bullet a bold label, a sentence and then 3 bullets each time. | 4 sections that each have 1 sentence and 3 bullets | a list for a list, a paragraph for a reason | reader |

## Flow

| Tell | Why it reads wrong | Bad | Good | Check |
|---|---|---|---|---|
| Announcing intro | It says a fact is coming instead of giving it. | "There are 2 things to know.", "This section covers the config file." | the first fact | `announcing intro` |
| Closing restatement | The point comes again, heavier. | "This keeps the build fast.", "Overall, ..." | delete it | `closing restatement` |
| Session context | The reader wasn't there. Would the sentence exist if this were the only thing done today? | "Every other repo gets the same file.", "no longer crashes", "now reads the header" in a comment | cut it, or say what the code does in the present | `history word`, `'now' in a comment` |
| Full coverage | The writer documents everything they wrote instead of what the reader needs. | 2 sentences on what happens when a variable isn't set, "and prints a line that lists them" | 1 clause, or nothing | reader |
| Padding and the obvious | Evidence or facts that add nothing. | "tested on Node 22.1 and 22.2", "nothing is released yet", "there is no construction from a string" | "tested on Node 22.2", or delete | reader |
| Absence or story framing | It sells the change instead of saying what it does. | "the missing piece", "adds what generators kept writing by hand" | "`codegen-kit` is a source-only package for writing generators." | reader |
| Follow-up pointer sentence | A 2nd sentence only points back at the 1st. | "That's the function where..." | fold it into the sentence before | reader |

## Stance

| Tell | Why it reads wrong | Bad | Good | Check |
|---|---|---|---|---|
| Hedge stack | It covers itself instead of answering. | "may potentially help in some cases" | "helps when the cache is cold", or "untested" | `hedge stack` |
| Validation and praise | It's left over from chat. | "You're right, the claim was wrong.", "Good catch" | "Whoops, I had that backwards.", or answer the point | `validation`, `praise for the reviewer` |
| Teaching tone | Messages and docs tell the reader what to do next when they can guess it. | "Please ensure that the path exists.", "X requires Y, so install it and try again." | "X requires Y." | `teaching tone` |
| Exclamation on a claim | Emphasis a person doesn't use for a fact. A greeting like "Hey!" is fine. | "This makes it much faster!" | "This makes it about 2 times faster." | `exclamation mark` |
| Dash or semicolon stand-in | Models use these far more than people do. | `the scan — which ...`, `the scan; it ...`, `the scan -- it` | 2 sentences, or a plain clause | `em or en dash`, `double hyphen used as a dash`, `spaced hyphen used as a dash`, `semicolon in prose` |
| Markup decoration | Headings and bold far beyond what a short body needs. | "- **Performance:** ...", "## Big Heading In Title Case", `*` bullets | plain bullets with `-`, `###` at most in a PR or issue, sentence case | `bold label bullet`, `Title Case heading`, `heading bigger than h3`, `'*' bullet instead of '-'` |
| Tool leftovers | Trailers, curly quotes and stray bytes come from tools, not people. | `Co-Authored-By: ...`, curly quotes, a NUL byte | delete them | `trailer`, `curly quote`, `NUL byte in a text file` |

## Review replies

| Bad | Good |
|---|---|
| "Returning None for them is the explicit exclusion, and the doc now says so." | "I updated the doc to say big-endian returns None." |
| "Added Windows paths. Same two files, backslashes." | "I ended up adding proper Windows paths instead of skipping those tests. They check the same two files, just with backslashes." |
| "Added a test." | "...and added a test for a config without `defaults`." |
| "You're right, the claim was wrong." | "Whoops, I had that backwards." |
