# Pilot by Beckie: design decisions

For maintainers. The agent never reads this file; it exists so the skill's instructions can stay short. Each entry is a decision and the reason it holds.

## Requirements and checks

- **The brief becomes a verbatim manifest, guarded by four gates.** The user's words are split into numbered requirements before anything is paraphrased. G1 (after briefing), G2 (after spec), G3 (after plan) and G4 (at acceptance) each check the run against that list. G2 and G4 are done by a subagent that sees neither the manifest nor the spec, only the brief and the artifact, so the orchestrator's own paraphrase cannot hide a gap.
- **The brief grows an addenda section.** Changes the user makes mid-run are appended to the brief file itself, not only to the manifest, because the independent checkers read the brief and nothing else.

## Who does what

- **The orchestrator never writes project code.** Nothing resets its context during a run, so any code loaded into it would make each subsequent decision worse.
- **One task, one executor, one fresh context.** No agent carries two tasks.
- **The spec populates the interfaces file ahead of task 01.** If it did not, the first task would set the module boundaries by accident.
- **Launch only by explicit command.** Model auto-invocation is disabled because the skill runs `git init`, writes files and commits.

## Sizing, review and repair

- **Size by code volume, about 3,000 changed lines per executor.** Not by spec length.
- **Targeted review is narrow.** It runs only for the foundation task and for tasks that own sign-in, keys, money or data deletion; it starts after the commit, runs alongside the next wave, and allows at most one re-check. A review of the whole branch always runs at the end.
- **Repairs get only the reviewer's BLOCKING lines, verbatim.** Passing the full review invites the repairing agent to widen its scope.
- **Wide changes go in three green steps:** put the new version next to the old one, move zones over one at a time, then remove the old version. Every step leaves the project passing its checks.

## Bookkeeping

- **One script call per event.** `ap.py` timestamps, recounts and renders; the call can be chained with the check and the commit that belong to the same event, so one event costs one turn.

## Dashboard

- **One source of truth, one page, no build step.** `state.js` holds the state; the page renders it. A snapshot is also embedded in the page so it shows something before the first fetch.
- **Served over http, not `file://`.** Embedded agent panels open `file://` as a `data:` page with a null origin, which cannot load `state.js`. The script serves the folder on `127.0.0.1`/`localhost` and the pane is navigated there.
- **Polling by script injection.** Panels block reloads, so every 10 s the page injects `state.js?t=…` as a new script element.
- **Server lifecycle.** At finish the server is stopped by a separate process about 12 s later, giving the page time to fetch the final state. The script recognises its own server strictly (`-m http.server` with the exact `--directory`) so it never kills a user's server. Restarts reuse the same port (`SO_REUSEADDR`), so an open tab recovers by itself.
- **Connection loss.** After two consecutive failed fetches the page displays a "connection lost" banner.
- **The refresh arrow means "refresh now"**, not an on/off toggle.
- **Time is computed by the script.** Working time and ETA come from `ap.py`: idle gaps are capped at 45 minutes and waits for the user are subtracted. The page only ticks the currently open interval.
- **Waiting is its own event**, so the page can switch state and stop clocks.
- **Feed, gate results and quotes are derived by the script**, not by the page.
- **Color is a state signal, not decoration.** Blue = being written and controls, green = delivered, violet = review, magenta = repair, orange = needed from the user, red = failed, gray = queued.
- **The narrow pane (380–900 px) is the primary screen.** Wide layouts are secondary.
- **The entrance animation plays only on the first render**, never on polls.

## Project memory

- **`AGENTS.md`, imported by a one-line `CLAUDE.md`.** Most agents read `AGENTS.md`; the import line covers Claude Code.
- **If the user already has a `CLAUDE.md`, no `AGENTS.md` is added next to it.** Claude Code would ignore the new file, and two parallel descriptions of the same project diverge over time.
- **Memory holds pointers, not a retelling** of the code.

## Maintenance rules

- Rationale meant only for humans lives in `docs/`, not in agent instructions.
- Mechanical work belongs in the script, not in the prompt.
- Never read the dashboard template into the agent's context, and never hand-edit it during a run.
- Test every new rule on a real run before keeping it.
