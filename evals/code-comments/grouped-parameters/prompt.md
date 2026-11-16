---
tags: [code-comments, design]
plugins: ["../../../skills/code-comments"]
max_turns: 20
allowed_tools: [Skill, Read, Glob, Grep]
append_system_prompt: "The workspace is empty on purpose. Treat what the user says about their repository and the earlier conversation as true, and don't look for the files. No shell is available, so give commands instead of running them."
---

Add a `TimeSpan retryDelay` parameter to this constructor. Keep the other names. Reply with only the new signature.

```csharp
public Exporter(
    string outputFolder,
    string fileNamePattern,
    bool overwrite,
    int retryCount,
    TimeSpan timeout,
    ILogger logger,
    IClock clock,
    IFileSystem fileSystem)
```
