export const meta = {
  name: 'commit-cycle',
  description: 'Run the agent stages of 1 work-loop commit and return their ledger records',
  whenToUse: 'A work-loop commit whose size and loop level call for stage agents. The driver runs the slice plan, state check, verify, gate and record itself.',
  phases: [
    { title: 'Plan', detail: 'research and plan the commit' },
    { title: 'Build', detail: 'failing tests, then the least code that passes' },
    { title: 'Harden', detail: 'adversarial tests, simplify, house style and docs' },
    { title: 'Review', detail: 'read-only review lenses, then a fix round' },
  ],
}

// args: subject, size, loop, spec, houseBrief, briefs (path of stage-briefs.md), ci (commands), base,
// models ({plan, review, impl}, each {model, effort}), plan (the driver's plan for a medium commit) and
// resumeNotes ({<stage>: note} for each stage that stopped). Returns {status, records} plus {stage, reason} on a stop.
// The script can't write files, so the driver writes each record to the ledger.

const SIZES = ['trivial', 'small', 'medium', 'large']
const LOOPS = ['light', 'standard', 'strict']

// The agent stages of the table in references/stages.md, by size. 'S' runs only at loop strict. A medium commit
// plans inline, so 'driver' means the driver passes its plan in args.plan.
const TABLE = {
  plan: ['', '', 'driver', 'yes'],
  red: ['', 'yes', 'yes', 'yes'],
  implement: ['yes', 'yes', 'yes', 'yes'],
  adversarial: ['', '', 'S', 'yes'],
  simplify: ['', 'S', 'yes', 'yes'],
  style: ['tools', 'yes', 'yes', 'yes'],
  docs: ['yes', 'yes', 'yes', 'yes'],
  review: ['', 'S', 'yes', 'yes'],
}

const text = { type: 'string' }
const flag = { type: 'boolean' }
const count = { type: 'integer', minimum: 0 }
const list = (items) => ({ type: 'array', items })
const filled = (items) => ({ ...list(items), minItems: 1 })
const object = (properties, required = Object.keys(properties)) => ({ type: 'object', properties, required })

const SCHEMAS = {
  plan: object({
    files: list(text),
    publicShape: text,
    tests: list(object({ name: text, pins: text })),
    risks: list(text),
    research: filled(object({ source: text, date: text, finding: text })),
  }),
  red: object({ command: text, tests: list(text), assertion: text }),
  implement: object({ green: flag, commands: filled(object({ command: text, lastLine: text })), staged: list(text) }),
  adversarial: object({ testsAdded: count, bugsFixed: list(object({ test: text, fix: text })), green: flag }),
  simplify: object({ cuts: list(object({ what: text, linesBefore: count, linesAfter: count })), checked: text, green: flag }),
  style: object({ format: count, lint: count, brief: object({ passed: count, total: count }), siblings: list(text), green: flag }),
  docs: object({
    docs: filled({
      ...object({ file: text, change: text, none: text }, ['file']),
      anyOf: [{ required: ['change'] }, { required: ['none'] }],
    }),
  }),
  review: object({
    verdict: text,
    findings: list(object({ severity: { enum: ['bug', 'design', 'prose', 'nit'] }, location: text, finding: text, trigger: text })),
  }),
  fix: object({ fixed: list(object({ finding: text, change: text })), skipped: list(object({ finding: text, why: text })), green: flag }),
}

const records = []

function stop(stage, reason) {
  log(`stopped at ${stage}: ${reason}`)
  return { status: 'stopped', stage, reason, records }
}

function record(stage, proof) {
  records.push({ stage, proof })
}

function column(size, loop) {
  const index = SIZES.indexOf(size)
  if (loop === 'light') {
    return index <= 1 ? 0 : 1
  }
  return index
}

function cell(stage) {
  return TABLE[stage][column(args.size, args.loop)]
}

function runs(stage) {
  return cell(stage) === 'S' ? args.loop === 'strict' : !['', 'driver'].includes(cell(stage))
}

function inputs(stage, plan) {
  const lines = [
    `Stage: ${stage}. Follow the "Every stage" and "${stage}" sections of ${args.briefs}.`,
    `Commit: ${args.subject} (size ${args.size}, loop ${args.loop})`,
    `Spec: ${args.spec}`,
    `House brief: ${args.houseBrief}`,
    `CI commands:\n${args.ci.map((command) => `- ${command}`).join('\n')}`,
    `Diff base: ${args.base}`,
  ]
  if (plan) {
    lines.push(`Plan:\n${typeof plan === 'string' ? plan : JSON.stringify(plan, null, 2)}`)
  }
  const note = args.resumeNotes && args.resumeNotes[stage]
  if (note) {
    lines.push(`Resume note: ${note}`)
  }
  return lines.join('\n\n')
}

function options(stage, label, model, phaseTitle) {
  const chosen = { label, phase: phaseTitle, schema: SCHEMAS[stage], agentType: `work-loop:stage-${stage}` }
  if (model && model.model) {
    chosen.model = model.model
  }
  if (model && model.effort) {
    chosen.effort = model.effort
  }
  return chosen
}

function lastLines(commands) {
  return commands.map((command) => command.lastLine).join('; ')
}

const models = args.models || {}

if (!SIZES.includes(args.size)) {
  return stop('start', `size ${args.size} isn't one of ${SIZES.join(', ')}`)
}
if (!LOOPS.includes(args.loop)) {
  return stop('start', `loop ${args.loop} isn't one of ${LOOPS.join(', ')}`)
}
if (!Array.isArray(args.ci) || args.ci.length === 0) {
  return stop('start', 'no CI commands to run')
}
if (cell('plan') === 'driver' && !args.plan) {
  return stop('start', "a medium commit needs the driver's plan in plan")
}
if (runs('review') && !(models.review && models.review.model)) {
  return stop('start', 'review agents need the review model by name in models.review.model')
}

phase('Plan')
let plan = args.plan
if (runs('plan')) {
  plan = await agent(inputs('plan'), options('plan', 'plan', models.plan, 'Plan'))
  if (!plan) {
    return stop('plan', "the agent didn't return")
  }
  record('plan', `${plan.files.length} files, ${plan.tests.length} tests, ${plan.research.length} sources`)
}

phase('Build')
if (runs('red')) {
  const red = await agent(inputs('red', plan), options('red', 'red', models.impl, 'Build'))
  if (!red) {
    return stop('red', "the agent didn't return")
  }
  if (!red.assertion.trim()) {
    return stop('red', `no test failed for the planned reason: ${red.tests.join(', ')}`)
  }
  record('red', red.assertion.trim())
}

const implemented = await agent(inputs('implement', plan), options('implement', 'implement', models.impl, 'Build'))
if (!implemented) {
  return stop('implement', "the agent didn't return")
}
if (!implemented.green) {
  return stop('implement', `CI commands still fail: ${lastLines(implemented.commands)}`)
}
record('green', lastLines(implemented.commands))

phase('Harden')
if (runs('adversarial')) {
  const adversarial = await agent(inputs('adversarial', plan), options('adversarial', 'adversarial', models.impl, 'Harden'))
  if (!adversarial) {
    return stop('adversarial', "the agent didn't return")
  }
  if (!adversarial.green) {
    return stop('adversarial', 'CI commands fail after the new tests')
  }
  record('adv', `+${adversarial.testsAdded} tests, ${adversarial.bugsFixed.length} bugs fixed`)
}

if (runs('simplify')) {
  const simplified = await agent(inputs('simplify', plan), options('simplify', 'simplify', models.impl, 'Harden'))
  if (!simplified) {
    return stop('simplify', "the agent didn't return")
  }
  if (!simplified.green) {
    return stop('simplify', 'CI commands fail after the cuts')
  }
  const removed = simplified.cuts.reduce((sum, cut) => sum + cut.linesBefore - cut.linesAfter, 0)
  record('simplify', simplified.cuts.length
    ? `${removed > 0 ? `-${removed}` : `+${-removed}`} lines, ${simplified.cuts.length} cuts`
    : `none, checked ${simplified.checked}`)
}

const toolsOnly = cell('style') === 'tools'
const stylePrompt = inputs('style', plan) + (toolsOnly ? '\n\nScope: tools only. Run the formatter and the linter and skip the brief and the siblings.' : '')
const styled = await agent(stylePrompt, options('style', 'style', models.impl, 'Harden'))
if (!styled) {
  return stop('style', "the agent didn't return")
}
if (!styled.green) {
  return stop('style', 'CI commands fail after formatting')
}
record('style', `format ${styled.format}, lint ${styled.lint}, brief ${styled.brief.passed}/${styled.brief.total}, sibling ${styled.siblings.length} files`)

const documented = await agent(inputs('docs', plan), options('docs', 'docs', models.impl, 'Harden'))
if (!documented) {
  return stop('docs', "the agent didn't return")
}
// The commit guard takes a docs record that starts with `none:` as the reason for a commit without a doc change.
const changed = documented.docs.some((doc) => doc.change)
record('docs', changed
  ? documented.docs.map((doc) => (doc.change ? `${doc.file} ${doc.change}` : `${doc.file} none: ${doc.none}`)).join(', ')
  : `none: ${documented.docs.map((doc) => `${doc.file}: ${doc.none}`).join(', ')}`)

if (runs('review')) {
  phase('Review')
  const lenses = column(args.size, args.loop) === 3 ? ['correctness', 'design', 'prose'] : ['all']
  const reviews = await parallel(lenses.map((lens) => () =>
    agent(`${inputs('review', plan)}\n\nLens: ${lens}`, options('review', `review:${lens}`, models.review, 'Review'))))
  if (reviews.some((review) => !review)) {
    return stop('review', "a review agent didn't return")
  }
  const findings = reviews.flatMap((review) => review.findings)
  const aboveNit = findings.filter((finding) => finding.severity !== 'nit')
  record('review', `${findings.length} findings, ${aboveNit.length} above nit`)

  if (aboveNit.length === 0) {
    record('fix', 'none, 0 findings above nit')
  } else {
    const fixPrompt = `${inputs('fix', plan)}\n\nFindings:\n${JSON.stringify(aboveNit, null, 2)}`
    const fixed = await agent(fixPrompt, options('fix', 'fix', models.impl, 'Review'))
    if (!fixed) {
      return stop('fix', "the agent didn't return")
    }
    if (!fixed.green) {
      return stop('fix', 'CI commands fail after the fixes')
    }
    const judged = fixed.fixed.length + fixed.skipped.length
    if (judged < aboveNit.length) {
      return stop('fix', `only ${judged} of ${aboveNit.length} findings came back as fixed or skipped`)
    }
    record('fix', `${fixed.fixed.length} fixed, ${fixed.skipped.length} skipped`)
  }
}

return { status: 'done', records }
