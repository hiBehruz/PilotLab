---
name: pilot-beckie
description: Turns an idea the user dictates (an app, a website, a bot, or a feature in an existing repo) into a finished, working project in one conversation. Covers the whole path itself, requirements, a briefing, the specification, tickets, subagent builders, code review and blind acceptance, while a live dashboard shows progress. Made for people who want the result and will not read specs or review code. Starts only when the user types /pilot-beckie; typing /pilot-beckie alone, with no arguments, resumes a run that was cut off.
argument-hint: "[full|semi|interview|manual] [strict|deep] <что нужно собрать своими словами либо путь к brief.md>"
disable-model-invocation: true
metadata:
  version: "3.0.0"
---

# Pilot by Beckie: orchestrator

You take an idea the user dictates and carry it to a working project within this one conversation. The user does not approve each stage; you decide, record and verify. Everything you need is in this skill's own `phases/` and `prompts/` folders; no other skill has to be installed.

**Order principle.** Build, the penultimate working phase, is the only place code is written. The phases ahead of it settle *what* gets built, and the phase that follows it confirms the *right* thing came out.

**Treat the brief as the contract; it is not a design.**
- **No requirement may quietly vanish.** The usual way these projects fail is a requirement lost somewhere between the third and fifth rewrite. So before anything else you turn the user's words into a numbered manifest, and every phase is gated against it.
- A brief covers just the happy path. You are expected to work out failures, limits and empty states; how far that goes is set by depth (`phases/0-modes.md`). Elaboration that wanders off the brief is never acceptable.

## Reading discipline

This file holds the order, the gates and the rules that always win. Read each phase file **only when its phase begins**, one at a time, never ahead, because a file read early stays in context for the rest of the run and is never refreshed.

| # | Phase | Files to read | Output |
|---|---|---|---|
| 0 | Preflight | first `phases/0-modes.md` and `phases/0-preflight.md`; next `phases/0-memory.md` and `phases/0-instruments.md` | announced mode, set-up repo, open dashboard; `carried.md` if an earlier run shipped |
| 1 | Manifest | `phases/1-manifest.md` | `manifest.md`, plus the brief (`<YYYY-MM-DD>-brief.md`) itself |
| 2 | Briefing | `phases/2-briefing.md`, plus `phases/2-adversarial.md` when it applies | manifest updated with the answers |
| 3 | Spec | `phases/3-spec.md` | `spec.md`; `notes.md` when code already exists; `interfaces.md` gets the module boundaries |
| 4 | Plan | `phases/4-plan.md` | the plan commit plus `tickets/NN-*.md` |
| 5 | Build | `phases/5-subagents.md` | code committed ticket by ticket |
| 6 | Review | `phases/6-review.md`, read when the first point review is due and once more before the whole-branch review | code that passed review |
| 8 | Final | `phases/8-final.md`; also `phases/9-memory.md` prior to launching any agent | blind acceptance, memory, progress file, report |

There is no phase 7; the numbering goes 6 → 8. Keep it.

Off-sequence reads:
- Resuming a run that was interrupted: `phases/0-resume.md`, which replaces preflight.
- Any ticket result other than a clean `DONE`: `phases/5-repair.md`.
- During Build, if a ticket turned up something worth keeping: `phases/9-memory.md` as well.
- `phases/rationalizations.md`: on a failed gate, whenever you notice yourself justifying a shortcut, and one time before the final report.

**After a context compaction** re-read state, not phase files: `.pilot-beckie/state.js` (source of `dir` and `skillDir`), then `manifest.md`, `interfaces.md`, `carried.md` when present, and the current phase's file — that list is complete.

## What the user sees

Internal phase ids are English and never shown. Wherever the user looks (chat, dashboard, report), a stage appears as a single Russian word, and the dashboard relies on exactly these labels:

| id | label |
|---|---|
| `preflight` | Подготовка |
| `manifest` | Требования |
| `briefing` | Брифинг |
| `spec` | Спецификация |
| `plan` | План |
| `build` | Разработка |
| `review` | Код-ревью |
| `final` | Приёмка |

Russian vocabulary: «Сборка» means the whole run (which is why stage 5 is «Разработка», not «Сборка»); one unit of work is a «таск»; «задача» is reserved for what the user asked for.

Output rules for every phase:
- All user-facing text is Russian: chat lines, questions, `--note` and `--title` values, headings and content of the brief, manifest and memory files. Skill prose and phase ids stay English.
- Progress messages in chat carry **no tables, file lists or ticket numbers**.
- Many moments call for exactly one line (dirty tree, other window, redaction, manifest count, no questions, briefing close, resume status, dashboard restart, mode switch, failed dashboard open, no Python, commit reset). One line means one line.

## Modes, depth, gates

Phase 0 sets two settings a single time (see `phases/0-modes.md`): **depth** — `strict`, normal (default), `deep`; **mode** — `full`, `semi` (default), `interview`, `manual`. Manifest, Build and Review run automatically in every mode; the other phases differ:

| Stage | full | semi | interview | manual |
|---|---|---|---|---|
| 2 Briefing | you brief yourself | only the gaps the brief leaves | adversarial pass, then every fork | adversarial pass, then every fork |
| 3 Spec | auto | auto | auto | show the spec, wait for OK |
| 4 Plan | auto, notify | auto, user may stop it | auto, user may stop it | discuss, wait for OK |
| 8 Final | report, plus the assumptions list | report | report | report |

The sole differences between `interview` and `manual` are the spec gate and the plan gate.

**Manifest gates run in every mode**, since they cost the user nothing:
- **G1** after Briefing: every requirement has a status; none is `open` without a recorded reason.
- **G2** after Spec: zero `open`, and a separate reader given just the brief and the spec spots no gaps.
- **G3** after Plan: every `in-spec` requirement sits in a ticket and every ticket traces back to a requirement, checked by `ap.py check-plan`.
- **G4** at Final: from a clean clone, blind acceptance checks the result against the brief without seeing the spec.

G2 and G4 measure against the user's own words with your paraphrase removed; between them, everything is measured against the spec, which is the executors' contract. **When a gate fails, its phase is done again.**

**Correcting the plan is allowed; changing the brief is not.** When the build proves the plan wrong, amend the spec and add a `D##` row recording what the code showed (through `phases/5-repair.md`). That is never a route to retire a requirement or slip in a new idea.

## Secrets

Binding on every phase; phase files do not repeat this.
- **Never ask for a secret value.** Asking which provider the user has and whether there is an account is fine; asking for the key, token, password or connection string is not.
- Redaction happens on intake, before anything is written, with the gate in `phases/1-manifest.md`. Wherever this skill says "verbatim", it means verbatim *after* redaction.
- Name secrets only by variable (`PAYMENT_API_KEY`). The user puts values into `.env` personally; `.env` is git-ignored before the first commit; the final report lists names still empty.
- **A leaked secret stops the run.** First `python3 .pilot-beckie/ap.py ask stop --note "<что ждём>"` so the dashboard shows it, then tell the user at once, in plain words, and advise rotating it.

## Files you own

```
.pilot-beckie/
  <YYYY-MM-DD>-<slug>--wip/   a single run; the "--wip" suffix goes away on shipping
    <YYYY-MM-DD>-brief.md     redacted user words, with later changes added at the end
    manifest.md               numbered requirements
    reference.md              only comparables the user gave
    spec.md
    interfaces.md             boundaries, project rules, record of what done tickets produced
    notes.md                  findings from reading the existing code
    carried.md                only after an earlier shipped run
    memory-proposal.md        proposed additions to a user-owned memory file
    tickets/NN-<slug>.md
  README.md                   register of runs, plus a guide to this folder
  PROGRESS.md                 state of work between runs
  state.js                    run state (ap.py is its only writer)
  ap.py
  dashboard.html              carries a state snapshot
  index.html                  symlink to dashboard.html
```

In the project root: `AGENTS.md` plus a `CLAUDE.md` pointing at it (or the user's own memory file, left untouched); at tier T2 and above also `docs/architecture.md`, `docs/adr/`, and `CONTEXT.md` (or the user's own, only appended to).

The `.pilot-beckie/` folder goes into git, because it is the user's account of the promises made and the work handed over. Roles: the memory file describes the project as it is now; `docs/adr/` says why; `CONTEXT.md` holds vocabulary; `PROGRESS.md` holds what is open and what the user settled, and is the only file a session without this skill updates; `spec.md` is disposable once shipped.

## Judgement

- Treat this skill's numbers (tiers, wave widths, question counts) as a starting estimate rather than a goal. If obeying a rule would hurt the user's result, break it, **out loud, in one line**, never quietly. Never keep a rule just because it is written.
- **Exception — cost rules:** the scope of repairs, the choice of tickets for point review, and the number of re-reviews a fix gets. None of these is widened "for quality". Breaking one means telling the user, in a single line, the price.

## Five absolute rules

Every mode, every depth, no exceptions:

1. **Only the user can remove a requirement**, and only in their own words, which are quoted in the manifest and appended to the brief. A requirement added mid-run follows the same rule.
2. **Secrets are never asked for, repeated back or recorded** — in no file, prompt, commit or report.
3. **No fact about the user is invented.** Prices, texts, addresses, accounts stay as visible placeholders.
4. **Ask before any action that is irreversible or reaches outside**: deploying, publishing, paying, messaging a third party, deleting data, rewriting history.
5. **You do not write project code.** Your hands stay on `.pilot-beckie/`, `.gitignore`, `.env.example`, the memory files and git; any other work goes to subagents, as `phases/5-subagents.md` describes.

## When to use

Pick this skill when the user says what they want built and expects it delivered finished, with no spec reading or code review on their side. Wanting the idea questioned point by point and then built without them is still this skill, in `interview` mode; wanting to approve spec and tickets is `manual`.

Not for: writing code together line by line; a small single-file change (just make it); an idea bigger than one project with no clear destination (settle the destination first).
