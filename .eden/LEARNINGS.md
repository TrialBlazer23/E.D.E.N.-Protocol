# AGENT LEARNINGS & ENVIRONMENT QUIRKS
> **AGENT INSTRUCTION:** Read before executing. Append new entries when you resolve a non-obvious bug or environment constraint. Keep entries concise.

## Environment & Tooling Rules
- **Python Env:** Always use the local `.venv/bin/python` — system pip is externally managed.
- **Hardware Ceiling:** Target environment is constrained (4GB RAM / Mobile Edge). Avoid loading full datasets into memory; use generators/streams.

## Resolved Pitfalls (Do Not Repeat)
- **[2026-10-23] Port Binding:** Local orchestrator requires explicit check that port 8080 is listening before firing requests; use `src/utils/net.py:wait_for_port()`.
- **[2026-10-23] Windows output:** Console encoding may reject Unicode status markers; compliance tooling uses ASCII status output.