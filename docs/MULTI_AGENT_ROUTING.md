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

### 3.1 Pointer files

The committed files in the protocol repository root are the canonical versions; they are not duplicated here so they cannot drift. The init scripts copy them byte-for-byte.

| Tool | File | Notes |
| :--- | :--- | :--- |
| Claude Code | `CLAUDE.md` | Links to `AGENTS.md` and the `.eden/` files |
| Cursor | `.cursor/rules/eden.mdc` | `alwaysApply: true` rule with front matter on line 1 |
| Cursor (legacy) | `.cursorrules` | Kept for older Cursor versions |
| GitHub Copilot | `.github/copilot-instructions.md` | |
| Gemini CLI / Antigravity | `GEMINI.md` | |
| Windsurf | `.windsurfrules` | |

Every pointer file says the same three things: read `AGENTS.md` first, search `.eden/REGISTRY.md` before adding helpers or packages, and run `python3 scripts/eden-audit.py --verify` before finishing a code change. Lane rules (read-only, trivial, normal, architectural) live only in `AGENTS.md`.

### 3.2 Encoding rules
- ASCII only, no byte-order mark. A BOM before the `---` front matter breaks Cursor's `.mdc` rule header, and non-ASCII characters were garbled by Windows PowerShell 5.1 when it read a BOM-less UTF-8 script.
- `tests/test_init.py` fails if a BOM or non-ASCII byte appears in `AGENTS.md`, a pointer file, or `init-eden.ps1`.

---

## 4. Bootstrapper Implementation

Both `init-eden.sh` (POSIX) and `init-eden.ps1` (PowerShell) copy these files from the protocol checkout into the target repository. An existing pointer file is never replaced unless `--force` / `-Force` is given, and then the old file is kept as `<file>.eden-bak`.
