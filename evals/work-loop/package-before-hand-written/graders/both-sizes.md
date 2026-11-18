---
type: llm
---

PASS if the plan looks for a maintained MQTT crate before planning any hand-written client, and states roughly how much code each way needs (using the crate against writing the protocol by hand).
FAIL if the plan goes straight to writing an MQTT client by hand, or picks a crate without comparing the size of the two ways.
