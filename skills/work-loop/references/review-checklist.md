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

## Shape

- Format and lint with CI's exact commands. Line length from the repo's config.
- Magic numbers, duplicated code, needless indirection, file and function size, names that misdescribe.
- Members with no caller and no planned consumer. Public API and planned members stay.
- Nothing in the diff the issue never mentioned.

## Prose

- Tells in comments, doc comments, test names, commit subjects and the PR draft, per repo-writing and code-comments. Run `python <skills>/repo-writing/scripts/prose_check.py` on the drafts and `--staged` on the diff.
- No trailers, no AI mention, no chat context, no private prior art in anything that lands on the repo.
