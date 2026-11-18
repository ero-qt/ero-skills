# Review checklist

The reviewer works through every item against the full diff and returns a verdict line plus a table of severity, location, finding and the input that shows it. Each item is a defect class an external review has caught before. Every finding that offers a smaller way gives 2 numbers: the lines in the diff and the lines the other way takes.

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
- A wrapper, helper or type with 1 caller and no job of its own goes. Point at the caller it folds into.
- Names and parameter lists follow section 2 of `<skills>/code-comments/SKILL.md`: role names, parameters grouped by concept, the object passed instead of a value it has and neutral names in generic code. A name from another role, like `client` for a server object, is a finding. Give the name it should have.
- Each case gets its own small type instead of a value widened to `object`, `any` or an untyped function field so 2 cases fit 1 slot.
- When 1 function branches per case and a 2nd case exists, like a 2nd file format, say which small interface each case could implement instead. Don't ask for it when there's only 1 case.
- Code ported from somewhere else gets reshaped for this codebase. A member-for-member copy that brings the old helpers and hacks along is a finding.

## Reuse

- Code in the repo that already does the job or most of it, with its location.
- A maintained package, the standard library, a standard file format or an existing tool that does what the diff writes by hand. A hand-written parser for a format the standard library reads is a finding.
- A large dependency pulled in for a few lines of code.
- Reuse that only pays off once a 2nd caller exists waits for that caller. Mention it in 1 line as a `nit`.

## Shape

- Format and lint with CI's exact commands. Line length from the repo's config.
- Magic numbers, duplicated code, file and function size.
- Nothing in the diff the issue never mentioned.

## Prose

- Tells in comments, doc comments, test names, commit subjects and the PR draft, per repo-writing and code-comments. Run `python <skills>/repo-writing/scripts/prose_check.py` on the drafts and `--staged` on the diff.
- No trailers, no AI mention, no chat context, no private prior art in anything that lands on the repo.
