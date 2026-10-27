# Multi-Agent Routing & Universal Trampolines
**E.D.E.N. Protocol Architecture Guide · Necessity Labs**

---

## 1. The Cross-Platform Symlink Problem

Historically, multi-agent frameworks attempted to create symbolic links pointing proprietary agent configuration files (like `CLAUDE.md`, `.cursorrules`, `.windsurfrules`) back to a central `AGENTS.md`.

In real-world development, this breaks down across platforms:
1. **Windows NTFS Privilege Restrictions:** By default, creating symlinks on Windows requires administrative privileges or Windows Developer Mode. Without these, commands like `ln -s` (in Git Bash) or `New-Item -ItemType SymbolicLink` (in PowerShell) fail with privilege errors (`A required privilege is not held by the client`).
2. **Git Checkout Degradation:** In Git on Windows, `core.symlinks` defaults to `false`. When a repository with symlinks is cloned, Git materializes symlinks as plain text files containing only the target path string (e.g. `AGENTS.md`, 9 bytes). When Claude Code or Cursor reads `CLAUDE.md`, it reads only the string `"AGENTS.md"` rather than following the link.
3. **Agent Parsing Failures:** Certain agent engines do not follow relative filesystem symlinks outside of their sandbox.

---

## 2. The Universal Forwarder Trampoline Solution

E.D.E.N. resolves this by generating **Universal Forwarder Trampolines**. Instead of fragile symlinks, lightweight, explicit pointer files are generated for each supported tool. Each trampoline:
- Explicitly directs the agent to `AGENTS.md` and `.eden/`.
- Declares the active project context and E.D.E.N. governance.
- Works 100% reliably across Windows, Linux, macOS, WSL, PRoot, and Termux.
- Commits cleanly to Git without platform-dependent translation flags.

---

## 3. Supported Agent Tools & Trampoline Standard

```
                     ┌──────────────────┐
                     │    Developer     │
                     └────────┬─────────┘
                              │
          ┌──────────────┬────┴─────────┬──────────────┐
          ▼              ▼              ▼              ▼
     Claude Code       Cursor        Copilot    Gemini / Antigravity
    (CLAUDE.md)    (.cursorrules)   (copilot)       (GEMINI.md)
          │              │              │              │
          └──────────────┴──────┬───────┴──────────────┘
                                ▼
                       ┌─────────────────┐
                       │    AGENTS.md    │
                       └────────┬────────┘
                                ▼
                       ┌─────────────────┐
                       │ .eden/ Control  │
                       │     Plane       │
                       └─────────────────┘
```

### 3.1 Claude Code (`CLAUDE.md`)
```markdown
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
```

### 3.2 Cursor (`.cursorrules` and `.cursor/rules/eden.mdc`)
`.cursorrules`:
```markdown
# .cursorrules — E.D.E.N. PROTOCOL ROUTER
# Governed by Necessity Labs E.D.E.N. Protocol.
# Read and strictly adhere to AGENTS.md and .eden/ control plane files.
Always read AGENTS.md, .eden/ARCHITECTURE.md, and .eden/REGISTRY.md before generating or modifying code.
Follow the 4-phase loop: Evaluate -> Define -> Execute -> Normalize.
Never create duplicate utilities. Run python scripts/eden-audit.py before finishing tasks.
```

`.cursor/rules/eden.mdc`:
```markdown
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
```

### 3.3 GitHub Copilot (`.github/copilot-instructions.md`)
```markdown
# GitHub Copilot Custom Instructions — E.D.E.N. Protocol
This repository adheres to the E.D.E.N. Protocol (Necessity Labs).
- Read and follow AGENTS.md for all architectural invariants and coding rules.
- Consult .eden/REGISTRY.md before creating new utilities to avoid duplication.
- Obey memory ceilings and hardware constraints specified in .eden/ARCHITECTURE.md.
- Run `python scripts/eden-audit.py` to verify state compliance.
```

### 3.4 Gemini CLI / Google Antigravity (`GEMINI.md`)
```markdown
# GEMINI.md — E.D.E.N. PROTOCOL ROUTER
This repository operates under the E.D.E.N. Protocol.
Read AGENTS.md and the .eden/ control plane before proposing or modifying code.
Strictly execute the 4-phase loop: Evaluate -> Define -> Execute -> Normalize.
```

### 3.5 Windsurf (`.windsurfrules`)
```markdown
# .windsurfrules — E.D.E.N. PROTOCOL ROUTER
Adhere to the E.D.E.N. Protocol defined in AGENTS.md and .eden/.
Search .eden/REGISTRY.md before creating utilities.
Execute the 4-phase loop and run python scripts/eden-audit.py before completing work.
```

---

## 4. Bootstrapper Implementation

Both `init-eden.sh` (POSIX) and `init-eden.ps1` (PowerShell) automatically generate and synchronize these trampolines without external dependencies.
