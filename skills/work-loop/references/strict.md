# Strict loop

How the stages of [stages.md](stages.md) run, who writes their records and how a stopped run goes on. Every level uses these rules for the stages it runs. `loop strict` adds the `S` stages and makes the commit guard stop a commit with a missing docs reason.

## Who does what

You're the driver. You run the slice plan, the state check, the driver verify, the gate and the record yourself, because each of them needs the user, the chat or the final say. Stage agents run the rest: plan and research, red test, implement, adversarial tests, simplify, house style, docs, review and fix. [stage-briefs.md](stage-briefs.md) has the brief of each one.

Pick how the agents run by what the session has:

| The session has | How the stages run |
|---|---|
| The Workflow tool | 1 run of the plugin's `commit-cycle` workflow per commit, as `/work-loop:commit-cycle`. Pass it `subject`, `size`, `loop`, `spec`, `houseBrief`, `briefs` (the path of stage-briefs.md), `ci`, `base`, `models` with `plan`, `review` and `impl`, and your `plan` for a medium commit. It runs the agents of the size in order, with the review agents at the same time, and returns `status` and the `records`. A stop also returns the `stage` and the `reason`. |
| Subagents | 1 subagent per stage, as the plugin's `work-loop:stage-<stage>` agent when it's there, in the order of the table in stages.md, each with its brief and the inputs of "Every stage". The review agents of 1 commit run at the same time. |
| No subagents | You do each stage yourself, in the same order. The review is a reread of the diff with [review-checklist.md](review-checklist.md). |

Pass each agent its model by name, from the `plan-model`, `review-model` and `impl-model` knobs. Plan and research use `plan-model`, review uses `review-model` and the rest use `impl-model`.

## Records

Write 1 ledger record per stage, in order, from what the agent returned. The proof column of stages.md gives the stage and the text. The record is the proof, so don't write it before the stage is done:

```bash
node <skills>/work-loop/scripts/ledger.js add red "test_parses_empty_file: expected 0 but was 1"
```

The first large commit of a branch writes a record for each of the 14 stages. Later commits skip `slice`. A stage that doesn't run for the size doesn't write anything.

## Stops

A stage that can't reach its proof stops the cycle. That happens when the red test passes on its first run, when a CI command still fails after implement, adversarial, simplify or fix, or when an agent doesn't return. Don't run the next stage. Fix the cause or show the user the stage, the reason and the last log lines.

To run the stopped stage again, relaunch the workflow with `resumeFromRunId` and a resume note for that stage. Without the note the saved result comes back and the run stops at the same place.

## House brief

Keep the house rules of a repo in `$(git rev-parse --git-common-dir)/work-loop/house.md`, 60 lines or fewer. Write it at the slice plan of the first branch, from the agents file, the editor and linter config, the CI commands, the corrections the user made in this repo and the defaults of these skills. Every stage agent gets its path, and the house style stage checks the diff against it line by line.

Claude Code asks before the Write and Edit tools or a shell redirect change a file under `.git`, so write the brief while the user can answer. When the user corrects something, add the line to the brief in the same turn. After a compaction, read the brief before you ask the user anything about the repo.

## Resume

- At the start of each commit, write the inputs of the stage agents to the ledger as 1 `inputs` record next to the stage records, so a rerun after a crash doesn't have to dig them out of the chat.
- A long or unattended run keeps a living plan file. [slice-plan.md](slice-plan.md) has its form. Write its path in the `slice` record.
- A workflow run that stopped goes on with `resumeFromRunId`, the same arguments and `resumeNotes` with a note for the stage that stopped, like `{"style": "the formatter already ran"}`. Keep the notes of earlier relaunches in it. The stages before return their saved results without running again, as long as the session is the same one.
- After a compaction or a resume, run `ledger.js show` and read the plan file. The first stage without a record is where the commit goes on. Tell the agent of that stage that the tree may already have part of its work, so it keeps what's right instead of starting over.

## Cost

A large commit runs up to 11 agents and takes about 40 to 90 minutes. Strict on small and medium commits costs about 3 times as much as standard, which is why the size picks the stages and strict only fills the `S` cells.
