# E.D.E.N. Protocol Migration & Retrofit Guide
**Step-by-Step Modernization for Existing Repositories · Necessity Labs**

---

## 1. Why Retrofit Existing Projects?

Most active software repositories accumulate documentation sprawl over time:
- Inconsistent notes scattered across root markdown files (`NEXT-STEPS.md`, `PROJECT_STATUS.md`, `TODO.md`, `SETUP.md`).
- Multi-hundred-line agent instruction files that exceed context budgets.
- AI agents creating duplicate utilities because they lack a centralized, lightweight index of existing code.

Retrofitting a codebase with E.D.E.N. Protocol replaces this chaotic sprawl with a clean, unified, multi-agent control plane.

---

## 2. 5-Step Migration Procedure

```mermaid
flowchart TD
    S1["Step 1: Run Bootstrapper<br/>(init-eden.sh / init-eden.ps1)"] --> S2["Step 2: Auto-Index Existing Code<br/>(eden-index.py)"]
    S2 --> S3["Step 3: Migrate Active State<br/>(Backlog -> PLAN.md, Invariants -> ARCHITECTURE.md)"]
    S3 --> S4["Step 4: Prune & Consolidate<br/>(Delete redundant status docs, move guides to docs/)"]
    S4 --> S5["Step 5: Audit & Lock<br/>(Run eden-audit.py & install pre-commit hook)"]
```

### Step 1: Run the Bootstrapper
Clone the protocol repository somewhere outside your project, then run its bootstrapper from the root of your existing repository (or pass the repository path):

**Linux / macOS / Termux:**
```bash
/path/to/E.D.E.N-Protocol/init-eden.sh            # current directory
/path/to/E.D.E.N-Protocol/init-eden.sh ~/src/app  # explicit target
```

**Windows PowerShell:**
```powershell
C:\src\E.D.E.N-Protocol\init-eden.ps1             # current directory
C:\src\E.D.E.N-Protocol\init-eden.ps1 C:\src\app
```

Existing `AGENTS.md`, pointer files, scripts, and pre-commit hooks are left alone; the bootstrapper lists what it skipped. Re-run with `--force` / `-Force` to replace them (each replaced file is kept as `<file>.eden-bak`). Existing `.eden/` state files are never replaced.

This creates:
- The `.eden/` control plane (`ARCHITECTURE.md`, `REGISTRY.md`, `PLAN.md`, `LEARNINGS.md`, `CHANGELOG_AGENT.jsonl`).
- The `scripts/` directory with `eden-audit.py` and `eden-index.py`.
- Universal forwarder trampolines (`CLAUDE.md`, `.cursorrules`, `.cursor/rules/eden.mdc`, `.github/copilot-instructions.md`, `GEMINI.md`, `.windsurfrules`).
- The `.git/hooks/pre-commit` hook (runs `eden-audit.py --staged`).

### Step 2: Auto-Index the Codebase
Generate the initial index of your internal modules, classes, and exported APIs:
```bash
python scripts/eden-index.py .
```
Verify that `.eden/REGISTRY.md` now lists your core modules in Section 2. Add any known `BANNED:` packages to Section 1.

### Step 3: Migrate Active Tasks & Invariants
1. **Backlogs & Roadmaps:** Move in-flight tasks and sprint items from legacy files (`NEXT-STEPS.md`, `TODO.md`) into `.eden/PLAN.md`.
2. **Hardware & Environment Boundaries:** Move memory ceilings, runtime constraints, toolchain notes, and data flow from legacy status documents into `.eden/ARCHITECTURE.md`.
3. **Past Pitfalls & Quirks:** Move troubleshooting tips and resolved environment bugs into `.eden/LEARNINGS.md`.

### Step 4: Prune Redundant Documents
1. **Delete Dead Status Files:** Once backlog and architecture have been absorbed into `.eden/`, delete legacy files like `PROJECT_STATUS.md` and `NEXT-STEPS.md`.
2. **Organize Guides:** Move standalone setup or design docs into categorized subdirectories in `docs/` (e.g. `docs/setup/`, `docs/hardware/`, `docs/design/`).
3. **Keep Root Clean:** Keep only `README.md`, `LICENSE`, `AGENTS.md`, and the universal forwarder trampolines in the root folder.

### Step 5: Verify Compliance
Record the migration in the agent mutation log:
```json
{"timestamp": "2026-10-27T16:00:00Z", "phase": "Normalize", "task_id": "EDEN-MIGRATION", "action": "REFACTORED", "files": ["AGENTS.md", ".eden/ARCHITECTURE.md", ".eden/PLAN.md", ".eden/REGISTRY.md"], "reused_modules": [], "summary": "Migrated repository to E.D.E.N. Protocol control plane."}
```
Fill in the `Commands` section of `AGENTS.md`, optionally add `.eden/verify` with your test and lint commands, then run the compliance auditor:
```bash
python3 scripts/eden-audit.py --verify
```
When it exits with `0`, your repository is fully compliant and ready for autonomous agent development.
