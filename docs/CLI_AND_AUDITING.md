# CLI Tooling & Compliance Auditing
**E.D.E.N. Protocol Developer & Automation Guide · Necessity Labs**

---

## 1. Overview

The E.D.E.N. Protocol enforces compliance not through LLM goodwill, but through **zero-dependency mechanical back-pressure**. The tooling suite consists of two core scripts:

1. `scripts/eden-audit.py`: Verifies repository compliance against the `.eden/` control plane.
2. `scripts/eden-index.py`: Parses source files across multiple programming languages and auto-indexes components into `.eden/REGISTRY.md`.

Both scripts are written using Python 3 standard library modules only (`ast`, `re`, `subprocess`, `json`, `pathlib`, `sys`). No virtual environment or external packages are required.

---

## 2. `scripts/eden-audit.py` (Compliance Auditor)

### 2.1 What it Audits
When invoked, `eden-audit.py` checks:
1. **Control Plane Integrity:** Verifies that `.eden/REGISTRY.md` and `.eden/CHANGELOG_AGENT.jsonl` exist.
2. **Unregistered Files:** Cross-references `git status --porcelain` to ensure every newly created or modified source code file is documented in `.eden/REGISTRY.md`.
3. **Agent Mutation Log:** Ensures that if code files are modified, a corresponding new JSON line is appended to `.eden/CHANGELOG_AGENT.jsonl` matching the required schema.
4. **Banned Dependencies:** Scans modified files for imports matching any `BANNED: <pkg>` entry defined in `.eden/REGISTRY.md`.

### 2.2 Exit Codes & Remediation
- **Exit Code 0:** All checks passed. Repository is synchronized and compliant.
- **Exit Code 1:** Compliance failed. A structured error summary is printed with actionable remediation instructions.

```text
========================================================================
❌ E.D.E.N. PROTOCOL AUDIT FAILED — NORMALIZE PHASE INCOMPLETE
========================================================================
  1. UNREGISTERED FILE: `app/src/main/NewHelper.kt` was modified but is not documented in `.eden/REGISTRY.md`.
  2. MISSING AUDIT LOG: Code files modified, but `.eden/CHANGELOG_AGENT.jsonl` was not updated.
------------------------------------------------------------------------
AGENT REMEDIATION REQUIRED:
  -> Register new/modified modules in `.eden/REGISTRY.md` (or run `python scripts/eden-index.py`)
  -> Append a valid JSON entry to `.eden/CHANGELOG_AGENT.jsonl`
  -> Re-run: `python scripts/eden-audit.py`
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
`init-eden.sh` automatically installs `.git/hooks/pre-commit`:
```bash
#!/usr/bin/env bash
python3 scripts/eden-audit.py
```
This ensures neither human developers nor autonomous CLI agents can create a git commit that violates registry indexing or changelog recording.

### 4.2 CI/CD Pipeline Integration
To enforce E.D.E.N. Protocol in GitHub Actions:
```yaml
name: E.D.E.N. Compliance Audit
on: [push, pull_request]

jobs:
  audit:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - name: Set up Python
        uses: actions/setup-python@v5
        with:
          python-version: '3.11'
      - name: Run E.D.E.N. Audit
        run: python scripts/eden-audit.py
```
