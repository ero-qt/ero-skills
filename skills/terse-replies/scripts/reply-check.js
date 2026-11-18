// Checks each chat reply against the terse-replies rules on Stop and writes every broken rule to slips.jsonl in the
// plugin data folder. It never blocks the turn or sends anything back, because a long reply can be one the user wanted.
// Hard findings break a rule the skill states outright. Soft findings are worth a look.

const fs = require('fs');
const os = require('os');
const path = require('path');

const CHECKED_LEVELS = ['full', 'ultra'];
const MAX_ANSWER_LINES = 3;
const MAX_BULLETS = 5;
const MAX_GATE_LINES = 12;
const MAX_WORDS_PER_LINE_AT_ULTRA = 12;
const TRANSCRIPT_CHUNK_BYTES = 64 * 1024;

const dataDir = process.env.CLAUDE_PLUGIN_DATA || path.join(os.homedir(), '.claude');

function readFile(file) {
    try {
        return fs.readFileSync(file, 'utf8').trim();
    } catch {
        return '';
    }
}

// Splits the reply into lines and marks each line that sits inside a fence, the fence lines included.
function readLines(message) {
    const lines = [];
    let fence = null;
    for (const text of message.split(/\r?\n/)) {
        const marker = text.trim().match(/^(`{3,}|~{3,})/);
        if (fence) {
            lines.push({ text, fenced: true });
            if (marker && marker[1][0] === fence[0] && marker[1].length >= fence.length && text.trim() === marker[1]) {
                fence = null;
            }
        } else if (marker) {
            fence = marker[1];
            lines.push({ text, fenced: true });
        } else {
            lines.push({ text, fenced: false });
        }
    }

    return lines;
}

function withoutInlineCode(text) {
    return text.replace(/`+[^`]*`+/g, ' ');
}

// Drops inline code and text in double quotes, because both repeat text from somewhere else.
function withoutQuotes(text) {
    return withoutInlineCode(text).replace(/"[^"]*"|[“„][^“”]*[“”]/g, ' ');
}

function wordCount(text) {
    return withoutInlineCode(text).split(/\s+/).filter((word) => /[\p{L}\p{N}]/u.test(word)).length;
}

function trimBlankEnds(lines) {
    const first = lines.findIndex((line) => line.text.trim());
    if (first < 0) {
        return [];
    }

    let last = lines.length - 1;
    while (!lines[last].text.trim()) {
        last--;
    }

    return lines.slice(first, last + 1);
}

// Drops the bold markers, so a label like `**State:**` reads like `State:`.
function withoutBold(text) {
    return text.replace(/\*\*|__/g, '');
}

function filledLines(plain) {
    return plain.filter((line) => line.trim()).map(withoutBold);
}

// A read-back or a plan ends on a bare `Go?`. It takes the place of the close like `Approve?` does. The length and
// subject rules are only for the commit gate.
function endsOnGo(plain) {
    return /^\s*Go\?\s*$/.test(filledLines(plain).at(-1) || '');
}

function checkGate(lines, findings, explain) {
    const gateIndex = lines.findIndex((line) => !line.fenced && /^\s*Approve\?/.test(line.text));
    if (gateIndex < 0) {
        return false;
    }

    const shown = trimBlankEnds(lines.filter((line) => !line.fenced));
    if (!explain && shown.length > MAX_GATE_LINES) {
        findings.push(hard('gate-length', `gate is ${shown.length} lines, max ${MAX_GATE_LINES}`));
    }

    const above = lines.slice(0, gateIndex).reverse().find((line) => line.text.trim());
    const subjectAbove = above && (above.fenced || /^\s*`[^`]+`\s*$/.test(above.text));
    if (!subjectAbove) {
        findings.push(hard('gate-subject', 'line above Approve? isn\'t the subject in inline code'));
    }

    return true;
}

function checkWording(plain, findings) {
    if (plain.some((line) => /[–—]| -- /.test(withoutQuotes(line)))) {
        findings.push(hard('dash', 'em dash, en dash or -- outside code and quotes'));
    }

    const first = plain.find((line) => line.trim()) || '';
    if (/^\s*(you['’]?re (absolutely )?right|sorry|i apologi[sz]e|i['’]ll|let me)\b/i.test(first)) {
        findings.push(hard('opener', 'first line is validation, an apology or an announcement'));
    }

    const closing = plain.filter((line) => line.trim()).slice(-3).map(withoutQuotes).join('\n');
    if (/\b(let me know|happy to|want me to)\b/i.test(closing)) {
        findings.push(hard('closing-offer', 'reply ends on an offer'));
    }
}

// Returns the length of the longest list. A line of text between 2 bullets starts a new list, so a list split
// under `Now:` and `Later:` counts per part. A blank line doesn't.
function longestList(plain) {
    let longest = 0;
    let current = 0;
    for (const line of plain) {
        if (/^\s*[-*+]\s/.test(line)) {
            current++;
            longest = Math.max(longest, current);
        } else if (line.trim()) {
            current = 0;
        }
    }

    return longest;
}

function checkLength(plain, findings, level) {
    const bullets = longestList(plain);
    if (bullets > MAX_BULLETS) {
        findings.push(soft('bullets', `${bullets} bullets in 1 list, max ${MAX_BULLETS}`));
    }

    const filled = plain.filter((line) => line.trim());
    if (level === 'ultra' && filled.length) {
        const average = filled.reduce((sum, line) => sum + wordCount(line), 0) / filled.length;
        if (average > MAX_WORDS_PER_LINE_AT_ULTRA) {
            findings.push(soft('line-words', `${average.toFixed(1)} words per line, max ${MAX_WORDS_PER_LINE_AT_ULTRA}`));
        }
    }
}

// A label like "1/2:" at the start of a line promises the other parts in the same reply.
function checkCountLabels(plain, findings) {
    const parts = new Map();
    for (const line of plain) {
        const match = line.match(/^\s*(?:part\s+)?([1-9])\/([2-9])[:).]/i);
        if (match) {
            const total = Number(match[2]);
            parts.set(total, (parts.get(total) || new Set()).add(Number(match[1])));
        }
    }

    for (const [total, seen] of parts) {
        if (seen.size < total) {
            findings.push(soft('count-half', `${[...seen].join(', ')} of ${total} parts shown`));
        }
    }
}

// Returns whether the entry is a prompt the user typed, which starts a turn. A tool result and a note that
// Claude Code adds itself with `isMeta` are user entries as well but start none.
function promptEntry(entry) {
    if (entry.type !== 'user' || entry.isMeta || !entry.message) {
        return false;
    }

    const content = entry.message.content;
    return typeof content === 'string'
        || (Array.isArray(content) && !content.some((block) => block?.type === 'tool_result'));
}

function toolEntry(entry) {
    return entry.type === 'assistant'
        && Array.isArray(entry.message?.content)
        && entry.message.content.some((block) => block?.type === 'tool_use');
}

// Yields the lines of a file from the last to the first. It reads the file in chunks from the end, so a caller
// that stops early never reads the start of a long file. A line is split at the `\n` byte before it is decoded,
// so a character of several bytes at a chunk border stays whole.
function* linesFromEnd(file) {
    const descriptor = fs.openSync(file, 'r');
    try {
        let position = fs.fstatSync(descriptor).size;
        let lineStart = Buffer.alloc(0);
        while (position > 0) {
            const size = Math.min(TRANSCRIPT_CHUNK_BYTES, position);
            position -= size;
            const chunk = Buffer.alloc(size);
            fs.readSync(descriptor, chunk, 0, size, position);

            const data = Buffer.concat([chunk, lineStart]);
            let end = data.length;
            while (end > 0) {
                const newline = data.lastIndexOf(0x0a, end - 1);
                if (newline < 0) {
                    break;
                }

                yield data.toString('utf8', newline + 1, end);
                end = newline;
            }

            lineStart = data.subarray(0, end);
        }

        yield lineStart.toString('utf8');
    } finally {
        fs.closeSync(descriptor);
    }
}

// Reads the transcript back from its end to the last typed prompt, so the time doesn't grow with the session.
// It skips a line that doesn't parse, like a last line that is only half written. Returns null when the file
// can't be read.
function turnUsedTools(transcriptPath) {
    try {
        for (const line of linesFromEnd(transcriptPath)) {
            let entry;
            try {
                entry = JSON.parse(line);
            } catch {
                continue;
            }

            if (!entry || typeof entry !== 'object') {
                continue;
            }

            if (toolEntry(entry)) {
                return true;
            }

            if (promptEntry(entry)) {
                return false;
            }
        }

        return false;
    } catch {
        return null;
    }
}

// Logs a missing close after a turn that used tools. The skill only has a close when work is pending, which the
// reply text doesn't show. So a reply of at most 3 lines without a list counts as a pure answer and is left alone.
function checkClose(plain, findings, transcriptPath) {
    const filled = filledLines(plain);
    const pureAnswer = filled.length <= MAX_ANSWER_LINES && !filled.some((line) => /^\s*([-*+]|\d+[.)])\s/.test(line));
    if (pureAnswer || !transcriptPath || turnUsedTools(transcriptPath) !== true) {
        return;
    }

    const labels = filled.slice(-2).filter((line) => /^\s*\p{L}+:\s/u.test(line)).length;
    if (labels < 2 && !filled.some((line) => /^\s*(State|Next):/.test(line))) {
        findings.push(soft('close', 'turn used tools, reply doesn\'t close on State and Next'));
    }
}

function hard(rule, detail) {
    return { rule, kind: 'hard', detail };
}

function soft(rule, detail) {
    return { rule, kind: 'soft', detail };
}

// The terse level is only ever saved in the user file, so the check reads it without the repo lookup. That lookup
// would start git at the end of every turn. The other scripts are loaded inside the functions and not at the top
// of the file, so a load error ends in the `catch` of the caller.
function check(event) {
    const { readUserKnobs } = require('../../work-ethic/scripts/knobs');
    const { flagFile } = require('./terse-reminder');
    const level = readUserKnobs(dataDir).terse;
    const message = event.last_assistant_message;
    if (!CHECKED_LEVELS.includes(level) || typeof message !== 'string' || !message.trim()) {
        return [];
    }

    const explain = readFile(flagFile(dataDir, event.session_id, 'terse-explain')) === '1';
    const lines = readLines(message);
    const plain = lines.filter((line) => !line.fenced).map((line) => line.text);
    const findings = [];

    const gated = checkGate(lines, findings, explain) || endsOnGo(plain);
    checkWording(plain, findings);
    checkCountLabels(plain, findings);
    if (!explain) {
        checkLength(plain, findings, level);
        if (!gated) {
            checkClose(plain, findings, event.transcript_path);
        }
    }

    return findings;
}

function log(findings, event) {
    if (!findings.length) {
        return;
    }

    const { flagFile } = require('./terse-reminder');

    const record = { time: new Date().toISOString(), check: 'reply', session_id: event.session_id, cwd: event.cwd };
    const lines = findings.map((finding) => JSON.stringify({ ...record, ...finding }) + '\n');
    fs.mkdirSync(dataDir, { recursive: true });
    fs.appendFileSync(path.join(dataDir, 'slips.jsonl'), lines.join(''));

    // terse-reminder.js prints these lines at the next prompt.
    const broken = findings.filter((finding) => finding.kind === 'hard').map((finding) => finding.detail);
    if (broken.length) {
        fs.writeFileSync(flagFile(dataDir, event.session_id, 'terse-slipped'), broken.join('\n'));
    }
}

let input = '';
process.stdin.setEncoding('utf8');
process.stdin.on('data', (chunk) => { input += chunk; });
process.stdin.on('end', () => {
    try {
        const event = JSON.parse(input);
        log(check(event), event);
    } catch {
        // A broken event or an unwritable log never fails the turn.
    }
});
