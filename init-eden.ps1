#!/usr/bin/env pwsh
param(
    [string]$ProjectName = (Split-Path -Leaf (Get-Location))
)

$ErrorActionPreference = "Stop"
Write-Host "Initializing E.D.E.N. Protocol scaffold for: $ProjectName"
New-Item -ItemType Directory -Force -Path ".eden", "scripts" | Out-Null

if (-not (Test-Path "AGENTS.md")) {
    @"
# E.D.E.N. PROTOCOL: AGENT OPERATING SYSTEM

Read `.eden/ARCHITECTURE.md`, `.eden/REGISTRY.md`, `.eden/LEARNINGS.md`, and
the recent `.eden/CHANGELOG_AGENT.jsonl` entries before changing code.

Before implementation, inspect `.eden/PLAN.md`, search the registry for
existing components, and state the files and modules that will be changed or
reused. After implementation, update the registry, append a valid changelog
entry, record non-obvious learnings, and run the compliance audit.
"@ | Set-Content -Encoding utf8 "AGENTS.md"
}

if (-not (Test-Path ".eden\ARCHITECTURE.md")) {
    @"
# SYSTEM ARCHITECTURE & CONSTRAINTS

Define project-specific runtime, dependency, performance, network, persistence,
and data-flow constraints here. Do not assume an operating system or shell.
"@ | Set-Content -Encoding utf8 ".eden\ARCHITECTURE.md"
}

if (-not (Test-Path ".eden\PLAN.md")) {
    @"
# ACTIVE EXECUTION PLAN

## Current objective
- [ ] Define project architecture and register project modules.

## Backlog
- [ ] Add project-specific milestones.

## Completed
- [x] Initialized the E.D.E.N. control plane.
"@ | Set-Content -Encoding utf8 ".eden\PLAN.md"
}

if (-not (Test-Path ".eden\REGISTRY.md")) {
    @"
# COMPONENT & DEPENDENCY REGISTRY
> Search this file before creating helpers or adding dependencies.

## 1. Approved External Dependencies
| Package | Purpose | Constraint |
| :--- | :--- | :--- |
| `standard-library` | Default runtime primitives | Prefer before adding dependencies |

## 2. Internal Modules & Source Files (Reuse Mandatory)
| File Path | Exported Symbols / Key API | Responsibility | Consumers |
| :--- | :--- | :--- | :--- |

## 3. Data Schemas & State Files
| Path | Format | Description |
| :--- | :--- | :--- |
| `.eden/CHANGELOG_AGENT.jsonl` | JSONL | Append-only agent mutation history |
| `.eden/ARCHITECTURE.md` | Markdown | Project constraints and data flow |
| `.eden/PLAN.md` | Markdown | Active task scope and milestones |
| `.eden/LEARNINGS.md` | Markdown | Persistent project and runtime learnings |
"@ | Set-Content -Encoding utf8 ".eden\REGISTRY.md"
}

if (-not (Test-Path ".eden\LEARNINGS.md")) {
    @"
# AGENT LEARNINGS & ENVIRONMENT QUIRKS

Record concise root-cause notes for non-obvious project, dependency, or
runtime issues. Do not encode assumptions that are not true for this project.
"@ | Set-Content -Encoding utf8 ".eden\LEARNINGS.md"
}

if (-not (Test-Path ".eden\CHANGELOG_AGENT.jsonl") -or (Get-Item ".eden\CHANGELOG_AGENT.jsonl").Length -eq 0) {
    '{"timestamp":"' + (Get-Date).ToUniversalTime().ToString("yyyy-MM-ddTHH:mm:ssZ") + '","phase":"Normalize","task_id":"TASK-00","action":"CREATED","files":["AGENTS.md",".eden/ARCHITECTURE.md",".eden/PLAN.md",".eden/LEARNINGS.md"],"reused_modules":[],"summary":"Initialized the E.D.E.N. control plane."}' | Set-Content -Encoding utf8 ".eden\CHANGELOG_AGENT.jsonl"
}

if (Test-Path "scripts\eden-index.py") {
    python scripts\eden-index.py (Get-Location).Path
}

Write-Host "E.D.E.N. scaffold ready. Run: python scripts/eden-audit.py"
