# Tells

Phrasings the user rejected in repo text and code comments, with the form that replaced them. Each one is the same habit underneath: decorating instead of saying the thing. The fix is always the sentence you would say out loud to a colleague who already works on this.

## Words

| Never | Write instead |
|---|---|
| "name", "names", "named", "naming" as a verb ("every match must name one file", "the options its config names") | "point at the same file", "listed in its config", "is", "identified by" |
| "says", "says so", "saying X" for code or output ("stops and says so") | "returns", "prints", "lists", "throws", "fails with" |
| "hold", "held" for checks or contents ("held to the entry", "what a build holds") | "checked against", "contains", "has" |
| "carry", "carries" ("releases carried the manifest") | "came with", "contains", "has" |
| "lands", "land on" ("lands on the 2017.3 offsets") | "uses", "gets", "ends up with" |
| "told by", "tell", "ask", "answer" for code | "reads", "returns", "checks", "finds", "refuses" |
| "owns", "stands on", "the root", "hole", "the seam", "the carve", "roots" | the concrete thing: "the assemblies vector and the type-info table" |
| "gap", "corpus", "afresh", "flavor", "watchdog", "hits", "all the way through", "the ... ones" | "missing", "found", "every", the plain word |
| "era", "v2", "v3", "older lineage" for real versions | the real artifact or version: "libfoo.so.2", "the Python versions" |
| "width" for pointer size, "Master" without explanation | "64-bit", "32-bit", "x64", "x86", say what it is |
| "vendored", "bisect" in text for outsiders | say what happened: "copied into the repo", "checked every patch between them" |
| "robust", "seamless", "comprehensive", "powerful", "crucial", "key", "pivotal" | delete, or state the fact |
| "simply", "easily", "basically", "actually", "obviously" | delete ("just" and "honestly" are fine in the user's casual voice, as in "I can just remove it") |
| "Good catch", "Great point" | delete; answer the point |
| "here", "this machine", "that editor install" for the user's setup | "on my machine", "I'm on Windows", the real OS or tool |
| British spelling ("favour", "behaviour") | American spelling ("favor", "behavior") |
| "json", "linux", "mac" | "JSON", "Linux", "Mac" |
| "thirty two bit", "twenty seven" | "32-bit", "27" |

## Shapes

| Shape | Bad | Good |
|---|---|---|
| Definition first | "`\r` is a line ending and the parser stops there" | "The parser stops at `\r` because it treats it as a line ending." |
| Fronted or inverted clause | "No CLI flag turns logging off, so the config file does" | "The config file turns logging off because there's no CLI flag for it." |
| Clipped negation | "finds no X" | "doesn't find a X" |
| Dramatic short sentence | "The exporter doesn't start." on its own | "...but the importer doesn't find any images on Linux and the exporter doesn't start at all." |
| Clipped clause, missing object | "and its tool says", "with it cleared" | the full clause: "and added a test for..." |
| Dropped noun | "to find the manager" | "to find the session manager" |
| Passive with no actor | "the log stays beside the asset", "the defaults are dropped" | "we keep the log beside the asset", "We drop zip's default features" |
| Lead-in colon with a three-item list | "measures where the runtime keeps the members of its own structures: thing 1, thing 2, and thing 3." | "measures the offsets of struct members" |
| Tacked on after a range | "any 3.8 to 3.12 build, Linux or Windows, CPython or PyPy" | "any 3.8 to 3.12 build" |
| ", and" chain or "X, and Y is also a thing" | "Everything is merged, and #172 fixed X" | "Everything is merged and #172 fixed X" |
| Follow-up pointer sentence | "That's the function where..." | fold it into the sentence before |
| Apposition introducing a type | "a `ManagedString<N>` type", "`Foo`, an X underneath" | "`ManagedString<N>`", "I added `Foo`. It wraps X." |
| Announcing intro | "Two short ranges get their own builds" | state the first fact |
| Universal-claim motivation | "every plugin hand-rolls this", "a common pain point" | state what the code did or lacked, or cut it |
| Absence framing | "the missing piece", "not yet" lists | state what the change adds |
| User-story or marketing tone | "adds what generators kept writing by hand" | "`codegen-kit` is a source-only package for writing generators." |
| Framing phrases | "note that", "worth mentioning", "one trap worth knowing", "that's only right if" | state the fact |
| Restating with more weight | a closing line that repeats the point | delete it |
| Padding evidence | "tested on Node 22.1 and 22.2" (two patches of one minor) | "tested on Node 22.2" |
| Stating the obvious | "nothing is released yet" | delete |
| Alternatives nobody has seen | "there is no construction from a string" | delete |
| Triads, "not X but Y", rhetorical questions, exclamation marks on claims (a greeting like "Hey!" is fine) | "fast, safe, and correct" | the one fact that matters |
| Em dash, en dash, semicolon stand-in | `the scan — which ...` / `the scan; it ...` | two sentences, or a plain clause |
| Bold-label bullets, emoji, Title Case headings, `##` headings in PR or issue bodies | "- **Performance:** ..." | plain bullets, `###` at most, sentence case |

## Review replies

| Bad | Good |
|---|---|
| "Returning None for them is the explicit exclusion, and the doc now says so." | "I updated the doc to say big-endian returns None." |
| "Added Windows paths. Same two files, backslashes." | "I ended up adding proper Windows paths instead of skipping those tests. They check the same two files, just with backslashes." |
| "Added a test." | "...and added a test for a config without `defaults`." |
| "You're right, the claim was wrong." | "Whoops, I had that backwards." |

## Mechanical grep

`scripts/prose_check.py` flags most of the word tells and every dash and trailer. It can't judge shapes, so read for the shapes yourself.
