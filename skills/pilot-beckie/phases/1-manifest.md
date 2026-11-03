# Phase 1 — Manifest

Read when Phase 1 begins (after `stage manifest`). The brief is the only artifact the user really wrote; everything after it is your paraphrase. This phase turns it into something that survives every rewrite. It comes **ahead of** the briefing, since asking questions already re-encodes the brief.

## 1. Redaction gate

Every piece of user text — the brief, each answer, each pasted fragment — passes this gate before it reaches a file, a prompt or the dashboard.

Look for:

| Kind | Pattern |
|---|---|
| OpenAI / Stripe style prefixes | `sk-`, `sk_live_`, `sk_test_`, `rk_live_`, `pk_live_` |
| Slack | `xoxb-`, `xoxp-`, `xoxa-` |
| Google | `AIza`, `ya29.` |
| AWS | `AKIA`, `ASIA` |
| GitHub | `ghp_`, `gho_`, `ghs_`, `github_pat_` |
| Telegram bot token | 8–10 digits + `:` + 35 characters from `[A-Za-z0-9_-]` |
| JWT | `eyJ` followed by `.` and further base64 |
| Private key | `-----BEGIN ... PRIVATE KEY-----` |
| Connection string | `<scheme>://<user>:<something>@<host>` |
| Generic | 32 or more hex/base64 characters beside a key/token/secret/password word such as `key`, `token`, `secret`, `password`, `ключ`, `токен`, `пароль`, `доступ` |

When something matches:
1. Replace the value with `[REDACTED:<VAR_NAME>]`, using the conventional name (`STRIPE_SECRET_KEY`, `TELEGRAM_BOT_TOKEN`, `DATABASE_URL`).
2. Add that name with an empty value to `.env.example`.
3. Tell the user in one plain line: the key was not saved; put it into `.env` yourself; revoke and reissue it, because it has passed through the chat.
4. Continue.

**The value is never repeated back**, even as confirmation of the find. Ahead of the first commit (the plan commit closing Phase 4), pass the whole of `.pilot-beckie/` through the gate.

## 2. Brief file

Save the brief, redacted but otherwise verbatim, as `.pilot-beckie/<dir>/<YYYY-MM-DD>-brief.md` dated today, and run `python3 .pilot-beckie/ap.py set briefFile=<name>`.

```markdown
# Исходная задача

> Записано <YYYY-MM-DD>. Текст задачи не редактируется: по нему проверяют результат. Всё, что сказано позже, дописывается ниже в «Дополнения».

<полный текст пользователя после редактуры секретов>

## Дополнения

- <YYYY-MM-DD>: «<слова пользователя дословно>»
```

- **Do not paraphrase, clean up or reorder.** Contradictions and poor grammar are kept, because once tidied the brief turns into a spec and stops being something to check against.
- All of it is part of the brief: constraints, asides, "would be nice too", stack preferences, a deadline mentioned in passing.
- The original text never changes; the file only grows. Every later statement — cancellation, addition, reversal, at any point — goes under `## Дополнения`, dated and verbatim. Reason: both independent checks (G2, G4) read the brief and may not read the manifest, so a change made only in the manifest does not exist for them.
- When more brief arrives on a later day, it gets its own file, dated that day, inside the same run folder.

## 3. Manifest

Break the brief down as finely as possible, so that every unit on its own can be true or false of the finished product. Write them to `.pilot-beckie/<dir>/manifest.md`, each row carrying the user's exact words.

```markdown
# Манифест требований

Источник: `<YYYY-MM-DD>-brief.md`. Убрать строку может только пользователь.

| ID | Дословно из задачи | Статус | Основание | Где |
|---|---|---|---|---|
| R01 | «<слова пользователя>» | open | | |
| R02 | «<…>» | open | | |
| R03i | (подразумевается) <что следует из R02> | open | | |
```

- **Column order is fixed**: the tool reads the ID from column 1 and the status from column 3, and appends ticket numbers and commits to column 5 («Где»). Write a `|` inside a quote as `\|`.
- IDs: `R`, `G` or `D`, two-digit zero-padded number, optional single lowercase suffix: `R01`, `R06i`, `G03`, `D02`.

### Statuses (exact tokens)

| Status | Meaning | Set by |
|---|---|---|
| `open` | unresolved; initial value | — |
| `in-spec` | covered by the spec, section recorded | you |
| `in-ticket` | some ticket will deliver it | `ap.py tickets` |
| `done` | committed after being built | `ap.py ticket … done` |
| `placeholder` | built, but a visible stub stands where a fact from the user goes | `ap.py ticket … done --placeholder` |
| `deferred` | postponed on purpose; the spec's «Вне рамок» has a line for it | you |
| `dropped` | cancelled by the user | **only the user** |

- When the user is still missing a fact ("prices later"), the row does not turn into a placeholder ahead of time. It remains live and passes through spec and ticket as usual, with the missing fact named in «Основание»; it becomes `placeholder` once the stub exists.
- For `dropped`, «Основание» must quote the user directly. Suggesting a drop is allowed only in the form of a question, never by editing the status.
- `deferred` is not `dropped`: every deferred row appears in the final report under what was not included.
- **Silence never cancels.** If the user simply stops bringing a requirement up, it remains live.

### Row kinds — never blur them

| Prefix | Origin |
|---|---|
| `R##` | the original brief |
| `R##i` | implicit: what the brief clearly implies but never says (taking orders implies somewhere to read them). Routed to the briefing as a question; in `full` becomes an `ASSUMPTION` in the report. |
| `G##` | added by the user later, in their words |
| `A##` | your own idea, a new capability under a parent requirement (`phases/3-spec.md`); never a manifest row of its own |
| `D##` | a constraint unknown to the plan that the build turned up |

- Once the briefing is over, the one row type you can still add is `D##`, and solely via `phases/5-repair.md`. Apart from that, the manifest grows only by a `G##` the user requested.
- No requirement is ever retired by a `D##`. A `D##` carries the status `in-spec` (pointing at the amended section); it is a constraint, not counted as a requirement, and needs no ticket of its own.

**Granularity:** one row = one thing that is independently true or false; a sentence joining two actions gives two rows. For calibration: around 2000 words of brief typically give 25–50 rows. A long brief reduced to under 10 rows has been summarised, not split.

## 4. Tell the user

One line: how many requirements the task became, and that each will be tracked to the end. No table in chat.

## 5. Gates (defined here, run later)

Gate failure is not a warning; it sends the phase back to be done again.

- **G1, after Briefing:** no row is without a status, and each row left `open` has its reason written down (in «Основание», the fact the user will provide later). In `full`, no question remains open. The tool computes G1 itself when `stage spec` is entered or completed, counting `open` rows except `D` rows.
- **G2, after Spec:** no `open` rows remain, and a separate reader holding just the brief and the spec detects no gap (`phases/3-spec.md`).
- **G3, after Plan:** `ap.py check-plan` confirms each `in-spec` row belongs to a ticket and each ticket maps back to a row (`phases/4-plan.md`).
- **G4, final phase:** blind acceptance compares the result with the brief while the spec stays hidden (`phases/8-final.md`).

## 6. Keeping it current

Edit only the affected rows; never rewrite the table. The tool moves rows to `in-ticket`, `done`, `placeholder`. You change rows:
- whenever a briefing answer comes in;
- once the spec is written (`in-spec` / `deferred`);
- when a `D##` appears;
- when the user alters something mid-run: either `dropped` with their quote or a fresh `G##`, with that wording also appended to the brief's `## Дополнения`. Procedure: `phases/2-briefing.md`.
