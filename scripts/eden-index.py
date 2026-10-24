#!/usr/bin/env python3
"""
E.D.E.N. Protocol Auto-Indexer (Zero-Dependency)
Scans an existing repository (Python, Kotlin, TS/JS, Rust, Go, C/C++, Bash)
and populates Section 2 of .eden/REGISTRY.md with exported classes, functions,
and inferred consumers so coding agents never duplicate existing components.
"""

import ast
import os
import re
import sys
from pathlib import Path

# ------------------------------------------------------------------------------
# Configuration & Filtering
# ------------------------------------------------------------------------------
CODE_EXTENSIONS = {".py", ".kt", ".kts", ".js", ".ts", ".tsx", ".sh", ".ps1", ".rs", ".go", ".c", ".cpp"}
DEPENDENCY_FILES = {
    "requirements.txt", "pyproject.toml", "package.json",
    "build.gradle", "build.gradle.kts", "libs.versions.toml", "Cargo.toml"
}
IGNORED_DIRS = {
    ".git", ".eden", ".venv", "venv", "env", "node_modules",
    "build", "dist", "target", "out", "__pycache__", ".gradle", ".idea", ".vscode"
}

MAX_SYMBOLS_PER_FILE = 8  # Caps table width so REGISTRY.md stays token-efficient


# ------------------------------------------------------------------------------
# Language-Specific Symbol & Doc Extractors
# ------------------------------------------------------------------------------
def clean_table_cell(text: str) -> str:
    """Sanitizes strings for safe Markdown table rendering."""
    if not text:
        return "—"
    cleaned = " ".join(text.strip().splitlines())
    cleaned = cleaned.replace("|", "\\|")
    return (cleaned[:85] + "...") if len(cleaned) > 88 else cleaned


def extract_python(content: str) -> tuple[list[str], str]:
    """Uses Python AST to extract top-level classes, functions, methods, and docstrings."""
    symbols = []
    doc_summary = ""
    try:
        tree = ast.parse(content)
        raw_doc = ast.get_docstring(tree)
        if raw_doc:
            doc_summary = raw_doc.strip().splitlines()[0]

        for node in tree.body:
            if isinstance(node, ast.ClassDef) and not node.name.startswith("_"):
                methods = [
                    n.name for n in node.body
                    if isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef))
                    and not n.name.startswith("_")
                ]
                if methods:
                    preview = ", ".join(methods[:3])
                    suffix = ", ..." if len(methods) > 3 else ""
                    symbols.append(f"`{node.name}` ({preview}{suffix})")
                else:
                    symbols.append(f"`{node.name}`")
            elif isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                if not node.name.startswith("_") or node.name == "main":
                    symbols.append(f"`{node.name}()`")
    except SyntaxError:
        return extract_generic_regex(content, ".py")

    return symbols, doc_summary


def extract_kotlin(content: str) -> tuple[list[str], str]:
    """Extracts Kotlin classes, objects, interfaces, and functions (including @Composable)."""
    symbols = []
    doc_summary = ""

    # Match top-level KDoc or header comment
    doc_match = re.search(r"/\*\*\s*(.*?)\s*\*/", content, re.DOTALL)
    if doc_match:
        lines = [line.lstrip(" *").strip() for line in doc_match.group(1).splitlines() if line.lstrip(" *").strip()]
        if lines:
            doc_summary = lines[0]

    # Classes, Objects, Interfaces, Enums
    type_pattern = re.compile(
        r"^\s*(?:(?:public|internal|open|abstract|sealed|data|value|enum|annotation)\s+)*"
        r"(class|interface|object)\s+([A-Za-z0-9_]+)",
        re.MULTILINE
    )
    for kind, name in type_pattern.findall(content):
        prefix = "obj " if kind == "object" else ""
        symbols.append(f"`{prefix}{name}`")

    # Top-level or key functions (including @Composable)
    fun_pattern = re.compile(
        r"(?:(@Composable)\s+)?^\s*(?:(?:public|internal|override|suspend|inline)\s+)*"
        r"fun\s+(?:<[^>]+>\s+)?(?:[A-Za-z0-9_<>?]+\.)?([A-Za-z0-9_]+)\s*\(",
        re.MULTILINE
    )
    for is_composable, name in fun_pattern.findall(content):
        tag = f"`@{name}()`" if is_composable else f"`{name}()`"
        if tag not in symbols:
            symbols.append(tag)

    return symbols, doc_summary


def extract_ts_js(content: str) -> tuple[list[str], str]:
    """Extracts exported classes, functions, types, and components from JS/TS/TSX."""
    symbols = []
    doc_summary = ""

    for match in re.finditer(
        r"export\s+(?:default\s+)?(?:async\s+)?(class|function|const|let|interface|type)\s+([A-Za-z0-9_]+)",
        content
    ):
        kind, name = match.groups()
        suffix = "()" if kind == "function" else ""
        symbols.append(f"`{name}{suffix}`")

    return symbols, doc_summary


def extract_generic_regex(content: str, suffix: str) -> tuple[list[str], str]:
    """Fallback extractor for Bash, Rust, Go, and C/C++."""
    symbols = []
    doc_summary = ""

    # Grab first meaningful top comment line
    for line in content.splitlines()[:10]:
        stripped = line.strip()
        if stripped.startswith(("#", "//")) and not stripped.startswith("#!"):
            cleaned = stripped.lstrip("#/ ").strip()
            if len(cleaned) > 5 and not set(cleaned) <= {"=", "-", "*"}:
                doc_summary = cleaned
                break

    if suffix == ".sh":
        for m in re.finditer(r"^\s*(?:function\s+)?([a-zA-Z0-9_\-]+)\s*\(\)\s*\{", content, re.MULTILINE):
            symbols.append(f"`{m.group(1)}()`")
    elif suffix == ".rs":
        for m in re.finditer(r"^\s*pub\s+(?:async\s+)?(fn|struct|enum|trait)\s+([A-Za-z0-9_]+)", content, re.MULTILINE):
            suffix_str = "()" if m.group(1) == "fn" else ""
            symbols.append(f"`{m.group(2)}{suffix_str}`")
    elif suffix == ".go":
        for m in re.finditer(r"^\s*(?:func|type)\s+(?:\([^)]+\)\s+)?([A-Z][A-Za-z0-9_]*)", content, re.MULTILINE):
            symbols.append(f"`{m.group(1)}`")

    return symbols, doc_summary


def infer_responsibility(rel_path: str, doc_summary: str) -> str:
    """Falls back to heuristic naming if a file lacks a module docstring."""
    if doc_summary:
        return doc_summary
    stem = Path(rel_path).stem.lower()
    heuristics = {
        "main": "Application entrypoint",
        "cli": "CLI command router and argument parser",
        "config": "Configuration & environment management",
        "orchestrator": "Core execution & agent orchestration loop",
        "server": "Local server & request handler",
        "client": "API / network client wrapper",
        "db": "Local database & persistence layer",
        "models": "Data structures and domain models",
        "utils": "Shared helper utilities",
        "viewmodel": "UI state holder and business logic",
        "repository": "Data source coordination layer",
    }
    for key, desc in heuristics.items():
        if key in stem:
            return desc
    return f"Module `{Path(rel_path).name}`"


# ------------------------------------------------------------------------------
# Repository Scanner & Cross-Reference Engine
# ------------------------------------------------------------------------------
def scan_codebase(root: Path):
    code_files = []
    dep_manifests = []

    for dirpath, dirnames, filenames in os.walk(root):
        # Prune ignored directories in-place for low-memory traversal
        dirnames[:] = [d for d in dirnames if d not in IGNORED_DIRS and not d.startswith(".Eden")]

        for fname in sorted(filenames):
            fpath = Path(dirpath) / fname
            rel_path = fpath.relative_to(root).as_posix()

            if fname in DEPENDENCY_FILES:
                dep_manifests.append(rel_path)

            if fpath.suffix in CODE_EXTENSIONS:
                code_files.append((rel_path, fpath))

    return code_files, dep_manifests


def build_module_rows(code_files: list[tuple[str, Path]]) -> list[str]:
    """Parses all files and cross-references stems to infer 'Consumers'."""
    parsed_records = []
    file_contents_cache = {}

    for rel_path, fpath in code_files:
        try:
            content = fpath.read_text(encoding="utf-8", errors="ignore")
        except OSError:
            continue

        file_contents_cache[rel_path] = content
        ext = fpath.suffix

        if ext == ".py":
            symbols, doc = extract_python(content)
        elif ext in {".kt", ".kts"}:
            symbols, doc = extract_kotlin(content)
        elif ext in {".js", ".ts", ".tsx"}:
            symbols, doc = extract_ts_js(content)
        else:
            symbols, doc = extract_generic_regex(content, ext)

        if len(symbols) > MAX_SYMBOLS_PER_FILE:
            shown = symbols[:MAX_SYMBOLS_PER_FILE]
            symbol_str = ", ".join(shown) + f" *(+{len(symbols) - MAX_SYMBOLS_PER_FILE} more)*"
        elif symbols:
            symbol_str = ", ".join(symbols)
        else:
            symbol_str = "*(script / definitions)*"

        responsibility = infer_responsibility(rel_path, doc)
        parsed_records.append((rel_path, symbol_str, responsibility))

    # Cross-reference module names across files to populate 'Consumers'
    rows = []
    for rel_path, symbol_str, responsibility in parsed_records:
        stem = Path(rel_path).stem
        consumers = []
        if stem not in {"__init__", "index", "main", "MainActivity"} and len(stem) > 3:
            pattern = re.compile(rf"\b{re.escape(stem)}\b")
            for other_path, other_content in file_contents_cache.items():
                if other_path != rel_path and pattern.search(other_content):
                    consumers.append(f"`{Path(other_path).name}`")

        if consumers:
            consumer_str = ", ".join(consumers[:3]) + ("..." if len(consumers) > 3 else "")
        else:
            consumer_str = "Entrypoint / Unreferenced"

        rows.append(
            f"| `{rel_path}` | {clean_table_cell(symbol_str)} | "
            f"{clean_table_cell(responsibility)} | {clean_table_cell(consumer_str)} |"
        )

    return rows


# ------------------------------------------------------------------------------
# Non-Destructive REGISTRY.md Updater
# ------------------------------------------------------------------------------
def update_registry_file(module_rows: list[str], dep_manifests: list[str], registry_path: Path):
    registry_path.parent.mkdir(parents=True, exist_ok=True)

    section_2_header = "## 2. Internal Modules & Source Files (Reuse Mandatory)"
    table_header = (
        "| File Path | Exported Symbols / Key API | Responsibility | Consumers |\n"
        "| :--- | :--- | :--- | :--- |"
    )
    new_section_2_body = f"{section_2_header}\n{table_header}\n" + "\n".join(module_rows) + "\n"

    if not registry_path.exists():
        # Create fresh REGISTRY.md if none exists
        manifests_note = ", ".join(f"`{m}`" for m in dep_manifests) if dep_manifests else "None detected"
        content = f"""# COMPONENT & DEPENDENCY REGISTRY
> **AGENT RULE:** Check this registry BEFORE writing any new helper or installing any package.
> To ban a duplicate library, list `BANNED: package_name` in the Notes column (enforced by `eden-audit.py`).

## 1. External Dependencies
*Detected Manifests: {manifests_note}*

| Package | Purpose | Constraint / Notes |
| :--- | :--- | :--- |
| `standard-library` | Default runtime primitives | Always prefer stdlib first |

{new_section_2_body}
## 3. Configuration & State Schemas
| Path | Type | Description |
| :--- | :--- | :--- |
| `.eden/CHANGELOG_AGENT.jsonl` | JSONL | Append-only agent mutation history |
| `.eden/LEARNINGS.md` | Markdown | Persistent environment & debugging memory |
"""
        registry_path.write_text(content, encoding="utf-8")
        return

    # If REGISTRY.md exists, surgically replace ONLY Section 2 so manual notes & BANNED rules survive
    existing = registry_path.read_text(encoding="utf-8")
    pattern = re.compile(
        r"(## 2\. Internal Modules & Source Files.*?)(\n## 3\.|\Z)",
        re.DOTALL
    )
    if pattern.search(existing):
        updated = pattern.sub(lambda m: f"{new_section_2_body.rstrip()}\n{m.group(2)}", existing)
        registry_path.write_text(updated, encoding="utf-8")
    else:
        registry_path.write_text(existing.rstrip() + "\n\n" + new_section_2_body, encoding="utf-8")


def main() -> int:
    root = Path(sys.argv[1]).resolve() if len(sys.argv) > 1 else Path.cwd()
    registry_path = root / ".eden" / "REGISTRY.md"
    print(f"[EDEN-INDEX] Scanning codebase at: {root}")

    code_files, dep_manifests = scan_codebase(root)
    if not code_files:
        print("[EDEN-INDEX] No matching source files found.")
        return 0

    rows = build_module_rows(code_files)
    update_registry_file(rows, dep_manifests, registry_path)

    print(f"[EDEN-INDEX] Indexed {len(rows)} source files into {registry_path}")
    if dep_manifests:
        print(f"[EDEN-INDEX] Detected dependency manifests: {', '.join(dep_manifests)}")
    return 0


if __name__ == "__main__":
    sys.exit(main())