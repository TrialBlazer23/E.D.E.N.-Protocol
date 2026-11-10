---
name: eden-adopt
description: Finish adopting the E.D.E.N. Protocol in an existing project after init-eden --adopt - review the merged EDEN blocks, fill in Commands and .eden/ARCHITECTURE.md from the real code, trim the generated registry, and move live TODOs into PLAN.md. Use when .eden/PLAN.md has an adoption task or eden-audit.py --doctor reports placeholders.
---

# E.D.E.N. Adopt (first pass on an existing project)

## Steps
1. Run `python3 scripts/eden-audit.py --doctor` and work through its Unfinished list.
2. AGENTS.md, CLAUDE.md, GEMINI.md, and `.github/copilot-instructions.md` may contain an `<!-- EDEN:BEGIN v1 -->` ... `<!-- EDEN:END -->` block. Edit only inside the block for E.D.E.N. rules; leave the project's own text outside it alone. If the project text contradicts the block, ask the human which wins.
3. Commands: check the detected Setup/Build/Test/Lint lines against package.json, pyproject.toml, Cargo.toml, go.mod, Gradle, or the Makefile, and actually run them. Fix anything wrong. Keep `.eden/verify` running the same Lint and Test commands.
4. `.eden/ARCHITECTURE.md`: replace every `<fill in>` with facts you verified in the code (languages, runtime, data flow, invariants). Write "unknown - ask" rather than guessing.
5. `.eden/REGISTRY.md`: keep rows for real modules; correct any Responsibility text that is wrong. Add approved packages to section 1.
6. Move live work from TODO.md / NEXT-STEPS.md (if any) into `.eden/PLAN.md` Backlog with acceptance criteria. Do not delete the old files without asking.
7. Append one changelog line for the adoption, run `python3 scripts/eden-audit.py --verify`, and report what still needs a human decision.
