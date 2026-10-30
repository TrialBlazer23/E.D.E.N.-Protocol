# ARCHITECTURE - E.D.E.N.-Protocol

This repository is the protocol itself: agent instruction files, `.eden/` templates, a bootstrapper, and two zero-dependency Python tools.

## Runtime & Environment
- Languages and versions: Python 3.9+ (stdlib only), POSIX `bash`, PowerShell 5.1+ / 7+.
- Supported platforms: Linux, macOS, Windows (PowerShell or Git Bash), WSL, Termux.
- Toolchain / package manager: none; `git` is required for the audit's change checks.

## Constraints & Limits
- Memory / performance ceiling: none known; tools must stay fast enough for a pre-commit hook.
- Network, ports, and external services: none. `EDEN_RAW_BASE` downloads are opt-in.

## Core Data Flow
```text
[protocol checkout] --init-eden.sh/.ps1--> [target repo: AGENTS.md, pointers, scripts/, .eden/, pre-commit]
[git status / index / base...HEAD] --eden-audit.py--> [REGISTRY + CHANGELOG checks, optional .eden/verify] -> exit 0/1
[source files] --eden-index.py--> [.eden/REGISTRY.md section 2]
```

## Invariants
- `AGENTS.md` and the six pointer files at the repo root are the only copies; init scripts copy them byte-for-byte.
- Agent-facing files and `init-eden.ps1` are ASCII-only with no BOM.
- Init never overwrites an existing file without `--force` / `-Force`, and never overwrites existing `.eden/` state.
- No third-party dependencies in `scripts/` or `tests/`.
