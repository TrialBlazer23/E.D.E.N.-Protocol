# PLAN

## Current Objective
- [x] **TASK-04:** Tool wiring and safe adoption: `--new`/`--adopt` with EDEN merge markers, `--tools`/`--legacy`, shared `eden_common.py`, stop hook for Cursor/Grok Build/Copilot/Antigravity, `.agents/skills`, command detection with `.eden/verify`, `--doctor`, docs, tests.
  - Acceptance: adopt keeps text outside the markers and re-runs are no-ops; Java and other added languages are registered and audited; the hook blocks unregistered changes in each tool's format and stops after 2 forced rounds; `python3 scripts/eden-audit.py --verify` exits 0.

## Backlog
- [ ] Folder-level registry depth (register directories, not only files) and registry intent preserved on reindex.
- [ ] husky / lefthook / pre-commit integration (today the installer prints the line to add).
- [ ] Parallel-work changelog strategy, strict heading checks, reading budgets, LICENSE and version tags.
- [ ] Dogfood CI: add `.github/workflows/eden-audit.yml` (needs a token with `workflow` scope to push).
- [ ] Confirm the stop hook on real Windows installs (PowerShell 5.1 `||`, `py -3`) and on each tool's current release.

## Completed
- [x] **TASK-03:** Review recommendations 1-5 (working setup, audit blind spots, correctness in the loop, AGENTS.md decision rules, encoding and placeholder facts).
- [x] **TASK-01:** Provider-neutral control plane and bootstrap paths.
- [x] **TASK-02:** Canonical template refactor with docs suite and pointer files.
