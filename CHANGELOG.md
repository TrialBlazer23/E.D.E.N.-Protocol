# Changelog

All notable changes to this project are documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project uses [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Added

- MIT `LICENSE`, `SECURITY.md`, `CONTRIBUTING.md`, and this changelog.
- Optional `EDEN_SHA256` check so `init-eden.sh` and `init-eden.ps1` can verify
  `scripts/eden-install.py` (or a checksums file) before running a download
  from `EDEN_RAW_BASE`.
- Broader `.gitignore` entries for env files, virtualenvs, editor metadata,
  logs, and `node_modules/`. `.cursor/` is not ignored; the protocol tracks
  and installs files there.

### Fixed

- Documentation and init-script examples now use the repository name
  `E.D.E.N.-Protocol`.

### Changed

- README states the Python 3.9+ requirement and links the license, security,
  contributing, and changelog files.

## [0.1.0] - 2026-11-10

First tagged-shape snapshot of `main` after
[pull request #2](https://github.com/TrialBlazer23/E.D.E.N.-Protocol/pull/2)
was squash-merged. There is not yet a GitHub Release or git tag for this
version; create `v0.1.0` after you publish if you want one.

### Added

- Provider-neutral agent control plane: `AGENTS.md` lane-based loop, `.eden/`
  state (architecture, registry, plan, learnings, JSONL changelog), and
  trampoline instruction files for Cursor, Copilot, Claude Code, Gemini /
  Antigravity, and Windsurf ([#1](https://github.com/TrialBlazer23/E.D.E.N.-Protocol/pull/1), earlier commits).
- Zero-dependency `scripts/eden-audit.py` and `scripts/eden-index.py`, with
  `--staged`, `--base`, `--verify`, and `--doctor` ([#1](https://github.com/TrialBlazer23/E.D.E.N.-Protocol/pull/1), [#2](https://github.com/TrialBlazer23/E.D.E.N.-Protocol/pull/2)).
- Docs suite: specification, multi-agent routing, CLI and auditing, migration
  guide.
- Safe adoption ([#2](https://github.com/TrialBlazer23/E.D.E.N.-Protocol/pull/2)):
  `init-eden.sh` / `init-eden.ps1` wrap `scripts/eden-install.py` with `--new`
  / `--adopt`, `<!-- EDEN:BEGIN v1 -->` merge markers, `--tools` / `--legacy`,
  command detection, and hook-config merging.
- Shared `scripts/eden_common.py` and broader language coverage for indexing
  and audit (including Java, C#, and others) ([#2](https://github.com/TrialBlazer23/E.D.E.N.-Protocol/pull/2)).
- Stop hook `scripts/eden-hook.py` for Cursor, Grok Build, Copilot / VS Code,
  and Antigravity, including multi-root workspace audits
  ([#2](https://github.com/TrialBlazer23/E.D.E.N.-Protocol/pull/2)).
- Shared skills in `.agents/skills/` (`eden-normalize`, `eden-architect`,
  `eden-adopt`) ([#2](https://github.com/TrialBlazer23/E.D.E.N.-Protocol/pull/2)).
- Stdlib unittest suite under `tests/` (audit, init, install, hook).

[Unreleased]: https://github.com/TrialBlazer23/E.D.E.N.-Protocol/compare/HEAD
[0.1.0]: https://github.com/TrialBlazer23/E.D.E.N.-Protocol/commits/main
