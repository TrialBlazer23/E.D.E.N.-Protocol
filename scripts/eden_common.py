#!/usr/bin/env python3
"""Shared constants and helpers for the E.D.E.N. scripts (audit, index, hook, install).

One list of source extensions and ignored folders, so the audit never demands a
registration that the indexer cannot produce.
"""

from __future__ import annotations

import re
import sys
from pathlib import Path, PurePosixPath

# Source files the audit tracks and the indexer registers.
SOURCE_EXTENSIONS = frozenset({
    ".py", ".kt", ".kts", ".java", ".scala",
    ".js", ".jsx", ".mjs", ".cjs", ".ts", ".tsx", ".vue", ".svelte",
    ".go", ".rs", ".c", ".cpp", ".h", ".cs", ".swift", ".dart", ".rb", ".php",
    ".sh", ".ps1",
})

# Folders that never hold project modules (build output, vendored code, tooling state).
# Hidden folders (".anything") are skipped as well.
IGNORED_DIRS = frozenset({
    ".git", ".eden", ".venv", "venv", "env", "node_modules", "vendor",
    "build", "dist", "target", "out", "obj", "coverage", "__pycache__",
    ".gradle", ".idea", ".vscode", ".next", ".nuxt", ".svelte-kit", ".dart_tool",
    "Pods", "DerivedData", "docs", "third_party", "test", "androidTest", ".cxx", "schemas",
})

# Files that belong to E.D.E.N. itself, not to the project: never registered or audited.
EDEN_OWNED_FILES = frozenset({
    "init-eden.sh",
    "init-eden.ps1",
    "scripts/eden-audit.py",
    "scripts/eden-index.py",
    "scripts/eden-hook.py",
    "scripts/eden-install.py",
    "scripts/eden_common.py",
})
EDEN_OWNED_PREFIXES = ("templates/eden/", "templates/hooks/")

DEPENDENCY_FILES = frozenset({
    "requirements.txt", "pyproject.toml", "package.json", "Cargo.toml", "go.mod",
    "build.gradle", "build.gradle.kts", "libs.versions.toml", "pom.xml", "Gemfile",
    "composer.json", "pubspec.yaml", "Package.swift", "build.sbt",
})


def configure_stdio() -> None:
    """Safe output on Windows consoles (cp1252/ascii)."""
    for stream in (sys.stdout, sys.stderr):
        if hasattr(stream, "reconfigure"):
            try:
                stream.reconfigure(encoding="utf-8", errors="replace")
            except Exception:
                pass


def is_ignored_dir(name: str) -> bool:
    return name in IGNORED_DIRS or name.startswith(".")


def is_eden_owned(rel_path: str) -> bool:
    rel = rel_path.replace("\\", "/")
    return rel in EDEN_OWNED_FILES or rel.startswith(EDEN_OWNED_PREFIXES)


def is_source_file(rel_path: str, include_eden: bool = False) -> bool:
    """True for project source files the audit tracks and the indexer registers.

    E.D.E.N.'s own scripts are excluded unless include_eden (the protocol repo indexing itself).
    """
    rel = rel_path.replace("\\", "/")
    if is_eden_owned(rel) and not include_eden:
        return False
    path = PurePosixPath(rel)
    if any(is_ignored_dir(part) for part in path.parts[:-1]):
        return False
    return path.suffix in SOURCE_EXTENSIONS


def is_protocol_repo(root: Path) -> bool:
    """The E.D.E.N.-Protocol checkout itself (it registers its own scripts)."""
    return (root / "templates" / "eden").is_dir() and (root / "init-eden.sh").is_file()


def parse_porcelain_z(raw: bytes) -> dict[str, str]:
    """Parses `git status --porcelain=v1 -z` output into {path: status_letter}."""
    parts = raw.decode("utf-8", errors="replace").split("\0")
    changes: dict[str, str] = {}
    i = 0
    while i < len(parts):
        entry = parts[i]
        if len(entry) < 4:
            i += 1
            continue
        xy, path = entry[:2], entry[3:]
        if "R" in xy or "C" in xy:
            i += 1  # the next NUL-separated field is the original path
        if xy == "??":
            letter = "A"
        elif "D" in xy:
            letter = "D"
        else:
            letter = "M"
        changes[path.replace("\\", "/")] = letter
        i += 1
    return changes


PLACEHOLDER_RE = re.compile(r"<fill in[^>]*>")
