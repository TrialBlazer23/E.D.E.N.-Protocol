# CLI Tooling & Compliance Auditing
**E.D.E.N. Protocol Developer & Automation Guide · Necessity Labs**

---

## 1. Overview

The E.D.E.N. Protocol enforces compliance not through LLM goodwill, but through **zero-dependency mechanical back-pressure**. The tooling suite consists of two core scripts:

1. `scripts/eden-audit.py`: Verifies repository compliance against the `.eden/` control plane.
2. `scripts/eden-index.py`: Parses source files across multiple programming languages and auto-indexes components into `.eden/REGISTRY.md`.

Both scripts are written using Python 3 standard library modules only (`ast`, `re`, `subprocess`, `json`, `pathlib`, `sys`). No virtual environment or external packages are required (Python 3.9+).

---

## 2. `scripts/eden-audit.py` (Compliance Auditor)

### 2.1 What it Audits
For every changed source file (by extension; `docs/`, `.eden/`, vendored and build folders are ignored):
1. **Control Plane Integrity:** `.eden/REGISTRY.md` and `.eden/CHANGELOG_AGENT.jsonl` exist.
2. **Registration:** the file's exact path is the first cell of a table row in `.eden/REGISTRY.md`. Mentions in prose, HTML comments, or code fences do not count.
3. **Change Log:** `.eden/CHANGELOG_AGENT.jsonl` gained at least one new line, every new line is valid JSON with `timestamp`, `phase`, `action`, `files`, `summary`, and the union of the new entries' `files` lists every changed source file. Existing lines must not be edited or removed (append-only). Editing other `.eden/` files does not satisfy this check.
4. **Banned Dependencies:** changed files must not import a package listed as `BANNED: <pkg>` in the registry.
5. **Verify (optional):** with `--verify` (or `EDEN_VERIFY=1`), runs `.eden/verify.py` (with the same Python) or `.eden/verify` (executable, or via `sh`). A non-zero exit fails the audit. If neither exists, the audit prints a note and continues.

### 2.2 Modes

| Command | Compares | Use for |
| :--- | :--- | :--- |
| `python3 scripts/eden-audit.py` | working tree (including files inside new untracked folders) vs `HEAD` | agents and humans before finishing |
| `python3 scripts/eden-audit.py --staged` | index vs `HEAD` | the pre-commit hook |
| `python3 scripts/eden-audit.py --base origin/main` | `merge-base(origin/main, HEAD)..HEAD` | CI on a clean checkout |

Add `--verify` to any mode to run the verify step, and `--root DIR` to audit a repository other than the auto-detected one.

### 2.3 The verify step
`.eden/verify` is where a project puts its correctness checks so the audit can run them. Keep it short and fast. Examples:

```sh
#!/bin/sh
# .eden/verify
set -e
npm run lint
npm test -- --watch=false
```

```python
# .eden/verify.py (portable; preferred on Windows)
import subprocess, sys
sys.exit(subprocess.call([sys.executable, "-m", "pytest", "-q"]))
```

A task is **done** when tests / verify pass, `python3 scripts/eden-audit.py --verify` exits 0, and the acceptance criteria in `.eden/PLAN.md` (or the request) are met.

### 2.4 Exit Codes & Remediation
- **Exit Code 0:** All checks passed.
- **Exit Code 1:** A check failed. A numbered list of errors and remediation steps is printed. After 3 failed fix rounds, agents should stop and report to a human (see `AGENTS.md`).

```text
========================================================================
[EDEN-AUDIT] FAILED (working tree): Normalize phase incomplete
========================================================================
  1. UNREGISTERED FILE: `src/pkg/mod.py` was created or modified but has no row in `.eden/REGISTRY.md` (its path must be the first cell of a table row).
  2. MISSING AUDIT LOG: source files changed but no new line was appended to `.eden/CHANGELOG_AGENT.jsonl` (editing other .eden/ files does not count).
------------------------------------------------------------------------
REMEDIATION:
  -> Register changed source files in `.eden/REGISTRY.md` (python3 scripts/eden-index.py .)
  -> Append one JSON line to `.eden/CHANGELOG_AGENT.jsonl` listing every changed source file in `files`
  -> Fix failing tests / .eden/verify
  -> Re-run the audit. After 3 failed fix rounds, stop and report to a human.
========================================================================
```

---

## 3. `scripts/eden-index.py` (Auto-Indexer)

### 3.1 Supported Languages & Parsers
`eden-index.py` extracts top-level classes, functions, and key abstractions across:
- **Kotlin (`.kt`, `.kts`):** Classes, interfaces, objects, `@Composable` functions, suspend functions.
- **Python (`.py`):** Uses Python `ast` to extract classes, public methods, top-level functions, and module docstrings.
- **TypeScript / JavaScript (`.ts`, `.tsx`, `.js`):** Exported classes, functions, types, and interfaces.
- **Rust (`.rs`):** Public structs, traits, and functions.
- **Go (`.go`):** Public structs, interfaces, and functions.
- **C / C++ (`.c`, `.cpp`, `.h`):** Function and class definitions.
- **Shell (`.sh`, `.ps1`):** Script definitions and helper functions.

### 3.2 Non-Destructive Regeneration
`eden-index.py` targets Section 2 of `.eden/REGISTRY.md` (`## 2. Internal Modules & Source Files`). It preserves manual notes in Section 1 (Approved External Dependencies & Banned libraries) and Section 3 (Data Schemas & State Files).

Usage:
```bash
python scripts/eden-index.py .
```

---

## 4. Automation & Git Hooks

### 4.1 Git Pre-Commit Hook
`init-eden.sh` / `init-eden.ps1` install `templates/hooks/pre-commit` into the repository's hooks folder (`git rev-parse --git-path hooks`, so `core.hooksPath` and worktrees work). The hook audits only what is staged:

```sh
#!/bin/sh
ROOT="$(git rev-parse --show-toplevel)" || exit 1
# ...finds python3/python, fails with a clear message if the audit script or Python is missing...
exec "$PY" "$ROOT/scripts/eden-audit.py" --root "$ROOT" --staged
```

An existing hook is never replaced without `--force` / `-Force` (the old one is kept as `pre-commit.eden-bak`). If you keep your own hook, add `python3 scripts/eden-audit.py --staged || exit 1` to it. Hooks are local and can be skipped with `--no-verify`, so also run the audit in CI.

### 4.2 CI/CD Pipeline Integration
A clean CI checkout has no working-tree changes, so audit the commits under review with `--base`:

```yaml
name: E.D.E.N. Compliance Audit
on: [push, pull_request]

jobs:
  audit:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
        with:
          fetch-depth: 0          # --base needs the base branch history
      - uses: actions/setup-python@v5
        with:
          python-version: '3.11'
      - name: Run E.D.E.N. Audit
        run: |
          if [ "${{ github.event_name }}" = "pull_request" ]; then
            BASE="origin/${{ github.base_ref }}"
          else
            BASE="${{ github.event.before }}"
            # New branch pushes have no "before" commit; compare with the default branch.
            case "$BASE" in 0000000*|"") BASE="origin/${{ github.event.repository.default_branch }}" ;; esac
          fi
          python scripts/eden-audit.py --base "$BASE" --verify
```
