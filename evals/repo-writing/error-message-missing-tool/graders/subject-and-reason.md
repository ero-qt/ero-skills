---
type: llm
---

PASS if the message is a short line that states the subject and the reason, in the style of "clipcut requires ffmpeg, which isn't on the PATH." or "ffmpeg not found on the PATH.".
FAIL if the message is longer than about 15 words, uses "please" or "make sure", or tells the user several steps to take.
