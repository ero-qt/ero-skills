// Runs a workflow script with stand-ins for the workflow runtime, for the unit tests.
//
// Reads 1 JSON object from stdin: `script` (the path), `args` and `replies`, which maps an agent label to what the
// agent returns. A label missing from `replies` fails the call. A null reply stands for an agent that died.
// Prints 1 JSON object: `meta`, `result`, `calls` (the prompt and options of each agent call), `phases`, `logs`
// and `error`.

const fs = require('fs');

const input = JSON.parse(fs.readFileSync(0, 'utf8'));
const source = fs.readFileSync(input.script, 'utf8');

const metaMatch = source.match(/^export const meta = (\{[\s\S]*?^\})/m);
const meta = metaMatch ? new Function(`return ${metaMatch[1]}`)() : null;
const body = source.replace(/^export const meta =/m, 'const meta =');

const calls = [];
const phases = [];
const logs = [];
let currentPhase = null;

async function agent(prompt, options = {}) {
    calls.push({ prompt, ...options, phase: options.phase || currentPhase });
    if (!Object.hasOwn(input.replies, options.label)) {
        throw new Error(`no reply for agent ${options.label}`);
    }

    return structuredClone(input.replies[options.label]);
}

async function parallel(thunks) {
    return Promise.all(thunks.map((thunk) => thunk().catch(() => null)));
}

async function pipeline(items, ...stages) {
    return Promise.all(items.map(async (item, index) => {
        let value = item;
        try {
            for (const stage of stages) {
                value = await stage(value, item, index);
            }
            return value;
        } catch {
            return null;
        }
    }));
}

function phase(title) {
    currentPhase = title;
    phases.push(title);
}

function log(message) {
    logs.push(message);
}

// The runtime makes these throw, because a script that reads the clock or random numbers can't resume.
Date.now = () => {
    throw new Error('Date.now() is not available in a workflow');
};
Math.random = () => {
    throw new Error('Math.random() is not available in a workflow');
};

const AsyncFunction = Object.getPrototypeOf(async () => {}).constructor;
const run = new AsyncFunction('agent', 'parallel', 'pipeline', 'phase', 'log', 'args', 'budget', 'workflow', body);
const budget = { total: null, spent: () => 0, remaining: () => Infinity };

run(agent, parallel, pipeline, phase, log, input.args, budget, null).then(
    (result) => console.log(JSON.stringify({ meta, result, calls, phases, logs, error: null })),
    (error) => console.log(JSON.stringify({ meta, result: null, calls, phases, logs, error: String(error) })),
);
