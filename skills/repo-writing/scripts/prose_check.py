"""Flags tells in repo prose: drafts, commit subjects and the comments in a staged diff.

Usage:
    python prose_check.py draft.md [more files]   check whole files
    python prose_check.py --text "add tick provider"
    python prose_check.py --staged                check added lines of the staged diff
    python prose_check.py < draft.md              check stdin
    python prose_check.py --explain "triad"       print why a rule flags and the fix

Each finding prints as `where:line: kind: rule: excerpt`. A `hard` finding breaks a
rule with no exceptions (dashes, trailers, curly quotes, NUL bytes) and makes the
exit code 1. A `check` finding needs a human look, since a regex can't tell a verb
from a noun or a real list from a comma chain.

A 2nd pass reads whole paragraphs and the whole text for rhythm: sentence lengths,
openers, a verb used over and over. Every file and stdin also get a line like
`draft.md: tells: 7 in 310 words, 2.3 per 100`. Read a text again when it's above
1 per 100. The flags follow the habits of today's models and change with them, so
a clean run proves nothing. A person still reads anything longer than a subject.
"""

import os
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
    ("clipped negation", re.compile(
        r"\b(has|have|had|finds?|found|returns?|allocates?) (no|nothing)\b|\bno other\b", re.I)),
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
        r"\bcoming soon\b|\btests? cover\b|\blet'?s dive\b|\bhere'?s the thing\b|\bimportantly\b|"
        r"\bin summary\b|\bto summari[sz]e\b|\bit'?s important to\b", re.I)),
    ("copula dodge", re.compile(r"\b(serves?|served|acts?|acted|functions?) as (a|an|the)\b|\bboasts?\b", re.I)),
    ("participle tail", re.compile(
        r", (ensuring|allowing|enabling|making|highlighting|reflecting|providing|leaving)\b", re.I)),
    ("contrast frame", re.compile(
        r"\bnot (just|only|merely) [^.]{1,60}\bbut\b|\b(isn'?t|is not|aren'?t|wasn'?t)\b[^.]{1,60}, "
        r"(it'?s|it is|they'?re)\b|\brather than\b", re.I)),
    # 3 lowercase words that end the clause, because a list of names like "Linux, Mac and Windows" or of
    # longer items like "the config, the cache and the log" is a real list.
    ("triad", re.compile(r"\b[a-z]+, [a-z]+,? (and|or) [a-z]+(?=[.,;:!?)]|$)")),
    ("fronted clause", re.compile(
        r"(^|[.!?] )\s*([-*] )?(Because|Since|While|Although|Given|With|By \w+ing)\b|(^|[.!?] )``,? is an?\b")),
    ("colon setup", re.compile(
        r"^(?!(Usage|Note|Example|Examples|Title|Body|Before|After|Bad|Good|Rejected|Written instead|Fix|Tip|"
        r"Warning|Important|Default|Output|Input|Source|Sources):)[A-Z][^.:`]{3,40}: [a-z]")),
    ("nominalization", re.compile(
        r"\b(perform|provide|make|do|give|offer)(s|ed|ing)? (a |an |the )?\w+(tion|ment|ance|ence|sion)\b|"
        r"\bprovides? support for\b", re.I)),
    ("formal connective", re.compile(
        r"(^|[.!?] )\s*([-*] )?(Moreover|Additionally|Furthermore|Consequently|Notably|Thus|Hence)\b")),
    ("significance claim", re.compile(
        r"\bplays? an? (key|important|crucial|vital|central|major) role\b|\bpain points?\b|"
        r"\bcommon (source of|pitfall)\b", re.I)),
    ("announcing intro", re.compile(
        r"\bthere are \d+ (things|steps|parts|ways|reasons)\b|"
        r"\bthis (section|document|page|guide|PR|change) (covers|describes|explains|walks)\b", re.I)),
    ("teaching tone", re.compile(r"\bplease (ensure|make sure|note|remember)\b|\bensure that\b", re.I)),
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

# Rules for code comments only, because people do know and want things in prose.
COMMENT_ONLY = [
    ("code that talks or thinks", re.compile(r"\b(tells?|asks?|answers?|knows?|wants?|decides?)\b", re.I)),
    ("'now' in a comment", re.compile(r"\bnow\b", re.I)),
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

# Files that quote bad examples on purpose. They only get the hard rules, since every other rule
# would flag the examples.
QUOTES_BAD_EXAMPLES = ("SKILL.md", "tells.md")
TELLS = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "references", "tells.md")

# Verbs a draft tends to use for every sentence about contents. Each group counts as 1 verb.
FLAT_VERBS = {
    "has": ("has", "have"), "contains": ("contains", "contain"), "holds": ("holds", "hold"),
    "keeps": ("keeps", "keep"), "lists": ("lists",), "shows": ("shows",), "provides": ("provides", "provide"),
    "includes": ("includes", "include"), "offers": ("offers", "offer"), "uses": ("uses",), "gives": ("gives",),
    "makes": ("makes",),
}
HEDGES = re.compile(r"\b(may|might|could(?! not)|potentially|possibly|perhaps|somewhat|arguably|likely|probably|"
                    r"generally|typically|in some (cases|setups|situations)|tends? to)\b", re.I)
REASONS = re.compile(r"\b(because|since|so|which)\b", re.I)
CLOSERS = re.compile(r"^(This|That|Overall|In short|Ultimately)\b")
SENTENCE_END = re.compile(r"(?<=[.!?])\s+(?=[A-Z0-9`\"(\[])")

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
    """Returns the comment part of a code line, or None when the line doesn't have a comment."""
    for pattern, endings in COMMENTS.items():
        if path.endswith(endings):
            match = pattern.search(line)
            return match.group(1).strip() if match else None
    return None


def strip_code(line):
    """Removes inline code spans and URLs, which hold names the rules must not judge."""
    line = re.sub(r"`[^`]*`", "``", line)
    return re.sub(r"https?://\S+", "", line)


def check_line(where, number, text, markdown, findings, comment=False):
    # Heading sizes only matter in PR, issue and comment bodies, not in files with their own heading format.
    if markdown and not where.rsplit("/", 1)[-1].upper().startswith(("README", "CHANGELOG", "SKILL")):
        for rule, pattern in MARKDOWN:
            if pattern.search(text):
                findings.append((where, number, "check", rule, text.strip()))

    prose = strip_code(text)
    for rule, pattern in HARD:
        if pattern.search(prose):
            findings.append((where, number, "hard", rule, text.strip()))
    if quotes_bad_examples(where):
        return
    for rule, pattern in CHECK + (COMMENT_ONLY if comment else []):
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


def words(text):
    """Returns the words of a line that went through strip_code, with each code span as 1 word."""
    return re.findall(r"``|[\w'-]*\w", text)


def paragraphs(lines):
    """Splits (number, line) pairs into paragraphs. A list item is a paragraph of its own.

    Headings, table rows, quotes and HTML comments end a paragraph and aren't part of any.
    """
    block = []
    for number, line in lines:
        item = re.match(r"\s*(?:[-*+]|\d+[.)]) (.*)$", line)
        if item or not line.strip() or re.match(r"\s*(#|\||>|<!--)", line):
            if block:
                yield block
            block = [(number, item.group(1))] if item else []
            continue
        block.append((number, line))
    if block:
        yield block


def sentences(block):
    """Returns (number, sentence) pairs for a paragraph, joining a sentence that wraps onto the next line."""
    found, current = [], None
    for number, line in block:
        for piece in SENTENCE_END.split(strip_code(line).strip()):
            if not piece:
                continue
            current = (current[0], current[1] + " " + piece) if current else (number, piece)
            if re.search(r"[.!?][\"')\]]*$", piece):
                found.append(current)
                current = None
    if current:
        found.append(current)
    return found


def check_paragraphs(where, lines, findings, report=None):
    """Checks the rhythm of each paragraph. Only findings on a line in `report` count, when it's given."""
    def add(numbers, rule, excerpt):
        number = next((number for number in numbers if report is None or number in report), None)
        if number is not None:
            findings.append((where, number, "check", rule, excerpt.strip()))

    for block in paragraphs(lines):
        found = sentences(block)
        counts = [len(words(sentence)) for _, sentence in found]
        for index, (number, sentence) in enumerate(found):
            if index and counts[index] <= 4 and counts[index - 1] >= 12 and "``" not in sentence:
                add([number], "dramatic short sentence", sentence)
            if counts[index] >= 28 and len(REASONS.findall(sentence)) >= 2:
                add([number], "decision packed into 1 sentence", sentence)
            if sum(1 for _ in HEDGES.finditer(sentence)) >= 2:
                add([number], "hedge stack", sentence)
            if index >= 2:
                three = found[index - 2:index + 1]
                openers = {words(text)[0].lower() for _, text in three if words(text)}
                if len(openers) == 1 or all(", and " in text for _, text in three):
                    add([line for line, _ in three], "same skeleton in a row", sentence)
        if len(found) >= 2 and CLOSERS.match(found[-1][1]):
            add([found[-1][0]], "closing restatement", found[-1][1])
        if len(found) >= 4 and max(counts) - min(counts) < 0.25 * sum(counts) / len(counts):
            add([number for number, _ in found], "flat sentence length", found[0][1])


def check_verbs(where, lines, findings):
    """Flags a content verb used 4 or more times per 300 words."""
    total = sum(len(words(strip_code(line))) for _, line in lines)
    for verb, forms in FLAT_VERBS.items():
        pattern = re.compile(r"\b(" + "|".join(forms) + r")\b", re.I)
        hits = [number for number, line in lines for _ in pattern.finditer(strip_code(line))]
        if len(hits) >= 4 and len(hits) * 300 >= 4 * total:
            findings.append((where, hits[0], "check", "same verb in many sentences",
                             f"'{verb}' {len(hits)} times in {total} words"))


def quotes_bad_examples(where):
    return where.replace("\\", "/").rsplit("/", 1)[-1] in QUOTES_BAD_EXAMPLES


def density(where, lines, findings):
    """Returns the density line for the findings and words of 1 text, or None when it doesn't have any words."""
    total = sum(len(words(strip_code(line))) for _, line in lines)
    if not total:
        return None
    count = sum(1 for finding in findings if finding[0] == where)
    return f"{where}: tells: {count} in {total} words, {count * 100 / total:.1f} per 100"


def check_text(where, text, markdown, findings, densities=None):
    fence = Fence()
    lines = []
    for number, line in enumerate(text.splitlines(), 1):
        if fence.skip(line) or "[!" in line:
            continue
        check_line(where, number, line, markdown, findings)
        lines.append((number, line))
    if not quotes_bad_examples(where):
        check_paragraphs(where, lines, findings)
        check_verbs(where, lines, findings)
    if densities is not None:
        densities.append(density(where, lines, findings))


def check_staged(findings, densities):
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
            prose = []
            for number, line in enumerate(staged.splitlines(), 1):
                if not fence.skip(line) and "[!" not in line:
                    prose.append((number, line))
            added_prose = [(number, line) for number, line in prose if number in lines]
            for number, line in added_prose:
                check_line(path, number, line, True, findings)
            if not quotes_bad_examples(path):
                check_paragraphs(path, prose, findings, set(lines))
                check_verbs(path, added_prose, findings)
            densities.append(density(path, added_prose, findings))
        else:
            for number, line in lines.items():
                comment = comment_text(path, line)
                if comment:
                    check_line(path, number, comment, False, findings, comment=True)

    names = subprocess.run(["git", "diff", "--cached", "--name-only", "-z"],
                           capture_output=True).stdout.split(b"\0")
    for name in filter(None, names):
        blob = subprocess.run(["git", "show", b":" + name], capture_output=True).stdout
        if b"\0" in blob and not blob.startswith((b"\x89PNG", b"GIF8", b"\xff\xd8", b"PK")):
            text_like = blob.count(b"\0") < len(blob) // 20
            if text_like:
                findings.append((name.decode(errors="replace"), 0, "hard", "NUL byte in a text file", ""))


def explain(rule):
    """Returns the row of a rule in tells.md as `label: value` lines, or None when tells.md doesn't list the rule.

    A row lists the rules that flag it in backticks in its last column.
    """
    with open(TELLS, encoding="utf-8") as file:
        level, header = None, None
        for line in file:
            if line.startswith("## "):
                level, header = line[3:].strip(), None
            elif not line.startswith("|"):
                header = None
            elif header is None:
                header = [cell.strip() for cell in line.strip().strip("|").split("|")]
            elif not set(line.strip()) <= set("|-: "):
                cells = [cell.strip() for cell in line.strip().strip("|").split("|")]
                if f"`{rule}`" in cells[-1]:
                    return "\n".join([f"Level: {level}"] + [f"{name}: {cell}" for name, cell in zip(header, cells)])
    return None


def main(args):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    sys.stdin.reconfigure(encoding="utf-8", errors="replace")
    findings, densities = [], []
    if not args:
        check_text("<stdin>", sys.stdin.read(), True, findings, densities)
    elif args[0] in ("-h", "--help"):
        print(__doc__.strip())
        return 0
    elif args[0] == "--explain":
        rule = " ".join(args[1:])
        row = explain(rule)
        print(row or f"tells.md doesn't list a rule called '{rule}'")
        return 0 if row else 1
    elif args[0] == "--staged":
        check_staged(findings, densities)
    elif args[0] == "--text":
        check_text("<text>", " ".join(args[1:]), False, findings)
    else:
        for path in args:
            with open(path, encoding="utf-8", errors="replace") as file:
                check_text(path, file.read(), path.endswith(PROSE_FILES), findings, densities)

    for where, number, kind, rule, excerpt in findings:
        print(f"{where}:{number}: {kind}: {rule}: {excerpt[:160]}")
    for line in filter(None, densities):
        print(line)
    hard = sum(1 for finding in findings if finding[2] == "hard")
    print(f"{hard} hard, {len(findings) - hard} to check")
    return 1 if hard else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
