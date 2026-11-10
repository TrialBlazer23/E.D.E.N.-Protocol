# Contributing

Thanks for helping with the E.D.E.N. Protocol. This repository is itself an
E.D.E.N.-governed project: read `AGENTS.md` and follow the lane that matches
your change (read-only, trivial, normal, or architectural).

## Development setup

Python 3.9 or newer is required. The tools and tests use the standard library
only; no virtual environment or packages are needed. `git` is required for
audit change detection.

This repository's own commands (the `AGENTS.md` Commands placeholders stay as
`<fill in>` because that file is copied into new projects and `--detect` only
replaces those placeholders):

- Setup: none (Python 3.9+ standard library)
- Build: none
- Test: `python3 -m unittest discover -s tests`
- Lint / audit: `python3 scripts/eden-audit.py --verify`
- Verify: `python3 scripts/eden-audit.py --verify` (runs `.eden/verify.py`,
  which is the same unittest suite)

## Before you open a pull request

1. Run `python3 -m unittest discover -s tests` and
   `python3 scripts/eden-audit.py --verify`. Both must pass.
2. Follow Normalize in `AGENTS.md`: register new or changed source files,
   append one line to `.eden/CHANGELOG_AGENT.jsonl` that lists them, and
   update `.eden/PLAN.md` when the work was planned there.
3. Keep `init-eden.ps1` and other agent-facing files ASCII-only with no BOM.
4. Do not add third-party dependencies under `scripts/` or `tests/`.
5. Do not commit secrets, `.env` files, or hook state.

Architectural changes (new boundaries, new dependencies, schema changes)
need a plan in `.eden/PLAN.md` and human approval before implementation.

A ready-to-copy GitHub Actions workflow lives in
[docs/CLI_AND_AUDITING.md](docs/CLI_AND_AUDITING.md) (section 4.2). This
repository does not ship `.github/workflows/` yet; adding that path requires a
token with the `workflow` scope.
