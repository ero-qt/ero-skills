# Examples

Texts in the voice this skill asks for. They follow the shapes of real approved texts with the project details swapped out. The repo always decides the shape (templates, relation lines, casing), and the voice stays the same.

## Issue

Title: `CSV import fails on files with a byte order mark`

````
`import_csv` fails on CSV files that start with a UTF-8 byte order mark. Excel adds one when you save as "CSV UTF-8", so most files people export from it hit this.

The reader opens the file as plain UTF-8 and then checks that the first header matches a known column. The BOM ends up in front of the first header, so the check fails even though only 3 invisible bytes are different. Here's the start of a file Excel 16.80 wrote, before and after I removed the BOM by hand:

```
before: ef bb bf 6e 61 6d 65 2c 65 6d 61 69 6c
after:  6e 61 6d 65 2c 65 6d 61 69 6c
```

The header check rejects it here:

https://github.com/owner/project/blob/1a2b3c4/src/import.py#L42

Files saved as plain "CSV" import fine, since Excel only adds the BOM for the UTF-8 option.

Opening the file with `utf-8-sig` would strip the BOM before the header check runs, and it reads files without a BOM the same as before.
````

## Bug fix PR

Title: `Fix CSV import for files with a byte order mark (#41)`

```
Closes #41.

The reader now opens files with `utf-8-sig`, so a byte order mark at the start of the file no longer ends up in the first header. Files without one read the same as before.

The first commit moves the header check into its own function and doesn't change anything.

An export from Excel 16.80 imports with this.
```

## Feature PR with an example

Title: `Let callers pass their own column map (#30)`

````
Part of #30.

`import_csv` can now take a column map, so a caller with unusual headers doesn't have to rename them first. The map goes from the file's header to the field name, and any header that isn't in it keeps the default lookup.

```python
rows = import_csv("export.csv", columns={"E-Mail": "email", "Full Name": "name"})
```

- An unknown field name in the map raises `ValueError` before the file is read.
- The map is checked case-insensitively, the same way the default lookup is.

---

Depends on #44.
````

## Small PR

Title: `Let callers build a reader from an open file (#30)`

```
Part of #30.

Adds `Reader.from_file(file, columns)`, so a caller that already opened the file can skip the path handling and still use every parser. Nothing checks the file's encoding. This is the same shape as `Writer.from_file`.

---

Depends on #45.
```

## Setup PR

```
Sets up the repository's base files ahead of any code:

- editor configuration, line ending policy, and ignores,
- `0BSD` license,
- a minimal `readme.md` to grow with the library.
```

A one-purpose PR can be one line: `License, readme, and build settings.`

## Commit subjects

The repo's casing and prefixes win. Some repos write subjects lowercase, some capitalize them, some use `fix(scope):` prefixes.

- `add column map to csv import`
- `stop caching failed header lookups`
- `split header check into own function`
- `Add repository scaffolding`
- `Adjust readme`
- `fix(import): strip byte order mark`

## Review replies

- "#52 replaces this whole lookup with a dictionary that also covers the old headers, so these special cases would get deleted anyway if that merges. I would honestly just drop the last commit here if #52 looks good to you."
- "I moved the `defaults?` check into the nested section branch so plain configs work without it now and added a test for a config without `defaults`."
- "I ended up adding proper Windows paths instead of skipping those tests. They check the same two files, just with backslashes."
- "Yeah I thought so. I can just remove it."
- "Hey. I have to apologize, I somehow completely forgot about this and made the same fix in #78 without linking back here."
- "Hey! Wanna flag some overlap with some of my open PRs:"

## Notes in issues

- "#33 touches this module too. I'll branch off main for now and rebase if it gets merged first."
- "Here's what I'd do:"

## Alert blocks in a README

```
> [!NOTE]
> Useful information that users should know, even when skimming content.

> [!TIP]
> Helpful advice for doing things better or more easily.

> [!IMPORTANT]
> Key information users need to know to achieve their goal.

> [!WARNING]
> Urgent info that needs immediate user attention to avoid problems.

> [!CAUTION]
> Advises about risks or negative outcomes of certain actions.
```
