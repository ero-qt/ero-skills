---
type: llm
---

PASS if the review says the hand-written parser in `RowReader` should give way to Python's `csv` module (such as `csv.DictReader`) and gives a number of lines for both ways: about how long the hand-written code is (such as 24 or 28 lines) and about how long the code with `csv` is (such as 2 or 3 lines). The numbers may sit in a table cell.
FAIL if the review misses the hand-written parser, or suggests the `csv` module without giving the size of both ways.
