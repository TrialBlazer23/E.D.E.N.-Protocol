# COMPONENT & DEPENDENCY REGISTRY
> **AGENT INSTRUCTION:** Search this file BEFORE writing new helpers, utilities, or installing packages. If it exists here, import it. When you create a new shared module, add it here immediately during the Normalize phase.

## 1. Approved External Dependencies
| Package / Library | Purpose | Version / Constraint |
| :--- | :--- | :--- |
| `standard-library` | Default runtime primitives | Prefer before adding dependencies |

## 2. Internal Modules & Source Files (Reuse Mandatory)
| File Path | Exported Symbols / Key API | Responsibility | Consumers |
| :--- | :--- | :--- | :--- |
| `init-eden.ps1` | *(script / definitions)* | Module `init-eden.ps1` | Entrypoint / Unreferenced |
| `init-eden.sh` | *(script / definitions)* | E.D.E.N. Protocol bootstrapper (POSIX shell). Needs Python 3. | Entrypoint / Unreferenced |
| `scripts/eden-audit.py` | `find_repo_root()`, `git()`, `is_git_repo()`, `has_head()`, `git_show()`, `parse_name... | E.D.E.N. Protocol Compliance Auditor (Zero-Dependency) | Entrypoint / Unreferenced |
| `scripts/eden-hook.py` | `detect_tool()`, `is_real_stop()`, `continuing()`, `session_key()`, `allow()`, `block... | E.D.E.N. stop hook for Cursor, Grok Build, VS Code / GitHub Copilot, and Google Antig... | Entrypoint / Unreferenced |
| `scripts/eden-index.py` | `clean_table_cell()`, `extract_python()`, `extract_kotlin()`, `extract_ts_js()`, `ext... | E.D.E.N. Protocol Auto-Indexer (Zero-Dependency) | Entrypoint / Unreferenced |
| `scripts/eden-install.py` | `files_for_tools()`, `git()`, `is_git_repo()`, `has_commits()`, `has_source_files()`,... | E.D.E.N. Protocol installer (zero-dependency). Called by init-eden.sh and init-eden.ps1; | Entrypoint / Unreferenced |
| `scripts/eden_common.py` | `configure_stdio()`, `is_ignored_dir()`, `is_eden_owned()`, `is_source_file()`, `is_p... | Shared constants and helpers for the E.D.E.N. scripts (audit, index, hook, install). | `init-eden.ps1`, `init-eden.sh`, `eden-audit.py`... |
| `tests/helpers.py` | `run()`, `make_repo()`, `init_repo()`, `audit()`, `register()`, `log_change()`, `clea... | Shared helpers for the E.D.E.N. smoke tests: temp git repos initialized with init-ede... | `eden_common.py`, `test_audit.py`, `test_hook.py`... |
| `tests/test_audit.py` | `AuditTests` (setUp, tearDown, write, ...) | Regression tests for scripts/eden-audit.py bypasses (stdlib unittest; run: python3 -m... | Entrypoint / Unreferenced |
| `tests/test_hook.py` | `is_block()`, `HookTests` (setUp, tearDown, hook, ...) | Smoke tests for scripts/eden-hook.py: caller detection, per-tool replies, and the rou... | Entrypoint / Unreferenced |
| `tests/test_init.py` | `InitTests` (setUp, tearDown, init, ...), `EncodingTests` (test_agent_files_are_ascii... | Smoke tests for init-eden.sh and the single-source-of-truth rule. | Entrypoint / Unreferenced |
| `tests/test_install.py` | `InstallTestCase` (setUp, tearDown, init, ...), `ModeTests` (test_empty_repo_defaults... | Tests for adopt vs new, EDEN merge markers, --tools/--legacy, hook-config merging, an... | Entrypoint / Unreferenced |

## 3. Data Schemas & State Files
| Path | Format | Description |
| :--- | :--- | :--- |
| `.eden/CHANGELOG_AGENT.jsonl` | JSONL | Append-only agent mutation history |
| `.eden/ARCHITECTURE.md` | Markdown | Project-specific constraints and data flow |
| `.eden/PLAN.md` | Markdown | Active task scope and milestones |
| `.eden/LEARNINGS.md` | Markdown | Persistent project and runtime learnings |
| `.eden/verify.py` | Python | Verify step for this repo: runs `tests/` (used by `eden-audit.py --verify`) |
| `templates/eden/` | Markdown | Starter `.eden/` files copied by the init scripts |
| `templates/hooks/pre-commit` | sh | Pre-commit hook template (`eden-audit.py --staged`) |
