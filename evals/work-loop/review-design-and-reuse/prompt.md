---
tags: [work-loop, design, reuse]
plugins: ["../../../skills/work-loop"]
max_turns: 20
allowed_tools: [Skill, Read, Glob, Grep]
append_system_prompt: "The workspace is empty on purpose. Treat what the user says about their repository and the earlier conversation as true, and don't look for the files. No shell is available, so give commands instead of running them."
---

The state check is done: the tree is clean, CI is green and there are no open PRs or issues. This repo doesn't use issues. You showed me the read-back and the plan and I said Go to both.

The task: add a `Report` class to my Python CLI that sums the `amount` column of a CSV export per `category`. The commit is medium sized. I wrote the code, the tests pass and everything is staged. Here's the staged diff without the tests:

```diff
diff --git a/report.py b/report.py
new file mode 100644
--- /dev/null
+++ b/report.py
@@ -0,0 +1,41 @@
+class RowReader:
+    def __init__(self, path):
+        self.path = path
+
+    def rows(self):
+        with open(self.path, encoding="utf-8") as file:
+            header = None
+            for line in file:
+                fields = []
+                current = ""
+                quoted = False
+                for char in line.rstrip("\n"):
+                    if char == '"':
+                        quoted = not quoted
+                    elif char == "," and not quoted:
+                        fields.append(current)
+                        current = ""
+                    else:
+                        current += char
+                fields.append(current)
+                if header is None:
+                    header = fields
+                else:
+                    yield dict(zip(header, fields))
+
+
+def fetch_rows(reader):
+    return list(reader.rows())
+
+
+class Report:
+    def __init__(self, writer: RowReader, title: str):
+        self.writer = writer
+        self.title = title
+
+    def totals(self):
+        totals = {}
+        for row in fetch_rows(self.writer):
+            totals[row["category"]] = totals.get(row["category"], 0) + float(row["amount"])
+        return totals
```

Now run the review step on it and give me the findings.
