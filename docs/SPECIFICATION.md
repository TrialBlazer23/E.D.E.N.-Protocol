# E.D.E.N. Protocol Specification
**Document Version:** 1.0.0 · **Status:** Canonical Standard · **Necessity Labs**

---

## 1. Scope & Objective

The **E.D.E.N. Protocol** defines an active filesystem control plane for autonomous and human-supervised AI coding agents. It solves cognitive drift, utility duplication, context bloat, and violation of local execution constraints by making repository state machine-readable and audit-enforced.

---

## 2. The Control Plane (`.eden/`)

The `.eden/` directory serves as the persistent state engine of the repository. Every file has an exact responsibility and contract.

### 2.1 `ARCHITECTURE.md` (System Constraints & Hardware Ceilings)
* **Purpose:** Defines physical execution ceilings, memory budgets, supported runtimes, network boundaries, and data flow.
* **Format:** Structured Markdown.
* **Required Sections:**
  1. `Hardware Ceiling`: Quantified limits (e.g., maximum memory, thread count, CPU architecture, thermal envelopes).
  2. `Environment & Toolchain`: Pinned toolchain, SDK versions, JNI/native bindings, and environment variables.
  3. `Core Data Flow`: Directional diagram or pipeline showing source-to-sink data paths.
  4. `Invariants`: Non-negotiable architectural axioms (e.g., local-first, zero cloud leakage, lossless persistence).

### 2.2 `REGISTRY.md` (Anti-Duplication Component Map)
* **Purpose:** Comprehensive index of internal modules, public APIs, and approved external dependencies. Acts as a shield against parallel implementations.
* **Format:** Markdown tables.
* **Sections:**
  1. `1. Approved External Dependencies`: Approved third-party packages, version constraints, and `BANNED:` patterns.
  2. `2. Internal Modules & Source Files`: File path, exported symbols, single responsibility, and consumers.
  3. `3. Data Schemas & State Files`: Schema path, format, and description.
* **`BANNED:` Dependency Mechanism:**
  When an approved package replaces an alternative (e.g., standard library or a specific HTTP client), the banned alternative is tagged as:
  `BANNED: <package_name>`
  The compliance auditor (`eden-audit.py`) automatically scans new code for imports matching this pattern and halts commits if detected.

### 2.3 `PLAN.md` (Single Source of Active Tasks & Backlog)
* **Purpose:** Single source of truth for active sprint tasks, acceptance criteria, and completed milestones. Replaces scattered backlog files.
* **Format:** Markdown task lists (`- [ ]`, `- [x]`).
* **Sections:**
  1. `Current Objective`: The single in-flight focus.
  2. `Active Sprint / Queue`: Prioritized backlog with acceptance criteria.
  3. `Completed`: Historical record of completed tasks.

### 2.4 `LEARNINGS.md` (Episodic & Debugging Memory)
* **Purpose:** Prevents agents across sessions from repeating previously resolved mistakes, fighting toolchain bugs, or misconfiguring environment quirks.
* **Format:** Chronological Markdown entries.
* **Standard Entry Format:**
  `- [YYYY-MM-DD] Subsystem: Symptom -> Root Cause -> Fix / Rule`

### 2.5 `CHANGELOG_AGENT.jsonl` (Append-Only Machine-Readable Mutation Log)
* **Purpose:** Provides high-density, low-token context on code modifications. Agents or scripts can ingest recent history (`tail -n 15`) without reading large diffs.
* **Format:** Strictly one valid JSON object per line (JSON Lines).
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

`AGENTS.md` is the universal root configuration for all AI coding agents. It details:
1. Core E.D.E.N. philosophy and the Law of Necessity.
2. The 4-Phase execution loop.
3. Architecture boundaries (Clean Architecture, unidirectional data flow, domain purity).
4. Build, lint, and test CLI commands.
5. Verification and normalization criteria.

---

## 4. Multi-Agent Interoperability

Because different coding tools search for proprietary instruction files, E.D.E.N. uses universal forwarder trampolines that route every tool directly into `AGENTS.md` and `.eden/`. See `docs/MULTI_AGENT_ROUTING.md` for implementation details.
