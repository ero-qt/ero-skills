// Checks each chat reply against the terse-replies rules on Stop and writes every broken rule to slips.jsonl in the
// plugin data folder. It never blocks the turn or sends anything back, because a long reply can be one the user wanted.
// Hard findings break a rule the skill states outright. Soft findings are worth a look.

const fs = require('fs');
const os = require('os');
const path = require('path');

const DEFAULT_LEVEL = 'full';
const CHECKED_LEVELS = ['full', 'ultra'];
const MAX_GATE_LINES = 12;
const MAX_BULLETS = 5;
const MAX_WORDS_PER_LINE_AT_ULTRA = 12;

const dataDir = process.env.CLAUDE_PLUGIN_DATA || path.join(os.homedir(), '.claude');

function readFile(name) {
    try {
        return fs.readFileSync(path.join(dataDir, name), 'utf8').trim();
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
    if (plain.some((line) => /[–—]| -- /.test(withoutInlineCode(line)))) {
        findings.push(hard('dash', 'em dash, en dash or -- outside code'));
    }

    const first = plain.find((line) => line.trim()) || '';
    if (/^\s*(you['’]?re (absolutely )?right|sorry|i apologi[sz]e|i['’]ll|let me)\b/i.test(first)) {
        findings.push(hard('opener', 'first line is validation, an apology or an announcement'));
    }

    const closing = plain.filter((line) => line.trim()).slice(-3).join('\n');
    if (/\b(let me know|happy to|want me to)\b/i.test(closing)) {
        findings.push(hard('closing-offer', 'reply ends on an offer'));
    }
}

function checkLength(plain, findings, level) {
    const bullets = plain.filter((line) => /^\s*[-*+]\s/.test(line)).length;
    if (bullets > MAX_BULLETS) {
        findings.push(soft('bullets', `${bullets} bullets, max ${MAX_BULLETS}`));
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

function promptEntry(entry) {
    if (entry.type !== 'user' || !entry.message) {
        return false;
    }

    const content = entry.message.content;
    return typeof content === 'string' || (Array.isArray(content) && !content.some((block) => block.type === 'tool_result'));
}

// Reads the transcript back to the last typed prompt. Returns null when the transcript doesn't parse.
function turnUsedTools(transcriptPath) {
    let entries;
    try {
        entries = fs.readFileSync(transcriptPath, 'utf8').split(/\r?\n/).filter(Boolean).map((line) => JSON.parse(line));
    } catch {
        return null;
    }

    const start = entries.map(promptEntry).lastIndexOf(true);
    return entries.slice(start + 1).some((entry) => entry.type === 'assistant'
        && Array.isArray(entry.message?.content)
        && entry.message.content.some((block) => block.type === 'tool_use'));
}

function checkClose(plain, findings, transcriptPath) {
    if (!transcriptPath || turnUsedTools(transcriptPath) !== true) {
        return;
    }

    const filled = plain.filter((line) => line.trim());
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

function check(event) {
    const level = readFile('terse-level') || DEFAULT_LEVEL;
    const message = event.last_assistant_message;
    if (!CHECKED_LEVELS.includes(level) || typeof message !== 'string' || !message.trim()) {
        return [];
    }

    const explain = readFile('terse-explain') === '1';
    const lines = readLines(message);
    const plain = lines.filter((line) => !line.fenced).map((line) => line.text);
    const findings = [];

    const gated = checkGate(lines, findings, explain);
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

function log(findings) {
    if (!findings.length) {
        return;
    }

    const time = new Date().toISOString();
    const lines = findings.map((finding) => JSON.stringify({ time, check: 'reply', ...finding }) + '\n');
    fs.mkdirSync(dataDir, { recursive: true });
    fs.appendFileSync(path.join(dataDir, 'slips.jsonl'), lines.join(''));

    // terse-hook.js prints the full reminder with these lines at the next prompt.
    const broken = findings.filter((finding) => finding.kind === 'hard').map((finding) => finding.detail);
    if (broken.length) {
        fs.writeFileSync(path.join(dataDir, 'terse-slipped'), broken.join('\n'));
    }
}

let input = '';
process.stdin.on('data', (chunk) => { input += chunk; });
process.stdin.on('end', () => {
    try {
        log(check(JSON.parse(input)));
    } catch {
        // A broken event or an unwritable log never fails the turn.
    }
});
