# Phase 0 — Preflight

Read at the very start, together with `phases/0-modes.md`. It decides which situation you are in, sets up git, picks the memory file, raises the dashboard and, after an earlier shipped run, carries its open items forward. **You ask the user nothing in this phase** — where files go is a process decision — apart from the two cases named in this file and in `0-modes.md` (two mode words; another window holds the run).

## 1. Which case (decide first; first match wins)

| Case | Signs | Do |
|---|---|---|
| Run active in another window | `state.js` has `finishedAt: null` **and** `updatedAt` is under five minutes old **and** the server whose PID is in `.pilot-beckie/serve.pid` answers | Nothing. One line to the user: the run is live elsewhere — which window should continue? |
| Resume | `state.js` with `finishedAt: null`, the row above not matched | Switch to `phases/0-resume.md`; it **replaces** this file. |
| New feature in a configured repo | `state.js` with `finishedAt` set | All steps below; the finished run's state gets archived by `init` into that run's own folder. |
| New run | no `.pilot-beckie/state.js` | All steps below, in order. |

"Another window" requires both marks. When two sessions write the same `state.js`, each clobbers the other's writes, and the one that finishes first leaves the other with a frozen dashboard. With only one mark present it is a plain interruption, so resume.

**More work on a run that already shipped.** When the user wants something added to the same run rather than a new one: the new brief becomes a new dated brief file in the same run folder (`phases/1-manifest.md`), then `python3 .pilot-beckie/ap.py reopen` (restores `--wip`, reopens stages from Требования on). After that, phases 1–8 run again for the new brief. Its requirements are added to the manifest under the next unused numbers, the spec gets amended, numbering of new tickets continues from the last existing ticket, and tickets already shipped remain shipped. Section 5 below also runs, since small fixes may have landed between the briefs.

## 2. Look before writing

- Git repo? `git rev-parse --git-dir`.
- `CLAUDE.md` / `AGENTS.md` — needed for the memory choice.
- Stack manifests (`package.json`, `pyproject.toml`, `go.mod`, `Cargo.toml`): if a stack is already there, keep it.
- Existing code: when present, exploring it comes before the spec (`phases/3-spec.md`).
- Vocabulary and settled decisions: `CONTEXT.md`, `GLOSSARY.md`, `docs/adr/`. Spec and tickets speak that vocabulary; whatever conflicts with a recorded decision is flagged, never quietly overridden.
- `.pilot-beckie/PROGRESS.md` — for section 5.

## 3. Git

- Not a repo → `git init` now.
- Create `.gitignore` first, before any other file, with at minimum:
  ```
  .env
  .env.*
  !.env.example
  node_modules/
  __pycache__/
  .DS_Store
  ```
- `.pilot-beckie/` stays tracked by git; `init` adds an ignore line just for its `serve.*` files.
- No commit happens before Phase 4 ends (`phases/4-plan.md`); that is where the first one is made.
- Uncommitted changes in the tree: mention them in one line and carry on. **Never stash, reset, clean or commit the user's work.** Every commit you make names explicit paths.

## 4. Memory and instruments

1. Read `phases/0-memory.md` and choose the memory file. **Do not read `phases/9-memory.md` now.**
2. Read `phases/0-instruments.md`: copy template and tool, run `init` with the memory choice, open the dashboard. Its command table is your complete instrument reference for the rest of the run.

Slug: short, kebab-case, Latin letters (`flower-shop-catalog`), fixed for the whole run. `init` names the run folder `<YYYY-MM-DD>-<slug>--wip` (date = run start; the suffix stays until the run ships) and stores it as `dir` in `state.js`. **Build every path from `dir`**, never from the slug.

## 5. Carry-over from the previous shipped run

Skip entirely on a first run. Run it when a run has shipped before: `PROGRESS.md` exists, or a commit with subject `Pilot by Beckie: сборка сдана` exists.

1. Read `PROGRESS.md` in full.
2. Read the history since that commit — code only, skill files excluded, never the whole log:
   ```sh
   L=$(git log -1 --format=%h --grep='^Pilot by Beckie: сборка сдана')
   git log --oneline --no-merges "$L"..HEAD -- . ':(exclude).pilot-beckie'
   ```
   A commit already listed under «Правки без Pilot by Beckie» in the progress file is accounted for. For any other, take only its message and `git show --stat <sha>`. More than about 30 commits → hand the reading to one subagent on a cheaper model that returns about ten lines (what changed, where, anything that looks like a decision); keep only that list.
3. Create `.pilot-beckie/<dir>/carried.md` holding a snapshot of the four sections of the progress file, plus a section «Изменено после сборки» with one line per change from the log. This is needed because the progress file is rewritten when this run ships and your context will not last the run.

Use each part exactly once:

| Part | Use |
|---|---|
| «Договорились — не пересматривать» (older files: «Договорились») | The spec must obey it, as it would an ADR; Phase 3 transfers it to `interfaces.md` as project rules. Should a new brief contradict it, tell the user; do not quietly follow or ignore either side. |
| «Не доделано», «Известные баги» | You offer these to the user and never pick them up on your own; the question comes in Phase 2's first round. Under `full` none is taken, and they stay in the progress file. |
| «Изменено после сборки» | Given to the Phase 3 exploring subagent so `notes.md` describes the current code. |

Do not mention empty parts.

## 6. Announce and go

- Post the opening block described in `phases/0-modes.md` (mode, depth, memory file, dashboard address, and the `↑` line whenever `init` printed it).
- After an earlier shipped run, add one line with the carry-over counts (unfinished items, bugs, edits made without Pilot) saying they will come up in the briefing. In `full` say instead that they are not taken into this run and stay on the list.
- Ask nothing here: run `python3 .pilot-beckie/ap.py stage manifest`, then move directly on to Phase 1.
