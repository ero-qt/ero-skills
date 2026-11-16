// Keeps the terse-replies level in effect for a whole session.
// `prompt` runs on UserPromptSubmit: it reads level commands from the prompt, marks prompts like "explain ..."
// and prints the level in 1 line. After a reply that broke a hard rule it prints the full reminder instead.
// `session` runs on SessionStart: it prints the full reminder, so the rules come back after a compaction.

const fs = require('fs');
const os = require('os');
const path = require('path');

const LEVELS = ['lite', 'full', 'ultra'];
const DEFAULT_LEVEL = 'full';
const SKILL = path.join(__dirname, '..', 'SKILL.md');

const mode = process.argv[2];
const dataDir = process.env.CLAUDE_PLUGIN_DATA || path.join(os.homedir(), '.claude');
const stateFile = path.join(dataDir, 'terse-level');
const explainFile = path.join(dataDir, 'terse-explain');
const slipFile = path.join(dataDir, 'terse-slipped');

function readLevel() {
    try {
        return fs.readFileSync(stateFile, 'utf8').trim() || DEFAULT_LEVEL;
    } catch {
        return DEFAULT_LEVEL;
    }
}

function writeLevel(level) {
    fs.mkdirSync(dataDir, { recursive: true });
    fs.writeFileSync(stateFile, level);
}

// Finds the level a prompt switches to and returns null when the prompt doesn't switch.
function findCommand(prompt) {
    const text = prompt.toLowerCase();
    if (/\b(normal replies|stop terse)\b/.test(text)) {
        return 'off';
    }

    const match = text.match(/\bterse (lite|full|ultra)\b/);
    return match ? match[1] : null;
}

// The skill allows a full explanation for these prompts, so reply-check.js leaves their length alone.
function asksForExplanation(prompt) {
    return /\b(explain|explanation|walk me through|in detail|elaborate)\b/i.test(prompt);
}

function writeExplainFlag(explain) {
    fs.mkdirSync(dataDir, { recursive: true });
    if (explain) {
        fs.writeFileSync(explainFile, '1');
    } else {
        fs.rmSync(explainFile, { force: true });
    }
}

// Reads the level's description from the levels table in SKILL.md, so the reminder can't drift from the skill.
function describeLevel(level) {
    const skill = fs.readFileSync(SKILL, 'utf8');
    const row = skill.split(/\r?\n/).find((line) => line.startsWith(`| "terse ${level}" |`));
    return row ? row.split('|')[3].trim() : '';
}

function reminder(level) {
    return `TERSE ${level.toUpperCase()} for every reply, from the terse-replies skill: ${describeLevel(level)} `
        + 'First line is the answer. No text between tool calls. Close with State: and Next:, '
        + 'or with the open work-loop gate line.';
}

function shortReminder(level) {
    return `TERSE ${level.toUpperCase()} for every reply, from the terse-replies skill.`;
}

// Returns the rules reply-check.js found broken in the last reply and clears them, so they come back only once.
function takeSlips() {
    try {
        const slips = fs.readFileSync(slipFile, 'utf8').trim();
        fs.rmSync(slipFile, { force: true });
        return slips ? slips.split(/\r?\n/) : [];
    } catch {
        return [];
    }
}

function promptReminder(level) {
    const slips = takeSlips();
    return slips.length ? `${reminder(level)} Last reply broke: ${slips.join(', ')}.` : shortReminder(level);
}

function print(eventName, level, text) {
    if (!LEVELS.includes(level)) {
        return;
    }

    const output = { hookSpecificOutput: { hookEventName: eventName, additionalContext: text(level) } };
    process.stdout.write(JSON.stringify(output));
}

let input = '';
process.stdin.on('data', (chunk) => { input += chunk; });
process.stdin.on('end', () => {
    if (mode === 'session') {
        print('SessionStart', readLevel(), reminder);
        return;
    }

    const prompt = (() => {
        try {
            return JSON.parse(input).prompt || '';
        } catch {
            return '';
        }
    })();

    const command = findCommand(prompt);
    if (command) {
        writeLevel(command);
    }

    writeExplainFlag(asksForExplanation(prompt));

    print('UserPromptSubmit', readLevel(), promptReminder);
});
