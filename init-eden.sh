#!/usr/bin/env bash
# ==============================================================================
# E.D.E.N. Protocol Repository Scaffolder (init-eden.sh)
# Necessity Labs — Model-Agnostic Coding Agent Control Plane
# ==============================================================================
set -euo pipefail

PROJECT_NAME="${1:-$(basename "$PWD")}"
TIMESTAMP="$(date -u +"%Y-%m-%dT%H:%M:%SZ")"

echo "Initializing E.D.E.N. Protocol Scaffold for: ${PROJECT_NAME}"

mkdir -p .eden scripts

# ------------------------------------------------------------------------------
# 1. Generate AGENTS.md (Master Router & Operating System)
# ------------------------------------------------------------------------------
if [ ! -f AGENTS.md ]; then
cat << 'EOF' > AGENTS.md
# E.D.E.N. PROTOCOL: AGENT OPERATING SYSTEM

You are operating inside an **E.D.E.N.** governed repository (**Necessity Labs**).
Adhere strictly to the **Law of Necessity**:
- **E — Everything is broken:** Assume zero-trust defaults. Do not rely on fragile cloud dependencies or bloated abstractions.
- **D — Define the mechanics:** Understand raw memory, I/O,ports, and execution constraints before touching code.
- **E — Engineer the architecture:** Build modular, sovereign, local-first systems.
- **N — Necessity dictates the output:** Zero dead code, zero duplicate utilities, zero unapproved packages.

---

## MANDATORY 4-PHASE EXECUTION LOOP

You MUST follow these phases sequentially for every task. Do NOT skip Phase 1, 2, or 4.

### Phase 1: E — Evaluate (Context & Constraint Ingestion)
Before proposing or writing any code, read:
1. `.eden/ARCHITECTURE.md` — System boundaries, target hardware ceiling, and ports/data flow.
2. `.eden/REGISTRY.md` — Complete index of existing internal modules and approved dependencies.
3. `.eden/LEARNINGS.md` — Known environment quirks and resolved pitfalls.
4. `tail -n 10 .eden/CHANGELOG_AGENT.jsonl` — Recent mutations for immediate context.

### Phase 2: D — Define (The Anti-Duplication Gate)
1. Check `.eden/PLAN.md` for the active task scope.
2. **STRICT ANTI-DUPLICATION RULE:** Search `.eden/REGISTRY.md` before creating any helper, utility, config loader, HTTP client, or logger. If a module with overlapping responsibility exists, you MUST import or extend it.
3. State your execution plan briefly: list the exact files you will touch and which existing `REGISTRY.md` components you are reusing.

### Phase 3: E — Execute (Lean Implementation)
1. Implement the solution within the hardware and dependency constraints defined in `.eden/ARCHITECTURE.md`.
2. Favor standard library primitives over third-party dependencies.
3. Strip dead code and unused imports immediately.

### Phase 4: N — Normalize (State Synchronization & Audit Gate)
**Your task is NOT complete until all four steps below are finished:**
1. **Update `.eden/REGISTRY.md`:** Add or update the row for every new/modified source file, exported class/function, or approved dependency.
2. **Append to `.eden/CHANGELOG_AGENT.jsonl`:** Append a single-line valid JSON record at the bottom of the file using this exact schema:
   `{"timestamp": "YYYY-MM-DDTHH:MM:SSZ", "phase": "Normalize", "task_id": "TASK-ID", "action": "CREATED|MODIFIED|REFACTORED", "files": ["path/to/file"], "reused_modules": ["path/to/reused"], "summary": "Concise technical summary"}`
3. **Update `.eden/LEARNINGS.md`:** If you resolved an environment bug, build failure, or hardware quirk, document the root cause and fix.
4. **Run the Compliance Audit:** Execute `python3 scripts/eden-audit.py` and resolve any reported errors before returning your final response.
EOF
  echo "  [+] Created AGENTS.md"
else
  echo "  [~] AGENTS.md already exists (skipped)"
fi

# ------------------------------------------------------------------------------
# 2. Generate .eden/ARCHITECTURE.md
# ------------------------------------------------------------------------------
if [ ! -f .eden/ARCHITECTURE.md ]; then
cat << EOF > .eden/ARCHITECTURE.md
# SYSTEM ARCHITECTURE & CONSTRAINTS (${PROJECT_NAME})

This file records project-specific constraints. Do not assume an operating
system, shell, hardware profile, or runtime in this template.

## Runtime and dependency constraints
- **Primary languages:** Define per project.
- **Supported environments:** Define per project.
- **Memory and performance ceiling:** Define measurable limits when known.
- **Network and persistence:** Document required local services, ports, and data stores.

## Data flow
\`\`\`text
[Input] -> [Application boundary] -> [Domain logic] -> [Local state or output]
\`\`\`
EOF
  echo "  [+] Created .eden/ARCHITECTURE.md"
fi

# ------------------------------------------------------------------------------
# 3. Generate .eden/REGISTRY.md (Anti-Duplication Index)
# ------------------------------------------------------------------------------
if [ ! -f .eden/REGISTRY.md ]; then
cat << 'EOF' > .eden/REGISTRY.md
# COMPONENT & DEPENDENCY REGISTRY
> **AGENT RULE:** Check this registry BEFORE writing any new helper or installing any package.
> To ban a duplicate library, list `BANNED: package_name` in the Notes column (enforced by `eden-audit.py`).

## 1. External Dependencies
| Package | Purpose | Constraint / Notes |
| :--- | :--- | :--- |
| `standard-library` | Default runtime primitives | Always prefer stdlib first |

## 2. Internal Modules & Source Files (Reuse Mandatory)
| File Path | Exported Symbols / Key API | Responsibility | Consumers |
| :--- | :--- | :--- | :--- |
| `scripts/eden-audit.py` | `main()` | Verifies registry & changelog compliance | CLI / Git Hook |

## 3. Configuration & State Schemas
| Path | Type | Description |
| :--- | :--- | :--- |
| `.eden/CHANGELOG_AGENT.jsonl` | JSONL | Append-only agent mutation history |
| `.eden/LEARNINGS.md` | Markdown | Persistent environment & debugging memory |
EOF
  echo "  [+] Created .eden/REGISTRY.md"
fi

# ------------------------------------------------------------------------------
# 4. Generate .eden/PLAN.md
# ------------------------------------------------------------------------------
if [ ! -f .eden/PLAN.md ]; then
cat << 'EOF' > .eden/PLAN.md
# ACTIVE EXECUTION PLAN

## Current Objective
- [ ] **TASK-01:** Define initial system architecture in `.eden/ARCHITECTURE.md` and register existing source files in `.eden/REGISTRY.md`.

## Backlog
- [ ] **TASK-02:** [Add next milestone]

## Completed
- [x] **TASK-00:** Initialized E.D.E.N. Protocol repository control plane.
EOF
  echo "  [+] Created .eden/PLAN.md"
fi

# ------------------------------------------------------------------------------
# 5. Generate .eden/LEARNINGS.md
# ------------------------------------------------------------------------------
if [ ! -f .eden/LEARNINGS.md ]; then
cat << 'EOF' > .eden/LEARNINGS.md
# AGENT LEARNINGS & ENVIRONMENT QUIRKS
Record concise root-cause notes for non-obvious project, dependency, or runtime
issues. Do not encode assumptions that are not true for this project.
EOF
  echo "  [+] Created .eden/LEARNINGS.md"
fi

# ------------------------------------------------------------------------------
# 6. Generate .eden/CHANGELOG_AGENT.jsonl
# ------------------------------------------------------------------------------
if [ ! -f .eden/CHANGELOG_AGENT.jsonl ]; then
cat << EOF > .eden/CHANGELOG_AGENT.jsonl
{"timestamp": "${TIMESTAMP}", "phase": "Normalize", "task_id": "TASK-00", "action": "CREATED", "files": ["AGENTS.md", ".eden/REGISTRY.md", "scripts/eden-audit.py"], "reused_modules": [], "summary": "Initialized E.D.E.N. Protocol repository control plane and audit script."}
EOF
  echo "  [+] Created .eden/CHANGELOG_AGENT.jsonl"
fi

# ------------------------------------------------------------------------------
# 7. Write scripts/eden-audit.py
# ------------------------------------------------------------------------------
cat << 'EOF' > scripts/eden-audit.py
#!/usr/bin/env python3
"""
E.D.E.N. Protocol Compliance Auditor (Zero-Dependency)
"""

import json
import re
import subprocess
import sys
from pathlib import Path

CODE_EXTENSIONS = {".py", ".kt", ".kts", ".js", ".ts", ".tsx", ".sh", ".ps1", ".rs", ".c", ".cpp", ".go"}
IGNORED_DIRS = {".git", ".eden", ".venv", "venv", "node_modules", "build", "dist", "__pycache__", ".gradle", ".idea"}
EXEMPT_FILES = {"scripts/eden-audit.py", "init-eden.sh"}

REGISTRY_PATH = Path(".eden/REGISTRY.md")
CHANGELOG_PATH = Path(".eden/CHANGELOG_AGENT.jsonl")


def get_git_changes():
    try:
        res = subprocess.run(
            ["git", "status", "--porcelain"],
            capture_output=True,
            text=True,
            check=True
        )
    except (subprocess.CalledProcessError, FileNotFoundError):
        print("[EDEN-AUDIT] WARNING: Not a git repository or git not installed. Skipping git-diff checks.")
        return {}

    changes = {}
    for line in res.stdout.splitlines():
        if not line.strip():
            continue
        status = line[:2].strip()
        raw_path = line[3:].strip()
        if " -> " in raw_path:
            raw_path = raw_path.split(" -> ", 1)[1]
        changes[raw_path.strip('"')] = status
    return changes


def is_tracked_code_file(filepath_str: str) -> bool:
    if filepath_str in EXEMPT_FILES:
        return False
    path = Path(filepath_str)
    if any(part in IGNORED_DIRS for part in path.parts):
        return False
    return path.suffix in CODE_EXTENSIONS


def parse_banned_imports(registry_text: str) -> list[str]:
    return re.findall(r"BANNED:\s*`?([a-zA-Z0-9_\-\.]+)`?", registry_text)


def validate_changelog_tail() -> tuple[bool, str]:
    if not CHANGELOG_PATH.exists():
        return False, "Missing .eden/CHANGELOG_AGENT.jsonl file."
    lines = [line.strip() for line in CHANGELOG_PATH.read_text(encoding="utf-8").splitlines() if line.strip()]
    if not lines:
        return False, ".eden/CHANGELOG_AGENT.jsonl is completely empty."
    try:
        last_entry = json.loads(lines[-1])
        required = {"timestamp", "phase", "action", "files", "summary"}
        missing = required - set(last_entry.keys())
        if missing:
            return False, f"Last JSONL entry is missing required keys: {', '.join(sorted(missing))}"
        return True, "Valid"
    except json.JSONDecodeError as e:
        return False, f"Last line of .eden/CHANGELOG_AGENT.jsonl is invalid JSON: {e}"


def main() -> int:
    errors = []

    if not REGISTRY_PATH.exists() or not CHANGELOG_PATH.exists():
        print("[EDEN-AUDIT] FATAL: .eden/ control plane missing. Run ./init-eden.sh first.")
        return 1

    registry_text = REGISTRY_PATH.read_text(encoding="utf-8")
    banned_packages = parse_banned_imports(registry_text)

    changes = get_git_changes()
    code_changes = [f for f, status in changes.items() if status != "D" and is_tracked_code_file(f)]

    for code_file in code_changes:
        normalized_path = code_file.replace("\\", "/")
        if normalized_path not in registry_text:
            errors.append(
                f"UNREGISTERED FILE: `{normalized_path}` was created or modified, "
                f"but is not documented in `.eden/REGISTRY.md`."
            )

        file_path = Path(code_file)
        if file_path.exists() and banned_packages:
            content = file_path.read_text(encoding="utf-8", errors="ignore")
            for pkg in banned_packages:
                pattern = rf"\b(import\s+{re.escape(pkg)}|from\s+{re.escape(pkg)}\s+import|require\(['\"]{re.escape(pkg)}['\"]\))"
                if re.search(pattern, content):
                    errors.append(
                        f"BANNED DEPENDENCY: `{normalized_path}` imports `{pkg}`, "
                        f"which is marked as BANNED in `.eden/REGISTRY.md`."
                    )

    if code_changes:
        if ".eden/CHANGELOG_AGENT.jsonl" not in changes:
            errors.append(
                "MISSING AUDIT LOG: Code files were modified, but `.eden/CHANGELOG_AGENT.jsonl` "
                "was not updated. Append a single-line JSON summary of your changes."
            )
        else:
            valid_json, msg = validate_changelog_tail()
            if not valid_json:
                errors.append(f"MALFORMED AUDIT LOG: {msg}")

    if errors:
        print("=" * 72)
        print("E.D.E.N. PROTOCOL AUDIT FAILED - NORMALIZE PHASE INCOMPLETE")
        print("=" * 72)
        for i, err in enumerate(errors, 1):
            print(f"  {i}. {err}")
        print("-" * 72)
        print("AGENT REMEDIATION REQUIRED:")
        print("  -> Register any new/modified modules in `.eden/REGISTRY.md`")
        print("  -> Append a valid JSON entry to `.eden/CHANGELOG_AGENT.jsonl`")
        print("  -> Record any non-obvious bugs/fixes in `.eden/LEARNINGS.md`")
        print("  -> Re-run: `python3 scripts/eden-audit.py`")
        print("=" * 72)
        return 1

    print("[EDEN-AUDIT] PASSED: Repository state and registry are synchronized.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
EOF
chmod +x scripts/eden-audit.py
echo "  [+] Created scripts/eden-audit.py"

# ------------------------------------------------------------------------------
# 8. Create Provider-Agnostic Symlinks & Git Pre-Commit Hook
# ------------------------------------------------------------------------------
ln -sf AGENTS.md CLAUDE.md
ln -sf AGENTS.md .cursorrules
ln -sf AGENTS.md .windsurfrules
mkdir -p .github
ln -sf ../AGENTS.md .github/copilot-instructions.md
echo "  [+] Linked CLAUDE.md, .cursorrules, .windsurfrules, and .github/copilot-instructions.md -> AGENTS.md"

if [ -d .git ]; then
  mkdir -p .git/hooks
  cat << 'EOF' > .git/hooks/pre-commit
#!/usr/bin/env bash
python3 scripts/eden-audit.py
EOF
  chmod +x .git/hooks/pre-commit
  echo "  [+] Installed .git/hooks/pre-commit enforcement hook"
else
  echo "  [i] Tip: Run 'git init' and re-run ./init-eden.sh to install the pre-commit hook."
fi

echo "E.D.E.N. Scaffold Ready. Test with: python scripts/eden-audit.py"