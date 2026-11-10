# ARCHITECTURE - E.D.E.N.-Protocol

This repository is the protocol itself: agent instruction files, `.eden/` templates, shared skills and stop-hook configs, a bootstrapper, and zero-dependency Python tools.

## Runtime & Environment
- Languages and versions: Python 3.9+ (stdlib only), POSIX `bash`, PowerShell 5.1+ / 7+.
- Supported platforms: Linux, macOS, Windows (PowerShell or Git Bash), WSL, Termux.
- Toolchain / package manager: none; `git` is required for the audit's change checks.

## Constraints & Limits
- Memory / performance ceiling: none known; tools must stay fast enough for a pre-commit hook.
- Network, ports, and external services: none by default. `EDEN_RAW_BASE` downloads are opt-in and execute the downloaded installer; optional `EDEN_SHA256` verifies `scripts/eden-install.py` or a checksums file first.

## Core Data Flow
```text
[protocol checkout] --init-eden.sh/.ps1 -> eden-install.py--> [target repo: AGENTS.md (full or EDEN block), pointers, hook configs, .agents/skills, scripts/, .eden/, pre-commit]
[agent stop event JSON] --eden-hook.py--> [eden-audit.py when source changed] -> per-tool allow / keep-working reply
[git status / index / base...HEAD] --eden-audit.py--> [REGISTRY + CHANGELOG checks, optional .eden/verify] -> exit 0/1
[source files] --eden-index.py--> [.eden/REGISTRY.md section 2]
```

## Invariants
- `AGENTS.md`, the pointer files, hook configs, and skills in this repo are the only copies; the installer copies them byte-for-byte (new mode) or merges them between `<!-- EDEN:BEGIN v1 -->` and `<!-- EDEN:END -->` (adopt mode), never touching text outside the markers.
- Source extensions and ignored folders are defined once, in `scripts/eden_common.py`.
- The stop hook fails open and forces at most 2 extra rounds per user turn. Only one hook config per tool runs it (no `.grok/hooks` or `.claude/settings.json`), so the audit never runs twice.
- Agent-facing files and `init-eden.ps1` are ASCII-only with no BOM.
- Init never overwrites an existing file without `--force` / `-Force`, never overwrites existing `.eden/` state, and a re-run with the same options changes nothing.
- No third-party dependencies in `scripts/` or `tests/`.
