#!/usr/bin/env bash
# ==============================================================================
# E.D.E.N. Protocol Repository Bootstrapper (init-eden.sh)
# Necessity Labs — Model-Agnostic Coding Agent Control Plane
# ==============================================================================
set -euo pipefail

PROJECT_NAME="${1:-$(basename "$PWD")}"
TIMESTAMP="$(date -u +"%Y-%m-%dT%H:%M:%SZ")"

echo "⚡ Initializing E.D.E.N. Protocol scaffold for: ${PROJECT_NAME}"

mkdir -p .eden scripts .cursor/rules .github

# ------------------------------------------------------------------------------
# 1. Master AGENTS.md
# ------------------------------------------------------------------------------
if [ ! -f AGENTS.md ]; then
cat << 'EOF' > AGENTS.md
# E.D.E.N. PROTOCOL: AGENT OPERATING SYSTEM

You are operating inside an **E.D.E.N.** governed repository (**Necessity Labs**).
Adhere strictly to the **Law of Necessity**:
- **E — Everything is broken:** Assume zero-trust defaults. Do not rely on fragile cloud dependencies or bloated abstractions.
- **D — Define the mechanics:** Understand raw memory, I/O, ports, and execution constraints before touching code.
- **E — Engineer the architecture:** Build modular, sovereign, local-first systems.
- **N — Necessity dictates the output:** Zero dead code, zero duplicate utilities, zero unapproved packages.

---

## MANDATORY 4-PHASE EXECUTION LOOP

You MUST follow these phases sequentially for every task. Do NOT skip Phase 1, 2, or 4.

### Phase 1: E — Evaluate (Context & Constraint Ingestion)
Before proposing or writing any code, read:
1. `.eden/ARCHITECTURE.md` — System boundaries, target hardware ceiling, and data flow.
2. `.eden/REGISTRY.md` — Complete index of existing internal modules and approved dependencies.
3. `.eden/LEARNINGS.md` — Known environment quirks and resolved pitfalls.
4. Recent entries in `.eden/CHANGELOG_AGENT.jsonl` — Recent mutations for immediate context.

### Phase 2: D — Define (The Anti-Duplication Gate)
1. Check `.eden/PLAN.md` for the active task scope.
2. **STRICT ANTI-DUPLICATION RULE:** Search `.eden/REGISTRY.md` before creating any helper, utility, or class. If a module with overlapping responsibility exists, you MUST import or extend it.
3. State your execution plan briefly: list the exact files you will touch and which existing `REGISTRY.md` components you are reusing.

### Phase 3: E — Execute (Lean Implementation)
1. Implement the solution within the hardware and dependency constraints defined in `.eden/ARCHITECTURE.md`.
2. Favor standard library primitives over third-party dependencies.
3. Strip dead code and unused imports immediately.

### Phase 4: N — Normalize (State Synchronization & Audit Gate)
Your task is **INCOMPLETE** until all steps below are finished:
1. **Update `.eden/REGISTRY.md`:** Add or update the row for every new/modified source file, exported class/function, or approved dependency.
2. **Append to `.eden/CHANGELOG_AGENT.jsonl`:** Append a single-line valid JSON record at the bottom of the file using the standard schema.
3. **Update `.eden/LEARNINGS.md`:** If you resolved an environment bug, build failure, or hardware quirk, document the root cause and fix.
4. **Update `.eden/PLAN.md`:** Mark completed criteria and update active backlog.
5. **Run the Compliance Audit:** Execute `python3 scripts/eden-audit.py` and resolve any reported errors before returning your final response.
EOF
  echo "  [+] Created AGENTS.md"
else
  echo "  [~] AGENTS.md already exists (skipped)"
fi

# ------------------------------------------------------------------------------
# 2. .eden Control Plane Files
# ------------------------------------------------------------------------------
if [ ! -f .eden/ARCHITECTURE.md ]; then
cat << EOF > .eden/ARCHITECTURE.md
# SYSTEM ARCHITECTURE & CONSTRAINTS (${PROJECT_NAME})

This file records project-specific constraints.

## 1. Runtime and Dependency Constraints
- **Primary languages:** Define per project.
- **Supported environments:** Define per project.
- **Memory and performance ceiling:** Define measurable limits when known.
- **Network and persistence:** Document required local services, ports, and data stores.

## 2. Core Data Flow
\`\`\`text
[Input] -> [Application Boundary] -> [Domain Logic] -> [Local State / Output]
\`\`\`
EOF
  echo "  [+] Created .eden/ARCHITECTURE.md"
fi

if [ ! -f .eden/PLAN.md ]; then
cat << 'EOF' > .eden/PLAN.md
# ACTIVE EXECUTION PLAN

## Current Objective
- [ ] **TASK-01:** Define initial system architecture in `.eden/ARCHITECTURE.md` and register source files in `.eden/REGISTRY.md`.

## Backlog
- [ ] **TASK-02:** [Add next milestone]

## Completed
- [x] **TASK-00:** Initialized E.D.E.N. Protocol repository control plane.
EOF
  echo "  [+] Created .eden/PLAN.md"
fi

if [ ! -f .eden/REGISTRY.md ]; then
cat << 'EOF' > .eden/REGISTRY.md
# COMPONENT & DEPENDENCY REGISTRY
> **AGENT RULE:** Check this registry BEFORE writing any new helper or installing any package.
> To ban a duplicate library, list `BANNED: package_name` in the Notes column (enforced by `eden-audit.py`).

## 1. Approved External Dependencies
| Package | Purpose | Constraint / Notes |
| :--- | :--- | :--- |
| `standard-library` | Default runtime primitives | Always prefer stdlib first |

## 2. Internal Modules & Source Files (Reuse Mandatory)
| File Path | Exported Symbols / Key API | Responsibility | Consumers |
| :--- | :--- | :--- | :--- |

## 3. Configuration & State Schemas
| Path | Type | Description |
| :--- | :--- | :--- |
| `.eden/CHANGELOG_AGENT.jsonl` | JSONL | Append-only agent mutation history |
| `.eden/LEARNINGS.md` | Markdown | Persistent environment & debugging memory |
| `.eden/ARCHITECTURE.md` | Markdown | Project constraints and data flow |
| `.eden/PLAN.md` | Markdown | Active task scope and milestones |
EOF
  echo "  [+] Created .eden/REGISTRY.md"
fi

if [ ! -f .eden/LEARNINGS.md ]; then
cat << 'EOF' > .eden/LEARNINGS.md
# AGENT LEARNINGS & ENVIRONMENT QUIRKS
> Record concise root-cause notes for non-obvious project, dependency, or runtime issues.
EOF
  echo "  [+] Created .eden/LEARNINGS.md"
fi

if [ ! -f .eden/CHANGELOG_AGENT.jsonl ] || [ ! -s .eden/CHANGELOG_AGENT.jsonl ]; then
cat << EOF > .eden/CHANGELOG_AGENT.jsonl
{"timestamp": "${TIMESTAMP}", "phase": "Normalize", "task_id": "TASK-00", "action": "CREATED", "files": ["AGENTS.md", ".eden/ARCHITECTURE.md", ".eden/PLAN.md", ".eden/LEARNINGS.md", ".eden/REGISTRY.md"], "reused_modules": [], "summary": "Initialized the E.D.E.N. control plane."}
EOF
  echo "  [+] Created .eden/CHANGELOG_AGENT.jsonl"
fi

# ------------------------------------------------------------------------------
# 3. Universal Multi-Agent Forwarder Trampolines
# ------------------------------------------------------------------------------
cat << 'EOF' > CLAUDE.md
# CLAUDE.md — E.D.E.N. PROTOCOL ROUTER

> **MANDATORY FOR CLAUDE CODE:** This repository is strictly governed by the **E.D.E.N. Protocol** (Necessity Labs).
> All operating instructions, 4-phase execution loop, build commands, and architectural invariants are defined in:
>
> 1. [`AGENTS.md`](AGENTS.md) — Master Agent Operating System & Execution Loop
> 2. [`.eden/ARCHITECTURE.md`](.eden/ARCHITECTURE.md) — System boundaries, hardware ceiling, and constraints
> 3. [`.eden/REGISTRY.md`](.eden/REGISTRY.md) — Component registry & anti-duplication shield
> 4. [`.eden/PLAN.md`](.eden/PLAN.md) — Active task scope and acceptance criteria
> 5. [`.eden/LEARNINGS.md`](.eden/LEARNINGS.md) — Persistent episodic memory of resolved pitfalls
>
> You MUST read AGENTS.md before proposing or writing code. Do NOT bypass Phase 1 (Evaluate) or Phase 2 (Define).
EOF

cat << 'EOF' > .cursorrules
# .cursorrules — E.D.E.N. PROTOCOL ROUTER
# Governed by Necessity Labs E.D.E.N. Protocol.
# Read and strictly adhere to AGENTS.md and the .eden/ control plane.
Always read AGENTS.md, .eden/ARCHITECTURE.md, and .eden/REGISTRY.md before generating or modifying code.
Follow the 4-phase loop: Evaluate -> Define -> Execute -> Normalize.
Never create duplicate utilities. Run python scripts/eden-audit.py before finishing tasks.
EOF

cat << 'EOF' > .cursor/rules/eden.mdc
---
description: E.D.E.N. Protocol Master Rule
globs: *
alwaysApply: true
---
# E.D.E.N. PROTOCOL ENFORCEMENT
All code generation and modification must adhere to AGENTS.md and the .eden/ control plane.
1. Evaluate: Read .eden/ARCHITECTURE.md and .eden/REGISTRY.md.
2. Define: Search .eden/REGISTRY.md before writing helpers or installing packages.
3. Execute: Adhere to hardware and memory constraints.
4. Normalize: Update .eden/REGISTRY.md, .eden/CHANGELOG_AGENT.jsonl, and run python scripts/eden-audit.py.
EOF

cat << 'EOF' > .github/copilot-instructions.md
# GitHub Copilot Custom Instructions — E.D.E.N. Protocol
This repository adheres to the E.D.E.N. Protocol (Necessity Labs).
- Read and follow AGENTS.md for all architectural invariants and coding rules.
- Consult .eden/REGISTRY.md before creating new utilities to avoid duplication.
- Obey memory ceilings and hardware constraints specified in .eden/ARCHITECTURE.md.
- Run `python scripts/eden-audit.py` to verify state compliance.
EOF

cat << 'EOF' > GEMINI.md
# GEMINI.md — E.D.E.N. PROTOCOL ROUTER
This repository operates under the E.D.E.N. Protocol (Necessity Labs).
Read AGENTS.md and the .eden/ control plane before proposing or modifying code.
Strictly execute the 4-phase loop: Evaluate -> Define -> Execute -> Normalize.
Never duplicate existing utilities. Run python scripts/eden-audit.py before returning results.
EOF

cat << 'EOF' > .windsurfrules
# .windsurfrules — E.D.E.N. PROTOCOL ROUTER
Adhere to the E.D.E.N. Protocol defined in AGENTS.md and .eden/.
Search .eden/REGISTRY.md before creating utilities.
Execute the 4-phase loop and run python scripts/eden-audit.py before completing work.
EOF

echo "  [+] Deployed universal multi-agent trampolines (CLAUDE, Cursor, Copilot, Gemini, Windsurf)"

# ------------------------------------------------------------------------------
# 4. Git Pre-Commit Hook
# ------------------------------------------------------------------------------
if [ -d .git ]; then
  mkdir -p .git/hooks
  cat << 'EOF' > .git/hooks/pre-commit
#!/bin/sh
if command -v python3 >/dev/null 2>&1; then
    python3 scripts/eden-audit.py
elif command -v python >/dev/null 2>&1; then
    python scripts/eden-audit.py
fi
EOF
  chmod +x .git/hooks/pre-commit
  echo "  [+] Installed .git/hooks/pre-commit enforcement hook"
fi

# ------------------------------------------------------------------------------
# 5. Run Auto-Indexer
# ------------------------------------------------------------------------------
if [ -f scripts/eden-index.py ]; then
  if command -v python3 >/dev/null 2>&1; then
    python3 scripts/eden-index.py .
  elif command -v python >/dev/null 2>&1; then
    python scripts/eden-index.py .
  fi
fi

echo "✅ E.D.E.N. Scaffold Ready. Test compliance with: python scripts/eden-audit.py"
