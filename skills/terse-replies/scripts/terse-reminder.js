// Builds the terse-replies reminder that the prompt and session hooks of the work-ethic plugin print.
// reply-check.js writes the hard rules a reply broke to `terse-slipped`. The next prompt shows them once in 1 short
// line. A prompt like "explain ..." sets `terse-explain`, so reply-check.js leaves the length of that reply alone.
// Each session has its own 2 flag files, so a flag never counts in another session.

const fs = require('fs');
const path = require('path');

const LEVELS = ['lite', 'full', 'ultra'];
const SKILL = path.join(__dirname, '..', 'SKILL.md');

// Reads the level's description from the levels table in SKILL.md, so the reminder can't drift from the skill.
function describeLevel(level) {
    const skill = fs.readFileSync(SKILL, 'utf8');
    const row = skill.split(/\r?\n/).find((line) => line.startsWith(`| "terse ${level}" |`));
    return row ? row.split('|')[3].trim() : '';
}

// Returns an empty string when terse is off.
function reminder(level) {
    if (!LEVELS.includes(level)) {
        return '';
    }

    return `TERSE ${level.toUpperCase()} for every reply, from the terse-replies skill: ${describeLevel(level)} `
        + 'First line is the answer. No text between tool calls. Close with State: and Next:, '
        + 'or with the open work-loop gate line.';
}

// Returns the path of a flag file of 1 session. The session id goes in the file name with only letters, digits,
// `_` and `-`, so it can't point outside the data folder.
function flagFile(dataDir, session, name) {
    const id = typeof session === 'string' ? session.replace(/[^\w-]/g, '_') : '';
    return path.join(dataDir, id ? `${name}-${id}` : name);
}

function asksForExplanation(prompt) {
    return /\b(explain|explanation|walk me through|in detail|elaborate)\b/i.test(prompt);
}

function writeExplainFlag(dataDir, session, prompt) {
    fs.mkdirSync(dataDir, { recursive: true });
    const file = flagFile(dataDir, session, 'terse-explain');
    if (asksForExplanation(prompt)) {
        fs.writeFileSync(file, '1');
    } else {
        fs.rmSync(file, { force: true });
    }
}

// Returns the rules reply-check.js found broken in the last reply and clears them, so they come back only once.
function takeSlips(dataDir, session) {
    const file = flagFile(dataDir, session, 'terse-slipped');
    try {
        const slips = fs.readFileSync(file, 'utf8').trim();
        fs.rmSync(file, { force: true });
        return slips ? slips.split(/\r?\n/) : [];
    } catch {
        return [];
    }
}

// Returns the broken rules in 1 line after a reply that broke some. Returns an empty string otherwise.
// The full rules stay out, because the session start already gave them.
function promptReminder(dataDir, session, level) {
    const slips = takeSlips(dataDir, session);
    return slips.length && LEVELS.includes(level) ? `Last reply broke: ${slips.join(', ')}.` : '';
}

module.exports = { flagFile, promptReminder, reminder, writeExplainFlag };
