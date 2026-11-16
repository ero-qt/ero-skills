// Counts the rules the hooks found broken, from slips.jsonl in the plugin data folder, per check and rule.
//
// Usage:
//     node status.js [--data <folder>] [--days <n>]    count the slips of the last n days, 7 by default

const fs = require('fs');
const os = require('os');
const path = require('path');

const DEFAULT_DAYS = 7;
const DAY_MS = 24 * 60 * 60 * 1000;
const USAGE = 'Usage: node status.js [--data <folder>] [--days <n>]';

function readArgs(argv) {
    const options = { days: DEFAULT_DAYS };
    for (let index = 0; index < argv.length; index++) {
        const arg = argv[index];
        if (arg === '--data' && argv[index + 1]) {
            options.data = argv[++index];
        } else if (arg === '--days' && /^[1-9]\d*$/.test(argv[index + 1] || '')) {
            options.days = Number(argv[++index]);
        } else {
            return null;
        }
    }

    return options;
}

function readSlips(file) {
    let text = '';
    try {
        text = fs.readFileSync(file, 'utf8');
    } catch {
        return [];
    }

    return text.split(/\r?\n/).filter(Boolean).flatMap((line) => {
        try {
            const slip = JSON.parse(line);
            return slip && typeof slip.rule === 'string' && !Number.isNaN(Date.parse(slip.time)) ? [slip] : [];
        } catch {
            return [];
        }
    });
}

function main(argv) {
    const options = readArgs(argv);
    if (!options) {
        console.error(USAGE);
        return 1;
    }

    const dataDir = options.data || process.env.CLAUDE_PLUGIN_DATA || path.join(os.homedir(), '.claude');
    const since = Date.now() - options.days * DAY_MS;
    const slips = readSlips(path.join(dataDir, 'slips.jsonl')).filter((slip) => Date.parse(slip.time) >= since);

    const counts = new Map();
    for (const slip of slips) {
        const label = `${slip.check || 'unknown'} ${slip.rule} (${slip.kind || 'unknown'})`;
        counts.set(label, (counts.get(label) || 0) + 1);
    }

    console.log(`slips in ${options.days} days: ${slips.length}`);
    [...counts].sort(([labelA, countA], [labelB, countB]) => countB - countA || labelA.localeCompare(labelB))
        .forEach(([label, count]) => console.log(`${label}: ${count}`));
    return 0;
}

process.exitCode = main(process.argv.slice(2));
