# Defaults for new projects

Use these in repos with no precedent of their own. A repo's existing style and its `.editorconfig` always win, and repos differ a lot (member order, widths, test names), so check before applying any line here.

## Any language

- One significant type per file, files around 300 to 400 lines without comments, split per operation once a file grows (`*.ReadString.cs`).
- Functions small, concerns inside them split by blank lines.
- Lists of one kind in their natural order: constants by value, struct fields by offset, settings and native methods alphabetically.
- Sibling entries in a file look exactly the same: same line breaks, same layout, one form for one construct.
- Defaults live where an option is declared, as initializers, not in the code that uses it.
- Generate or derive data instead of keeping it by hand. One source of truth.
- Prefer built-in language and library features and established packages over hand-rolled code, with the same approach across sibling tools.
- One implementation per concept. Code sits in the layer that owns its concern. Engine-agnostic code goes in shared modules.
- `null` means absence everywhere. Invalid combinations should be impossible to build. State is immutable unless it really has to change.
- Logs are terse and technical, trace logs go everywhere behind a level check, each event logs once. An expected exit doesn't log.
- Error messages read like the platform's own: short ("Requires X version Y or later."), values in single quotes, nothing the output already shows. No custom teaching messages where the platform's error is clear.
- No member without a caller today or a planned one, but public API and planned members stay.

## C#

- Idiomatic BCL-style C#: simple, single responsibility and composition (as a habit, not a dogma), no hacks.
- Widths: 150 columns for code, 120 for doc comments and markdown, unless `.editorconfig` sets other widths. Wrap a signature or argument list with one item per line, and put every primary constructor and record parameter on its own line regardless of width.
- Member order goes `const`, then `static`, then instance. `readonly` comes before mutable, public before private, and the kinds go fields, constructors, properties, indexers, methods. Test helpers sit at the top of the test class.
- Empty bodies on the declaring line (`: this(...) { }`, `catch (X) { }`). No blank line between a `get` body and its `set`. Braces on switch case bodies. Trailing commas in multi-line lists.
- Primary constructors instead of fields that copy a parameter. `required` instead of a marker attribute. `params ReadOnlySpan<T>` where it saves allocations. Extension methods on the relevant type instead of static helper classes, in a class with the `Extensions` suffix. Flag enums for options that combine.
- Failures through typed results with one named factory per case (`ConfigError.MissingKey(name, section)`), never a bare error string.
- Positive guard for a single call: `if (x?.Flag is true) { x.Call(); }`.
- Doc comments in the BCL voice: "Represents..." or "Provides..." on types, "Initializes a new instance of the <see cref="X"/> class." on constructors, "Gets..." or "Gets or sets..." on properties, "Gets a value indicating whether..." on booleans, a verb on methods.
- The body of `<summary>`, `<remarks>`, `<returns>`, `<value>` and `<exception>` goes on its own line, indented 4 spaces, even for one-liners. `<param>` and `<typeparam>` stay on one line. `<remarks>` sits second to last, above `<exception>`.

  ```csharp
  /// <summary>
  ///     Gets the target's process id.
  /// </summary>
  ```

- Overrides get `<inheritdoc/>` plus `<remarks>` for what the implementation adds, with their own summary only on `ToString`, `Equals` and `GetHashCode`. A partial type has its summary on exactly one declaration.
- A blank line goes before a comment inside a body unless the comment opens the block or follows another comment. A comment about a `catch` sits above the `catch` line.
- Tests use `Method_Scenario_Expected` names, a `//` line stating the fact they pin, and expected values inline (`Is.EqualTo(["release", "master"])`), one element per line when long.
- Scratch experiments run as file-based apps (`dotnet run file.cs`), never a new project.

## Rust

- rustdoc conventions: a one-line summary that opens with a verb for functions, then sections.
- Layouts read at several offsets or in several places are `#[repr(C)]` types with offsets from `mem::offset_of!`. A small header read once can use typed chunks (`split_first_chunk::<4>()`) instead. Constants are called by the spec's names.
- Unit tests in `*_tests.rs` files beside the code, so they reach private items. Test names are short behavior claims with no leading article.
- `cargo clippy` and `cargo fmt` clean with the repo's features. Use `--offline` so nothing installs silently.
