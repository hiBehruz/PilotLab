# Phase 9 — Project memory

Open this file in Phase 5 if a ticket turned up something that deserves to be kept (Moment 2), and in Phase 8 before spawning the memory and ADR agents (Moments 3 and 4). Moment 1 — choosing the file and writing the skeleton — is `phases/0-memory.md`.

## 1. What lives where

| File | Holds | Tense / lifetime |
|---|---|---|
| Run folder | What was promised and delivered this run | History |
| `interfaces.md` | What the remaining tickets need | Dies with the run |
| Memory file (`memoryFile`) | What tomorrow's agent must know to work in this repo: commands, traps, pointers | Present |
| `docs/adr/` | Why, and what was rejected | Past |
| `CONTEXT.md` | What project words mean; synonyms to avoid. No code. | Present |
| `.pilot-beckie/PROGRESS.md` | Open work, known bugs, user settlements, edits without Pilot | Rewritten each landing |

- The memory file describes the repository **in its current state**, never the plan.
- The memory file explains how to work here; `PROGRESS.md` says where work stands. The memory file points to `PROGRESS.md` and never repeats it.

## 2. Ownership — `memoryOwner` in `state.js`

| Owner | Rule |
|---|---|
| `pilot-beckie` | All content sits inside the `<!-- pilot-beckie:start -->` … `<!-- pilot-beckie:end -->` pair. An update replaces only what is between them; text outside is never touched. Markers missing but the skill's sections recognisable → wrap them in markers; do not append a duplicate. |
| `user` | The run never writes to the file; Moments 2 and 3 go to `.pilot-beckie/<dir>/memory-proposal.md` instead. Only the user's say-so changes the file. |

## 3. Moment 2 — during the build

Keep only facts that **cost real effort to find**, a line apiece:

- the actual check command and the command for a single test;
- traps that ate time (ordering dependency, version pin, platform quirk);
- a new `.env.example` variable;
- a decision the next ticket must not relitigate.

Most tickets add nothing. Never record: generic advice, restated names, commit history, explanations of standard tech, or anything `interfaces.md` holds during the run.

Where: skill-owned file → one line between the markers. User-owned → one line appended to `memory-proposal.md`.

## 4. Moment 3 — the description (Phase 8)

Done by a cheaper-model subagent, one of the three Phase 8 agents alongside blind acceptance. Neither sees the other's work except that this one receives the checker's verified commands, which is why it starts after the checker is back (`phases/8-final.md` §1). It is given: the tier, `interfaces.md`, the memory file as it is now, the repository, and the verified commands (your full-suite run and the blind checker's commands). **Never `spec.md` or tickets.**

Content — pointers and traps, not retelling. No directory tree, no paraphrase of package manifests, no "module X does Y".

Sections:

1. One-line header: what it is, for whom.
2. Commands, all of them verified: install, run, a single test file, and the check (tests + types + lint).
3. 3–8 pointers to entry points and frequently edited places. Not a tree.
4. Non-obvious traps that have already bitten.
5. Environment variables: names and purpose, never values.
6. The skeleton's "how Pilot by Beckie works here" section (`phases/0-memory.md`), unchanged.

At `T2`+, architecture — data flow, module boundaries, settled conventions, folded from `interfaces.md` minus the per-ticket framing — goes to `docs/architecture.md`, with one pointer line in the memory file.

Before the block is written:

- Commands verified: reuse the handed-in commands that already ran (name which run proved each); verify only the uncovered ones; drop any that fails.
- Every path exists.
- No secret values — the redaction gate (`phases/1-manifest.md`) applies.
- Length proportional to the tier.

### Memory agent prompt

```
Ты пишешь память проекта для агента, который придёт сюда впервые и не будет ничего исследовать.
Источники: только видимый код и <path>/interfaces.md. Остальное в .pilot-beckie/ не открывай.
Не вызывай skills и slash-команды, не запускай агентов.
Одна строка — одна мысль. Указатели, а не пересказ. Не повторяй очевидное и не объясняй известные технологии.
Каждая команда должна запускаться копированием; каждый путь — существовать.
Уже проверенные команды: <команды и результаты>. Ссылайся на них; проверяй только непокрытые; упавшую не включай.
Раздел, за которым нет кода, пропусти.
Пиши только между <!-- pilot-beckie:start --> и <!-- pilot-beckie:end --> в <memoryFile>; вне маркеров ничего не трогай.
[T2+] Архитектуру (поток данных, границы модулей, принятые соглашения) запиши в docs/architecture.md и поставь на него одну строку-указатель.
[файл пользователя] <memoryFile> не трогай. Запиши предложения в .pilot-beckie/<dir>/memory-proposal.md.
```

### User-owned file: the proposal

The agent writes `memory-proposal.md` listing, each as a ready-to-paste line:

- missing items — commands, variables, traps, pointers;
- statements in their text that are now false.

If the user's file is missing them, the proposal always adds the two subsections defined in `phases/0-memory.md`: «История git» and «Правка без Pilot by Beckie». Nothing beyond that.

A single question in the report, at the very end (`semi` / `interview` / `manual`), whether to apply the N proposed items, summarising them. In `full`, nothing is asked; the report names the file. On approval: additions go into a marked Pilot block at the end of their file; their own lines change only as approved.

## 5. Moment 4 — ADRs and glossary (Phase 8, `T2`+)

Runs as a cheaper-model subagent in parallel with the rest. Its inputs: `notes.md` when it exists, `interfaces.md`, `manifest.md`, `spec.md`. **No repository access.**

### ADR sources

- Every `D##` row — the most valuable.
- Implementation decisions that carry weight (external service, module boundaries, data model) — whatever would be costly to undo.

Excluded: vocabulary (goes to the glossary), decisions with no alternative, decisions a linter or framework made, obvious defaults.

Count: 3–6 files at `T2`, 5–12 at `T3`.

When `docs/adr/` is already there, keep its format and carry on its numbering, without renumbering anything. ADRs go into the final commit and get one line in the report.

### Glossary sources

- Usual size 3–15 terms. Later runs read it first (preflight, spec phase).
- Existing glossary → hand it to the agent (it cannot see the repo) with one line stating whose it is:

| Existing file | Instruction line in the brief |
|---|---|
| `CONTEXT.md` with `<!-- pilot-beckie:glossary -->` (skill's) | Keep it true: rewrite definitions whose meaning this run's spec changed; remove terms for concepts that this run eliminated (through a `D##` or the user's word); leave untouched terms the run did not touch. |
| `GLOSSARY.md` without marker (user's) | Continue it in its own format. |
| `CONTEXT.md` without marker (user's) | Add new terms only; change no existing term. A term now used differently comes back to you and becomes a report question. |
| `CONTEXT-MAP.md` present (several contexts) | Drop the glossary part from the brief; the report says so in one line. |

Over ~40 terms: do not split; the report suggests a split in one line; the user decides. The glossary is committed in the final commit, together with the ADRs.

### ADR + glossary prompt

```
Источники: <interfaces.md>, <manifest.md>, <spec.md> и <notes.md>, если он есть. Репозиторий тебе не нужен.
Не вызывай skills, не запускай агентов.

ADR:
- Одна запись на каждое решение, которое дорого развернуть, и на каждую строку D## манифеста.
- Файлы docs/adr/NNNN-<slug>.md, нумерация с 0001 (или продолжи существующую), один файл — одно решение.
- Ровно четыре раздела:
  Контекст — 1–2 строки: что было известно.
  Решение — в настоящем времени.
  Почему — включая отвергнутые варианты, у каждого своя причина.
  Последствия — включая неприятные.
- Для D##: контекст = что предполагал план, решение = что доказал код.
- Решение без альтернатив — без ADR. Не пересказывай спецификацию, не описывай код.

Глоссарий — CONTEXT.md в корне репозитория:
- Только слова этого проекта, которые новичок назовёт или поймёт иначе.
  Термины предметной области — да; общие (пользователь, API, таймаут) — нет.
- Термин пиши на языке задания и тем же словом, что в коде и спецификации (см. interfaces.md, notes.md); синонимы не годятся.
- Таких слов нет — файла нет.
- Формат: первая строка <!-- pilot-beckie:glossary -->; название проекта; 1–2 строки о предметной области;
  затем раздел «Язык». Каждый термин — ровно три строки, между терминами пустая строка:
  строка 1 — термин жирным и двоеточие: **Термин**:
  строка 2 — 1–2 предложения, что это такое (не что с ним делает код);
  строка 3 — _Избегать_: синонимы через запятую (нет синонимов — _Избегать_: —).
  Пример:
    **Запись**:
    Время, которое клиент забронировал у конкретного мастера на конкретную услугу.
    _Избегать_: бронь, слот, визит
- Одно понятие под разными именами в задании и спецификации: оставь одно имя главным, прочие перечисли в _Избегать_.
- Пути к файлам, поля данных и стек в глоссарий не пишутся.
<строка о существующем глоссарии, если есть>
```

## 6. On resume

Read the memory file first, before `state.js`. If it is missing or plainly stale against the code, fix it as part of this run. Do not read `docs/adr/` on resume; open an ADR only when about to reverse its decision.
