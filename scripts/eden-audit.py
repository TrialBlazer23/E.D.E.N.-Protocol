#!/usr/bin/env python3
"""
E.D.E.N. Protocol Compliance Auditor (Zero-Dependency)
Enforces the 'Normalize' phase by cross-referencing git status against:
1. .eden/REGISTRY.md (All source files must be indexed to prevent duplication)
2. .eden/CHANGELOG_AGENT.jsonl (Code mutations require an updated audit log)
3. Banned duplicate imports/patterns (Defined in .eden/REGISTRY.md)
"""

import json
import os
import re
import subprocess
import sys
from pathlib import Path

# Configuration: Adjust tracked extensions for Python, Kotlin, JS/TS, Rust, C/C++, etc.
CODE_EXTENSIONS = {".py", ".kt", ".kts", ".js", ".ts", ".tsx", ".sh", ".ps1", ".rs", ".c", ".cpp", ".go"}
IGNORED_DIRS = {".git", ".eden", ".venv", "venv", "node_modules", "build", "dist", "__pycache__", ".gradle", ".idea"}
EXEMPT_FILES = {"scripts/eden-audit.py", "init-eden.sh"}

REGISTRY_PATH = Path(".eden/REGISTRY.md")
CHANGELOG_PATH = Path(".eden/CHANGELOG_AGENT.jsonl")


def get_git_changes():
    """Returns a dict of modified/added/untracked file paths -> git status code."""
    try:
        res = subprocess.run(
            ["git", "status", "--porcelain"],
            capture_output=True,
            text=True,
            check=True
        )
    except (subprocess.CalledProcessError, FileNotFoundError):
        print("[EDEN-AUDIT] WARNING: Not a git repository or git not installed. Skipping git-diff checks.")
        return {}

    changes = {}
    for line in res.stdout.splitlines():
        if not line.strip():
            continue
        status = line[:2].strip()
        raw_path = line[3:].strip()
        # Handle git rename syntax: "old_path -> new_path"
        if " -> " in raw_path:
            raw_path = raw_path.split(" -> ", 1)[1]
        changes[raw_path.strip('"')] = status
    return changes


def is_tracked_code_file(filepath_str: str) -> bool:
    if filepath_str in EXEMPT_FILES:
        return False
    path = Path(filepath_str)
    if any(part in IGNORED_DIRS for part in path.parts):
        return False
    return path.suffix in CODE_EXTENSIONS


def parse_banned_imports(registry_text: str) -> list[str]:
    """Extracts banned packages wrapped in `BANNED: <pkg>` from REGISTRY.md."""
    return re.findall(r"BANNED:\s*`?([a-zA-Z0-9_\-\.]+)`?", registry_text)


def validate_changelog_tail() -> tuple[bool, str]:
    """Verifies the last line of CHANGELOG_AGENT.jsonl is valid JSON with required keys."""
    if not CHANGELOG_PATH.exists():
        return False, "Missing .eden/CHANGELOG_AGENT.jsonl file."
    lines = [line.strip() for line in CHANGELOG_PATH.read_text(encoding="utf-8").splitlines() if line.strip()]
    if not lines:
        return False, ".eden/CHANGELOG_AGENT.jsonl is completely empty."
    try:
        last_entry = json.loads(lines[-1])
        required = {"timestamp", "phase", "action", "files", "summary"}
        missing = required - set(last_entry.keys())
        if missing:
            return False, f"Last JSONL entry is missing required keys: {', '.join(sorted(missing))}"
        return True, "Valid"
    except json.JSONDecodeError as e:
        return False, f"Last line of .eden/CHANGELOG_AGENT.jsonl is invalid JSON: {e}"


def main() -> int:
    errors = []

    # 1. Verify .eden control plane exists
    if not REGISTRY_PATH.exists() or not CHANGELOG_PATH.exists():
        print("[EDEN-AUDIT] FATAL: .eden/ control plane missing. Run ./init-eden.sh first.")
        return 1

    registry_text = REGISTRY_PATH.read_text(encoding="utf-8")
    banned_packages = parse_banned_imports(registry_text)

    changes = get_git_changes()
    code_changes = [f for f, status in changes.items() if status != "D" and is_tracked_code_file(f)]

    # 2. Check every modified/new code file against REGISTRY.md and Banned Imports
    for code_file in code_changes:
        normalized_path = code_file.replace("\\", "/")
        if normalized_path not in registry_text:
            errors.append(
                f"UNREGISTERED FILE: `{normalized_path}` was created or modified, "
                f"but is not documented in `.eden/REGISTRY.md`."
            )

        # Scan file content for banned duplicate packages
        file_path = Path(code_file)
        if file_path.exists() and banned_packages:
            content = file_path.read_text(encoding="utf-8", errors="ignore")
            for pkg in banned_packages:
                pattern = rf"\b(import\s+{re.escape(pkg)}|from\s+{re.escape(pkg)}\s+import|require\(['\"]{re.escape(pkg)}['\"]\))"
                if re.search(pattern, content):
                    errors.append(
                        f"BANNED DEPENDENCY: `{normalized_path}` imports `{pkg}`, "
                        f"which is marked as BANNED in `.eden/REGISTRY.md`."
                    )

    # 3. Require CHANGELOG_AGENT.jsonl update whenever code files are mutated
    if code_changes:
        if ".eden/CHANGELOG_AGENT.jsonl" not in changes:
            errors.append(
                "MISSING AUDIT LOG: Code files were modified, but `.eden/CHANGELOG_AGENT.jsonl` "
                "was not updated. Append a single-line JSON summary of your changes."
            )
        else:
            valid_json, msg = validate_changelog_tail()
            if not valid_json:
                errors.append(f"MALFORMED AUDIT LOG: {msg}")

    # 4. Report Verdict
    if errors:
        print("=" * 72)
        print("❌ E.D.E.N. PROTOCOL AUDIT FAILED — NORMALIZE PHASE INCOMPLETE")
        print("=" * 72)
        for i, err in enumerate(errors, 1):
            print(f"  {i}. {err}")
        print("-" * 72)
        print("AGENT REMEDIATION REQUIRED:")
        print("  -> Register any new/modified modules in `.eden/REGISTRY.md`")
        print("  -> Append a valid JSON entry to `.eden/CHANGELOG_AGENT.jsonl`")
        print("  -> Record any non-obvious bugs/fixes in `.eden/LEARNINGS.md`")
        print("  -> Re-run: `python3 scripts/eden-audit.py`")
        print("=" * 72)
        return 1

    print("[EDEN-AUDIT] PASSED: Repository state and registry are synchronized.")
    return 0


if __name__ == "__main__":
    sys.exit(main())