// Builds the terse-replies reminder that the prompt and session hooks of the work-ethic plugin print.
// reply-check.js writes the hard rules a reply broke to `terse-slipped`. The next prompt shows them once with the
// full reminder. A prompt like "explain ..." sets `terse-explain`, so reply-check.js leaves the length of that reply
// alone.

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

function asksForExplanation(prompt) {
    return /\b(explain|explanation|walk me through|in detail|elaborate)\b/i.test(prompt);
}

function writeExplainFlag(dataDir, prompt) {
    fs.mkdirSync(dataDir, { recursive: true });
    const file = path.join(dataDir, 'terse-explain');
    if (asksForExplanation(prompt)) {
        fs.writeFileSync(file, '1');
    } else {
        fs.rmSync(file, { force: true });
    }
}

// Returns the rules reply-check.js found broken in the last reply and clears them, so they come back only once.
function takeSlips(dataDir) {
    const file = path.join(dataDir, 'terse-slipped');
    try {
        const slips = fs.readFileSync(file, 'utf8').trim();
        fs.rmSync(file, { force: true });
        return slips ? slips.split(/\r?\n/) : [];
    } catch {
        return [];
    }
}

// Returns the full reminder with the broken rules after a reply that broke one. Returns an empty string otherwise.
function promptReminder(dataDir, level) {
    const slips = takeSlips(dataDir);
    const text = reminder(level);
    return slips.length && text ? `${text} Last reply broke: ${slips.join(', ')}.` : '';
}

module.exports = { promptReminder, reminder, writeExplainFlag };
