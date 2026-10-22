// Keeps the terse-replies level in effect for a whole session.
// `prompt` runs on UserPromptSubmit: it reads level commands from the prompt and prints a reminder of the level.
// `session` runs on SessionStart: it prints the same reminder, so the level comes back after a compaction.

const fs = require('fs');
const os = require('os');
const path = require('path');

const LEVELS = ['lite', 'full', 'ultra'];
const DEFAULT_LEVEL = 'full';
const SKILL = path.join(__dirname, '..', 'SKILL.md');

const mode = process.argv[2];
const dataDir = process.env.CLAUDE_PLUGIN_DATA || path.join(os.homedir(), '.claude');
const stateFile = path.join(dataDir, 'terse-level');

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

function print(eventName, level) {
    if (!LEVELS.includes(level)) {
        return;
    }

    const output = { hookSpecificOutput: { hookEventName: eventName, additionalContext: reminder(level) } };
    process.stdout.write(JSON.stringify(output));
}

let input = '';
process.stdin.on('data', (chunk) => { input += chunk; });
process.stdin.on('end', () => {
    if (mode === 'session') {
        print('SessionStart', readLevel());
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

    print('UserPromptSubmit', readLevel());
});
