# Phase 0 — Mode and depth

Read during Phase 0, together with `phases/0-preflight.md`. Decide both settings once from what the user typed, announce them in one block, and from then on only apply them.

## Parsing the invocation

Split the text after `/pilot-beckie` into three parts: a mode word, a depth word, and the brief (everything else). Both words are bare, optional, in any order; anything you do not recognise belongs to the brief.

`/pilot-beckie full deep <idea>` → mode `full`, depth `deep`, brief `<idea>`.

## Mode

Accept the keyword or a natural-language equivalent in Russian or English. The phrases below are examples, not an exhaustive list: match by meaning, including other inflections.

| Mode | Triggers (English) | Triggers (Russian) | Human gates |
|---|---|---|---|
| `full` | `full`; "fully automatic", "do it all yourself", "don't ask me anything" | «полный автомат», «полностью сам», «полностью автоматически», «ничего не спрашивай», «без вопросов», «делай всё сам» | none |
| `semi` (default) | `semi`; "semi-automatic"; no mode word given | «полуавтомат», «полуавтоматически», «спрашивай только неясное», «уточни только главное» | only real forks get a question |
| `interview` | `interview`; "interview mode", "grill me", "interrogate me", "ask all questions", "work through the task with me", "interview me", "ask me everything" | «интервью», «погриль меня», «допроси», «допроси меня», «устрой мне интервью», «проинтервьюируй меня», «спроси меня обо всём», «задай все вопросы» | all questions |
| `manual` | `manual`; "manual mode", "approve every step" | «ручной режим», «согласовывай каждый шаг», «каждый шаг через меня» | the same questions, plus approval of spec and tickets |

- `interview` asks about the product. `manual` = `interview` + approval of the two process artifacts (spec, tickets), nothing more.
- Ambiguous → `semi`. A mode word that contradicts the rest of the sentence wins over the sentence. Two mode words → ask which one, in a single line.
- Switching mid-run on request: effective from the next phase, acknowledged in one line, nothing replayed.
- Instructions inside the brief (stack, budget, "no database", a deadline) are manifest requirements. They constrain the build; they never replace or skip a phase.
- **No mode removes manifest gates or safety gates.** Deploying, publishing, paying, messaging a third party, deleting data and rewriting history are always asked about, in each of the four modes including `full`, and the question always comes right after `python3 .pilot-beckie/ap.py ask action --note "<что нужно подтвердить>"`.

## Depth

Deepening an existing requirement is labelled `R##.n`; a new capability is `A##`.

| Depth | Triggers (English) | Triggers (Russian) | Deepening (`R##.n`) | New capabilities (`A##`) |
|---|---|---|---|---|
| `strict` | `strict`; "strictly per the brief", "only what I said", "add nothing", "strictly as written" | «строго», «строго по брифу», «строго по задаче», «строго по тексту», «только то, что я сказал», «ничего не добавляй», «меньше додумывай» | only the minimum a requirement needs to function | forbidden |
| normal (default) | no depth word | «обычная глубина», «как обычно» | where judgement says it clearly helps | allowed, each with a parent, in proportion |
| `deep` | `deep`; "work it out deeply", "think it through", "think it through for me", "go deep" | «глубоко», «проработай глубоко», «продумай за меня», «продумай глубже», «додумай всё» | all aspects of each requirement | encouraged, under the same limits |

- `strict` still handles errors and empty states; only unrequested extras are cut.
- Attachment rules stay in force at `deep`: each `A##` points to its parent requirement, and proportion still applies.
- Two cases trigger the adversarial pass (`phases/2-adversarial.md`): depth `deep`, whatever the mode; and mode `interview` or `manual`, whatever the depth.
- Depth can change mid-run («меньше додумывай», «продумай глубже»; "less invention", "think deeper"), effective from the next phase. Spec sections already written are not trimmed retroactively unless the user asks. Per-level detail lives in `phases/3-spec.md`.

## Opening block

It goes out a single time ahead of Phase 1, along with the memory-file and dashboard lines. It informs; it does not ask — say it and continue. It is the only place the user learns these settings exist, so do not skip it, and never repeat it: a later switch gets one acknowledgement line.

```
Режим: <режим своими словами> · глубина: <глубина своими словами>. <Что это значит — одна фраза; для semi, например: «уточню только неясное в задаче, а собирать буду сам».>
Прогресс: http://localhost:PORT/dashboard.html — обновляется сама раз в 10 секунд, считает рабочее время (пока жду твой ответ — пауза) и замирает, когда сборка сдана.
<строка «Память проекта — …» из phases/0-memory.md, без изменений>
<строка «↑ …» из вывода init — только если она была>

Переключить можно в любой момент, просто напиши:
- «делай всё сам» — полностью автоматически;
- «устрой мне интервью» — вопросы до конца, потом соберу без тебя;
- «ручной режим» — то же, плюс ты утверждаешь спецификацию и список тасков;
- «строго по задаче» / «продумай глубже» — меньше или больше проработки сверх сказанного.
```

- Every switch phrase in this block must appear in a trigger table above; if you change one, change both.
- Without a server, the progress line names the file `.pilot-beckie/dashboard.html` instead of a URL and still says it refreshes by itself.
- The refresh / working-time / freeze sentence is said here once; never explain the dashboard in chat again.
