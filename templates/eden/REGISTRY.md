# REGISTRY
> Search this file before adding a helper, module, or package. Reuse what is listed.
> To ban a library, write `BANNED: package_name` in a Notes cell of section 1 (enforced by `eden-audit.py`).
> The audit only accepts a source file as registered when its path is the first cell of a table row.

## 1. Approved External Dependencies
| Package | Purpose | Constraint / Notes |
| :--- | :--- | :--- |
| `standard-library` | Default runtime primitives | Prefer before adding dependencies |

## 2. Internal Modules & Source Files (Reuse Mandatory)
| File Path | Exported Symbols / Key API | Responsibility | Consumers |
| :--- | :--- | :--- | :--- |

## 3. Data Schemas & State Files
| Path | Format | Description |
| :--- | :--- | :--- |
| `.eden/CHANGELOG_AGENT.jsonl` | JSONL | Append-only agent change log |
| `.eden/ARCHITECTURE.md` | Markdown | Constraints, data flow, invariants |
| `.eden/PLAN.md` | Markdown | Current objective, backlog, completed |
| `.eden/LEARNINGS.md` | Markdown | Verified pitfalls and fixes |
