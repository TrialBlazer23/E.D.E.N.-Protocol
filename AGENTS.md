# E.D.E.N. PROTOCOL: AGENT OPERATING SYSTEM

You are operating inside an E.D.E.N. governed repository. You must adhere strictly to the Law of Necessity: local sovereignty, zero bloat, and strict hardware efficiency.

## MANDATORY EXECUTION LOOP
Do NOT write or modify code until you have completed Phase 1 and Phase 2.

### Phase 1: E — Evaluate (Pre-Flight Check)
1. Read `.eden/ARCHITECTURE.md` to understand hardware/memory constraints.
2. Read `.eden/REGISTRY.md` to see ALL existing utilities, models, and modules.
3. Read `.eden/LEARNINGS.md` to avoid repeating past architectural mistakes.
4. Review the recent entries in `.eden/CHANGELOG_AGENT.jsonl`.

### Phase 2: D — Define (Anti-Duplication Gate)
1. Check `.eden/PLAN.md` for the current active task.
2. **ANTI-DUPLICATION LAW:** Before creating any new function, class, helper, or installing a package, search `.eden/REGISTRY.md`. If a similar component exists, you MUST import or extend it. Never build parallel implementations.
3. State your proposed file changes and which existing registry modules you will reuse before writing code.

### Phase 3: E — Execute (Lean Implementation)
1. Write modular, single-responsibility code with minimal external dependencies.
2. Respect the target hardware ceiling (e.g., 4GB RAM limit, edge execution). Avoid heavy abstractions when standard library primitives suffice.

### Phase 4: N — Normalize (Mandatory Post-Flight State Update)
Your task is **INCOMPLETE** until you update the repository state:
1. **Update `.eden/REGISTRY.md`:** If you created a new file, class, or shared function, register its path, purpose, and signature.
2. **Append to `.eden/CHANGELOG_AGENT.jsonl`:** Log a single-line JSON entry of what changed and why.
3. **Update `.eden/LEARNINGS.md`:** If you hit an environment quirk, port conflict, or tricky bug, document the root cause and fix.
4. Run `python scripts/eden-audit.py` (or the equivalent interpreter command for the project) and resolve all reported errors.