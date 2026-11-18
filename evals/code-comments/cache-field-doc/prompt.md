---
tags: [code-comments, ai-tells]
plugins: ["../../../skills/code-comments"]
max_turns: 20
allowed_tools: [Skill, Read, Glob, Grep]
append_system_prompt: "The workspace is empty on purpose. Treat what the user says about their repository and the earlier conversation as true, and don't look for the files. No shell is available, so give commands instead of running them."
---

Write the XML doc comment for the `_types` field in this C# class. Reply with only the comment.

```csharp
public sealed class TypeResolver
{
    private readonly Dictionary<string, Type> _types = new();

    public Type Resolve(string assemblyQualifiedName)
    {
        if (!_types.TryGetValue(assemblyQualifiedName, out Type? type))
        {
            type = Type.GetType(assemblyQualifiedName, throwOnError: true)!;
            _types[assemblyQualifiedName] = type;
        }

        return type;
    }
}
```
