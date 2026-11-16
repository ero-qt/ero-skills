// Runs on PreToolUse before Bash or PowerShell runs a `git commit` and denies the commit when:
// - the same command stages files, since the checks read the index before the command runs,
// - the message has a trailer,
// - the prose check finds a hard rule broken in the staged lines or the message,
// - a staged path is one that must never be staged,
// - at loop strict, source changed without a doc change and the ledger doesn't have a reason for that.
// Below strict the docs finding only warns Claude. Prose findings in staged text that the ledger keeps also warn.
// Every finding goes to slips.jsonl in the plugin data folder.
// A clean commit gets no output and goes through the normal permission prompt.

const { spawnSync } = require('child_process');
const fs = require('fs');
const os = require('os');
const path = require('path');
const { currentRecords, ledgerPath } = require('./ledger');

const CHECKED_TOOLS = ['Bash', 'PowerShell'];
const COMMIT_STAGING_FLAGS = ['all', 'include', 'interactive', 'only', 'patch', 'pathspec-from-file'];
const COMMIT_VALUE_FLAGS = ['author', 'cleanup', 'date', 'file', 'fixup', 'message', 'reedit-message',
    'reuse-message', 'squash', 'template', 'trailer'];
const DEFAULT_KNOBS = { docs: 'repo', loop: 'standard' };
const GIT_VALUE_OPTIONS = ['-c', '--config-env', '--git-dir', '--namespace'];
const NEVER_STAGE = ['.env', '.claude/settings.local.json'];
const LEDGER_SCRIPT = path.join(__dirname, 'ledger.js');
const PREFIX_WORDS = ['!', '{', 'command', 'do', 'elif', 'else', 'exec', 'if', 'nohup', 'then', 'time', 'until',
    'while'];
const PROSE_CHECK = path.join(__dirname, '..', '..', 'repo-writing', 'scripts', 'prose_check.py');
const PYTHON = process.platform === 'win32' ? 'python' : 'python3';
const STAGING_SUBCOMMANDS = ['add', 'mv', 'rm', 'stage'];
const TRAILER = /^\s*(co-authored-by|signed-off-by):|generated with \[?claude|\u{1F916}/imu;

const CHANGELOG = /^(changelog|changes|history)(\.(md|markdown|rst|txt))?$/i;
const DOC = /\.(md|markdown|rst|adoc)$|^docs?\//i;
const TEST = /(^|\/)(tests?|__tests__|specs?)\/|(^|\/)[^/]+\.Tests?\/|(^|\/)(test_[^/]*|[^/]*_test\.[^/.]+|[^/]*\.(test|spec)\.[^/.]+)$/i;
const CI = /^\.github\/|^\.circleci\/|^\.gitlab-ci\.ya?ml$|^azure-pipelines\.ya?ml$/i;
const NO_DOCS = /(^|\/)(\.[^/]+|[^/]*[.-]lock(\.json|\.ya?ml)?|go\.sum|(licen[cs]e|copying)(\.[^/]*)?)$/i;

const dataDir = process.env.CLAUDE_PLUGIN_DATA || path.join(os.homedir(), '.claude');

function git(cwd, ...args) {
    const result = spawnSync('git', args, { cwd, encoding: 'utf8', maxBuffer: 64 * 1024 * 1024, timeout: 30000 });
    return result.status === 0 ? result.stdout : null;
}

// Splits a command into words and operators the way Bash or PowerShell does, close enough to find a commit in it.
// A Bash heredoc body goes to the `heredocs` list of the command it belongs to.
function parseCommands(text, powershell) {
    const commands = [{ words: [], heredocs: [] }];
    const escape = powershell ? '`' : '\\';
    let word = null;
    let pendingHeredocs = [];
    let substitutions = 0;
    let i = 0;

    const current = () => commands[commands.length - 1];
    const append = (value) => {
        word = (word || '') + value;
    };
    const endWord = () => {
        if (word !== null) {
            current().words.push(word);
            word = null;
        }
    };
    const endCommand = () => {
        endWord();
        commands.push({ words: [], heredocs: [] });
    };

    while (i < text.length) {
        const char = text[i];
        if (char === '\n') {
            endWord();
            const owner = current();
            i++;
            for (const delimiter of pendingHeredocs) {
                const lines = [];
                while (i < text.length) {
                    let end = text.indexOf('\n', i);
                    end = end < 0 ? text.length : end;
                    const line = text.slice(i, end);
                    i = end + 1;
                    if (line.replace(/^\t+/, '').trim() === delimiter) {
                        break;
                    }
                    lines.push(line);
                }
                owner.heredocs.push(lines.join('\n'));
            }
            pendingHeredocs = [];
            endCommand();
        } else if (/\s/.test(char)) {
            endWord();
            i++;
        } else if (text.startsWith('&&', i) || text.startsWith('||', i)) {
            endCommand();
            i += 2;
        } else if (char === ';' || char === '|' || char === '&') {
            endCommand();
            i++;
        } else if (char === '(' && word !== null && word.endsWith('$')) {
            append(char);
            substitutions++;
            i++;
        } else if (char === ')' && substitutions > 0) {
            append(char);
            substitutions--;
            i++;
        } else if (char === '(' || char === ')') {
            endCommand();
            i++;
        } else if (!powershell && text.startsWith('<<', i)) {
            endWord();
            const match = text.slice(i).match(/^<<-?\s*(['"]?)([\w.-]+)\1/);
            if (match) {
                pendingHeredocs.push(match[2]);
                i += match[0].length;
            } else {
                i += 2;
            }
        } else if (powershell && word === null && /^@['"]\r?\n/.test(text.slice(i, i + 4))) {
            const start = text.indexOf('\n', i) + 1;
            const close = text.slice(start).match(new RegExp(`(^|\\r?\\n)${text[i + 1]}@`));
            const end = close ? start + close.index : text.length;
            append(text.slice(start, end));
            i = close ? end + close[0].length : text.length;
        } else if (char === "'") {
            i++;
            while (i < text.length) {
                if (text[i] !== "'") {
                    append(text[i++]);
                } else if (powershell && text[i + 1] === "'") {
                    append("'");
                    i += 2;
                } else {
                    break;
                }
            }
            append('');
            i++;
        } else if (char === '"') {
            i++;
            while (i < text.length) {
                if (powershell && text.startsWith('""', i)) {
                    append('"');
                    i += 2;
                } else if (text[i] === '"') {
                    break;
                } else if (text[i] === escape && i + 1 < text.length && (powershell || '"\\$`'.includes(text[i + 1]))) {
                    append(text[i + 1]);
                    i += 2;
                } else {
                    append(text[i++]);
                }
            }
            append('');
            i++;
        } else if (char === escape && i + 1 < text.length) {
            if (text[i + 1] !== '\n') {
                append(text[i + 1]);
            }
            i += 2;
        } else {
            append(char);
            i++;
        }
    }

    endWord();
    return commands.filter((command) => command.words.length);
}

// Drops the words in front of the command itself, like `VAR=1`, `env -i`, `{`, `then` or `while`.
function commandWords(words) {
    let index = 0;
    let afterEnv = false;
    while (index < words.length) {
        const item = words[index];
        if (item === 'env') {
            afterEnv = true;
        } else if (!PREFIX_WORDS.includes(item) && !/^\w+=/.test(item) && !(afterEnv && item.startsWith('-'))) {
            break;
        }
        index++;
    }

    return words.slice(index);
}

// Returns the folder, subcommand and arguments of a git command. Returns null for any other command.
function readGitCall(args, dir) {
    if (!/(^|[\\/])git(\.exe)?$/i.test(args[0] || '')) {
        return null;
    }

    let index = 1;
    let gitDir = dir;
    while (index < args.length && args[index].startsWith('-')) {
        const option = args[index];
        const workTree = option.match(/^--work-tree=(.+)$/s);
        if ((option === '-C' || option === '--work-tree') && args[index + 1]) {
            gitDir = path.resolve(gitDir, args[index + 1]);
            index += 2;
        } else if (workTree) {
            gitDir = path.resolve(gitDir, workTree[1]);
            index++;
        } else if (GIT_VALUE_OPTIONS.includes(option)) {
            index += 2;
        } else {
            index++;
        }
    }

    return { dir: gitDir, subcommand: args[index], args: args.slice(index + 1) };
}

// Returns the first `git commit` in the command. Returns null when it doesn't commit. `staging` lists what stages
// files in the same command, since the guard reads the index before any of the command runs.
function findCommit(text, powershell, cwd) {
    let dir = cwd;
    const staging = [];
    for (const { words, heredocs } of parseCommands(text, powershell)) {
        const args = commandWords(words);
        if (/^(cd|set-location|pushd)$/i.test(args[0] || '') && args[1]) {
            dir = path.resolve(dir, args[1]);
            continue;
        }

        const call = readGitCall(args, dir);
        if (call && STAGING_SUBCOMMANDS.includes(call.subcommand)) {
            staging.push(`git ${call.subcommand}`);
        } else if (call && call.subcommand === 'commit') {
            const commit = readCommitArgs(call.args, heredocs, call.dir);
            return { ...commit, dir: call.dir, staging: staging.concat(commit.staging) };
        }
    }

    return null;
}

// Reads the message of `git commit` from -m, --message, -F and --file. Also lists the flags and paths
// that stage files and notes --signoff. Short flags can come joined, like -qm. `-F -` reads the heredoc.
function readCommitArgs(args, heredocs, dir) {
    const parts = [];
    const staging = [];
    let hasMessage = false;
    let signoff = false;
    const readFile = (name) => {
        if (name === '-') {
            parts.push(...heredocs);
            return;
        }

        try {
            parts.push(fs.readFileSync(path.resolve(dir, name), 'utf8'));
        } catch {
            // A message file that can't be read is git's problem to report.
        }
    };
    const takeValue = (flag, value) => {
        if (flag === 'm' || flag === 'message') {
            hasMessage = true;
            parts.push(value);
        } else if (flag === 'F' || flag === 'file') {
            hasMessage = true;
            readFile(value);
        }
    };

    for (let index = 0; index < args.length; index++) {
        const arg = args[index];
        const long = arg.match(/^--([^=]+)(?:=(.*))?$/s);
        if (arg === '--') {
            if (index + 1 < args.length) {
                staging.push('a path after the commit flags');
            }
            break;
        } else if (long) {
            const [, flag, joined] = long;
            if (COMMIT_STAGING_FLAGS.includes(flag)) {
                staging.push(`--${flag}`);
            } else if (flag === 'signoff') {
                signoff = true;
            } else if (COMMIT_VALUE_FLAGS.includes(flag)) {
                takeValue(flag, joined !== undefined ? joined : args[++index] || '');
            }
        } else if (/^-[^-]/.test(arg)) {
            for (let at = 1; at < arg.length; at++) {
                const flag = arg[at];
                if ('aiop'.includes(flag)) {
                    staging.push(`-${flag}`);
                } else if (flag === 's') {
                    signoff = true;
                } else if ('mFCct'.includes(flag)) {
                    takeValue(flag, arg.slice(at + 1) || args[++index] || '');
                    break;
                } else if ('uS'.includes(flag)) {
                    break;
                }
            }
        } else {
            staging.push('a path after the commit flags');
        }
    }

    return { message: parts.join('\n\n'), hasMessage, signoff, staging };
}

function readJson(file) {
    try {
        return JSON.parse(fs.readFileSync(file, 'utf8'));
    } catch {
        return {};
    }
}

// The repo's knobs win over the user's defaults.
function readKnobs(workLoopDir) {
    return {
        ...DEFAULT_KNOBS,
        ...readJson(path.join(dataDir, 'knobs.json')),
        ...readJson(path.join(workLoopDir, 'knobs.json')),
    };
}

function globToRegex(glob) {
    return glob.split(/(\*\*|\*|\?)/).map((part) => {
        if (part === '**') {
            return '.*';
        }
        if (part === '*') {
            return '[^/]*';
        }
        if (part === '?') {
            return '[^/]';
        }
        return part.replace(/[.+^${}()|[\]\\]/g, '\\$&');
    }).join('');
}

// A pattern ending in `/` matches a folder and everything in it. A pattern without a `/` matches a file or
// folder name at any depth. Any other pattern matches from the repo root.
function matchesPattern(name, pattern) {
    const folder = pattern.endsWith('/');
    const trimmed = pattern.replace(/^\/|\/$/g, '');
    const anchored = trimmed.includes('/');
    const prefix = anchored ? '^' : '(^|/)';
    const suffix = folder ? '/' : '(/|$)';
    return new RegExp(prefix + globToRegex(trimmed) + suffix).test(name);
}

function readNeverStage(workLoopDir) {
    let lines = [];
    try {
        lines = fs.readFileSync(path.join(workLoopDir, 'never-stage'), 'utf8').split(/\r?\n/);
    } catch {
        // The repo doesn't add any paths of its own.
    }

    return NEVER_STAGE.concat(lines.map((line) => line.trim()).filter((line) => line && !line.startsWith('#')));
}

// Runs prose_check.py and returns its hard findings. Returns an empty list when Python or the script is missing.
function proseCheck(dir, args, where) {
    if (!fs.existsSync(PROSE_CHECK)) {
        return [];
    }

    const env = { ...process.env, PYTHONIOENCODING: 'utf-8' };
    const result = spawnSync(PYTHON, [PROSE_CHECK, ...args], { cwd: dir, encoding: 'utf8', env, timeout: 30000 });
    if (result.error || typeof result.stdout !== 'string') {
        return [];
    }

    return result.stdout.split(/\r?\n/)
        .filter((line) => /:\d+: hard: /.test(line))
        .map((line) => (where ? line.replace(/^<text>/, where) : line));
}

// True when the ledger has a record like `docs: none: <reason>` for the commit in progress.
function hasLedgerReason(dir, stage, label) {
    const proof = new RegExp(`^${label}:\\s*\\S`);
    return currentRecords(dir).some((record) => record.stage === stage && proof.test(record.proof));
}

function docsOn(knobs, dir) {
    if (knobs.docs === 'on' || knobs.docs === 'off') {
        return knobs.docs === 'on';
    }

    const names = git(dir, 'ls-files', '--full-name', '--', ':(top,icase,glob)changelog*', ':(top,icase,glob)changes*',
        ':(top,icase,glob)history*');
    return (names || '').split(/\r?\n/).some((name) => CHANGELOG.test(name));
}

function check(event) {
    const command = event.tool_input && event.tool_input.command;
    if (!CHECKED_TOOLS.includes(event.tool_name) || typeof command !== 'string') {
        return [];
    }

    const commit = findCommit(command, event.tool_name === 'PowerShell', event.cwd || process.cwd());
    const ledger = commit && ledgerPath(commit.dir);
    if (!ledger) {
        return [];
    }

    const { dir, message } = commit;
    const workLoopDir = path.dirname(ledger);
    const findings = [];
    if (commit.staging.length) {
        const what = [...new Set(commit.staging)].join(', ');
        findings.push(hard('staging', `${what} stages files in the same command as the commit, so the checks `
            + 'below read an index that is about to change. Stage by path first, then commit in its own command.'));
    }

    // The whole command only counts when the message flag has a value the parser can't read, like `-m $msg`.
    const unread = commit.hasMessage && !message.trim();
    const trailer = commit.signoff || TRAILER.test(message) || (unread && TRAILER.test(command));
    if (trailer) {
        findings.push(hard('trailer', 'the commit message has a Co-Authored-By, Signed-off-by or generated-with line'));
    }

    // A ledger reason keeps someone else's text in staged files, like a license. The message is always new text.
    const keep = hasLedgerReason(dir, 'prose', 'keep');
    const stagedProse = proseCheck(dir, ['--staged']);
    const hint = keep ? undefined : 'When the staged text belongs to someone else and has to stay, record why: '
        + `node "${LEDGER_SCRIPT}" add prose "keep: <reason>"`;
    for (const line of stagedProse) {
        findings.push({ rule: 'prose check', kind: keep ? 'soft' : 'hard', detail: line, hint });
    }

    const messageProse = message.trim() ? proseCheck(dir, ['--text', message], 'message') : [];
    for (const line of trailer ? messageProse.filter((item) => !/: hard: trailer:/.test(item)) : messageProse) {
        findings.push(hard('prose check', line));
    }

    const staged = (git(dir, 'diff', '--cached', '--name-only', '-z') || '').split('\0').filter(Boolean);
    const patterns = readNeverStage(workLoopDir);
    for (const name of staged.filter((item) => patterns.some((pattern) => matchesPattern(item, pattern)))) {
        findings.push(hard('never-stage', name));
    }

    const knobs = readKnobs(workLoopDir);
    const source = staged.filter((name) => !DOC.test(name) && !CHANGELOG.test(path.posix.basename(name))
        && !TEST.test(name) && !CI.test(name) && !NO_DOCS.test(name));
    const docStaged = staged.some((name) => DOC.test(name) || CHANGELOG.test(path.posix.basename(name)));
    if (source.length && !docStaged && docsOn(knobs, dir) && !hasLedgerReason(dir, 'docs', 'none')) {
        const detail = 'source changed and no doc is staged. Stage the changelog, readme or agents file change, '
            + `or record why none is needed: node "${LEDGER_SCRIPT}" add docs "none: <reason>"`;
        findings.push({ rule: 'docs', kind: knobs.loop === 'strict' ? 'hard' : 'soft', detail });
    }

    return findings;
}

function hard(rule, detail) {
    return { rule, kind: 'hard', detail };
}

function log(findings) {
    try {
        const time = new Date().toISOString();
        fs.mkdirSync(dataDir, { recursive: true });
        fs.appendFileSync(path.join(dataDir, 'slips.jsonl'),
            findings.map(({ rule, kind, detail }) => JSON.stringify({ time, check: 'commit', rule, kind, detail }) + '\n')
                .join(''));
    } catch {
        // An unwritable log never blocks the commit decision.
    }
}

function respond(findings) {
    if (!findings.length) {
        return;
    }

    log(findings);
    const hints = new Set(findings.map((finding) => finding.hint).filter(Boolean));
    const lines = findings.map((finding) => `- ${finding.rule}: ${finding.detail}`).concat([...hints]);
    const output = { hookEventName: 'PreToolUse' };
    if (findings.some((finding) => finding.kind === 'hard')) {
        output.permissionDecision = 'deny';
        output.permissionDecisionReason = ['commit-guard denied this commit:', ...lines].join('\n');
    } else {
        output.additionalContext = ['commit-guard let this commit through with a warning:', ...lines].join('\n');
    }

    process.stdout.write(JSON.stringify({ hookSpecificOutput: output }));
}

let input = '';
process.stdin.on('data', (chunk) => { input += chunk; });
process.stdin.on('end', () => {
    let findings = [];
    try {
        findings = check(JSON.parse(input));
    } catch {
        // A broken event never fails the tool call.
    }

    respond(findings);
});
