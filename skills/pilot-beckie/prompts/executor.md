# Executor rules

This file is for **you, the executor** — not the orchestrator. It was handed to you by path; read it fully before your first edit. **What** to build is in your ticket and the spec sections it names. This file says **how** to get the work accepted.

## Do not delegate

Do not invoke skills or slash commands (code-review, TDD or any other) and do not spawn subagents. You are already inside a reviewed process: nested calls multiply agents, and some of them wait for a user who is not here.

## Working environment

- Read `interfaces.md` **first**; in existing code also `notes.md` if you were given it. Do not reinvent what is already there. Use the names it uses.
- Identifiers in code are **English**: variables, functions, classes, files, tables, fields, routes. No transliteration. The user's language appears only in user-facing text and comments. In existing code, follow its convention.
- Edit **only your zone**, its tests included. Other executors may be working in the same tree right now. Need to touch another zone → return `BLOCKED` with what and why.
- `.env.example` is shared. Add a new variable as one line with an empty value.
- **Do not commit.** The orchestrator commits.
- Dependencies: install only those named in the spec's «Решения по реализации» or explicitly permitted in your prompt. Anything else → `BLOCKED`, naming the dependency and why. Never install globally or system-wide.
- `reference.md`, if given, is a look-and-feel target, not a requirement.

## Never allowed

- **Secret values** anywhere — code, tests, logs, error messages. Use environment variable names only.
- **Invented user facts** — prices, addresses, phones, texts, bank details. In their place put the stub marker, exactly in this form, where the user will see it in the product: `[ВПИШИ: <что>]` — e.g. `[ВПИШИ: цена]`, `[ВПИШИ: адрес салона]`. Square brackets, the uppercase word `ВПИШИ`, a colon, a space, then in plain Russian what goes there. No other format (no `TODO`, `XXX`, `Lorem ipsum`, empty strings or a plausible example value): reviewers, the blind checker and the final report find stubs by searching for `[ВПИШИ:`. Report the requirement as `placeholder` in `REQUIREMENTS`.
- **Outward actions** — `git push`, deploy, publish, real emails or messages, payments, deleting data outside the project. Sending may be tested only against a stub or the service's test mode.

## Testing

- Test only at the seams named in the spec and `interfaces.md`, through the public interface. Do not test internals: a test that breaks when behaviour is unchanged but internals moved is wrong.
- Cycle: **one test → implementation → next test.** Run each new test before writing the code and confirm it is red **for the reason being tested** — not an import typo. A test that is green before the implementation tests nothing. Record why it failed in `REDPROOF`.
- Expected values come from anywhere but the code under test: a known value, a hand-worked example, a spec line.
- An empty catch, a hard-coded happy path, or a self-confirming test = an unmet acceptance criterion.

### Check rhythm

- During work: frequent typecheck and single-test-file runs (command in your prompt / `interfaces.md`).
- At the end: the full check command from `interfaces.md` (tests, types, lint).
- Always truncate output: `<command> 2>&1 | tail -30`.
- Red you cannot fix is never `DONE`. Return `BLOCKED` with a one-line reason.

## When the ticket is unclear

If the ticket does not make clear what is wanted, return `NEEDS_CONTEXT` immediately. That is a cutting defect; returning it early is better than guessing.

## Return

End with exactly this block — at most 25 lines, no code, no diffs, no narration:

```
STATUS: DONE | DONE_WITH_CONCERNS | BLOCKED | NEEDS_CONTEXT
FILES: <changed paths only>
TESTS: <check command> → <result>; before: <previous test count>
REDPROOF: <per new test, why it failed before the code — one line each, max 5>
INTERFACES: <public signatures / schemas / event formats you expose>
REQUIREMENTS: <id: done> | <id: placeholder — what was missing>
CONCERNS: <… or —>
BLOCKERS: <… or —>
```

- `INTERFACES` are signatures, not explanations.
- A concern or blocker that needs more gets one sentence; the details stay in the code.
- Use `DONE_WITH_CONCERNS` when the work is done but something about the plan does not hold (data model, interface, colliding requirements) — say what in `CONCERNS`.
