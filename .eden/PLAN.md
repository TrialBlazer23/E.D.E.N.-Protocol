# PLAN

## Current Objective
- [ ] **TASK-03:** Land review recommendations 1-5 (working setup, audit blind spots, correctness in the loop, AGENTS.md decision rules, encoding and placeholder facts).
  - Acceptance: fresh `init-eden` repo commits through the hook; `--staged` and `--base` modes work; untracked-dir, comment-fake, and other-.eden-file bypasses fail the audit; `python3 scripts/eden-audit.py --verify` exits 0.

## Backlog
- [ ] Review recommendations 6-13 (tool wiring, registry intent on reindex, parallel-work changelog strategy, strict heading checks, dogfood CI, reading budgets, LICENSE and version tags).

## Completed
- [x] **TASK-01:** Provider-neutral control plane and bootstrap paths.
- [x] **TASK-02:** Canonical template refactor with docs suite and pointer files.
