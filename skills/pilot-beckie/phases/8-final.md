# Phase 8 — Acceptance and landing

Read this file when the branch review is done. It checks the build blind against the brief (gate G4), writes project memory, the progress file and the final report, and lands the run. Read `phases/9-memory.md` before spawning the memory and ADR agents.

`ap.py` below means `python3 .pilot-beckie/ap.py`.

## 1. Enter and spawn

Call `ap.py stage final`. Then three mutually isolated subagents — none sees another's output except as stated:

| Agent | Answers | Gets | Never gets | Model |
|---|---|---|---|---|
| Blind checker | How much of the brief is built? | The repository and the brief files | tickets, `manifest.md`, `spec.md` | strong |
| ADR agent (`T2`+ only) | Why it was built this way; project vocabulary | `notes.md`, `interfaces.md`, `manifest.md`, `spec.md` | The repository | cheaper |
| Memory agent | How to use the project tomorrow | Repository, memory file, `interfaces.md`, tier, commands the checker ran | `spec.md`, tickets | cheaper |

Launch the blind checker and the ADR agent **in one message**. Launch the memory agent after the blind checker returns — it needs the commands the checker proved.

## 2. Blind acceptance — gate G4

The checker receives the repository and all `*-brief.md` files from `<dir>` in full, from oldest to newest, with their `## Дополнения`. Because `.pilot-beckie/` is committed, its prompt must forbid opening it. Prompt along these lines:

```
Задание — в этих файлах, по порядку дат: <brief-1>, <brief-2>, …
Разделы «Дополнения» — часть задания; при противоречии побеждает более позднее.
Не открывай .pilot-beckie/ (там спецификация, манифест, задачи) — тебе нужен взгляд без них.
Не вызывай skills и не запускай агентов.
Никаких действий наружу: письма, сообщения реальным людям, оплаты, публикации.
Остановись за шаг до отправки и запиши, что осталось непроверенным.

1. Сделай git clone репозитория во временную папку и установи зависимости заново,
   опираясь только на содержимое репозитория. Понадобится .env — перенеси его в клон, не читая.
   Если что-то работает в рабочей папке, а в клоне нет, это находка
   (незаписанная зависимость, незакоммиченный файл, шаг, завязанный на эту машину).
2. Запусти проект и пройди главный сценарий так, как прошёл бы пользователь.
   Не запустилось или сценарий сломался — это первая находка.
   Не можешь запустить вовсе (нужен аккаунт, ключ, внешний сервис) — скажи, что помешало;
   не выдавай чтение кода за проверку.
3. Места, где вместо данных пользователя стоит метка вида [ВПИШИ: <что>], — это ожидаемые заглушки, а не ошибка: перечисли их отдельно.
   Правдоподобное значение вместо такой метки (цена, адрес, телефон, текст) — находка.
4. Для каждого требования задания укажи «сделано», «частично» или «нет» и в одной строке — где это видно.
   Формально есть, но по сути не работает — «частично».
5. Отдельно и дословно верни команды, которыми запускал проект, и их результаты.
Только факты: без оценки качества кода, без советов, без оправданий.
```

### Compare with the manifest

| Manifest status | Checker says | Meaning | Action |
|---|---|---|---|
| `done` | implemented | Agreed | — |
| `done` | partial / not | Drift: the manifest is mistaken | Fix it through a ticket or note it in the report; never edit it yourself. |
| `placeholder` | partial | Expected | Confirm the stub is visible as `[ВПИШИ: <что>]` and not an invented value. |
| `dropped` / `deferred` | not | Expected | Reported as not built. |
| — (not in brief) | implemented | Unparented scope growth | Report it. |

Record in one call — one `--mismatch` per drift:

```
ap.py blind checked=N matched=M --mismatch "<R02 — …>" [--mismatch "…"]
```

The tool passes G4 only with no mismatches; `matched` must not exceed `checked`.

A build that cannot be run here goes into «Что нужно от тебя», not the accepted column. Never hide drift.

## 3. Memory and ADRs

Follow `phases/9-memory.md` (Moments 3 and 4). If `memoryOwner` is `user`, the user's file stays untouched and the memory agent produces `memory-proposal.md` in its place.

## 4. Final report

1. Rerun the check once: `<check> 2>&1 | tail -30`; record `ap.py tests N/M`.
2. Read `phases/rationalizations.md` once.
3. Re-read the sources from disk now — `manifest.md`, `state.js`, checker and agent returns. Never write from memory.
4. Use the user's language and simple words; avoid jargon.

| Section (Russian heading) | Source |
|---|---|
| **Что я решил за тебя** — first in `full` mode | Every «Основание» in `manifest.md` that starts with `ASSUMPTION — решено за пользователя:` (format from `phases/2-briefing.md` §6); one line each, the text after the colon. |
| **Что готово** | Based on what the blind checker found, never on rows marked `done` in the manifest. 3–6 plain lines from the user's side, plus how to run it: commands, and URL if any. |
| **Что нужно от тебя** | `placeholder` rows + `state.js` → `debt`: env variable names to fill in `.env` (`.env.example` is the template), visible stubs to replace — find them by searching the repository for the marker `[ВПИШИ:` (`prompts/executor.md`), and list each with what goes in it. Builds that could not be run here. |
| **Что не вошло** | Rows that are `dropped` or `deferred`, quoted. Table: что / почему. |
| **Что я добавил сверх заказа** | The `additions` list in `state.js`, verified against the `A##` items of the spec. Table: добавка / зачем. |
| **Что пошло не по плану** | All failed tickets and all `D##` rows. Table: что не сработало / как сделали. |
| **Что осталось после проверки** | The `report` list in `state.js`. |
| **Открытые вопросы** | Mismatches stored under `blind` in `state.js`, said plainly; `coverage` → `items` that ended up unbuilt. |
| **Память проекта** — present only if the user owns the file | A single question about `memory-proposal.md` ("N пунктов, применить?"); under `full`, just one line that names the file. |
| **Где что лежит** | `memoryFile`, `briefFile`, commands verified by the memory agent; pointers to the memory file, `.pilot-beckie/PROGRESS.md` (small fixes can be done in a plain session that reads it), `docs/adr/` and `CONTEXT.md` when present, `dashboard.html`, the run folder. |

- «Что нужно от тебя» is **mandatory** even if empty — then say everything is filled in.
- «Что не вошло» is always written — one line if nothing was excluded.
- Other empty sections are omitted.
- Secrets by name only. No embellishment: failures, incomplete work and discrepancies are stated directly, with what is needed to fix them. No diffs, code file names or test names.
- One line each, where they apply: ADRs written; glossary split suggested; glossary skipped because of `CONTEXT-MAP.md`; files left uncommitted (§6); `PROGRESS.md` over ~60 lines → "стоит перенести в трекер".

## 5. Progress file

Write `.pilot-beckie/PROGRESS.md` from freshly re-read files. Rewrite it **whole** at every landing — its previous content was preserved in `carried.md`.

```
<!-- pilot-beckie:progress -->
# <проект> — что осталось

Последняя сборка: `<run folder>` — <одна строка итога>.

## Договорились — не пересматривать
- …

## Не доделано
- …

## Известные баги
- …

## Правки без Pilot by Beckie
<!-- Обычная сессия: после правки допиши строку «дата — что — зачем». -->
```

| Section | From |
|---|---|
| Договорились — не пересматривать | Quoted `dropped` rows; durable preferences found in the briefs' `Дополнения`; assumptions confirmed by the user; agreements from `carried.md` that still hold. Content that belongs in an ADR gets a pointer here, nothing more. |
| Не доделано | Quoted `deferred` rows; failed tickets; coverage items never built; whatever in `carried.md` was left untouched by this run. |
| Известные баги | Mismatches from blind acceptance; unfixed `concerns` and `report` entries; `carried.md` bugs not fixed. |
| Правки без Pilot by Beckie | Left empty. Each carried entry has been moved to «Договорились — не пересматривать», «Не доделано», or dropped if git already holds the fix. |

- Placeholders and env variables are not repeated here.
- An empty section shows `—`.
- One thought per line, with the requirement id where relevant.
- Whole file under ~60 lines; if more, the report says in one line it belongs in a tracker.

## 6. Landing — this order

1. Write the memory file or `memory-proposal.md`, the ADRs, the glossary, `PROGRESS.md`.
2. `ap.py finish --result "<one line: what now exists>"`. This closes the stages, fills in `finishedAt`, uses `git mv` to rename `<dir>--wip` → `<dir>`, closes the row for this run in `.pilot-beckie/README.md`, and shuts the server down about 12 s afterwards. Ignore a `!` line about the rename (name taken / dirty index).
3. Final commit of only what the skill wrote since the plan commit. Omit paths that do not exist and the user's own memory file:
   ```
   P=".pilot-beckie AGENTS.md CLAUDE.md docs/architecture.md docs/adr CONTEXT.md GLOSSARY.md .env.example .gitignore"
   git add -A -- $P && git commit -q -m "Pilot by Beckie: сборка сдана" \
     --trailer "Pilot-Run: <run name>" -- $P
   ```
   The subject must be exact: later runs and plain sessions find the landing by it.
   Then `git status`. Any changed file outside every ticket's zone is **not** committed by you; list it in the report as left uncommitted.
4. Deliver the report. Say nothing about the dashboard freezing or the server shutting down.
