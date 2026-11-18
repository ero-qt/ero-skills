// Keeps the stage records of the work loop in .git/work-loop/ledger.jsonl, 1 JSON line per record.
// A record belongs to the commit in progress when its head is the current HEAD, so the records of earlier
// commits stay in the file but drop out of `show`. The file sits under .git, so it can't be staged.
//
// Usage:
//     node ledger.js add <stage> <proof>   add a record for the commit in progress
//     node ledger.js show                  print the records of the commit in progress
//     node ledger.js last                  print the newest record

const { execFileSync } = require('child_process');
const fs = require('fs');
const path = require('path');

const USAGE = 'Usage: node ledger.js add <stage> <proof> | show | last';

function git(cwd, ...args) {
    return execFileSync('git', args, { cwd, encoding: 'utf8', stdio: ['ignore', 'pipe', 'ignore'] }).trim();
}

// Returns the ledger path of the repo at cwd, or null when cwd isn't in a git repository.
// A worktree uses the ledger of its main repo.
function ledgerPath(cwd) {
    try {
        const common = git(cwd, 'rev-parse', '--path-format=absolute', '--git-common-dir');
        return path.join(common, 'work-loop', 'ledger.jsonl');
    } catch {
        return null;
    }
}

// Returns the hash of HEAD, or an empty string before the first commit.
function head(cwd) {
    try {
        return git(cwd, 'rev-parse', '--verify', '--quiet', 'HEAD');
    } catch {
        return '';
    }
}

function readRecords(cwd) {
    const file = ledgerPath(cwd);
    if (!file || !fs.existsSync(file)) {
        return [];
    }

    return fs.readFileSync(file, 'utf8').split(/\r?\n/).filter(Boolean).flatMap((line) => {
        try {
            return [JSON.parse(line)];
        } catch {
            return [];
        }
    });
}

// The `commit` record is written after the commit, so its head is the new HEAD. It belongs to the commit before.
function currentRecords(cwd) {
    const current = head(cwd);
    return readRecords(cwd).filter((record) => record.head === current && !isCommitOf(record, current));
}

function isCommitOf(record, hash) {
    const proof = String(record.proof).trim();
    return record.stage === 'commit' && proof.length >= 4 && hash.startsWith(proof);
}

function addRecord(cwd, stage, proof) {
    const file = ledgerPath(cwd);
    const record = { time: new Date().toISOString(), head: head(cwd), stage, proof };
    fs.mkdirSync(path.dirname(file), { recursive: true });
    fs.appendFileSync(file, JSON.stringify(record) + '\n');
    return record;
}

function format(record) {
    return `${record.stage}: ${record.proof}`;
}

// Returns the newest record with the commit it belongs to, or null when the ledger is empty.
function lastLine(cwd) {
    const last = readRecords(cwd).at(-1);
    return last ? `${last.head.slice(0, 7) || 'unborn'} ${format(last)}` : null;
}

function main(args) {
    const [command, stage, ...proofWords] = args;
    const proof = proofWords.join(' ').trim();
    const known = (command === 'add' && stage && proof) || (['show', 'last'].includes(command) && !stage);
    if (!known) {
        console.error(USAGE);
        return 1;
    }

    const cwd = process.cwd();
    if (!ledgerPath(cwd)) {
        console.error(`${cwd} isn't a git repository.`);
        return 1;
    }

    if (command === 'add') {
        console.log(format(addRecord(cwd, stage, proof)));
    } else if (command === 'show') {
        currentRecords(cwd).forEach((record) => console.log(format(record)));
    } else {
        const last = lastLine(cwd);
        if (last) {
            console.log(last);
        }
    }

    return 0;
}

module.exports = { addRecord, currentRecords, lastLine, ledgerPath, readRecords };

if (require.main === module) {
    process.exitCode = main(process.argv.slice(2));
}
