# CLAUDE.md - E.D.E.N. Protocol pointer

This repository follows the E.D.E.N. Protocol. Read [AGENTS.md](AGENTS.md) first; it holds the commands, task lanes, and rules.

Project state lives in `.eden/`:
- [.eden/ARCHITECTURE.md](.eden/ARCHITECTURE.md) - constraints, data flow, invariants
- [.eden/REGISTRY.md](.eden/REGISTRY.md) - existing modules and approved dependencies
- [.eden/PLAN.md](.eden/PLAN.md) - current objective and acceptance criteria
- [.eden/LEARNINGS.md](.eden/LEARNINGS.md) - verified pitfalls and fixes

Before finishing a code change, run `python3 scripts/eden-audit.py --verify`.
