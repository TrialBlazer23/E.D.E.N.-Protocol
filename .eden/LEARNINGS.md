# LEARNINGS

Verified root causes of non-obvious problems in this project. Add an entry only after you have confirmed the cause and the fix.

<!--
Format (one line per entry):
- [YYYY-MM-DD] Subsystem: Symptom -> Root cause -> Fix / rule
-->

## Entries
- [2026-10-23] Windows output: console rejects Unicode status markers -> cp1252 console encoding -> tools print ASCII status lines and reconfigure stdout with errors="replace".
- [2026-10-30] PowerShell: pointer files began with a BOM and garbled em-dashes -> `Set-Content -Encoding utf8` on 5.1 writes a BOM, and 5.1 reads a BOM-less UTF-8 .ps1 as ANSI -> keep `init-eden.ps1` ASCII-only and copy files byte-for-byte; write generated files with UTF8Encoding($false).
- [2026-10-30] Audit: files inside a new folder were not seen -> `git status --porcelain` collapses untracked dirs to `?? dir/` -> use `--untracked-files=all`.
- [2026-10-30] Audit: CI always passed -> a clean checkout has no working-tree changes -> CI must use `--base <ref>` with full history (`fetch-depth: 0`).
- [2026-11-10] AGENTS.md Commands: filling this repo's `<fill in>` placeholders with protocol-specific commands would ship those values to every `--new` install and stop `--detect` from replacing them -> `AGENTS.md` is copied or merged as the template and `fill_commands` only matches `<fill in...>` -> keep the placeholders here; document this repo's commands in CONTRIBUTING.md and the README.
