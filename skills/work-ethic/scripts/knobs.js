// Saves and reads the knobs. A knob is a choice of the user about how the skills work, like the loop level.
// The user file `knobs.json` in the plugin data folder has the user's defaults and the terse level.
// The repo file `.git/work-loop/knobs.json` wins over it. Autonomy lasts for 1 session, so it goes in `session.json`
// with the session id and never in a knobs file.
//
// Usage:
//     node knobs.js prompt                    UserPromptSubmit hook: saves the knob phrases of the prompt.
//                                             It prints the knobs in 1 line when the prompt changed one
//                                             and the broken terse rules after a reply that broke some.
//                                             Any other prompt prints nothing
//     node knobs.js session                   SessionStart hook: prints the full terse rules and the knobs.
//                                             After a compaction it also prints what to reload. After a
//                                             compaction, a resume or a fork it prints the house brief
//                                             and the newest ledger record. Auto mode ends at any session
//                                             start but a compaction
//     node knobs.js show [--json]             print the knobs in effect
//     node knobs.js set <knob> <value> [--user]
//                                             save a knob for this repo, or for every repo with --user
// Each command takes --data <folder> in place of CLAUDE_PLUGIN_DATA and --session <id> for the session's autonomy.

const fs = require('fs');
const os = require('os');
const path = require('path');
const { promptReminder, reminder, writeExplainFlag } = require('../../terse-replies/scripts/terse-reminder');
const { lastLine, ledgerPath } = require('../../work-loop/scripts/ledger');

const EFFORTS = ['low', 'medium', 'high', 'xhigh', 'max'];
const MODEL_KNOBS = ['review-model', 'plan-model', 'impl-model'];
const SESSION_MODEL = 'session model';
const USAGE = 'Usage: node knobs.js [--data <folder>] [--session <id>] prompt | session | show [--json] '
    + '| set <knob> <value> [--user]';

// The order of this table is the order of the knob line.
const KNOBS = {
    terse: { values: ['off', 'lite', 'full', 'ultra'], default: 'full' },
    loop: { values: ['light', 'standard', 'strict'], default: 'standard' },
    autonomy: { values: ['gated', 'auto'], default: 'gated' },
    docs: { values: ['repo', 'on', 'off'], default: 'repo' },
    issues: { values: ['house', 'after-code', 'never'], default: 'house' },
    narrate: { values: ['silent', 'milestones'], default: 'silent' },
    'review-model': { default: SESSION_MODEL },
    'plan-model': { default: SESSION_MODEL },
    'impl-model': { default: SESSION_MODEL },
    worktrees: { values: ['off', 'parallel'], default: 'off' },
    cleanup: { values: ['ask', 'auto'], default: 'ask' },
};
const ALWAYS_SHOWN = ['terse', 'loop', 'autonomy'];
const RELOAD_ORDER = ['terse-replies', 'repo-writing', 'code-comments', 'work-loop'];

function defaults() {
    return Object.fromEntries(Object.entries(KNOBS).map(([name, knob]) => [name, knob.default]));
}

// Returns the value as saved, or null when the knob doesn't take it. A model knob takes a model and an effort.
function validValue(name, words) {
    const knob = KNOBS[name];
    if (!knob || !words.length) {
        return null;
    }

    if (MODEL_KNOBS.includes(name)) {
        const [model, effort, ...rest] = words;
        const valid = /^[\w.:[\]-]+$/.test(model) && !rest.length && (!effort || EFFORTS.includes(effort.toLowerCase()));
        return valid ? words.join(' ') : null;
    }

    const value = words.join(' ').toLowerCase();
    return knob.values.includes(value) ? value : null;
}

// Finds the knobs a prompt sets. A terse phrase counts anywhere in the prompt, as in the terse-replies skill.
// Any other phrase has to be a line of its own, because words like "docs on" turn up in normal requests.
// `auto on` has to be the whole prompt, because a subagent report or a message from another session also
// comes in as a prompt.
function findChanges(prompt) {
    const changes = {};
    const text = prompt.toLowerCase();
    if (/\b(normal replies|stop terse)\b/.test(text)) {
        changes.terse = 'off';
    }

    const terse = text.match(/\bterse (lite|full|ultra)\b/);
    if (terse) {
        changes.terse = terse[1];
    }

    const lines = prompt.trim().split(/\r?\n/);
    for (const line of lines) {
        const words = line.trim().replace(/[.!]+$/, '').split(/\s+/).filter(Boolean);
        if (words.length < 2) {
            continue;
        }

        const phrase = words.join(' ').toLowerCase();
        if (phrase === 'auto off' || (phrase === 'auto on' && lines.length === 1)) {
            changes.autonomy = phrase === 'auto on' ? 'auto' : 'gated';
            continue;
        }

        const name = words[0].toLowerCase();
        const value = name !== 'terse' && validValue(name, words.slice(1));
        if (value) {
            changes[name] = value;
        }
    }

    return changes;
}

function readJson(file) {
    try {
        const value = JSON.parse(fs.readFileSync(file, 'utf8'));
        return value && typeof value === 'object' && !Array.isArray(value) ? value : {};
    } catch {
        return {};
    }
}

function writeJson(file, value) {
    fs.mkdirSync(path.dirname(file), { recursive: true });
    fs.writeFileSync(file, JSON.stringify(value, null, 2) + '\n');
}

function repoFile(cwd) {
    const ledger = ledgerPath(cwd);
    return ledger && path.join(path.dirname(ledger), 'knobs.json');
}

// Drops the names and values a file can't set, so a broken file can't break the knob line.
function known(values) {
    return Object.fromEntries(Object.entries(values)
        .filter(([name, value]) => name !== 'autonomy' && typeof value === 'string'
            && validValue(name, value.split(/\s+/).filter(Boolean)) !== null));
}

function readKnobs({ dataDir, cwd, session }) {
    const repo = repoFile(cwd);
    const knobs = { ...defaults(), ...known(readJson(path.join(dataDir, 'knobs.json'))), ...known(repo ? readJson(repo) : {}) };
    const saved = readJson(path.join(dataDir, 'session.json'));
    if (session && saved.session === session && KNOBS.autonomy.values.includes(saved.autonomy)) {
        knobs.autonomy = saved.autonomy;
    }

    return knobs;
}

// Terse is a chat setting, so it goes in the user file. Autonomy goes with the session. The rest go in the repo
// file. Outside a repo or with `user` they go in the user file.
function saveKnobs(changes, { dataDir, cwd, session, user }) {
    for (const [name, value] of Object.entries(changes)) {
        if (name === 'autonomy') {
            writeJson(path.join(dataDir, 'session.json'), { session: session || '', autonomy: value });
            continue;
        }

        const repo = !user && name !== 'terse' && repoFile(cwd);
        const file = repo || path.join(dataDir, 'knobs.json');
        writeJson(file, { ...readJson(file), [name]: value });
    }
}

function knobLine(knobs) {
    const parts = Object.keys(KNOBS)
        .filter((name) => ALWAYS_SHOWN.includes(name) || knobs[name] !== KNOBS[name].default)
        .map((name) => (name === 'autonomy' ? knobs[name] : `${name} ${knobs[name]}`));
    return `knobs: ${parts.join(', ')}`;
}

function readArgs(argv) {
    const options = { words: [] };
    for (let index = 0; index < argv.length; index++) {
        const arg = argv[index];
        if (arg === '--data' || arg === '--session') {
            options[arg.slice(2)] = argv[++index];
        } else if (arg === '--user' || arg === '--json') {
            options[arg.slice(2)] = true;
        } else {
            options.words.push(arg);
        }
    }

    return options;
}

function dataDirOf(options) {
    return options.data || process.env.CLAUDE_PLUGIN_DATA || path.join(os.homedir(), '.claude');
}

function readEvent(input) {
    try {
        const event = JSON.parse(input);
        return event && typeof event === 'object' ? event : {};
    } catch {
        return {};
    }
}

// Prints nothing when every line is empty, because each printed character goes into the context of the model.
function print(eventName, lines) {
    const text = lines.filter(Boolean).join('\n');
    if (text) {
        const output = { hookEventName: eventName, additionalContext: text };
        process.stdout.write(JSON.stringify({ hookSpecificOutput: output }));
    }
}

// The session start already printed the knobs, so the knob line only comes back when the prompt changed a knob.
function runPrompt(context, event) {
    const prompt = typeof event.prompt === 'string' ? event.prompt : '';
    const changes = findChanges(prompt);
    let slipped = '';
    try {
        saveKnobs(changes, context);
        writeExplainFlag(context.dataDir, context.session, prompt);
        slipped = promptReminder(context.dataDir, context.session, readKnobs(context).terse);
    } catch {
        // An unwritable file never fails the prompt.
    }

    print('UserPromptSubmit', [Object.keys(changes).length ? knobLine(readKnobs(context)) : '', slipped]);
}

function resumeLines(cwd) {
    const repo = repoFile(cwd);
    const house = repo && path.join(path.dirname(repo), 'house.md');
    const last = repo && lastLine(cwd);
    return [
        house && fs.existsSync(house) ? `house brief: read ${house} before the next action` : '',
        last ? `ledger: ${last}` : '',
    ];
}

// Auto mode lasts for 1 stretch of work, so it ends at any session start but a compaction.
function endAuto({ dataDir, session }) {
    const file = path.join(dataDir, 'session.json');
    if (session && readJson(file).session === session) {
        fs.rmSync(file, { force: true });
    }
}

function runSession(context, event) {
    if (event.source !== 'compact') {
        try {
            endAuto(context);
        } catch {
            // An unwritable file never fails the session start.
        }
    }

    const knobs = readKnobs(context);
    const lines = [reminder(knobs.terse), knobLine(knobs)];
    if (event.source === 'compact') {
        lines.push(`reload: ${RELOAD_ORDER.join(', ')}`);
    }
    if (['compact', 'resume', 'fork'].includes(event.source)) {
        lines.push(...resumeLines(context.cwd));
    }

    print('SessionStart', lines);
}

function runHook(mode, options, input) {
    const event = readEvent(input);
    const context = { dataDir: dataDirOf(options), cwd: event.cwd || process.cwd(), session: event.session_id };
    if (mode === 'prompt') {
        runPrompt(context, event);
    } else {
        runSession(context, event);
    }
}

function main(argv) {
    const options = readArgs(argv);
    const [command, ...rest] = options.words;
    const context = { dataDir: dataDirOf(options), cwd: process.cwd(), session: options.session, user: options.user };

    if (command === 'show' && !rest.length) {
        const knobs = readKnobs(context);
        console.log(options.json ? JSON.stringify(knobs, null, 2) : knobLine(knobs));
        return 0;
    }

    if (command === 'set' && rest.length >= 2) {
        const [name, ...words] = rest;
        if (name === 'autonomy') {
            console.error('autonomy only changes when the user says "auto on" or "auto off" in the chat.');
            return 1;
        }

        const value = validValue(name, words);
        if (value === null) {
            const knob = KNOBS[name];
            const values = !knob ? `Knobs: ${Object.keys(KNOBS).join(', ')}.`
                : knob.values ? `Values: ${knob.values.join(', ')}.` : `Values: <model> [${EFFORTS.join('|')}].`;
            console.error(`${name} doesn't take "${words.join(' ')}". ${values}`);
            return 1;
        }

        saveKnobs({ [name]: value }, context);
        console.log(knobLine(readKnobs(context)));
        return 0;
    }

    console.error(USAGE);
    return 1;
}

module.exports = { findChanges, knobLine, readKnobs, saveKnobs };

if (require.main === module) {
    const options = readArgs(process.argv.slice(2));
    if (options.words.length === 1 && ['prompt', 'session'].includes(options.words[0])) {
        let input = '';
        process.stdin.on('data', (chunk) => { input += chunk; });
        process.stdin.on('end', () => runHook(options.words[0], options, input));
    } else {
        process.exitCode = main(process.argv.slice(2));
    }
}
