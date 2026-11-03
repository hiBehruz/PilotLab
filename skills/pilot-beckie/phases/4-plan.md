# Phase 4 — Plan

Read this file when Phase 4 starts. It cuts the spec into tickets, each built by one subagent in a fresh context, passes gate G3, and makes the run's first commit.

`ap.py` below means `python3 .pilot-beckie/ap.py`.

## 1. Enter and size

Call `ap.py stage plan`.

Every ticket is a cold start: the executor spends ~60–80K tokens just getting oriented in a new repo, over 100K in a large existing one. So prefer **fewer, denser** tickets — but never bigger than one context can hold.

Estimate size from **expected code volume** (changed lines, tests included), never from spec length. One executor ≈ 3,000 lines.

Before cutting, write one internal line with the volume estimate broken down by area — screens, endpoints, tables, flows; in existing code, how much each changes (use `notes.md`).

| Volume | Tickets | Tier |
|---|---|---|
| up to ~3K lines | 1 | `T0` — one executor builds the whole spec; no waves, no point review |
| ~3K–6K | 2 | `T1` |
| ~6K–18K | 3–6 (roughly 3K each) | `T2` |
| ~18K–36K | 7–12 (roughly 3K each) | `T3` |
| above | — | Not allowed. Split into two runs. |

- A list of edits in existing code defaults to `T0`: even many fixes across many files rarely pass 3K lines.
- A long `deep` spec for one small product is still `T0`.

Tell the user volume, tier and ticket count in one line. Record: `ap.py set tier=T<n>`.

## 2. Cutting rules

- A ticket is a **thin yet complete vertical slice** that crosses all the layers it involves (data, logic, UI, tests); once it lands, something works from end to end.
- The shell, the schema and shared primitives together make up **ticket 01, on its own**, with nothing in parallel.
- Groundwork that unblocks others is scheduled early, and tickets that close an `R` precede tickets closing nothing but `A`.
- Numbering starts at `01` and follows dependency order; every ticket lists what it depends on.

Tests to apply to every candidate ticket:

| Test | Rule |
|---|---|
| Size | When neighbours add up to less than ~3K lines, combine them, even if parallel runs were possible. Split only a ticket over ~3K lines, or one facing a long debugging loop (unfamiliar integration). |
| Payback | If the executor would spend more effort ramping up than building, merge it into a neighbour. |
| Neighbour | A ticket with under three acceptance criteria **that also** shares its files with an adjacent ticket → fold it into that ticket as a checklist item. |

**Merge pass — mandatory before writing any ticket file.** Combine neighbouring tickets that touch the same files; fold thin tickets into the parent they naturally belong to; collapse chains whose first ticket proves nothing by itself. Calibration: 12 tickets for ~18K lines means T2 was cut too thin. The expand/migrate/contract chain (§3) is exempt.

## 3. Wide change (existing code only)

When one requirement changes a shared thing used across many zones (rename a field, change a money type, split a name, swap a library) and it spans more zones than one ticket owns, split it into three steps that each pass the checks independently:

1. **Expand** — add the new thing next to the old one; the old keeps working (both fields kept in sync; new function with the old delegating to it). `Ревью: да — фундамент`, `Модель: сильная`.
2. **Migrate** — one ticket per zone moving its callers. Zones not yet moved stay green. Migrate tickets on different zones may share a wave. Acceptance criterion: no reference to the old thing remains in that zone.
3. **Contract** — remove the old thing once nothing uses it. If this drops a column holding user data: `Ревью: да — удаление данных`.

Every ticket in the chain carries the same requirement. If the shared thing lives in a single zone, an ordinary ticket handles it. Greenfield projects never need this.

## 4. Zones and waves

- `wave = 1 + max(wave of dependencies)`; a ticket without dependencies is wave 1.
- Next, divide every wave by zone: tickets that write the same files may not sit in one wave, so the later of the two is pushed to the following wave.
- A ticket states its **zone**, i.e. the directories/modules it owns, including tests.
- Waves come from the dependency graph. Never split a ticket to manufacture parallelism. A one-ticket wave is normal.
- Once written, wave numbers are never renumbered. A genuine re-cut is announced to the user in one line.

## 5. Review flag and model

Point review never blocks the build, and every ticket is reviewed anyway in the whole-branch review. So mark review sparingly:

| `Ревью:` value | When |
|---|---|
| `да — фундамент` | Just two cases: ticket 01, if other tickets build on top of it, and a wide change's expand step. |
| `да — <risk>` | Just when code written by the ticket itself implements money; deletion or migration of user data (e.g. `да — удаление данных`); keys and secrets; authentication (sign-in, sessions, passwords, 2FA). Checking permissions inside an ordinary feature does not qualify. |
| `нет` | Everything else — the majority. At `T0` the single ticket is always `нет`. |

`да — ремонт ветки` is reserved for the branch-review fix ticket (`phases/6-review.md`).

| `Модель:` value | When |
|---|---|
| `сильная` | Every ticket with `Ревью: да …`; plus any ticket built around a truly difficult algorithm or an integration nobody here knows well. |
| `обычная` | All others (cheaper model). |

## 6. Ticket file

Path: `.pilot-beckie/<dir>/tickets/NN-<slug>.md`. `ap.py` parses the header lines — keep the labels exact.

```
# NN — <название>

**Требования:** R01, R01.2, A01
**Зависит от:** 01, 02        (или —)
**Зона:** `src/orders/` · `tests/orders/`
**Волна:** 2
**Ревью:** нет
**Модель:** обычная

## Что заработает после таска
<сквозное поведение простыми словами, включая нужные сбои и продолжение после прерывания>

## Слова пользователя
> <дословная цитата из задания>

## Разделы спецификации
<номера историй и разделов решений>

## Приёмка
- [ ] <проверяемое условие>
```

Rules:

- **Verbatim brief quotes are mandatory.** They stop reinterpretation and are the point reviewer's source for the Manifest axis.
- Each acceptance criterion can be **checked**, and at the executor's starting commit it is **not yet true**.
- No file paths or code snippets, except structures prose expresses worse (schema, state machine).
- `Зависит от` lists ticket ids only (`01, 02`) or `—`. Any other reference fails `check-plan`.

## 7. Project rules in `interfaces.md`

Before the first ticket, add the project rules executors cannot derive:

- stack and versions;
- install and run commands;
- **exactly one** check command covering tests + types + lint;
- how to run a single test file;
- what must not be touched.

No check command exists → ticket 01 creates it. Ticket 01 also installs every dependency named in «Решения по реализации»; any other dependency later surfaces as `BLOCKED`.

## 8. Gate G3

Run `ap.py tickets` (publishes tickets to the dashboard, moves their manifest rows to `in-ticket`), then `ap.py check-plan`.

`check-plan` verifies: every live requirement is in some ticket; every ticket traces to a requirement; each ticket carries a zone and a wave; no wave comes before its dependencies; tickets in the same wave never share a zone. **A line of output beginning with `!` signals a defect in the plan.** Correct the ticket files, then run both commands again, repeating until no `!` is left.

Tickets that exist only in the dialogue are not tickets. Whatever you show the user summarises files already on disk.

## 9. Plan commit

This is the run's first commit and the base of every later diff.

1. Pass the whole of `.pilot-beckie/` through the redaction gate described in `phases/1-manifest.md`.
2. The commit contains **nothing but** what the skill created: `.env.example`, `.gitignore`, `.pilot-beckie`, `CLAUDE.md`, `AGENTS.md`. Omit paths that do not exist, and omit the memory file when `memoryOwner` is `user`. Never anything else in the tree.

```
P=".pilot-beckie .gitignore AGENTS.md CLAUDE.md .env.example"   # minus missing / user-owned
git add -A -- $P && git commit -q -m "Pilot by Beckie: план сборки" \
  --trailer "Pilot-Run: <run name>" -- $P \
  && python3 .pilot-beckie/ap.py set baseCommit=$(git rev-parse --short HEAD)
```

`<run name>` is `<dir>` without `--wip`. The `Pilot-Run` value is identical in every commit of the run.

## 10. Show the plan

Mention parallelism in one line only when it is real ("N задач в M волнах, часть идёт параллельно").

| Mode | What to do |
|---|---|
| `semi`, `interview` | A single screen with, for every ticket, one simple line about what the user will be able to do after it lands. Then say you are starting and that they can say stop — and start immediately. Never promise a countdown you cannot honour. |
| `full` | Show that screen as a notification only. |
| `manual` | A gate. `ap.py ask plan`; discuss technical detail, granularity and order; require explicit approval before Phase 5. |

Then go to `phases/5-subagents.md`.
