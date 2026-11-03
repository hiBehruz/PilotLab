# Phase 3 — Spec

Read this file when Phase 3 starts, not before. Its job is to produce `.pilot-beckie/<dir>/spec.md` out of the manifest plus the briefing answers; that file is the contract executors build to and reviewers check against. It also fixes module boundaries in `interfaces.md` and passes gate G2.

`ap.py` below means `python3 .pilot-beckie/ap.py`.

## 1. Enter

1. Call `ap.py stage spec`.
2. If Phase 0 found existing code, run the exploration (§2) before writing anything.
3. If `carried.md` exists, apply §3.
4. Write the spec (§4–§7).
5. Pass G2 (§8): your own pass, then the independent coverage subagent, then `ap.py coverage …`.
6. Only then tell the user (§9) — in `manual`, that is the `ap.py ask spec` approval gate.

## 2. Explore existing code (existing repos only)

Spawn **exactly one** subagent on the cheaper model. After a single pass over the repository it writes `.pilot-beckie/<dir>/notes.md`, covering:

- where things live (entry points, layers, tests);
- conventions in use (naming, error handling, test style, formatting);
- commands that install, run and check the project;
- the names, **spelled exactly**, of every entity, field and function this run will touch, so that two tickets running in parallel cannot coin different names for the same field.

Every later executor reads `notes.md` instead of exploring again. A brand-new repo gets no exploration and no `notes.md`.

## 3. Carried context from a landed run

When `carried.md` exists:

- Hand its «Изменено после сборки» section to the exploring subagent, instructing it to describe those places **as they are in the code now**.
- Copy its «Договорились — не пересматривать» section (older progress files may call it just «Договорились») **verbatim** into `interfaces.md`, under the project rules, so executors and reviewers see it without reading history.
- If a spec section would break an item from that section: rewrite the section. If the new brief explicitly asks for that very change, ask the user one line. Never settle the conflict alone.

## 4. No new interview

Briefing is closed. Anything still unresolved becomes a `placeholder`.

- **Non-full modes, one exception:** a real fork the briefing missed, where each branch would be a different project. Ask once, one line, with your recommendation.
- **`full`:** no exception. Decide, and record it in the manifest as `ASSUMPTION — решено за пользователя: <что и почему>` (`phases/2-briefing.md` §6).

## 5. Depth pass

The brief describes the happy path. The spec must work out what the brief leaves unsaid. A spec that only restates the brief is a defect.

| Dimension | Question to answer |
|---|---|
| First run | The user's view while there is still no data. |
| Empty | No items or no results, plus the call to action displayed. |
| Wrong input | The message (in the user's language) and which of their input is kept. |
| Failure | Disk, network, external service: what stops working, what the user is told, what gets retried, what is lost. |
| Interruption | Closed halfway, refresh, double submit: resume, restart or duplicate. |
| Growth | Behaviour at 10 vs 10,000 items. |
| Boundaries | Who may act; what happens to those who may not. |
| Aftermath | Where the result goes, who is notified, how to undo. |

How far to go depends on the depth:

| Depth | Dimensions | `A##` |
|---|---|---|
| `strict` | Just failure and wrong input, and just in places where the requirement obviously fails without them. | **Forbidden.** |
| `normal` | The ones that plainly matter for each requirement (judgement). | Allowed, with parent and proportion. |
| `deep` | Every dimension of every requirement — answered or marked "not applicable". | Encouraged, same limits. |

Rules:

- Every answer turns into an `R##.n` story carrying its own acceptance line. How many stories result is a consequence, never a goal; padding hurts as much as leaving things out.
- Answers that belong to the user are proposals — they should have been briefing questions. Craft answers (error text, retry policy, limits, defaults) are yours: decide, write them in, mention them in the two-line summary (§9).
- In `full`, decide everything and list it for the final report. At `strict`, offer nothing beyond the request.

### Keep depth tied to the brief

- `R##` and `G##` are untouchable.
- `R##.n` is uncapped.
- `A##` must name a parent `R##`; an `A##` without one is cut.
- Proportion: the number of `A` stories never exceeds the number of `R` + `G` combined.
- Precedence: tickets that close `R` requirements come before tickets that close only `A`.
- `D##` is created **only** through `phases/5-repair.md`, never here.

## 6. Boundaries → `interfaces.md`

For each unit or module of the build decide:

- what it **owns**;
- what it **exposes** — signatures that other units invoke, described by name and shape, never by implementation;
- what it **hides**.

Then:

- Exposed names are English, never transliterated Russian — unless existing code uses another convention.
- Pick the **test seams**: a minimal subset of those boundaries; prefer seams that already exist.
- Boundaries come out of the depth pass rather than the bare list of requirements. If no ticket ever crosses it, it is not really a boundary. Favour a handful of deep modules over lots of shallow ones.
- Record them directly in `.pilot-beckie/<dir>/interfaces.md`, under the heading «Границы, решённые в спецификации». The spec only points there.

Because tickets start cold and in parallel, a boundary left for "ticket 1 to define" gets defined twice.

## 7. Shape of `spec.md`

**Small product** (one surface or feature, expected tier T0/T1) — short spec, sections:

1. Problem.
2. Solution — one line per live requirement (depth included): what the user gets.
3. Решения по реализации.
4. Вне рамок.
5. Open places.

No stories table: acceptance criteria live once, in the ticket.

**Everything else** — sections in this order:

1. Title.
2. Problem — in the user's words, from the point of view of whoever suffers it.
3. Solution — what the user will have; non-technical.
4. Stories table: `№ | метка | история | приёмка`. At least one story per live requirement; separate rows for deepenings (`R##.n`) and additions (`A## → R##`).
5. «Решения по реализации» — stack, data schema, contracts, external services; each with a one-line reason. No paths or code, except structures better expressed as code.
6. Boundaries and seams — a pointer to `interfaces.md`.
7. «Вне рамок» — table: requirement / why not now.
8. Open places — for each placeholder: what is stubbed, where, what is needed from the user.

Also:

- The requirement → section mapping lives in the manifest's «Где» column. Do not add a second mapping table to the spec.
- When the repo has `CONTEXT.md`, `GLOSSARY.md` or `docs/adr/`, stick to their terms without synonyms, and state openly any conflict with a decision already recorded.
- Executors may install only the dependencies named in «Решения по реализации»; name every one you expect.

## 8. Gate G2 — before the user sees anything

The user (or, in `manual`, the approval gate) only ever sees a spec that has passed G2. Do not send the summary or call `ap.py ask spec` until the `coverage` call below has been made.

### Self-pass

Every manifest row leaves `open`:

- → `in-spec`, with its spec section in «Где»; or
- → `deferred`, with a line in «Вне рамок».

Zero `open` rows. If any remain, write the missing section.

### Independent coverage check

As its author, you are blind to the spec's gaps. Spawn one subagent on the strong model and give it **exactly** these files, by path:

1. every `*-brief.md` in `<dir>`, oldest first;
2. `spec.md`.

Never the manifest, the conversation, or a summary. Prompt it along these lines:

```
Читай только эти файлы: <brief-1>, <brief-2>, …, <spec.md>.
Не открывай никаких других файлов — ни manifest.md, ни что-либо ещё в .pilot-beckie/.
Ты полезен именно потому, что не знаешь, как автор понял задачу.
Не вызывай skills, не запускай агентов.
Файлы задания идут по дате. Разделы «Дополнения» — более поздние слова пользователя;
при противоречии побеждает более позднее. Последний файл — спецификация.
Верни три списка:
1. Просили, но не покрыто: цитата из задания + одна строка, чего не хватает.
2. Покрыто наполовину: так, как написано, построить нельзя.
3. Есть в спецификации, но нет в задании.
Без оценок качества и без предложений. Если расхождений нет — напиши прямо: «расхождений нет».
```

### Act on the findings

| Finding | Action |
|---|---|
| Not covered | Write the section. |
| Half-covered | Complete it. |
| Not in brief | Attach to a parent as `A##`, or cut. |

Record in **one** call — all three numbers are mandatory:

```
ap.py coverage found=N fixed=N deferred=N --item "<R07 — …>" [--item "…"]
```

One `--item` per finding not fixed in the spec. The tool marks G2 passed when found ≤ fixed + deferred.

## 9. Tell the user — only after G2

The spec shown here is the one G2 just passed.

| Mode | What to do |
|---|---|
| `full`, `semi`, `interview` | About two lines: what will be built, what deliberately will not, where the file is. Continue without waiting. The full document is not owed, even in `interview`. |
| `manual` | Gate. Call `ap.py ask spec`, show the **whole** spec, wait for an explicit approval word ("ок"). Rewrite on every objection; a rewrite that adds, drops or changes a section reruns G2 (§8) before you show it again. Silence or work already begun is not approval. The boundaries in `interfaces.md` are the most important part of this discussion. |


Then go to `phases/4-plan.md`.
