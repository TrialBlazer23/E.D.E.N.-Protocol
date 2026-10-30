---
name: eden-normalize
description: Finish an E.D.E.N. code change - register changed source files in .eden/REGISTRY.md, append a changelog line, record verified learnings, update PLAN.md, and get scripts/eden-audit.py to pass. Use after editing source code in a repo that has an .eden/ folder, or when the E.D.E.N. audit or stop hook reports UNREGISTERED FILE, MISSING AUDIT LOG, or INCOMPLETE AUDIT LOG.
---

# E.D.E.N. Normalize

Run this after Execute, before you say a code change is done. AGENTS.md has the full rules.

## Steps
1. List what changed: `git status --porcelain --untracked-files=all`.
2. Register every new or changed source file in `.eden/REGISTRY.md` section 2. The path must be the first cell of a table row, exactly as git shows it. `python3 scripts/eden-index.py .` regenerates section 2 for you; review the result.
3. Append ONE line to `.eden/CHANGELOG_AGENT.jsonl` (never edit existing lines):
   `{"timestamp":"<UTC ISO-8601>","phase":"Normalize","task_id":"<TASK-ID>","action":"CREATED|MODIFIED|REFACTORED|DELETED","files":["<every changed source file>"],"reused_modules":[],"summary":"<one sentence>"}`
4. If you confirmed the root cause of a non-obvious problem, add one line to `.eden/LEARNINGS.md` under Entries. Never write guesses.
5. Tick or update the task in `.eden/PLAN.md`.
6. Run `python3 scripts/eden-audit.py --verify` (use `python` or `py -3` on Windows if `python3` is missing).

## When the audit fails
- Read the numbered errors; each names the file and the fix.
- Fix and re-run. After 3 failed rounds, stop and report the remaining errors to the human. Do not loosen the audit, edit old changelog lines, or skip hooks with `--no-verify`.
