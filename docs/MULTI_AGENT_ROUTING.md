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
     Antigravity    Cursor/Grok     Copilot     Claude Code (opt-in)
     (GEMINI.md)    (eden.mdc)     (copilot)       (CLAUDE.md)
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

### 3.1 What each tool loads

The committed files in the protocol repository root are the canonical versions; they are not duplicated here so they cannot drift. The installer copies them byte-for-byte (new mode) or merges them as an EDEN block (adopt mode). `--tools` picks which rows are installed; the default is the first four.

| Tool (`--tools` name) | Instructions | Skills | Stop hook |
| :--- | :--- | :--- | :--- |
| Google Antigravity (`antigravity`) | `AGENTS.md`, `GEMINI.md` | `.agents/skills/` | `.agents/hooks.json` |
| Cursor (`cursor`) | `AGENTS.md`, `.cursor/rules/eden.mdc` (`alwaysApply`, front matter on line 1) | `.agents/skills/` | `.cursor/hooks.json` |
| Grok Build (`grok`) | `AGENTS.md` | `.agents/skills/` | `.cursor/hooks.json` (Grok reads Cursor's hook file; trust the folder with `grok --trust` or `/hooks-trust`, check with `grok inspect`) |
| VS Code / GitHub Copilot (`vscode`) | `.github/copilot-instructions.md`, `AGENTS.md` | `.agents/skills/` where supported | `.github/hooks/eden.json` |
| Claude Code (`claude`, opt-in) | `CLAUDE.md` | - | none shipped (see 3.3) |
| Legacy (`--legacy`) | `.cursorrules`, `.windsurfrules` | - | - |

Every pointer file says the same three things: read `AGENTS.md` first, search `.eden/REGISTRY.md` before adding helpers or packages, and run `python3 scripts/eden-audit.py --verify` before finishing a code change. Lane rules (read-only, trivial, normal, architectural) live only in `AGENTS.md`. `python3 scripts/eden-audit.py --doctor` prints this table for a real repository, with what is present and what is missing.

### 3.2 Encoding rules
- ASCII only, no byte-order mark. A BOM before the `---` front matter breaks Cursor's `.mdc` rule header, and non-ASCII characters were garbled by Windows PowerShell 5.1 when it read a BOM-less UTF-8 script.
- `tests/test_init.py` fails if a BOM or non-ASCII byte appears in `AGENTS.md`, a pointer file, a skill, or `init-eden.ps1`.

### 3.3 One stop hook, four callers

`scripts/eden-hook.py` is the single hook script. It reads the hook JSON on stdin, works out which tool called it, and answers in that tool's format:

| Caller | Detected by | "Keep working" reply | Gated stops |
| :--- | :--- | :--- | :--- |
| Cursor | `loop_count`, `cursor_version`, `workspace_roots` | `{"followup_message": ...}` | `status == "completed"` |
| Grok Build | `GROK_HOOK_EVENT` env, `hookEventName`, `stopHookActive` | `{"decision": "block", "reason": ...}` | `reason == "end_turn"`, not a subagent |
| Copilot | `stopReason` / `stop_reason`, `stop_hook_active` | `decision: block` + `reason` (flat and in `hookSpecificOutput`) | `end_turn` |
| Antigravity | `executionNum`, `terminationReason`, `workspacePaths` | `{"decision": "continue", "reason": ...}` | `model_stop`, fully idle |

Behavior:
- Audits only when source files changed (`git status`); otherwise it allows the stop at once.
- Caps forced continuations at 2 per user turn (state in `<git-dir>/eden-hook-state.json`), so with the original attempt the agent gets 3 tries, then stops and reports, as `AGENTS.md` says. Cursor's `loop_limit` is also 2; Grok and Copilot have their own cap of 8.
- Fails open: bad input, a missing repository, a timeout, or an internal error never traps the agent.
- `EDEN_HOOK_VERIFY=1` also runs `.eden/verify`; `EDEN_HOOK_DISABLE=1` turns the hook off.

Do not add the same hook under `.grok/hooks/` or `.claude/settings.json`: Grok Build also loads those, so the audit would run twice per stop. Claude Code users who want the gate can point a `Stop` hook in their own `.claude/settings.local.json` at `scripts/eden-hook.py` (it answers in the Claude-compatible format), but only if they do not also use Grok Build in that repository.

Windows: the hook commands try `python3`, then `python`, then `py -3`. Copilot gets a dedicated `powershell` command that probes each interpreter (skipping the Microsoft Store stub). The `a || b` fallback in the Cursor and Antigravity commands needs a shell that understands `||` (cmd, Git Bash, PowerShell 7); in Windows PowerShell 5.1 make sure `python3` resolves or edit the command.

---

## 4. Bootstrapper Implementation

`init-eden.sh` (POSIX) and `init-eden.ps1` (PowerShell) are thin wrappers: they parse options, fetch the protocol files if needed (`EDEN_RAW_BASE`), find Python 3, and run `scripts/eden-install.py` from the protocol checkout. The installer never replaces an existing file without `--force` / `-Force` (the old file is kept as `<file>.eden-bak`); in adopt mode it merges an EDEN block or hook entry instead.
