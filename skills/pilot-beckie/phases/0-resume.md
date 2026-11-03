# Phase 0 — Resume an interrupted run

Open this file only if `state.js` is present with `finishedAt: null` and the run is not held by another window (`phases/0-preflight.md`, section 1). **Your memory is the files**: leave the old dialogue unread, leave finished phases finished, and leave answered questions answered.

1. **Reading order:** first the memory file (`memoryFile` in state), then `state.js` (`dir`, `skillDir`, `mode`, `depth`, `tier`, stages, tickets); `interfaces.md`; `manifest.md`; all `*-brief.md` files in `dir` from oldest to newest, `## Дополнения` included; `carried.md` if present; then the phase file of the active stage.
2. **Re-raise the instruments.** Run the copy step from `phases/0-instruments.md` (that way an older run receives the current page and `ap.py`), followed by a bare `python3 .pilot-beckie/ap.py` to restart the server on the port it used before. Point the pane at it again every time and give the address.
3. **One line to the user** on where things stand: tasks done out of total, what comes next.
4. **Check commits** with `python3 .pilot-beckie/ap.py commits`. A `!` line marks a `done` ticket whose commit has disappeared from `HEAD` (after a reset, a rebase, a branch switch). Say so in one line, run `ticket <id> reset`, and relaunch it as in step 5. A rebase may have left the code in the zone with a different sha, in which case the executor completes the ticket from there. **History is never rewritten to recover a commit.**
5. **Tickets interrupted while running** (status `in-progress`, `review` or `repair`, no commit yet): `ticket <id> reset`, then relaunch as ordinary tickets. Tell the new executor its zone may hold uncommitted edits from the interrupted attempt and that it decides whether to finish from them or discard them. **Do not commit a partly applied ticket in its current state.**
6. **A `waiting` entry** still sitting in `state.js` means the interrupted session had asked something. Re-ask it if still open; if the dialogue shows it was answered, call `answered`.
7. **Before launching anything, run the project's check one time.** On red, include the failure in the prompt of the next executor, so it does not blame itself for breakage that was already there.
8. **Pick up at the frontier:** either the phase in progress or whichever tickets are next ready to launch.
