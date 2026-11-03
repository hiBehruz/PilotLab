# Phase 5 — Repair, failure, plan amendments

Read this file whenever a ticket returns anything but a clean `DONE`: a `BLOCKING` review line, a red check, `BLOCKED`, `NEEDS_CONTEXT`, or a plan contradiction. Code is still written only by subagents.

`ap.py` below means `python3 .pilot-beckie/ap.py`.

## 1. Limits

Three separate limits per ticket. Each is checked on its own:

| Limit | Cap | Tracked by |
|---|---|---|
| Follow-ups (дозапросы) into **one** context | 2 | you; after the second, switch to a fresh context |
| `repairs` counter for the ticket | 2 | `ap.py ticket NN repair` |
| `retries` counter for the ticket | 2 | `ap.py ticket NN retry` |

Exhausting `repairs` or `retries` means the cut was wrong. That goes to the report (via `fail`, §5), not into another attempt.

## 2. Routing

| What came back | Kind | Route |
|---|---|---|
| Red check; reviewer `BLOCKING` line; criterion met in letter but dodged in substance | Incomplete work | Дозапрос to the **same** executor by message, context intact (§3). |
| `BLOCKED`, `NEEDS_CONTEXT`, or a repair that already failed | Refusal | **Strong model, fresh context**: hand over the ticket once more together with the error, the name of the failing test and the path that is now spelled out (§5). |
| `BLOCKED` on a missing dependency | Not a failure | §4. |
| Executor shows the plan is wrong | Plan contradiction | §6. |
| Reviewer `FINDINGS` | Not a repair | `ap.py add concerns "…"`; wait for the branch review. |

Only `BLOCKING` lines and red checks become a дозапрос.

## 3. Follow-up request (дозапрос)

1. Call `ap.py ticket NN repair --note "<condition in one line>"` before sending.
2. If a ticket in flight owns any file of this zone, wait until it lands.
3. Send only:
   - the failing test or condition — reviewer `BLOCKING` lines **verbatim and nothing else**;
   - the last ~10 lines of output;
   - the instruction:
     ```
     Сначала одной строкой назови причину. Затем исправь так, чтобы условие выполнялось.
     Больше ничего не трогай. Верни блок-контракт заново.
     Причину не нашёл — верни BLOCKED, а не обходной путь.
     Ослабить или удалить проверку в тесте — не ремонт.
     ```
4. Word every item as a concrete condition ("this field is shown", "this test passes", "this error is caught"), never as "fix it".
5. The repair returns a fresh contract with new `FILES` and `TESTS`. Run the after-ticket steps from `phases/5-subagents.md` §6 again.

Following a point review, the fix lands as **another commit in that same zone**: subject `T<NN>: ремонт — <short>`, same `Pilot-Run` and `Requirements` trailers. The re-review reads exactly that commit.

### Re-review

- Reviewed ticket repaired → re-review in mode `ремонт` scoped to the fix: fresh reviewer, repair commit diff plus the conditions; answers closed/not closed per condition; new breakage only inside the fix (`phases/6-review.md`).
- Unreviewed ticket repaired (red check) → only the check must be green.
- **At most one re-review per ticket.** Items still open → `ap.py add concerns "…"` for the branch review (fixed in `F1` or reported). Never a third round. A red check stays blocking and is closed by the check, not by more review.

### Harness cannot continue a subagent

Start a fresh context instead, giving it the complete ticket prompt and the finding. Do not make the edits yourself.

## 4. `BLOCKED` on a missing dependency

| Dependency | Action |
|---|---|
| Fits an existing decision | Add it to «Решения по реализации»; relaunch with permission to install exactly that. |
| New decision (paid service, heavy framework, different stack) | `semi` / `interview` / `manual`: ask the user (`ap.py ask action --note "…"`). `full`: record an `ASSUMPTION`, then relaunch. |

## 5. Ticket failure

1. Run `ap.py ticket NN retry` and start a new context on the strong model, attaching the error.
2. A second retry is allowed only if the **approach changes** — another design decision, another library, or a path named explicitly. Repeating the same attempt is forbidden.
3. After that: `ap.py ticket NN fail --note "<what blocks>"`; write the reason into «Основание» of the ticket's manifest rows; tell the user plainly what blocks, what is needed from them, and which tickets now wait.

Never improvise around a blocker. Never shrink the ticket to whatever worked. Independent wave-mates keep landing.

## 6. Plan contradiction

When an executor proves the plan wrong (`BLOCKED` or `DONE_WITH_CONCERNS`), **you** decide — never the executor — and code is still written by subagents:

1. Edit the spec section where it stands, preserving its marks, and add a single line saying which ticket showed what in code.
2. Put a `D##` row into the manifest, with the finding in «Основание» naming the requirement it serves; status `in-spec`, pointing to the amended section.
3. Re-cut only what is invalidated. Landed tickets stay. Unstarted ones get updated references. A ticket that lost its purpose is removed, and its rows return to `in-spec`. Rerun `ap.py tickets`.
4. Whatever the mode, give the user a single line: what didn't hold, how it was fixed, that the requirement is unchanged.

Limits of `D##`:

- It never removes a requirement. An impossible requirement is a question to the user (in `full`: `ASSUMPTION` + placeholder).
- A new idea never travels as a `D##`; it would be an `A##` attached to a parent, which `strict` does not allow.
