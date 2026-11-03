# Phase 0 — Instruments: dashboard and ap.py

Read once, in Phase 0. The user follows the run on `.pilot-beckie/dashboard.html`, a template copy that renders `.pilot-beckie/state.js`. **Neither file is ever hand-edited.** Each run event maps to a single `ap.py` call: it stamps the time, recounts requirements from `manifest.md`, closes passed stages, writes a state snapshot into the page and keeps a local static server alive. The command table in section 4 is your instrument reference for the whole run.

Where `python3` does not actually run (on Windows it can be the Store stub), substitute `python` or `py -3` for every `python3` in this skill.

## 1. Copy template and tool

Run on every run — new repo, new feature, resume. Each step is idempotent, and re-copying picks up improvements from the installed skill.

```sh
A="$(git rev-parse --show-toplevel 2>/dev/null || pwd -P)/.pilot-beckie"
T=$(find -L ~/.claude/skills ~/.agents/skills ~/.claude/plugins .claude/skills .agents/skills \
      -maxdepth 6 -path '*pilot-beckie/phases/dashboard-template.html' 2>/dev/null | head -n 1)
[ -n "$T" ] && T="$(cd "$(dirname "$T")" && pwd -P)/$(basename "$T")"
[ -n "$T" ] && command -v cygpath >/dev/null 2>&1 && T="$(cygpath -m "$T")"
S="${T%/phases/*}"; echo "skillDir = $S"
mkdir -p "$A" && cp "$T" "$A/dashboard.html" && ln -sfn dashboard.html "$A/index.html"
cp "$S/tools/ap.py" "$A/ap.py"
```

- `find -L`, because skills are installed through symlinks that plain `find` does not follow. Keep the `*` pattern quoted: an unmatched unquoted glob aborts the whole line in zsh.
- The `-path` filter keeps you from picking up another skill's dashboard template (a fork, say).
- `cygpath -m` on Windows gives `C:/...`, not `/c/...`.
- Empty result: widen the search by hand once, then continue.
- Thanks to the `index.html` symlink, a request for `/` returns the dashboard rather than a folder listing.
- **`skillDir` is essential.** Subagent contracts (`prompts/executor.md`, `prompts/review.md`) are passed as paths built from it. Hand it to `init` so that `state.js` keeps it; your context alone is not a safe place for it.
- **Never regenerate, read into context, or edit the template.**

## 2. Start the run

```sh
python3 .pilot-beckie/ap.py init --slug <slug> --title "<название по-русски>" \
  --mode <mode> --depth <depth> --memory-file <file> --memory-owner <pilot-beckie|user> \
  --skill-dir "<skillDir>" --check-update
```

`init`:
- makes the folder `<YYYY-MM-DD>-<slug>--wip/` containing `tickets/`;
- creates `state.js` listing the eight stages, with `preflight` marked active;
- registers the run in `.pilot-beckie/README.md` (the file is created in a fresh repo);
- adds `.pilot-beckie/serve.*` to `.gitignore`;
- launches the server, then prints the address it listens on.

If the existing `state.js` belongs to a finished run, it is archived into that run's folder first. If the run is unfinished, this is a resume: `init` declines, and `phases/0-resume.md` applies. The tool has a `--force` flag; do not use it.

A printed line starting with `↑` means a newer skill version exists. Put it into the opening block verbatim as one line, not a question. **Never update mid-run.**

## 3. Open the dashboard

Open it once, right after `init`, before Phase 1 asks anything. On resume, always re-point it (tabs do not outlive sessions).

- **Side pane next to the chat, over http (first choice).** Claude Code: call `preview_start` with `url: "http://localhost:PORT"`, and after that `navigate` to `/dashboard.html`. Calling `navigate` on localhost without a prior `preview_start` gets refused; `127.0.0.1` is refused as well. Missing `preview_start` in your tools? Look among the deferred tools before you conclude no pane exists. **Never give the pane a `file://` path**: it loads as `data:`, cannot fetch `state.js`, and the clocks stop.
- **Put the address in chat every time, too** — in some clients the pane appears merely as a card carrying an Open button.
- **No pane:** run `open` / `xdg-open` / `start` with `.pilot-beckie/dashboard.html`. Loaded from `file://`, a real browser keeps polling `state.js` without help.
- With `$SSH_CONNECTION` or `$CI` present → only print the path; do not open anything.
- If opening fails, that is not an error: give the path in a single line and go on.
- The server binds only `127.0.0.1` and serves only the run's files.
- **No working Python at all** → no tool, no dashboard. Mention it in one line, go without the dashboard, maintain manifest statuses manually and verify G3 manually against the ticket files. Everything else is unchanged.
- **User says the dashboard died** (machine slept, server gone): run a bare `python3 .pilot-beckie/ap.py`. That brings the server back on its old port, and the open tab reconnects unaided; point the pane again only when the printed address is different. Report it in one chat line and do not dig further.

## 4. Event → command

Every command is `python3 .pilot-beckie/ap.py …`.

| Event | Command |
|---|---|
| entering a phase | `stage <id>` (the previous stage closes itself) |
| a phase skipped on purpose | `stage <id> skip --note "<причина>"` |
| tier chosen | `set tier=T2` |
| ticket files are on disk | `tickets` (publishes all; manifest `in-spec` → `in-ticket`) |
| G3 check | `check-plan` |
| plan commit made | `set baseCommit=<sha>`, chained with the commit (`phases/4-plan.md`) |
| ticket / wave launched | `ticket 02 03 start`, before dispatching subagents |
| ticket sent to point review | `ticket 02 review` |
| blocking finding returned to the executor | `ticket 02 repair --note "<условие одной строкой>"` |
| failed ticket restarted | `ticket 02 retry` |
| commit for a ticket made | `ticket 02 done --tests 34/0 --commit <sha>` (add `--placeholder R05` when a row got a stub); closes manifest rows whose tickets are all done |
| ticket failed for good | `ticket 02 fail --note "<блокер>"` |
| deferred finding | `add concerns "<file:line — проблема>"` |
| empty env var / stub / assumption | `add debt.emptyEnv NAME`, `add debt.placeholders "…"`, `add debt.assumptions "…"` |
| code now contains an `A##` | `add additions "<что — для R01>"` |
| something to include in the final report | `add report "…"` |
| outcome of G2 | `coverage found=N fixed=N deferred=N --item "<R07 — отложено: …>"` |
| blind acceptance (single call) | `blind checked=N matched=N --mismatch "…" [--mismatch "…"]` |
| full check run between tickets | `tests 34/0` |
| waiting on the user (stop condition, briefing round, manual spec/plan gate, yes/no before an irreversible action) | `ask briefing\|spec\|plan\|action\|stop --note "<чего ждём, в одну строку>"` — never chained; the message goes out after it |
| answer received | `answered` — or nothing, if the next call is `stage` or `ticket` (they close the wait) |
| run ships | `finish --result "<одна строка: что теперь есть>"` |
| resume, before relaunching | `commits` (checks every done ticket's commit is still in `HEAD`; a `!` line = ticket to reset) |
| reopen a shipped run / reset a ticket / sync and re-raise the server | `reopen`, `ticket <id> reset`, bare call |

Rules:
- One `add` call accepts multiple values.
- Join each tool call to the command of the same event, keeping an event to a single turn (for example a ticket's commit together with its `done`, step 7 of `phases/5-subagents.md`). **Do not chain a commit behind a check until you have read that check's output** — exit status of `| tail` is always 0.
- `!` lines come in two kinds. From ordinary calls (stage skipped in the books, ticket without `start`) they are bookkeeping: fix in the same turn with one call, do not investigate. From `check-plan` they are plan defects: G3 does not pass until none remain.
- Some statuses are invisible to the tool: `in-spec`, `deferred`, `dropped`, and fresh `G##` or `D##` rows. Those you change in `manifest.md` yourself. `in-ticket`, `done`, `placeholder` belong to the tool. Dashboard counts update on the next call.
- **Never put a secret value in a call.** `emptyEnv` accepts nothing but names; the note of an `ask` describes what you are waiting for and never contains a value.
- Only `ask` switches the page to "waiting for you" and stops its clocks, since the user's answer time is not build time. A question sent without it leaves the page counting as if work went on.
- Every ten seconds the page redraws; it measures working time, not wall-clock time, and stops at `finish`. This is said once in the opening block; never explain it in chat.
- After each ticket, send the user one plain line: what is now possible, plus done out of total. No file lists, no ticket numbers.
