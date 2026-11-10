# PLAN

## Current Objective
- [x] **TASK-06:** Dogfood CI workflow: copy the workflow in `docs/CLI_AND_AUDITING.md` section 4.2 to `.github/workflows/eden-audit.yml`.
  - Acceptance: `.github/workflows/eden-audit.yml` matches `docs/CLI_AND_AUDITING.md` section 4.2; `python3 scripts/eden-audit.py` exits 0.

## Backlog
- [ ] Folder-level registry depth (register directories, not only files) and registry intent preserved on reindex.
- [ ] husky / lefthook / pre-commit integration (today the installer prints the line to add).
- [ ] Parallel-work changelog strategy, strict heading checks, reading budgets, and a `v0.1.0` git tag / GitHub Release (LICENSE is in-tree).
- [ ] Confirm the stop hook on real Windows installs (PowerShell 5.1 `||`, `py -3`) and on each tool's current release.

## Completed
- [x] **TASK-05:** Public-readiness docs and bootstrap hardening: MIT LICENSE, SECURITY.md, CONTRIBUTING.md, CHANGELOG.md, expanded `.gitignore`, `E.D.E.N.-Protocol` path typo, README Python 3.9+ and community links, optional `EDEN_SHA256` on the init wrappers.
- [x] **TASK-04:** Tool wiring and safe adoption (`--new`/`--adopt`, merge markers, stop hook, skills, command detection, `--doctor`, tests).
- [x] **TASK-03:** Review recommendations 1-5 (working setup, audit blind spots, correctness in the loop, AGENTS.md decision rules, encoding and placeholder facts).
- [x] **TASK-01:** Provider-neutral control plane and bootstrap paths.
- [x] **TASK-02:** Canonical template refactor with docs suite and pointer files.
