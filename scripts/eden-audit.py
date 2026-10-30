#!/usr/bin/env python3
"""
E.D.E.N. Protocol Compliance Auditor (Zero-Dependency)

Checks the changed source files of a repository against the .eden/ control plane:
1. Every changed source file is registered in a .eden/REGISTRY.md table row (exact path).
2. .eden/CHANGELOG_AGENT.jsonl gained new, valid entries whose "files" cover every
   changed source file. Existing lines must not be edited (append-only).
3. Changed files do not import packages marked `BANNED:` in the registry.
4. Optionally (--verify or EDEN_VERIFY=1) runs .eden/verify or .eden/verify.py.

Modes:
  (default)      working tree vs HEAD, including untracked files in new directories
  --staged       index vs HEAD (used by the pre-commit hook)
  --base REF     REF...HEAD (used by CI on a clean checkout)
"""

from __future__ import annotations

import argparse
import json
import os
import re
import subprocess
import sys
from pathlib import Path

# Safe output for Windows consoles (cp1252/ascii). Status markers are ASCII anyway.
if hasattr(sys.stdout, "reconfigure"):
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
        sys.stderr.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass

CODE_EXTENSIONS = {
    ".py", ".kt", ".kts", ".java", ".js", ".ts", ".tsx",
    ".sh", ".ps1", ".rs", ".c", ".cpp", ".h", ".go"
}
IGNORED_DIRS = {
    ".git", ".eden", ".venv", "venv", "node_modules",
    "build", "dist", "__pycache__", ".gradle", ".idea", "docs",
    "third_party", "test", "androidTest", ".cxx", "schemas"
}
EXEMPT_FILES = {
    "scripts/eden-audit.py",
    "scripts/eden-index.py",
    "init-eden.sh",
    "init-eden.ps1",
}
REGISTRY_REL = ".eden/REGISTRY.md"
CHANGELOG_REL = ".eden/CHANGELOG_AGENT.jsonl"
REQUIRED_KEYS = {"timestamp", "phase", "action", "files", "summary"}
MAX_REPORTED_ROUNDS = 3


# ------------------------------------------------------------------------------
# Repository access
# ------------------------------------------------------------------------------
def find_repo_root(explicit: str | None = None) -> Path:
    """--root, then the repo containing this script, then the git toplevel of CWD, then CWD."""
    if explicit:
        return Path(explicit).resolve()
    script_root = Path(__file__).resolve().parent.parent
    if (script_root / ".eden").is_dir():
        return script_root
    cwd = Path.cwd()
    try:
        top = subprocess.run(["git", "rev-parse", "--show-toplevel"], cwd=cwd,
                             capture_output=True, text=True, check=True).stdout.strip()
        if top and (Path(top) / ".eden").is_dir():
            return Path(top)
    except (subprocess.CalledProcessError, FileNotFoundError):
        pass
    return cwd


def git(root: Path, *args: str, check: bool = True) -> subprocess.CompletedProcess:
    return subprocess.run(["git", "-C", str(root), *args], capture_output=True, check=check)


def is_git_repo(root: Path) -> bool:
    try:
        return git(root, "rev-parse", "--git-dir", check=False).returncode == 0
    except FileNotFoundError:
        return False


def has_head(root: Path) -> bool:
    return git(root, "rev-parse", "--verify", "-q", "HEAD", check=False).returncode == 0


def git_show(root: Path, spec: str) -> str | None:
    """Returns file content for a git object spec like HEAD:path or :path, or None if absent."""
    res = git(root, "show", spec, check=False)
    if res.returncode != 0:
        return None
    return res.stdout.decode("utf-8", errors="replace")


def parse_name_status_z(raw: bytes) -> dict[str, str]:
    """Parses `git diff --name-status -z` output into {path: status_letter}."""
    parts = raw.decode("utf-8", errors="replace").split("\0")
    changes: dict[str, str] = {}
    i = 0
    while i < len(parts):
        status = parts[i]
        if not status:
            i += 1
            continue
        letter = status[0]
        if letter in ("R", "C"):
            # status, old path, new path
            if i + 2 < len(parts):
                changes[parts[i + 2]] = "A"
            i += 3
        else:
            if i + 1 < len(parts):
                changes[parts[i + 1]] = letter
            i += 2
    return changes


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
        changes[path] = letter
        i += 1
    return changes


class Snapshot:
    """The set of changed paths plus how to read 'after' and 'before' content for the mode."""

    def __init__(self, root: Path, mode: str, base: str | None = None):
        self.root = root
        self.mode = mode
        self.base = base
        self.changes: dict[str, str] = {}
        self.before_ref: str | None = None  # None means "empty" (no commits yet)

        if mode == "staged":
            if has_head(root):
                self.before_ref = "HEAD"
                res = git(root, "diff", "--cached", "--name-status", "-z", "-M")
                self.changes = parse_name_status_z(res.stdout)
            else:
                # First commit: everything in the index is new.
                res = git(root, "ls-files", "-z", "--cached")
                self.changes = {p: "A" for p in res.stdout.decode("utf-8", errors="replace").split("\0") if p}
        elif mode == "base":
            mb = git(root, "merge-base", base, "HEAD", check=False)
            if mb.returncode != 0:
                raise SystemExit(f"[EDEN-AUDIT] FATAL: cannot find merge-base of '{base}' and HEAD. "
                                 f"Fetch it first (e.g. actions/checkout with fetch-depth: 0).")
            self.before_ref = mb.stdout.decode().strip()
            res = git(root, "diff", "--name-status", "-z", "-M", f"{self.before_ref}..HEAD")
            self.changes = parse_name_status_z(res.stdout)
        else:
            self.before_ref = "HEAD" if has_head(root) else None
            res = git(root, "status", "--porcelain=v1", "-z", "--untracked-files=all")
            self.changes = parse_porcelain_z(res.stdout)

        self.changes = {p.replace("\\", "/"): s for p, s in self.changes.items()}

    def after(self, rel: str) -> str | None:
        if self.mode == "staged":
            return git_show(self.root, f":{rel}")
        if self.mode == "base":
            return git_show(self.root, f"HEAD:{rel}")
        path = self.root / rel
        if not path.is_file():
            return None
        return path.read_text(encoding="utf-8", errors="replace")

    def before(self, rel: str) -> str | None:
        if self.before_ref is None:
            return None
        return git_show(self.root, f"{self.before_ref}:{rel}")


class WorkingTreeOnly:
    """Fallback when git is unavailable: nothing is 'changed', but files are readable."""

    def __init__(self, root: Path):
        self.root = root
        self.changes: dict[str, str] = {}

    def after(self, rel: str) -> str | None:
        path = self.root / rel
        return path.read_text(encoding="utf-8", errors="replace") if path.is_file() else None

    def before(self, rel: str) -> str | None:
        return None


# ------------------------------------------------------------------------------
# Rules
# ------------------------------------------------------------------------------
def is_tracked_code_file(filepath_str: str) -> bool:
    if filepath_str in EXEMPT_FILES:
        return False
    path = Path(filepath_str)
    if any(part in IGNORED_DIRS for part in path.parts):
        return False
    return path.suffix in CODE_EXTENSIONS


def strip_non_content(markdown: str) -> str:
    """Removes HTML comments and fenced code blocks so they cannot fake registration."""
    text = re.sub(r"<!--.*?-->", "", markdown, flags=re.DOTALL)
    text = re.sub(r"^\s*(```|~~~).*?^\s*\1[^\n]*$", "", text, flags=re.DOTALL | re.MULTILINE)
    return text


def parse_registered_paths(registry_text: str) -> set[str]:
    """Returns the exact paths in the first cell of every Markdown table row."""
    paths = set()
    for line in strip_non_content(registry_text).splitlines():
        line = line.strip()
        if not line.startswith("|"):
            continue
        cells = [c.strip() for c in line.strip("|").split("|")]
        if not cells:
            continue
        first = cells[0].strip().strip("`").strip().replace("\\", "/")
        if first.startswith("./"):
            first = first[2:]
        if not first or set(first) <= set(":- "):
            continue
        paths.add(first)
    return paths


def parse_banned_imports(registry_text: str) -> list[str]:
    """Extracts banned packages written as BANNED: <pkg> in REGISTRY.md (comments ignored)."""
    return re.findall(r"BANNED:\s*`?([a-zA-Z0-9_\-\.]+)`?", strip_non_content(registry_text))


def normalize_path(path: str) -> str:
    path = path.strip().replace("\\", "/")
    return path[2:] if path.startswith("./") else path


def jsonl_lines(text: str | None) -> list[str]:
    if not text:
        return []
    return [line.strip() for line in text.splitlines() if line.strip()]


def check_changelog(before_text: str | None, after_text: str | None,
                    code_changes: list[str]) -> list[str]:
    """Changelog must be append-only and its new entries must list every changed source file."""
    errors = []
    old, new = jsonl_lines(before_text), jsonl_lines(after_text)
    if after_text is None:
        return [f"MISSING AUDIT LOG: `{CHANGELOG_REL}` does not exist."]
    if new[:len(old)] != old:
        errors.append(f"CHANGELOG REWRITTEN: existing lines in `{CHANGELOG_REL}` were edited or removed. "
                      "The log is append-only; restore them and append a new line instead.")
        return errors
    added = new[len(old):]
    if not added:
        return [f"MISSING AUDIT LOG: source files changed but no new line was appended to `{CHANGELOG_REL}` "
                f"(editing other .eden/ files does not count)."]

    covered: set[str] = set()
    for n, line in enumerate(added, len(old) + 1):
        try:
            entry = json.loads(line)
        except json.JSONDecodeError as e:
            errors.append(f"MALFORMED AUDIT LOG: line {n} of `{CHANGELOG_REL}` is not valid JSON ({e}).")
            continue
        if not isinstance(entry, dict):
            errors.append(f"MALFORMED AUDIT LOG: line {n} of `{CHANGELOG_REL}` is not a JSON object.")
            continue
        missing = REQUIRED_KEYS - set(entry)
        if missing:
            errors.append(f"MALFORMED AUDIT LOG: line {n} is missing keys: {', '.join(sorted(missing))}.")
        files = entry.get("files", [])
        if not isinstance(files, list):
            errors.append(f"MALFORMED AUDIT LOG: line {n} `files` must be a list of paths.")
            continue
        covered.update(normalize_path(str(f)) for f in files)

    uncovered = [f for f in code_changes if f not in covered]
    if uncovered and not errors:
        errors.append("INCOMPLETE AUDIT LOG: the new changelog entries do not list these changed files in "
                      "`files`: " + ", ".join(f"`{f}`" for f in uncovered))
    return errors


def find_verify(root: Path) -> list[str] | None:
    py = root / ".eden" / "verify.py"
    sh = root / ".eden" / "verify"
    if py.is_file():
        return [sys.executable, str(py)]
    if sh.is_file():
        if os.name != "nt" and os.access(sh, os.X_OK):
            return [str(sh)]
        return ["sh", str(sh)]
    return None


def run_verify(root: Path) -> tuple[bool, str]:
    cmd = find_verify(root)
    if cmd is None:
        return True, ("[EDEN-AUDIT] NOTE: no .eden/verify or .eden/verify.py found; "
                      "run the Test/Lint commands from AGENTS.md yourself.")
    print(f"[EDEN-AUDIT] Running verify: {' '.join(cmd)}")
    sys.stdout.flush()
    try:
        res = subprocess.run(cmd, cwd=root)
    except FileNotFoundError as e:
        return False, f"VERIFY FAILED: could not start {cmd[0]} ({e})."
    if res.returncode != 0:
        return False, f"VERIFY FAILED: `{' '.join(cmd)}` exited with code {res.returncode}."
    return True, "[EDEN-AUDIT] Verify passed."


# ------------------------------------------------------------------------------
# Entry point
# ------------------------------------------------------------------------------
def parse_args(argv: list[str]) -> argparse.Namespace:
    p = argparse.ArgumentParser(description="E.D.E.N. Protocol compliance auditor")
    mode = p.add_mutually_exclusive_group()
    mode.add_argument("--staged", action="store_true", help="audit only staged changes (pre-commit hook)")
    mode.add_argument("--base", metavar="REF", help="audit REF...HEAD (CI on a clean checkout)")
    p.add_argument("--verify", action="store_true",
                   help="also run .eden/verify or .eden/verify.py (same as EDEN_VERIFY=1)")
    p.add_argument("--root", help="repository root (default: auto-detect)")
    return p.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(sys.argv[1:] if argv is None else argv)
    root = find_repo_root(args.root)
    errors: list[str] = []

    if not (root / REGISTRY_REL).exists() or not (root / CHANGELOG_REL).exists():
        print(f"[EDEN-AUDIT] FATAL: .eden/ control plane missing at {root}. Run init-eden first.")
        return 1

    if is_git_repo(root):
        mode = "staged" if args.staged else ("base" if args.base else "worktree")
        snap = Snapshot(root, mode, args.base)
    else:
        if args.staged or args.base:
            print("[EDEN-AUDIT] FATAL: --staged/--base require a git repository.")
            return 1
        print("[EDEN-AUDIT] WARNING: not a git repository (or git missing); skipping change checks.")
        mode, snap = "no-git", WorkingTreeOnly(root)

    registry_text = snap.after(REGISTRY_REL) or ""
    registered = parse_registered_paths(registry_text)
    banned = parse_banned_imports(registry_text)

    code_changes = sorted(f for f, s in snap.changes.items() if s != "D" and is_tracked_code_file(f))

    for code_file in code_changes:
        if code_file not in registered:
            errors.append(f"UNREGISTERED FILE: `{code_file}` was created or modified but has no row in "
                          f"`{REGISTRY_REL}` (its path must be the first cell of a table row).")
        if banned:
            content = snap.after(code_file) or ""
            for pkg in banned:
                pattern = (rf"\b(import\s+{re.escape(pkg)}\b|from\s+{re.escape(pkg)}\s+import"
                           rf"|require\(['\"]{re.escape(pkg)}['\"]\))")
                if re.search(pattern, content):
                    errors.append(f"BANNED DEPENDENCY: `{code_file}` imports `{pkg}`, which is marked "
                                  f"BANNED in `{REGISTRY_REL}`.")

    if code_changes:
        errors.extend(check_changelog(snap.before(CHANGELOG_REL), snap.after(CHANGELOG_REL), code_changes))

    verify_requested = args.verify or os.environ.get("EDEN_VERIFY") == "1"
    if verify_requested:
        ok, msg = run_verify(root)
        if ok:
            print(msg)
        else:
            errors.append(msg)

    scope = {"staged": "staged changes", "base": f"{args.base}...HEAD", "worktree": "working tree",
             "no-git": "no git"}[mode]
    if errors:
        print("=" * 72)
        print(f"[EDEN-AUDIT] FAILED ({scope}): Normalize phase incomplete")
        print("=" * 72)
        for i, err in enumerate(errors, 1):
            print(f"  {i}. {err}")
        print("-" * 72)
        print("REMEDIATION:")
        print(f"  -> Register changed source files in `{REGISTRY_REL}` (python3 scripts/eden-index.py .)")
        print(f"  -> Append one JSON line to `{CHANGELOG_REL}` listing every changed source file in `files`")
        print("  -> Fix failing tests / .eden/verify")
        print("  -> Re-run the audit. After " + str(MAX_REPORTED_ROUNDS) +
              " failed fix rounds, stop and report to a human.")
        if mode == "staged":
            print("  -> Remember to `git add` the .eden/ updates; this mode only sees staged content.")
        print("=" * 72)
        return 1

    print(f"[EDEN-AUDIT] PASSED ({scope}): {len(code_changes)} changed source file(s) registered and logged.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
