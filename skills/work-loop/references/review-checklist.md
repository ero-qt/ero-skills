# Review checklist

The reviewer works through every item against the full diff and returns a verdict line plus a table of severity, location, finding and the input that shows it. Each item is a defect class an external review has caught before.

## Claims

- Every claim in the PR body, every doc sentence and every test name has a test that reaches it end to end through the public entry point and fails when the claim is false. A test that builds by hand the object the entry point would have produced proves nothing about the entry point.
- Every done criterion of the issue has a test.
- A lookup answers only inside what was measured. Floor or nearest rules that extrapolate past the last sample, or drop part of the key, are findings unless the design says so on purpose.
- Docs examples match the real checked-in files byte for byte in structure.

## Correctness

- Bugs in the diff, each with a reproducing input.
- Untested edges: empty, None or null, zero, negative, huge, unicode, off-by-one boundaries, and combinations picked to corrupt state.
- Every table or buffer a walk touches is bounded, not only the last one: entry size at least the struct size, `offset + size * count` checked and inside its container.
- Every fixed buffer for variable-length input either has its cap in the public doc with a test on both sides or the cap goes.
- Completeness checks validate by role, never by count.
- Errors separate "could not start" from "failed" and never point at a file that may not exist yet.
- A replacement for a safety check is not weaker: list what the old check proved, member by member.

## Parity and siblings

- The change covers every parallel path (other OS, other engine, other runtime, 32 and 64 bit) or the PR explains why not.
- Siblings of every fixed defect elsewhere in the function, the file and the repo.
- Did our own earlier work introduce the problem? Then the fix belongs in that commit or PR.

## Verification

- A regression check that compares output files proves the files were rewritten (outputs deleted first, or timestamps and counts asserted).
- Warning and path greps match how tools print paths on this host (backslashes on Windows), or totals are compared against the base.
- The end-to-end run ran the changed code (fresh build, right target dir, right binary).

## Design

- Every new type, member and option has a caller in the diff or in the slice plan. Public API and planned members stay.
- A wrapper, helper or type with 1 caller and no job of its own goes. Point at the caller it folds into and give the lines it saves.
- A function takes the object it works with, not a value it could read from that object. A constructor that gets a pointer size next to a process object that already has one is a finding.
- Parameters are grouped by concept, in the order a caller thinks of them, with 1 naming scheme per list.
- A parameter or variable name ends with its role and starts with what it works on, like `symbolLocator` for a `SymbolLocator`. A name from another role, like `client` for a server object, is a finding. Give the name it should have.
- A seam keeps its types. When a value gets widened to `object`, `any` or an untyped function field so 2 cases fit 1 slot, each case gets its own small type.
- Point out where a part could plug in its own piece through a small interface instead of a branch in 1 central place, when that opens a real use like a 2nd file format. Don't ask for it when there's only 1 case.
- Generic code and its tests use neutral names, never the name of 1 product that uses them.
- Code ported from somewhere else gets reshaped for this codebase. A member-for-member copy that brings the old helpers and hacks along is a finding.

## Reuse

- Code in the repo that already does the job or most of it, with its location.
- A maintained package, the standard library, a standard file format or an existing tool that does what the diff writes by hand. A hand-written parser for a format the standard library reads is a finding. Give both sizes in lines: the code in the diff and the code that uses what exists.
- A large dependency pulled in for a few lines of code. Give both sizes here too.
- Reuse that only pays off once a 2nd caller exists waits for that caller. Mention it in 1 line as a `nit`.

Every design and reuse finding gives the smaller or plainer way with 2 numbers, the lines in the diff and the lines the other way takes, so the author can weigh it.

## Shape

- Format and lint with CI's exact commands. Line length from the repo's config.
- Magic numbers, duplicated code, file and function size, names that misdescribe.
- Nothing in the diff the issue never mentioned.

## Prose

- Tells in comments, doc comments, test names, commit subjects and the PR draft, per repo-writing and code-comments. Run `python <skills>/repo-writing/scripts/prose_check.py` on the drafts and `--staged` on the diff.
- No trailers, no AI mention, no chat context, no private prior art in anything that lands on the repo.
