# COMPONENT & DEPENDENCY REGISTRY
> **AGENT INSTRUCTION:** Search this file BEFORE writing new helpers, utilities, or installing packages. If it exists here, import it. When you create a new shared module, add it here immediately during the Normalize phase.

## 1. Approved External Dependencies
| Package / Library | Purpose | Version / Constraint |
| :--- | :--- | :--- |
| `standard-library` | Default runtime primitives | Prefer before adding dependencies |

## 2. Internal Modules & Source Files (Reuse Mandatory)
| File Path | Exported Symbols / Key API | Responsibility | Consumers |
| :--- | :--- | :--- | :--- |
| `init-eden.ps1` | *(script / definitions)* | Module `init-eden.ps1` | `init-eden.sh`, `eden-audit.py` |
| `init-eden.sh` | *(script / definitions)* | E.D.E.N. Protocol Repository Bootstrapper (init-eden.sh) | `eden-audit.py` |
| `scripts/eden-audit.py` | `find_repo_root()`, `get_git_changes()`, `is_tracked_code_file()`, `parse_banned_impo... | E.D.E.N. Protocol Compliance Auditor (Zero-Dependency) | `init-eden.ps1`, `init-eden.sh`, `eden-index.py` |
| `scripts/eden-index.py` | `clean_table_cell()`, `extract_python()`, `extract_kotlin()`, `extract_ts_js()`, `ext... | E.D.E.N. Protocol Auto-Indexer (Zero-Dependency) | `init-eden.ps1`, `init-eden.sh`, `eden-audit.py` |

## 3. Data Schemas & State Files
| Path | Format | Description |
| :--- | :--- | :--- |
| `.eden/CHANGELOG_AGENT.jsonl` | JSONL | Append-only agent mutation history |
| `.eden/ARCHITECTURE.md` | Markdown | Project-specific constraints and data flow |
| `.eden/PLAN.md` | Markdown | Active task scope and milestones |
| `.eden/LEARNINGS.md` | Markdown | Persistent project and runtime learnings |
