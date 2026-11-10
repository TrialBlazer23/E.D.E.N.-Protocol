# CLI Tooling & Compliance Auditing
**E.D.E.N. Protocol Developer & Automation Guide · Necessity Labs**

---

## 1. Overview

The E.D.E.N. Protocol enforces compliance not through LLM goodwill, but through **zero-dependency mechanical back-pressure**. The tooling suite:

1. `scripts/eden-audit.py`: Verifies repository compliance against the `.eden/` control plane; `--doctor` reports per-tool setup.
2. `scripts/eden-index.py`: Parses source files across multiple programming languages and auto-indexes components into `.eden/REGISTRY.md`.
3. `scripts/eden-hook.py`: The agent stop hook for Cursor, Grok Build, Copilot, and Antigravity (section 4.3).
4. `scripts/eden_common.py`: The source extensions and ignored folders shared by the audit, the index, and the hook, so they always agree on what counts as source.
5. `scripts/eden-install.py` (protocol repository only): the installer behind `init-eden.sh` / `init-eden.ps1` (section 5).

All scripts are written using Python 3 standard library modules only (`ast`, `re`, `subprocess`, `json`, `pathlib`, `sys`). No virtual environment or external packages are required (Python 3.9+).

---

## 2. `scripts/eden-audit.py` (Compliance Auditor)

### 2.1 What it Audits
For every changed source file (by extension, from `eden_common.py`: `.py .kt .kts .java .scala .ts .tsx .js .jsx .mjs .cjs .vue .svelte .go .rs .c .cpp .h .cs .rb .swift .php .dart .sh .ps1`; `docs/`, `.eden/`, hidden, vendored, and build folders are ignored, and so are E.D.E.N.'s own scripts):
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

`python3 scripts/eden-audit.py --doctor` does not audit. It lists, per tool (Antigravity, Cursor, Grok Build, VS Code/Copilot, Claude Code), which instruction files, hook configs, and skills are present, then flags unfinished setup: a missing or non-E.D.E.N. `AGENTS.md`, a hook config without `scripts/eden-hook.py`, hook configs that would make the audit run twice (`.grok/hooks/`, `.claude/settings*.json`), leftover `<fill in>` placeholders, a missing `.eden/verify`, and a pre-commit hook (or husky / lefthook / pre-commit config) that does not run the audit. It always exits 0.

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
- **Java, C#, Scala, Swift, Dart (`.java`, `.cs`, `.scala`, `.swift`, `.dart`):** Classes, interfaces, enums, records, structs, traits, objects.
- **PHP (`.php`):** Classes, interfaces, traits, and functions.
- **Ruby (`.rb`):** Classes, modules, and methods.
- **Python (`.py`):** Uses Python `ast` to extract classes, public methods, top-level functions, and module docstrings.
- **TypeScript / JavaScript (`.ts`, `.tsx`, `.js`, `.jsx`, `.mjs`, `.cjs`, `.vue`, `.svelte`):** Exported classes, functions, types, and interfaces.
- **Rust (`.rs`):** Public structs, traits, and functions.
- **Go (`.go`):** Public structs, interfaces, and functions.
- **C / C++ (`.c`, `.cpp`, `.h`):** Function and class definitions.
- **Shell (`.sh`, `.ps1`):** Script definitions and helper functions.

### 3.2 Non-Destructive Regeneration
Files owned by E.D.E.N. (`scripts/eden-*.py`, `scripts/eden_common.py`, the init scripts, `templates/`) are left out of the registry, except in the protocol repository itself.

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

An existing hook is never replaced without `--force` / `-Force` (the old one is kept as `pre-commit.eden-bak`). If you keep your own hook, add `python3 scripts/eden-audit.py --staged || exit 1` to it. If the repository uses husky (`.husky/`), lefthook (`lefthook.yml`), or pre-commit (`.pre-commit-config.yaml`), the installer does not touch git hooks and prints the line to add to that manager's pre-commit step instead; automatic integration with those managers is not implemented yet. Hooks are local and can be skipped with `--no-verify`, so also run the audit in CI.

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

In the protocol repository, `--verify` also runs the unit tests (`.eden/verify.py`).

### 4.3 Agent Stop Hook (`scripts/eden-hook.py`)
The pre-commit hook only fires when someone commits. The stop hook fires when an agent tries to end its turn, so unregistered or unlogged changes are caught while the agent can still fix them. The installed configs (`.cursor/hooks.json` for Cursor and Grok Build, `.github/hooks/eden.json` for Copilot, `.agents/hooks.json` for Antigravity) all run the same script:

1. Detects the calling tool from the stdin JSON (the `--tool` argument is only a fallback) and ignores aborts, errors, subagent stops, and session-end events.
2. Allows the stop at once when no source file changed.
3. Otherwise runs `eden-audit.py` (plus `--verify` when `EDEN_HOOK_VERIFY=1`). On failure it tells the agent to keep working, quoting the audit errors (up to 6000 characters), in that tool's reply format.
4. Forces at most 2 extra rounds per user turn; on the last one it tells the agent to stop and report what still fails. The round count lives in `<git-dir>/eden-hook-state.json` and resets on a pass or a new turn.
5. Fails open on any internal error. `EDEN_HOOK_DISABLE=1` turns it off.

Smoke test it by hand:
```bash
echo '{"hookEventName":"Stop","stopHookActive":false,"sessionId":"t","reason":"end_turn"}' | python3 scripts/eden-hook.py
```
`{}` means the stop is allowed. See [Multi-Agent Routing](MULTI_AGENT_ROUTING.md#33-one-stop-hook-four-callers) for the per-tool formats.

---

## 5. Installer (`init-eden.sh`, `init-eden.ps1`, `scripts/eden-install.py`)

| Option (sh / PowerShell) | Effect |
| :--- | :--- |
| `--new` / `-New` | Write full files. Default when the target has no commits and no source files. |
| `--adopt` / `-Adopt` | Merge `<!-- EDEN:BEGIN v1 -->` ... `<!-- EDEN:END -->` blocks into existing instruction files, merge hook configs, detect commands. Default otherwise. |
| `--tools LIST` / `-Tools LIST` | Any of `antigravity,cursor,grok,vscode,claude`. Default: `antigravity,cursor,grok,vscode`. |
| `--legacy` / `-Legacy` | Also write `.cursorrules` and `.windsurfrules`. |
| `--force` / `-Force` | Replace managed files wholesale, with `<file>.eden-bak` backups. `.eden/` state is never replaced. |
| `--detect`, `--no-detect` / `-Detect`, `-NoDetect` | Command detection (on by default only in adopt mode). Fills the Commands section of `AGENTS.md` and creates `.eden/verify`. |
| `--reindex` / `-Reindex` | Regenerate section 2 of an existing registry. |
| `--name NAME` / `-ProjectName NAME` | Project name for `.eden/ARCHITECTURE.md`. |
| `--source DIR` / `-SourceDir DIR` | Protocol checkout to copy from (or set `EDEN_RAW_BASE`). |
| `EDEN_RAW_BASE` (env) | Raw-file URL used only when `--source` has no protocol files. This is a trust boundary; pin to a commit. See [SECURITY.md](../SECURITY.md). |
| `EDEN_SHA256` (env) | Optional. 64-hex SHA-256 of `scripts/eden-install.py`, or a path to a `sha256sum`-format file. A mismatch aborts before the installer runs. |

The installer is idempotent: a second run with the same options changes nothing and adds no changelog line. The first changelog line (`TASK-00` for new, `EDEN-ADOPT` for adopt) lists exactly the files the run wrote or merged; later runs that change something append an `EDEN-SETUP` line.
