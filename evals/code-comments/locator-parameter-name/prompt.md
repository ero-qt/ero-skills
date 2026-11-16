---
tags: [code-comments, design]
plugins: ["../../../skills/code-comments"]
max_turns: 20
allowed_tools: [Skill, Read, Glob, Grep]
append_system_prompt: "The workspace is empty on purpose. Treat what the user says about their repository and the earlier conversation as true, and don't look for the files. No shell is available, so give commands instead of running them."
---

What should I call the first parameter of this constructor? It gets a `SymbolLocator` that finds the addresses of functions by their names.

```csharp
public FunctionTable(SymbolLocator ???, ProcessMemory memory)
```

Give me the name and one line why.
