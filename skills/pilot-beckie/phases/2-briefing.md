# Phase 2 — Briefing

Read when Phase 2 begins. On entry: `python3 .pilot-beckie/ap.py stage briefing`. Goal: resolve anything that cannot be built in its written form and, if mode or depth requires it, catch the brief's mistakes while fixing them costs nothing. **A question is only worth asking if it moves a manifest row.**

How much gets opened is up to depth; who closes it is up to mode. Mode does not change what counts as a fork found at `deep`: under `full` you resolve and label it yourself, under `interview` it becomes a question.

**Adversarial pass first** when it applies (depth `deep` under any mode, or mode `interview`/`manual` under any depth): before the first question, open `phases/2-adversarial.md` and carry it out. If it does not apply, skip it.

**Which sections apply in which mode.** `full` skips only the parts that talk to the user; every rule about *what* gets decided and recorded applies in all four modes.

| Section | `semi` / `interview` / `manual` | `full` |
|---|---|---|
| 1. Rounds | yes | **skip** — no questions are sent |
| 2. What reaches the user | yes | **skip** — nothing reaches the user |
| 3. Priority list (incl. carry-over) | the order of the questions you ask | the order of the questions you answer yourself; carry-over: nothing is offered |
| 4. Reference | yes | yes — `reference.md` holds only comparables the brief itself names |
| 5. Recording answers (incl. «Changes mid-run») | yes | yes — your own answers are recorded the same way; mid-run changes from the user follow the same procedure |
| 6. Self-briefing | — | yes |
| 7. Close (G1) | yes | yes |

So in `full`, go §3 → §4 → §5 → §6 → §7, skipping only §1 and §2.

## 1. Rounds (not in `full`)

- Ask in **rounds**, not one question at a time. Each round covers the entire current frontier, meaning all questions not waiting on the answer to some other open question — numbered, and **no more than four in one message**.
- Each question carries a recommended answer with a half-line reason, so the user can reply "ok" to accept everything or override by number. End the message with how to answer.
- Before sending each round: `python3 .pilot-beckie/ap.py ask briefing --note "<о чём вопросы, коротко>"`. The answers close it through `answered`, or the next round's `ask` does.
- The next round is shaped by the answers: which rows they closed and which new ones they opened.

```
1. <Вопрос>
   Предлагаю: <ответ> — <зачем, полстроки>.
2. <Вопрос>
   Предлагаю: <ответ> — <зачем>.

Ответь по номерам («2 — другое, остальное ок») или просто «ок».
```

Rules for every question:
- Internally it points to the row it will close; if it closes none, it is not asked.
- **Facts you find out; only decisions are asked.** What stack the repo uses is a fact; the payment provider where the user holds an account is a decision.
- Unknowns that block go into round one: payment, hosting, existing accounts, where the data lives, any system to integrate with. Left for later, they cost half the project.
- Ask about decisions, not secrets: the provider and whether there is an account are fine to ask; the key never is.
- **Never answer for the user.** "I don't know" → the row stays live, the missing fact goes into «Основание», and the build places the visible stub marker `[ВПИШИ: <что>]` (`prompts/executor.md`).

## 2. What reaches the user (not in `full`)

The number of questions equals the number of open points in the brief, and zero is a valid number.
- `semi`: only forks whose branches give a visibly different product. Settle and record the rest yourself.
- `interview` / `manual`: every fork, plus everything the adversarial pass opened.

Decide yourself, in every mode: error wording, retry policy, defaults, naming, layout. But send a decision to the user if it:
- costs money or creates vendor lock-in;
- changes what the user sees or can do;
- would need a rebuild, not an edit, to undo;
- encodes a business rule (prices, deadlines, permissions, the fate of someone's data).

If you cannot tell which side it falls on, ask.

Nothing open → one line saying there are no questions and the spec comes next, then `python3 .pilot-beckie/ap.py stage briefing skip --note "вопросов нет"`.

Calibration only: `semi` usually 1–2 rounds; `interview`/`manual` 3–6 on a real project. Padding is what makes an interview bad, not length. If it will be long, say so once; never apologise for the count along the way. In `interview`/`manual`, do not drift into process questions (which stack? split tasks finer? show you the spec?) — this skill answers those itself.

## 3. Priority — ask only what is actually unresolved (every mode)

In `full` this is the list you put to yourself (§6), in this order.

1. External blockers: hosting, payment, domain, accounts with third parties, data that must be imported.
2. Findings of the adversarial pass, if it ran; no other questions can alter *what* is built.
3. Implicit requirements (`R##i`).
4. Depth only the user can settle: business-policy edge cases. At `strict`, only clarifications of what was already said.
5. Untestable wishes ("beautiful", "easy to use"): make them checkable the cheapest way, by asking what it should be like (section 4).
6. Places where the brief contradicts itself: quote each side and ask which one prevails.
7. Scope edges: what the user explicitly does not need. Answers become `dropped` rows and save tickets.

**Carry-over.** When `carried.md` exists, the items under «Не доделано» and «Известные баги» make up one question of round one regardless of what else that round contains, so round one always happens. Number the items and add a recommendation. Saying yes means the user adds a requirement: a fresh `G##` row containing their answer and the item they named, with identical wording placed under `## Дополнения`. Saying no, or not answering about an item, keeps it in the progress file; ignoring an item never drops it. Under `full`, no offer is made and no item is taken.

## 4. Reference — what it should be like (every mode)

- Anything the user gives that the result could be measured against (favourite sites, a competitor, screenshots, a text with the right tone, "like my bank's app") is recorded in `.pilot-beckie/<dir>/reference.md`, one line per item, word for word after redaction, with where it came from. Executors of tickets that build a user-facing surface get it (`phases/5-subagents.md`).
- The file holds the user's items only; you never contribute comparables of your own. If the user gave none, the file is not created.
- Comparables are not requirements: none of them turns into a manifest row or acts as a gate. A concrete demand ("must have a dark theme") is a requirement and goes into the manifest.
- Ask about references once at most, inside a round, and only if the product has a user-facing surface. Under `full`, `reference.md` contains just what the brief already mentions.

## 5. Recording answers (every mode)

After each round — in `full`, after each answer you give yourself — update rows at once:

| Answer | Manifest |
|---|---|
| a decision | recorded in «Основание» |
| a cancellation | status `dropped`, quoting the user |
| something new | a `G##` row worded as the user put it |
| "don't know" | the missing fact into «Основание»; row stays live |

Any answer that adds, cancels or reverses something is additionally written, dated and word for word, into the brief's `## Дополнения`.

### Changes mid-run (any phase, every mode)

One procedure for changes arriving at any time — a feature removed during Build, one added during Review:
1. **Start with the brief file**: put the user's words under `## Дополнения`. It goes first because this is the step people forget most.
2. **Manifest**: either `dropped` plus the quote, or a fresh `G##`.
3. **Plan**: the new `G##` turns into one of three things — a ticket, a `deferred` row, a report line. Tell the user which one and how it affects the rest (other work may move). Choosing a ticket means walking the whole path: spec story, row set to `in-spec`, a ticket file written, then `ap.py tickets` and `ap.py check-plan`; if a row bypasses the spec, neither of the last two can see it.

## 6. `full` mode: self-briefing

There is no interview. Run `python3 .pilot-beckie/ap.py stage briefing skip --note "автомат: брифинг без пользователя"`, then work through the priority list of §3 in its order, answering each item yourself, and record every answer per §5. §4 and «Changes mid-run» apply unchanged; under §3's carry-over rule nothing is offered.

- **You make the decisions** (stack, structure, provider, data model, layout). Choose options that run locally on the user's machine, cost nothing and need no third-party account. In «Основание» write exactly `ASSUMPTION — решено за пользователя: <что и почему>` (e.g. `ASSUMPTION — решено за пользователя: SQLite — работает локально и бесплатно`), and call `ap.py add debt.assumptions "<что и почему>"` with the same text. Each one becomes a report line.
- **Facts about the user are not yours** (prices, texts, addresses, business rules, brand colours). Name the missing fact in «Основание», have the code carry the visible stub marker `[ВПИШИ: <что>]` (e.g. `[ВПИШИ: цена]`; format defined in `prompts/executor.md`), never a plausible fake value — and add a report line.
- Any service that costs money or needs an account is wrapped in an adapter: a single interface backed by a local stub, with its credential listed by name, empty, in `.env.example`.

## 7. Close

Gate **G1**: each row has a status, and any row left `open` has its reason recorded. Send one brief line (got it, moving on to the spec) and enter Phase 3. Never recap the interview for the user.
