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
| `init-eden.sh` | `install_file()` | E.D.E.N. Protocol bootstrapper (POSIX shell) | Entrypoint / Unreferenced |
| `tests/helpers.py` | `run()`, `make_repo()`, `init_repo()`, `audit()`, `register()`, `log_change()`, `clea... | Shared helpers for the E.D.E.N. smoke tests: temp git repos initialized with init-ede... | `test_audit.py`, `test_init.py` |
| `tests/test_audit.py` | `AuditTests` (setUp, tearDown, write, ...) | Regression tests for scripts/eden-audit.py bypasses (stdlib unittest; run: python3 -m... | Entrypoint / Unreferenced |
| `tests/test_init.py` | `InitTests` (setUp, tearDown, init, ...), `EncodingTests` (test_agent_files_are_ascii... | Smoke tests for init-eden.sh and the single-source-of-truth rule. | Entrypoint / Unreferenced |
| `scripts/eden-audit.py` | `find_repo_root()`, `git()`, `is_git_repo()`, `has_head()`, `git_show()`, `parse_name... | E.D.E.N. Protocol Compliance Auditor (Zero-Dependency) | Entrypoint / Unreferenced |
| `scripts/eden-index.py` | `clean_table_cell()`, `extract_python()`, `extract_kotlin()`, `extract_ts_js()`, `ext... | E.D.E.N. Protocol Auto-Indexer (Zero-Dependency) | Entrypoint / Unreferenced |

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
