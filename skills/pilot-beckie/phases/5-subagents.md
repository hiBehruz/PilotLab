# Phase 5 — Build

Read this file when Phase 5 starts. It dispatches tickets to executor subagents, lands each one as its own commit, and ends when every ticket is settled. Anything other than a clean `DONE` sends you to `phases/5-repair.md`. Once the first point review comes up, open `phases/6-review.md`.

`ap.py` below means `python3 .pilot-beckie/ap.py`.

## 1. Principles

- Call `ap.py stage build` on entry. This phase behaves the same in all four modes and runs without the user.
- **Each ticket gets its own subagent with its own fresh context.** No context ever holds two tickets. The single `T0` ticket also goes to an executor.
- **Project code is never yours to write.** What you may touch: `.pilot-beckie/**`, `.env.example`, `.gitignore`, the memory files, and git limited to `add`, `commit`, `status` and `--stat` (diffs stay unread). No exception for "it's two lines" or "the executor failed, I'll finish it".

## 2. Executor prompt

Pass files **by path**, never their contents. Anything a subagent can read from disk is not pasted.

| Pass | Note |
|---|---|
| `<skillDir>/prompts/executor.md` | `skillDir` from `state.js`. Mark it: **read before the first edit**. |
| The ticket file | |
| `spec.md` + the section headings the ticket names | Never paste the whole spec. |
| `interfaces.md` | To be read first. |
| `notes.md` | Existing code only. |
| `reference.md` | Only when the ticket builds something user-visible. |

State in the prompt itself:

- the check command and the single-test-file command (copied from `interfaces.md`);
- the zone it owns, plus everything off-limits, the zones of concurrently running tickets among them;
- credential **variable names** only, never values;
- for a dependency relaunch: permission to install exactly that dependency.

A rule binds the executor only if it appears in the prompt or in `prompts/executor.md`; rules written solely in phase files never get to it.

Model: `Модель: сильная` → the session's model; `обычная` → the cheaper model (for Claude Code, set `model: "sonnet"` in the Agent call; harnesses that offer no model choice just skip this). Any ticket that failed before goes back out on the strong model.

## 3. Dependencies during build

A ticket needing an unlisted dependency returns `BLOCKED` naming it. If it fits an existing decision: add it to «Решения по реализации», then send the ticket out again, allowed to install precisely that one dependency (the manifest/lock files it changes go into that ticket's commit), and run no other installing ticket at the same time. A new decision → `phases/5-repair.md`.

## 4. Waves

- A wave launches **within a single message**, with a separate background Agent call for each ticket.
- **At most 3 executors in flight.** A wave of five goes as three, then two. Point reviewers do not count toward the limit.
- Re-check zone disjointness at launch. Overlapping files → serialise. Unsure → serialise.
- Waves are not barriers. As soon as a ticket comes back, start by launching whichever next ticket has every dependency committed, and only **after that** handle the returned one.
- Never launch a dependent on an uncommitted parent.
- A single `ap.py ticket <ids…> start` covers the entire batch and goes in the **very message** carrying the Agent calls, with Bash first and the launches following.
- **One event → one message.** The commit, the `ap.py` mark, the following launch and the user line travel together; do not send a marking-only message and then a separate launching-only one.
- To wait, **end your turn**; background subagents will wake you up. Do not start an agent or a loop whose sole purpose is waiting.
- Parallel executors share one working tree. Each touches only its zone plus `.env.example`; commits are made per zone.
- A check failure confined to files of a zone still being written is the neighbour's unfinished work. The returning ticket may land on its own green tests; the full check reruns when the neighbour lands.

## 5. Return contract

`prompts/executor.md` requires this block:

```
STATUS: DONE | DONE_WITH_CONCERNS | BLOCKED | NEEDS_CONTEXT
FILES: <paths only>
TESTS: <check command> → <result>; before: <previous count>
REDPROOF: <per new test: why it failed before the code — one line each, max 5>
INTERFACES: <public signatures / schemas / event formats exposed>
REQUIREMENTS: <id: done | id: placeholder — what was missing>
CONCERNS: <…>
BLOCKERS: <…>
```

At most 25 lines; no code, no diffs, no narrative. If the block runs longer, skip reading it and request it again with a one-line message.

## 6. After each ticket — strict order

1. **Contract.** Read the block and `STATUS`.
   - Block missing → treat the ticket as unfinished and ask for the block.
   - `BLOCKED` / `NEEDS_CONTEXT` → go to `phases/5-repair.md` immediately.
   - A `CONCERNS` line reporting that the plan breaks down (data model, interface, colliding requirements) → `phases/5-repair.md`, plan contradiction.
   - Two `NEEDS_CONTEXT` in one run → the tickets are cut too thin overall.
2. **Scope.** `git status --porcelain`. If a file changed outside the ticket's zone, the in-flight zones and `.env.example`, send a follow-up request (дозапрос): undo the change or explain it.
3. **Interfaces.** You — never executors — append the returned `INTERFACES` to `interfaces.md`. Two returns claiming the same interface = plan defect: keep the one that fits, re-cut the other.
4. **Check.** Run `<check> 2>&1 | tail -30`, and read its output before doing anything else: pass or fail, names of failures, number of tests. Hold it against the contract; a `DONE` with new criteria yet no new tests → дозапрос. A suite reporting zero tests is red whatever its exit code.
5. **Red → `phases/5-repair.md`.** A red check means no commit, and the fixing is not yours to do.
6. **Commit and record — one chained call, only this ticket's zone:**
   ```
   P="<every existing path of the zone> [.env.example if changed]"
   git add -A -- $P && git commit -qm "T<NN>: <title>" \
     --trailer "Pilot-Run: <run name>" --trailer "Requirements: <ids>" -- $P \
     && python3 .pilot-beckie/ap.py ticket NN done --tests <passed>/<failed> \
        --commit $(git rev-parse --short HEAD) [--placeholder R##]
   ```
   `--tests` = what step 4 actually printed. One `--placeholder` id per row the contract reports as stub. One commit per ticket.
7. **Point review** when the ticket says `Ревью: да …`, or its contract reports one of its own requirements not done: `ap.py ticket NN review`, launch the reviewer in the background (`phases/6-review.md`), carry on immediately. Its `BLOCKING` lines go to `phases/5-repair.md`.
8. **Ledger:**
   - each stub → `ap.py add debt.placeholders "…"`;
   - every new env variable → `ap.py add debt.emptyEnv NAME`;
   - every `A##` now present in code → `ap.py add additions "…"`;
   - each craft `CONCERNS` line → `ap.py add concerns "…"`.
   - Project memory (`phases/9-memory.md`, Moment 2) only if the ticket discovered something.
9. **User line.** One plain line: what now works, and progress as "k из n готово".

When several tickets come back at once, take them through this list one by one, each with its own check and its own commit.

## 7. Build end

The build ends when:

- all tickets are `done`, or `failed` with the user told which dependents now wait on them;
- no point review is still running;
- every review-requested repair has landed.

Then `ap.py stage review` and the whole-branch review in `phases/6-review.md`.
