# Phase 2 — Adversarial pass

Open this file only for runs where the pass applies: depth `deep` under any mode, or mode `interview`/`manual` under any depth. Apply it to `manifest.md` and the brief file **ahead of the first briefing question**.

Ordinary briefing questions target gaps in the brief. This pass looks instead for the points where the idea itself fails. A brief may be full and free of contradictions yet describe something unworkable; since every later check compares the build with the request, no downstream step would notice.

## Seven angles

Apply them to the task yourself; do not pose them to the user.

1. **Empty room.** It shipped, it works, nobody uses it. Why?
2. **Clash.** Which two manifest rows cannot both be true?
3. **Taken for granted.** What does the user treat as settled that is not — that people will come, that data will appear from somewhere?
4. **Expensive corner.** Which requirement would eat half the build for a small share of the value, and does the user know?
5. **Missing precondition.** What, absent from the brief, makes the result pointless if it is missing — who fills it with content, who maintains it, where the first data comes from?
6. **Week two.** What happens when the novelty wears off — growth, duplicates, moderation, support, other people's hands?
7. **Someone else.** Who besides the described user will touch it?

Normal yield is 5–7 findings. On a real project, under 3 findings signals the pass was a formality.

## Routing — by mode, not by how alarming the finding looks

| Finding | Route |
|---|---|
| Only the user can settle it | `full`: `ASSUMPTION` in the manifest and the report. `semi`: asked only when the alternatives would lead to products that clearly differ. `interview`/`manual`: asked, no later than the second round. |
| Craft you can settle | decide it and write it into the spec — all modes |
| A whole capability | `A##` under its parent requirement, or a «Вне рамок» line; in `interview`/`manual` may instead be offered as a question |
| Outside the task | one line in «Вне рамок» — all modes |

- **Nothing gets removed by this pass.** What comes out is questions, `A##` stories, `ASSUMPTION` rows and «Вне рамок» lines; it never yields a `dropped` row or a requirement narrowed on the quiet. If you consider a requirement a bad idea, you get one question at most, stating what it costs.
- **Challenge the task, not the person.** Concrete operational questions ("who answers incoming orders on a Sunday?") are right. Doubting whether the idea is needed at all is an opinion, and is not allowed.
