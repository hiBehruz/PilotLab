# Rationalizations checklist

Read this file at exactly three moments: when a gate fails; when you notice yourself arguing to skip something; once before the final report. It covers the long tail. The five absolute rules live in `SKILL.md`.

## Temptation → what to do instead

| If you catch yourself thinking… | Do this |
|---|---|
| "The user said no questions." | Still ask the decisive questions. Only superfluous ones are dropped. |
| "The brief is in the dialogue; no file needed." | Write it to its file. Dialogue gets compressed, oldest first. |
| "They stopped mentioning it, so it's cancelled." | Silence never cancels. You may propose `deferred`; only the user removes, by quote. |
| "They changed their mind — edit the manifest, the brief is immutable." | Never rewrite what was said, but always append the later words under the brief's `## Дополнения`. Independent checkers never see the manifest. |
| "Log this mid-build wish as a `D##`." | User words are always `G##`, plus a `Дополнения` line, plus an explicit statement: taken as a ticket, deferred, or to the report. |
| "Stub payment/hosting/accounts; they'll clarify later." | These are resolved in the briefing's first round, before the build. |
| "The executor failed / it's two lines — I'll do it." | Дозапрос or a fresh context. Never your keyboard. |
| "Short brief, so short spec." | The brief is a silhouette. At `normal`/`deep`, work out empty states, errors, interruptions. |
| "I thought of a useful feature." | Deepening: yes. A new capability: only with a parent, in proportion, and reported. Never at `strict`. |
| "Full auto means I can deploy." | Automation removes product questions, not the duty to ask before irreversible actions. |
| "In full auto I can invent everything about the user." | Decisions: yes, each logged as `ASSUMPTION`. Facts about the user: no — placeholder plus a report line. |
| "I'll check coverage myself; I wrote the spec." | At G2 and G4 a subagent reads from the brief, without spec or manifest. |
| "The testing rule is in a phase file, so it applies." | Only what is in the executor's prompt or `prompts/executor.md` reaches it. |
| "Interfaces will settle; ticket 01 will define them." | Decide boundaries in the spec. |
| "I'll write the report from memory." | Build it from files re-read from disk. |
| "Nothing blocking, but since it's found, fix it." | Only `BLOCKING` blocks; the rest waits for the branch review. Widening = a one-line note to the user with its cost. |
| "Simple ticket; skip its marked review." | `Ревью: да` in the plan is binding. Foundation and risk tickets are always reviewed — after the commit, without holding the build. |
| "Built and green means it works." | Tests share authorship with the code. Until someone actually runs the project, "works" is a hypothesis. |
| "They didn't ask about modes; don't burden them." | The opening announcement is the only place they learn the run's knobs. Always announce. |

## Red flags — redo the phase

If any of these is true, go back and redo the phase where it happened:

**Brief and manifest**
- Code appeared while there was still no spec, or the brief never made it into a file.
- A requirement lacks a status, or is `dropped` with no quote from the user.
- A requirement quietly narrowed to what worked, or the spec amended without a `D##`.
- An invented user fact where a stub belongs.

**Announcement, briefing, depth**
- Started without announcing mode and depth, or behaving differently from the announcement.
- Announced depth contradicting the spec: bare restatement at `normal`/`deep`; any `A##` at `strict`.
- `reference.md` lists a comparable that did not come from the user.
- In `interview` the adversarial pass was skipped, or it served to persuade the user to give up a requirement.
- A blocking unknown (payment, hosting, account, data location) left unasked because the brief seemed clear — or a question invented to fill a round.
- A process question outside `manual` (tracker, memory file, ticket granularity).
- A promised time-based wait that cannot be honoured.

**Spec and plan**
- Spec or tickets existing only in the dialogue.
- `ap.py check-plan` left with `!` lines.
- Dashboard disagreeing with chat: stale active stage, ticket running but shown not started, `state.js` hand-edited.

**Gates and isolation**
- G2 or G4 judged by you.
- A blind, coverage or memory agent received the spec, manifest or tickets, or was not forbidden to open `.pilot-beckie/`.

**Build**
- One context or one commit holding two tickets.
- A commit picking up files beyond the ticket's zone, or sweeping in the user's own work.
- You editing files outside `.pilot-beckie/`, memory files, `.gitignore`, `.env.example`.
- Your context took in a diff or a raw test log.
- A дозапрос included anything beyond the reviewer's `BLOCKING` lines.
- Executors working on the same files at once, or independent tickets forced into sequence.
- A subagent started without `prompts/executor.md` or `interfaces.md`, or returned without its contract block.
- A dependency nobody decided on was installed, or something was installed outside the project (system packages, global tools).

**Review**
- A reviewer reused across tickets.
- A `Ревью: да` ticket finished without its review.
- A wave held to wait for a review.

**Secrets**
- A secret requested, echoed, or written anywhere.

**Landing**
- The report composed from memory rather than files and checker returns.
- A `T2`+ run finished without a single ADR.
- Nobody ever actually ran the finished project.
- Edits to text lying outside the pilot-beckie markers; the user's memory file written without approval; a run ending with neither memory file nor proposal.
