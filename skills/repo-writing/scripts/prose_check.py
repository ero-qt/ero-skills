"""Flags tells in repo prose: drafts, commit subjects and the comments in a staged diff.

Usage:
    python prose_check.py draft.md [more files]   check whole files
    python prose_check.py --text "add tick provider"
    python prose_check.py --staged                check added lines of the staged diff
    python prose_check.py < draft.md              check stdin

Each finding prints as `where:line: kind: rule: excerpt`. A `hard` finding breaks a
rule with no exceptions (dashes, trailers, curly quotes, NUL bytes) and makes the
exit code 1. A `check` finding needs a human look, since a regex can't tell a verb
from a noun or a real list from a comma chain.
"""

import re
import subprocess
import sys

HARD = [
    ("em or en dash", re.compile(r"[—–]")),
    ("double hyphen used as a dash", re.compile(r"\w -- \w")),
    ("trailer", re.compile(r"^\s*(co-authored-by|signed-off-by):|generated with \[?claude|\U0001F916", re.I)),
    ("curly quote", re.compile(r"[“”‘’]")),
]

CHECK = [
    ("'name' as a verb", re.compile(r"\b(names|named|naming)\b|\bname (the|a|an|its|one|each|every|both|them|it)\b", re.I)),
    ("'says' for code or output", re.compile(r"\b(says|saying)\b|\bsays so\b", re.I)),
    ("'lands'", re.compile(r"\b(lands?|landed|landing)\b", re.I)),
    ("'hold' or 'held'", re.compile(r"\b(hold|holds|held|holding)\b", re.I)),
    ("'carry'", re.compile(r"\b(carry|carries|carried|carrying)\b", re.I)),
    ("'told by' or 'stands on'", re.compile(r"\btold by\b|\bstands? on\b", re.I)),
    ("jargon or sales word", re.compile(
        r"\b(gap|corpus|afresh|flavou?r|watchdog|seamless(ly)?|robust|comprehensive|crucial|pivotal|"
        r"delve|leverag(e|es|ed|ing)|utili[sz](e|es|ed|ing)|vendored|era|lineage)\b", re.I)),
    ("filler word", re.compile(r"\b(simply|easily|basically|actually|obviously)\b", re.I)),
    ("praise for the reviewer", re.compile(r"\bgood catch\b|\bgreat (point|catch|question)\b", re.I)),
    ("validation", re.compile(r"\byou'?re (absolutely )?right\b", re.I)),
    ("framing phrase", re.compile(
        r"\bnote that\b|\bworth (noting|mentioning)\b|\bit'?s worth\b|\bone trap\b|\bnext up\b|"
        r"\bcoming soon\b|\btests? cover\b|\blet'?s dive\b|\bhere'?s the thing\b", re.I)),
    ("'here' for the user's machine", re.compile(
        r"\b(run|runs|ran|installed|works?|worked|built|build|test(ed)?) (it |them )?here\b|\bthis machine\b", re.I)),
    ("history word", re.compile(r"\b(previously|used to|no longer|anymore)\b", re.I)),
    ("comma before 'and' or 'or'", re.compile(r", (and|or)\b")),
    ("semicolon in prose", re.compile(r"\w; [A-Za-z]")),
    ("spelled-out number", re.compile(
        r"\b(two|three|four|five|six|seven|eight|nine|ten|eleven|twelve|twenty|thirty|forty|fifty|hundred)\b", re.I)),
    ("British spelling", re.compile(
        r"\b(favour|colour|behaviour|honour|neighbour|centre)\w*\b|\b\w+(is(e|ed|es|ing)|isation)\b", re.I)),
    # Skips greetings like "Hey!" and "Thanks!", which the user writes on purpose.
    ("exclamation mark", re.compile(r"\w(?<!\bhey)(?<!\bhi)(?<!\bthanks)(?<!\bthank you)!(\s|$)", re.I)),
    ("spaced hyphen used as a dash", re.compile(r"\w - \w")),
]

MARKDOWN = [
    ("heading bigger than h3", re.compile(r"^#{1,2} ")),
    ("Title Case heading", re.compile(r"^#+\s+([A-Z][\w'-]*\s+){2,}[A-Z]")),
    ("bold label bullet", re.compile(r"^\s*[-*] \*\*[^*]+:\*\*")),
    ("'*' bullet instead of '-'", re.compile(r"^\s*\* ")),
]

# British words that only look like -ise forms.
NOT_BRITISH = {"raise", "raised", "raises", "raising", "praise", "praised", "praises", "noise", "noises", "promise",
               "promised", "promising", "surprising", "surprises", "exercising", "cruise", "bruise", "demise",
               "promises", "precise", "otherwise", "likewise", "wise", "rise", "rises", "rising", "arise",
               "arises", "arising", "concise", "exercise", "exercised", "exercises", "advise", "advised",
               "revise", "revised", "revising", "comprise", "comprises", "surprise", "surprised", "enterprise",
               "expertise", "franchise", "televise", "premise", "premises", "paradise", "devise", "devised",
               "supervise", "improvise", "compromise", "disguise", "chastise", "despise", "excise", "incise",
               "poise", "turquoise", "tortoise", "porpoise", "treatise", "merchandise", "anise"}

SLASH = re.compile(r"(?<![:\"'])(?://[/!]?|/\*+|^\s*\*(?!/))\s?(.*)$")
HASH = re.compile(r"(?<![\w\"'])#(?![\[!])\s?(.*)$")
DASHES = re.compile(r"(?<![\w-])--\s?(.*)$")
ANGLE = re.compile(r"<!--\s?(.*?)(-->|$)")
COMMENTS = {
    SLASH: (".rs", ".cs", ".js", ".jsx", ".ts", ".tsx", ".c", ".h", ".cc", ".cpp", ".hpp", ".java", ".kt",
            ".go", ".swift", ".scala", ".dart", ".zig"),
    HASH: (".py", ".sh", ".bash", ".ps1", ".psm1", ".toml", ".yml", ".yaml", ".rb", ".cfg", ".ini", ".conf",
           ".editorconfig", ".gitignore", ".gitattributes", "Dockerfile", "Makefile"),
    DASHES: (".sql", ".lua", ".hs"),
    ANGLE: (".xml", ".html", ".htm", ".csproj", ".props", ".targets", ".xaml", ".slnx", ".svg"),
}
PROSE_FILES = (".md", ".markdown", ".txt", ".rst")


def comment_text(path, line):
    """Returns the comment part of a code line, or None when the line has no comment."""
    for pattern, endings in COMMENTS.items():
        if path.endswith(endings):
            match = pattern.search(line)
            return match.group(1).strip() if match else None
    return None


def strip_code(line):
    """Removes inline code spans and URLs, which hold names the rules must not judge."""
    line = re.sub(r"`[^`]*`", "``", line)
    return re.sub(r"https?://\S+", "", line)


def check_line(where, number, text, markdown, findings):
    # Heading sizes only matter in PR, issue and comment bodies, not in files with their own heading format.
    if markdown and not where.rsplit("/", 1)[-1].upper().startswith(("README", "CHANGELOG", "SKILL")):
        for rule, pattern in MARKDOWN:
            if pattern.search(text):
                findings.append((where, number, "check", rule, text.strip()))

    prose = strip_code(text)
    for rule, pattern in HARD:
        if pattern.search(prose):
            findings.append((where, number, "hard", rule, text.strip()))
    for rule, pattern in CHECK:
        matches = [match.group(0).lower() for match in pattern.finditer(prose)]
        if rule == "British spelling":
            matches = [word for word in matches if word not in NOT_BRITISH]
        if matches:
            findings.append((where, number, "check", rule, text.strip()))


class Fence:
    """Tracks code fences, so a 3-backtick fence inside a 4-backtick one doesn't end it.

    A fence of 4 or more backticks with no language is a draft wrapper around a PR or issue body,
    so the prose inside it is checked and only the code fences inside it are skipped.
    """

    def __init__(self):
        self.open = None
        self.wrapper = None

    def skip(self, line):
        """Returns whether the line is a fence or sits inside a code fence."""
        mark = re.match(r"\s*(`{3,}|~{3,})(.*)$", line)
        if self.open is None:
            if not mark:
                return False
            ticks, info = mark.group(1), mark.group(2).strip()
            if self.wrapper and ticks[0] == self.wrapper[0] and len(ticks) >= len(self.wrapper) and not info:
                self.wrapper = None
            elif self.wrapper is None and ticks[0] == "`" and len(ticks) >= 4 and not info:
                self.wrapper = ticks
            else:
                self.open = ticks
            return True
        if mark and mark.group(1)[0] == self.open[0] and len(mark.group(1)) >= len(self.open) and not mark.group(2).strip():
            self.open = None
        return True


def check_text(where, text, markdown, findings):
    fence = Fence()
    for number, line in enumerate(text.splitlines(), 1):
        if fence.skip(line) or "[!" in line:
            continue
        check_line(where, number, line, markdown, findings)


def check_staged(findings):
    diff = subprocess.run(["git", "diff", "--cached", "-U0", "--no-color"],
                          capture_output=True, text=True, encoding="utf-8", errors="replace").stdout
    added = {}
    path, number = None, 0
    for line in diff.splitlines():
        if line.startswith("+++ "):
            path = line[6:] if line.startswith("+++ b/") else None
            continue
        hunk = re.match(r"@@ -\S+ \+(\d+)", line)
        if hunk:
            number = int(hunk.group(1))
            continue
        if path and line.startswith("+"):
            added.setdefault(path, {})[number] = line[1:]
            number += 1

    for path, lines in added.items():
        if path.endswith(PROSE_FILES):
            # Reads the whole staged file so fences opened above an added line are known.
            staged = subprocess.run(["git", "show", f":{path}"], capture_output=True, text=True,
                                    encoding="utf-8", errors="replace").stdout
            fence = Fence()
            for number, line in enumerate(staged.splitlines(), 1):
                if not fence.skip(line) and number in lines:
                    check_line(path, number, line, True, findings)
        else:
            for number, line in lines.items():
                comment = comment_text(path, line)
                if comment:
                    check_line(path, number, comment, False, findings)

    names = subprocess.run(["git", "diff", "--cached", "--name-only", "-z"],
                           capture_output=True).stdout.split(b"\0")
    for name in filter(None, names):
        blob = subprocess.run(["git", "show", b":" + name], capture_output=True).stdout
        if b"\0" in blob and not blob.startswith((b"\x89PNG", b"GIF8", b"\xff\xd8", b"PK")):
            text_like = blob.count(b"\0") < len(blob) // 20
            if text_like:
                findings.append((name.decode(errors="replace"), 0, "hard", "NUL byte in a text file", ""))


def main(args):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    sys.stdin.reconfigure(encoding="utf-8", errors="replace")
    findings = []
    if not args:
        check_text("<stdin>", sys.stdin.read(), True, findings)
    elif args[0] in ("-h", "--help"):
        print(__doc__.strip())
        return 0
    elif args[0] == "--staged":
        check_staged(findings)
    elif args[0] == "--text":
        check_text("<text>", " ".join(args[1:]), False, findings)
    else:
        for path in args:
            with open(path, encoding="utf-8", errors="replace") as file:
                check_text(path, file.read(), path.endswith(PROSE_FILES), findings)

    for where, number, kind, rule, excerpt in findings:
        print(f"{where}:{number}: {kind}: {rule}: {excerpt[:160]}")
    hard = sum(1 for finding in findings if finding[2] == "hard")
    print(f"{hard} hard, {len(findings) - hard} to check")
    return 1 if hard else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
