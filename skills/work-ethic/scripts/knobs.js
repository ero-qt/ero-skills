// Saves and reads the knobs. A knob is a choice of the user about how the skills work, like the loop level.
// The user file `knobs.json` in the plugin data folder has the user's defaults and the terse level.
// The repo file `.git/work-loop/knobs.json` wins over it. Autonomy lasts for 1 session, so it goes in `session.json`
// with the session id and never in a knobs file.
//
// Usage:
//     node knobs.js prompt                    UserPromptSubmit hook: saves the knob phrases of the prompt
//                                             and prints the knobs in 1 line
//     node knobs.js show [--json]             print the knobs in effect
//     node knobs.js set <knob> <value> [--user]
//                                             save a knob for this repo, or for every repo with --user
// Each command takes --data <folder> in place of CLAUDE_PLUGIN_DATA and --session <id> for the session's autonomy.

const fs = require('fs');
const os = require('os');
const path = require('path');
const { ledgerPath } = require('../../work-loop/scripts/ledger');

const EFFORTS = ['low', 'medium', 'high', 'xhigh', 'max'];
const MODEL_KNOBS = ['review-model', 'plan-model', 'impl-model'];
const SESSION_MODEL = 'session model';
const USAGE = 'Usage: node knobs.js [--data <folder>] [--session <id>] prompt | show [--json] '
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

    for (const line of prompt.split(/\r?\n/)) {
        const words = line.trim().replace(/[.!]+$/, '').split(/\s+/).filter(Boolean);
        if (words.length < 2) {
            continue;
        }

        const first = words[0].toLowerCase();
        if (first === 'auto' && words.length === 2 && ['on', 'off'].includes(words[1].toLowerCase())) {
            changes.autonomy = words[1].toLowerCase() === 'on' ? 'auto' : 'gated';
            continue;
        }

        const model = first.match(/^(review|plan|impl)(-model)?$/);
        if (model && !model[2] && words[1].toLowerCase() === 'model') {
            words.splice(0, 2, `${model[1]}-model`);
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

function runPrompt(options, input) {
    let event = {};
    try {
        event = JSON.parse(input);
    } catch {
        // A broken event still gets the knob line.
    }

    const context = { dataDir: dataDirOf(options), cwd: event.cwd || process.cwd(), session: event.session_id };
    try {
        saveKnobs(findChanges(typeof event.prompt === 'string' ? event.prompt : ''), context);
    } catch {
        // An unwritable file never fails the prompt.
    }

    const output = { hookEventName: 'UserPromptSubmit', additionalContext: knobLine(readKnobs(context)) };
    process.stdout.write(JSON.stringify({ hookSpecificOutput: output }));
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
    if (options.words.length === 1 && options.words[0] === 'prompt') {
        let input = '';
        process.stdin.on('data', (chunk) => { input += chunk; });
        process.stdin.on('end', () => runPrompt(options, input));
    } else {
        process.exitCode = main(process.argv.slice(2));
    }
}
