# AGENTS.md - E.D.E.N. Protocol

This repository uses the E.D.E.N. Protocol. `.eden/` holds project state; `scripts/eden-audit.py` checks it. These rules apply to every agent and human working here.

## Commands
Fill these in for this project and keep them current.
- Setup: `<fill in>`
- Build: `<fill in, or "none">`
- Test: `<fill in>`
- Lint: `<fill in, or "none">`
- Verify: `python3 scripts/eden-audit.py --verify` (runs `.eden/verify` or `.eden/verify.py` when present; put test and lint there)

## Pick a lane first
- **Read-only** (questions, reviews): read what you need and answer. Change nothing; skip Normalize.
- **Trivial** (typo, comment, formatting, docs-only): make the change and run the audit. No plan or registry update.
- **Normal** (code change inside the existing design): run the full loop.
- **Architectural** (new module boundary, new dependency, schema or data change, deleting a component, touching an invariant in `.eden/ARCHITECTURE.md`): Evaluate and Define, write the plan into `.eden/PLAN.md`, then stop and wait for human approval before Execute.

## The loop
1. **Evaluate** - Read `.eden/ARCHITECTURE.md`, `.eden/REGISTRY.md`, `.eden/LEARNINGS.md`, and the last 10 lines of `.eden/CHANGELOG_AGENT.jsonl`.
2. **Define** - Check `.eden/PLAN.md`. Search the registry before adding a helper, class, or package; reuse or extend what exists. Name the files you will touch.
3. **Execute** - Make the smallest change that meets the acceptance criteria. Prefer the standard library.
4. **Normalize** - Register new or changed source files in `.eden/REGISTRY.md` (`python3 scripts/eden-index.py .` helps). Append one JSON line to `.eden/CHANGELOG_AGENT.jsonl` whose `files` lists every changed source file. Add verified root causes to `.eden/LEARNINGS.md`. Update `.eden/PLAN.md`.

## Skills and stop hook
- Shared skills live in `.agents/skills/`: `eden-normalize` (finish a change), `eden-architect` (plan an Architectural change), `eden-adopt` (first pass on an existing project).
- When you end a turn with changed source files, the stop hook (`scripts/eden-hook.py`) runs the audit. If it reports errors, fix them; it forces at most 2 extra rounds, then you report what still fails.

## If the request conflicts with PLAN.md
The human's current request wins. If it contradicts an acceptance criterion or invariant, say so before starting, then update `.eden/PLAN.md` to match what was done.

## Done means
1. Tests and `.eden/verify` pass, or you report exactly what fails and why.
2. `python3 scripts/eden-audit.py --verify` exits 0.
3. The acceptance criteria are met.

## Stop and escalate
After 3 rounds of audit or test fixes that still fail, stop and report the remaining errors. Ask when requirements are ambiguous.

## Never
- Commit or print secrets, tokens, or credentials.
- Force-push, rewrite published history, or skip hooks with `--no-verify`.
- Delete user data, untracked files, or branches you did not create.
- Edit or remove existing changelog lines (append only).
- Add a `BANNED:` dependency, or any new dependency outside the Architectural lane.
- Write guesses into LEARNINGS.md.
