---
name: eden-architect
description: Plan an Architectural-lane change in an E.D.E.N. repo (new module boundary, new dependency, schema or data change, deleting a component, or touching an invariant in .eden/ARCHITECTURE.md). Writes the plan into .eden/PLAN.md and stops for human approval before any code is written.
---

# E.D.E.N. Architect (plan, then wait)

Use this when the request is in the Architectural lane of AGENTS.md. Do not edit source files in this skill.

## Steps
1. Evaluate: read `.eden/ARCHITECTURE.md`, `.eden/REGISTRY.md`, `.eden/LEARNINGS.md`, and the last 10 lines of `.eden/CHANGELOG_AGENT.jsonl`.
2. Check reuse: search the registry for modules and approved packages that already cover the need. Note any `BANNED:` packages.
3. Write the plan into `.eden/PLAN.md` under Current Objective as a new task:
   - `**TASK-NN:** <goal>`
   - Approach: modules to add or change, and why existing ones are not enough.
   - Files to touch, new dependencies (with reason), data or schema changes and migration.
   - Invariants affected in ARCHITECTURE.md and how they stay true (or the proposed change to them).
   - Acceptance: tests and checks that prove it works.
   - Risks and rollback.
4. Summarize the plan for the human and ask for approval. Stop here. Do not start Execute until the human approves in this conversation.
5. After approval, run the normal loop, then the eden-normalize skill. Update ARCHITECTURE.md if an invariant or the data flow changed.
