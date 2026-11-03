# Phase 6 — Review

Read this file at the first point review during the build, and again for the whole-branch review after the last ticket. Reviewers read and judge; they never write code. Fixes go through executors (`phases/5-repair.md`).

`ap.py` below means `python3 .pilot-beckie/ap.py`.

## 1. Two moments

| Moment | Which tickets | When |
|---|---|---|
| Point review | Tickets flagged `Ревью: да …`, plus any ticket whose contract admits that a requirement it owns is not done. **None at `T0`.** | Always after the commit, never before. Runs alongside the next wave. |
| Whole-branch review | Everything | Exactly once, after the last ticket, as stage `review` — every tier, every mode. |

All other tickets are reviewed only within the branch review.

## 2. Three axes, each reported on its own

| Axis | What is checked | Failure looks like |
|---|---|---|
| Manifest | Is what the user asked for, in the user's words, actually delivered? | A requirement got smaller without anyone saying so. |
| Spec | Do the spec's decisions show up in the implementation? | The executor made things up. |
| Craft | Can further work safely be built on this code? | It runs today but stands in the way of tomorrow's work. |

Never merge or rank the axes together.

**Which axis?** Ask whether the information was available to the executor, given what it received: the ticket, the spec sections named in it, `interfaces.md`.

- Yes → Spec or Craft; the fix happens inside this ticket.
- No → Manifest. The fault lies in the spec or in how tickets were cut, so fix those first. Never rerun an executor against information it never received.

## 3. Point review

- One **fresh** reviewer per review, strong model. Never reuse a reviewer across tickets.
- As soon as the commit lands, run `ap.py ticket NN review` and start the subagent in the background, then continue building. Never hold a wave for a review.

Reviewer prompt:

| By path | Pasted |
|---|---|
| `<skillDir>/prompts/review.md` — mark: read before the diff | Mode: `таск` |
| The ticket file | The executor's `TESTS` and `REDPROOF` lines |
| The spec sections the ticket names | The review reason: foundation / named risk / requirement caveat — it decides what may block |
| `interfaces.md` | The command `git show <commit>` |
| Repo coding conventions (where documented) | "Only review: no fixes, no refactoring, no skills, no new agents." |

Handling the result (you see only the verdict block — neither diff nor reasoning enters your context):

| Result | Action |
|---|---|
| `BLOCKING: нет` | `ap.py ticket NN done` again. Ticket finished. |
| `BLOCKING` lines | To `phases/5-repair.md` with the lines copied exactly; the fix becomes one more commit in the same zone. |
| `FINDINGS` | One call: `ap.py add concerns "<file:line — …>" "<…>"`. |

When a blocking fix alters an interface that running tickets depend on, record the change in `interfaces.md`; each affected ticket then gets a one-line notice on its return, ahead of its commit.

### Re-review of a repair

Mode `ремонт`, fresh subagent, **at most once per ticket**. Give it `git diff <ticket commit>..<repair commit> -- <zone>` and the list of conditions. It answers closed / not closed per condition.

## 4. What may block — closed list

Only these may appear in `BLOCKING`:

- Manifest `partial` or `missing`;
- an invented fact where user data belongs (the only accepted stub is the marker `[ВПИШИ: <что>]` from `prompts/executor.md`; search the diff for `[ВПИШИ:` to see where stubs are);
- Spec **extra** — unrequested surface, unless genuinely needed;
- a red check;
- a test tied to internals that a later ticket may rewrite;
- foundation tickets: a defect later tickets will build on (wrong schema key, shared client failing the next call, access ignoring the spec boundary);
- risk tickets: a hole in that risk per the security list in `prompts/review.md`.

**Do not widen this list** — not "nothing blocking, but fix it anyway", not promoting a `FINDINGS` item. Widening needs a one-line message to the user stating its cost.

## 5. Whole-branch review

1. `ap.py stage review`.
2. A single fresh subagent on the strong model; for a big diff at `T3`, as many as three running in parallel, each given its own set of zones.
3. Give it:
   - `<skillDir>/prompts/review.md` with mode `ветка`;
   - the range for it to diff on its own, `git diff <baseCommit>..HEAD` (`baseCommit` comes from `state.js`);
   - paths to `spec.md` and `interfaces.md`, plus the repo's conventions;
   - the deferred findings from `state.js` → `concerns`, to confirm or drop.
   It may open files outside the diff to see interactions. It does **not** judge the Manifest axis — G4 covers that.
4. It sorts every finding:

| Bucket | Meaning |
|---|---|
| `FIX NOW` | Cheaper to close than to leave; bounded fix. Anything repeated across ≥3 tickets. |
| `REPORT` | Real, but not worth delaying delivery. |
| `DROP` | Taste, or the target code is gone. |

Security findings are `FIX NOW` or `REPORT`, never `DROP`.

### Fix ticket `F1`

All `FIX NOW` findings become one ticket, `tickets/F1-<slug>.md`:

```
# F1 — <название>

**Требования:** <ids the fixed code serves>
**Зависит от:** —
**Зона:** <union of the named files, backticked, joined by ` · `>
**Волна:** <last wave + 1>
**Ревью:** да — ремонт ветки
**Модель:** сильная

## Приёмка
- [ ] <each FIX NOW finding, verbatim>
```

Then: `ap.py tickets`; one executor (`phases/5-subagents.md` §2); the check; one commit made like a ticket commit (`phases/5-subagents.md` §6, subject `F1: <title>`, same trailers); one re-review in mode `ремонт`. Items still open go to the report — no second round. **Never fixed by you or by the reviewer.**

### Report items

Each `REPORT` finding → `ap.py add report "…" "…"`, phrased for the user.

### Tell the user

Nothing per ticket. After the branch review, one line: how many findings, how many fixed, how many go to the report. Then `phases/8-final.md`.
