# E.D.E.N. Protocol Specification
**Document Version:** 1.1.0 · **Status:** Canonical Standard · **Necessity Labs**

---

## 1. Scope & Objective

The **E.D.E.N. Protocol** defines an active filesystem control plane for autonomous and human-supervised AI coding agents. It solves cognitive drift, utility duplication, context bloat, and violation of local execution constraints by making repository state machine-readable and audit-enforced.

---

## 2. The Control Plane (`.eden/`)

The `.eden/` directory serves as the persistent state engine of the repository. Every file has an exact responsibility and contract.

### 2.1 `ARCHITECTURE.md` (Constraints, Data Flow & Invariants)
* **Purpose:** Records the project's real runtime, limits, data flow, and non-negotiable rules. Only facts that are true for this project belong here.
* **Format:** Structured Markdown. Template: `templates/eden/ARCHITECTURE.md`.
* **Required Sections:**
  1. `Runtime & Environment`: Languages and versions, supported platforms, toolchain / package manager.
  2. `Constraints & Limits`: Measurable memory or performance ceilings, network, ports, external services.
  3. `Core Data Flow`: Directional diagram or pipeline showing source-to-sink data paths.
  4. `Invariants`: Non-negotiable architectural rules (e.g., local-first, no network in the domain layer).

### 2.2 `REGISTRY.md` (Anti-Duplication Component Map)
* **Purpose:** Comprehensive index of internal modules, public APIs, and approved external dependencies. Acts as a shield against parallel implementations.
* **Format:** Markdown tables.
* **Sections:**
  1. `1. Approved External Dependencies`: Approved third-party packages, version constraints, and `BANNED:` patterns.
  2. `2. Internal Modules & Source Files`: File path, exported symbols, single responsibility, and consumers.
  3. `3. Data Schemas & State Files`: Schema path, format, and description.
* **Registration rule:** A source file counts as registered only when its exact repository-relative path is the first cell of a table row. Prose mentions, HTML comments, and code fences are ignored by the auditor.
* **`BANNED:` Dependency Mechanism:**
  When an approved package replaces an alternative (e.g., standard library or a specific HTTP client), the banned alternative is tagged as:
  `BANNED: <package_name>`
  The compliance auditor (`eden-audit.py`) automatically scans new code for imports matching this pattern and halts commits if detected.

### 2.3 `PLAN.md` (Single Source of Active Tasks & Backlog)
* **Purpose:** Single source of truth for the current objective, its acceptance criteria, the backlog, and completed work. Replaces scattered backlog files.
* **Format:** Markdown task lists (`- [ ]`, `- [x]`). Template: `templates/eden/PLAN.md`.
* **Sections:**
  1. `Current Objective`: The single in-flight task, with acceptance criteria.
  2. `Backlog`: Prioritized next tasks, each with acceptance criteria.
  3. `Completed`: Historical record of completed tasks.
* **Conflicts:** The human's current request takes precedence over `PLAN.md`; agents flag the conflict and update the plan to match what was done.

### 2.4 `LEARNINGS.md` (Episodic & Debugging Memory)
* **Purpose:** Prevents agents across sessions from repeating previously resolved mistakes or misconfiguring environment quirks.
* **Format:** Chronological Markdown entries under `## Entries`. Template: `templates/eden/LEARNINGS.md` (ships with no entries; the format example lives in an HTML comment).
* **Standard Entry Format:**
  `- [YYYY-MM-DD] Subsystem: Symptom -> Root Cause -> Fix / Rule`
* **Rule:** Only verified root causes. Agents treat every entry as fact, so never ship sample or speculative entries.

### 2.5 `CHANGELOG_AGENT.jsonl` (Append-Only Machine-Readable Mutation Log)
* **Purpose:** Provides high-density, low-token context on code modifications. Agents or scripts can ingest recent history (`tail -n 15`) without reading large diffs.
* **Format:** Strictly one valid JSON object per line (JSON Lines), no blank lines. Append-only: existing lines are never edited or removed.
* **Audit contract:** Any change to a source file must come with at least one new line whose `files` array lists that file (see `docs/CLI_AND_AUDITING.md`).
* **Schema Contract:**
  ```json
  {
    "timestamp": "ISO-8601 UTC string (e.g. 2026-10-27T16:00:00Z)",
    "phase": "Normalize",
    "task_id": "STRING (e.g. TASK-01)",
    "action": "CREATED | MODIFIED | REFACTORED | DELETED",
    "files": ["array", "of", "relative/paths"],
    "reused_modules": ["array", "of", "existing/registry/paths"],
    "summary": "Concise technical description of change"
  }
  ```

---

## 3. The Root Operating System (`AGENTS.md`)

`AGENTS.md` is the universal root instruction file for all AI coding agents. The init scripts copy the committed `AGENTS.md` byte-for-byte, so there is one source of truth. It is written as short decision rules (~250-400 words) and contains:
1. `Commands`: setup, build, test, lint, and verify commands (placeholders the adopter fills in).
2. `Pick a lane first`: read-only (skip Normalize), trivial (change + audit), normal (full loop), architectural (plan, then wait for human approval).
3. `The loop`: Evaluate -> Define -> Execute -> Normalize, applied by lane.
4. Conflict rule: the human's current request wins over `PLAN.md`; flag the conflict.
5. `Done means`: tests / `.eden/verify` pass, `eden-audit.py --verify` exits 0, acceptance criteria met.
6. `Stop and escalate`: after 3 failed audit or test fix rounds, report to a human.
7. `Never`: secrets, force-push / history rewrites / `--no-verify`, deleting user data, editing changelog history, banned or unapproved dependencies, guesses in LEARNINGS.

### 3.1 Optional `.eden/verify`
A project may add `.eden/verify` (shell script) or `.eden/verify.py` with its test and lint commands. `eden-audit.py --verify` runs it and fails on a non-zero exit. It is optional and adds no dependencies.

---

## 4. Multi-Agent Interoperability

Because different coding tools search for proprietary instruction files, E.D.E.N. uses universal forwarder trampolines that route every tool directly into `AGENTS.md` and `.eden/`. The pointer files are ASCII-only, have no BOM, and are copied byte-for-byte by the init scripts; in an existing project they are merged as an `<!-- EDEN:BEGIN v1 -->` ... `<!-- EDEN:END -->` block instead. Each supported tool also gets a stop hook config that runs `scripts/eden-hook.py`, and all tools share the skills in `.agents/skills/`. See `docs/MULTI_AGENT_ROUTING.md` for details.
