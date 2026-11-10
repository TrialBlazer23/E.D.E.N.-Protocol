#!/usr/bin/env python3
"""
E.D.E.N. Protocol installer (zero-dependency). Called by init-eden.sh and init-eden.ps1;
it can also be run directly:

  python3 scripts/eden-install.py --target DIR [--new | --adopt] [--tools LIST] [--legacy]
                                  [--force] [--detect | --no-detect] [--reindex] [--name NAME]

Modes:
  new    write the full AGENTS.md and pointer files (empty repository or no commits yet)
  adopt  existing project: merge an <!-- EDEN:BEGIN v1 --> ... <!-- EDEN:END --> block into
         existing AGENTS.md, CLAUDE.md, GEMINI.md, and .github/copilot-instructions.md, leave
         everything outside the markers alone, and detect the project's commands
  (default: new when the target has no commits and no source files, otherwise adopt)

Re-running is safe: up-to-date files are left alone, the EDEN block is updated in place,
hook configs gain the E.D.E.N. stop hook only once, and .eden/ state is never replaced.
--force replaces E.D.E.N.-managed files wholesale, keeping <file>.eden-bak backups.
"""

from __future__ import annotations

import argparse
import json
import os
import re
import shutil
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from eden_common import configure_stdio, is_ignored_dir, is_source_file  # noqa: E402

configure_stdio()

ALL_TOOLS = ("antigravity", "cursor", "grok", "vscode", "claude")
DEFAULT_TOOLS = ("antigravity", "cursor", "grok", "vscode")
SCRIPTS = ["scripts/eden-audit.py", "scripts/eden-index.py", "scripts/eden-hook.py",
           "scripts/eden_common.py"]
SKILLS = [".agents/skills/eden-normalize/SKILL.md", ".agents/skills/eden-architect/SKILL.md",
          ".agents/skills/eden-adopt/SKILL.md"]
MARKER_FILES = ["AGENTS.md", "CLAUDE.md", "GEMINI.md", ".github/copilot-instructions.md"]
HOOK_MANAGERS = [".husky", "lefthook.yml", "lefthook.yaml", ".lefthook.yml", ".pre-commit-config.yaml"]

BEGIN = "<!-- EDEN:BEGIN v1 -->"
END = "<!-- EDEN:END -->"
BLOCK_RE = re.compile(r"<!-- EDEN:BEGIN[^>]*-->.*?<!-- EDEN:END -->", re.DOTALL)
COMMAND_KEYS = ("setup", "build", "test", "lint")


# ------------------------------------------------------------------------------
# Selection
# ------------------------------------------------------------------------------
def files_for_tools(tools: set[str], legacy: bool) -> tuple[list[str], list[str]]:
    """Returns (instruction files, stop-hook configs) for the selected tools."""
    files = ["AGENTS.md"]
    if "antigravity" in tools:
        files.append("GEMINI.md")
    if "cursor" in tools:
        files.append(".cursor/rules/eden.mdc")
    if "vscode" in tools:
        files.append(".github/copilot-instructions.md")
    if "claude" in tools:
        files.append("CLAUDE.md")
    if legacy:
        files += [".cursorrules", ".windsurfrules"]
    hooks = []
    if tools & {"cursor", "grok"}:
        hooks.append(".cursor/hooks.json")  # Grok Build reads Cursor's hooks file too
    if "vscode" in tools:
        hooks.append(".github/hooks/eden.json")
    if "antigravity" in tools:
        hooks.append(".agents/hooks.json")
    return files, hooks


def git(target: Path, *args: str) -> subprocess.CompletedProcess:
    return subprocess.run(["git", "-C", str(target), *args], capture_output=True, text=True)


def is_git_repo(target: Path) -> bool:
    try:
        return git(target, "rev-parse", "--git-dir").returncode == 0
    except FileNotFoundError:
        return False


def has_commits(target: Path) -> bool:
    return is_git_repo(target) and git(target, "rev-parse", "--verify", "-q", "HEAD").returncode == 0


def has_source_files(target: Path, limit: int = 5000) -> bool:
    seen = 0
    for dirpath, dirnames, filenames in os.walk(target):
        dirnames[:] = [d for d in dirnames if not is_ignored_dir(d)]
        for fname in filenames:
            seen += 1
            rel = (Path(dirpath) / fname).relative_to(target).as_posix()
            if is_source_file(rel) or seen > limit:
                return True
    return False


def guess_mode(target: Path) -> str:
    return "adopt" if has_commits(target) or has_source_files(target) else "new"


# ------------------------------------------------------------------------------
# Command detection
# ------------------------------------------------------------------------------
def _read(path: Path) -> str:
    try:
        return path.read_text(encoding="utf-8-sig", errors="replace")
    except OSError:
        return ""


def detect_node(t: Path) -> dict[str, str]:
    try:
        pkg = json.loads(_read(t / "package.json"))
    except ValueError:
        return {}
    scripts = pkg.get("scripts") or {}
    if (t / "pnpm-lock.yaml").exists():
        pm, setup = "pnpm", "pnpm install --frozen-lockfile"
    elif (t / "yarn.lock").exists():
        pm, setup = "yarn", "yarn install --frozen-lockfile"
    elif (t / "bun.lockb").exists() or (t / "bun.lock").exists():
        pm, setup = "bun", "bun install"
    elif (t / "package-lock.json").exists():
        pm, setup = "npm", "npm ci"
    else:
        pm, setup = "npm", "npm install"
    run = "npm run" if pm == "npm" else f"{pm} run"
    out = {"setup": setup}
    if "build" in scripts:
        out["build"] = f"{run} build"
    test = str(scripts.get("test", ""))
    if test and "no test specified" not in test:
        out["test"] = "npm test" if pm == "npm" else f"{run} test"
    if "lint" in scripts:
        out["lint"] = f"{run} lint"
    return out


def detect_python(t: Path) -> dict[str, str]:
    py = _read(t / "pyproject.toml")
    reqs = (t / "requirements.txt").exists()
    if not py and not reqs:
        return {}
    has_pytest = "pytest" in py or "pytest" in _read(t / "requirements-dev.txt") or \
        "pytest" in _read(t / "requirements.txt") or (t / "pytest.ini").exists() or (t / "conftest.py").exists()
    has_ruff = "ruff" in py or (t / "ruff.toml").exists() or (t / ".ruff.toml").exists()
    if (t / "uv.lock").exists():
        prefix, setup = "uv run ", "uv sync"
    elif (t / "poetry.lock").exists() or "[tool.poetry]" in py:
        prefix, setup = "poetry run ", "poetry install"
    elif py:
        prefix, setup = "python -m ", "python -m pip install -e ."
    else:
        prefix, setup = "python -m ", "python -m pip install -r requirements.txt"
    out = {"setup": setup}
    tool = (lambda name: f"{prefix}{name}") if prefix != "python -m " else (lambda name: f"python -m {name}")
    if has_pytest:
        out["test"] = tool("pytest")
    elif (t / "tests").is_dir():
        out["test"] = (prefix + "python -m " if prefix != "python -m " else "python -m ") + \
            "unittest discover -s tests"
    if has_ruff:
        out["lint"] = tool("ruff check .")
    return out


def detect_cargo(t: Path) -> dict[str, str]:
    if not (t / "Cargo.toml").exists():
        return {}
    return {"setup": "cargo fetch", "build": "cargo build", "test": "cargo test",
            "lint": "cargo clippy -- -D warnings"}


def detect_go(t: Path) -> dict[str, str]:
    if not (t / "go.mod").exists():
        return {}
    return {"setup": "go mod download", "build": "go build ./...", "test": "go test ./...",
            "lint": "go vet ./..."}


def detect_gradle(t: Path) -> dict[str, str]:
    if not (t / "gradlew").exists():
        return {}
    out = {"build": "./gradlew assemble", "test": "./gradlew test"}
    text = _read(t / "build.gradle") + _read(t / "build.gradle.kts") + \
        _read(t / "app" / "build.gradle") + _read(t / "app" / "build.gradle.kts")
    if "com.android" in text:
        out["lint"] = "./gradlew lint"
    return out


def detect_make(t: Path) -> dict[str, str]:
    text = _read(t / "Makefile")
    if not text:
        return {}
    targets = set(re.findall(r"^([A-Za-z][\w-]*)\s*:(?!=)", text, re.MULTILINE))
    out = {}
    for key, names in (("setup", ("setup", "install", "deps")), ("build", ("build",)),
                       ("test", ("test", "check")), ("lint", ("lint",))):
        for name in names:
            if name in targets:
                out[key] = f"make {name}"
                break
    return out


def detect_commands(target: Path) -> dict[str, str]:
    """First detector to supply a command wins; a Makefile target wraps everything else."""
    found: dict[str, str] = {}
    for detector in (detect_make, detect_node, detect_python, detect_cargo, detect_go, detect_gradle):
        for key, cmd in detector(target).items():
            found.setdefault(key, cmd)
    return found


def fill_commands(text: str, cmds: dict[str, str]) -> str:
    for key in COMMAND_KEYS:
        if key in cmds:
            label = key.capitalize()
            text = re.sub(rf"^(\s*- {label}: )`<fill in[^`]*>`", lambda m: f"{m.group(1)}`{cmds[key]}`",
                          text, count=1, flags=re.MULTILINE)
    return text


def verify_script(cmds: dict[str, str]) -> str | None:
    steps = [cmds[k] for k in ("lint", "test") if k in cmds]
    if not steps:
        return None
    return ("#!/bin/sh\n"
            "# E.D.E.N. verify step, generated by init-eden from the detected commands. Edit freely.\n"
            "# Run by: python3 scripts/eden-audit.py --verify\n"
            "set -e\n" + "".join(f"{s}\n" for s in steps))


# ------------------------------------------------------------------------------
# Markdown block merge
# ------------------------------------------------------------------------------
def block_body(full_text: str) -> str:
    """Turns a full E.D.E.N. file into a section: drop the H1, demote headings one level."""
    lines = full_text.replace("\r\n", "\n").split("\n")
    if lines and lines[0].startswith("# "):
        lines = lines[1:]
    while lines and not lines[0].strip():
        lines = lines[1:]
    out, fence = [], False
    for line in lines:
        if line.lstrip().startswith(("```", "~~~")):
            fence = not fence
        if not fence and re.match(r"^#{1,5} ", line):
            line = "#" + line
        out.append(line)
    return "## E.D.E.N. Protocol\n\n" + "\n".join(out).strip() + "\n"


def merge_block(existing: str, body: str) -> str:
    """Inserts or updates the EDEN block; text outside the markers is untouched."""
    eol = "\r\n" if "\r\n" in existing else "\n"
    block = f"{BEGIN}\n{body.strip()}\n{END}".replace("\n", eol)
    if BLOCK_RE.search(existing):
        return BLOCK_RE.sub(lambda m: block, existing, count=1)
    if "<!-- EDEN:BEGIN" in existing or END in existing:
        raise ValueError("unbalanced EDEN markers")
    return existing.rstrip("\r\n") + eol + eol + block + eol


# ------------------------------------------------------------------------------
# Installer
# ------------------------------------------------------------------------------
class Installer:
    def __init__(self, source: Path, target: Path, force: bool):
        self.source, self.target, self.force = source, target, force
        self.written: list[str] = []
        self.skipped = False
        self.backups = False

    def src_bytes(self, rel: str) -> bytes:
        return (self.source / rel).read_bytes()

    def _backup(self, dest: Path) -> None:
        shutil.copy2(dest, str(dest) + ".eden-bak")
        self.backups = True

    def _record(self, rel: str, log: bool) -> None:
        if log and rel not in self.written:
            self.written.append(rel)

    def write(self, rel: str, data: bytes, executable: bool = False, keep: bool = False,
              log: bool = True) -> bool:
        """Writes a file unless it exists (then: same -> nothing, keep -> nothing, --force -> backup)."""
        dest = self.target / rel
        dest.parent.mkdir(parents=True, exist_ok=True)
        if dest.exists():
            if dest.read_bytes() == data:
                print(f"  [=] {rel} (already up to date)")
                return False
            if keep:
                print(f"  [=] {rel} exists (project state; kept)")
                return False
            if not self.force:
                print(f"  [~] {rel} exists; skipped (re-run with --force to replace it; a backup is kept)")
                self.skipped = True
                return False
            self._backup(dest)
            print(f"  [!] {rel} replaced (backup: {rel}.eden-bak)")
        else:
            print(f"  [+] {rel}")
        dest.write_bytes(data)
        if executable and os.name != "nt":
            dest.chmod(0o755)
        self._record(rel, log)
        return True

    def merge_markdown(self, rel: str, full_text: str) -> None:
        dest = self.target / rel
        data = full_text.encode("utf-8")
        if not dest.exists() or self.force or dest.read_bytes() == data:
            self.write(rel, data)
            return
        with open(dest, encoding="utf-8-sig", errors="replace", newline="") as fh:
            existing = fh.read()
        has_block = bool(BLOCK_RE.search(existing))
        first = full_text.split("\n", 1)[0].strip()
        if not has_block and existing.lstrip().split("\n", 1)[0].strip() == first:
            print(f"  [~] {rel} is an edited full E.D.E.N. file; kept (use --force to replace it)")
            self.skipped = True
            return
        try:
            merged = merge_block(existing, block_body(full_text))
        except ValueError as e:
            print(f"  [~] {rel}: {e}; fix the markers by hand. Skipped.")
            self.skipped = True
            return
        if merged == existing:
            print(f"  [=] {rel} (EDEN block up to date)")
            return
        with open(dest, "w", encoding="utf-8", newline="") as fh:
            fh.write(merged)
        print(f"  [*] {rel} ({'updated' if has_block else 'added'} EDEN block; your text kept)")
        self._record(rel, True)

    def merge_hook_config(self, rel: str) -> None:
        src_text = self.src_bytes(rel).decode("utf-8")
        dest = self.target / rel
        if not dest.exists() or self.force:
            self.write(rel, src_text.encode("utf-8"))
            return
        existing = _read(dest)
        if "eden-hook.py" in existing:
            print(f"  [=] {rel} (already runs eden-hook.py)")
            return
        try:
            data = json.loads(existing)
            ours = json.loads(src_text)
            if not isinstance(data, dict):
                raise ValueError("not a JSON object")
            if "hooks" in ours:  # Cursor / Copilot shape: {"version": 1, "hooks": {event: [...]}}
                hooks = data.setdefault("hooks", {})
                for event, entries in ours["hooks"].items():
                    if not isinstance(hooks.setdefault(event, []), list):
                        raise ValueError(f"hooks.{event} is not a list")
                    hooks[event].extend(entries)
                data.setdefault("version", ours.get("version", 1))
            else:  # Antigravity shape: {hook_name: {Event: [...]}}
                for name, cfg in ours.items():
                    data.setdefault(name, cfg)
        except ValueError as e:
            print(f"  [~] {rel} could not be merged ({e}); add the E.D.E.N. stop hook by hand. Skipped.")
            self.skipped = True
            return
        dest.write_text(json.dumps(data, indent=2) + "\n", encoding="utf-8")
        print(f"  [*] {rel} (added the E.D.E.N. stop hook; your hooks kept)")
        self._record(rel, True)


def install_git_hook(inst: Installer, target: Path) -> None:
    if not is_git_repo(target):
        print("  [-] Not a git repository; pre-commit hook not installed (run 'git init' and re-run).")
        return
    managers = [m for m in HOOK_MANAGERS if (target / m).exists()]
    if managers and not inst.force:
        print(f"  [~] Hook manager found ({', '.join(managers)}); git hook not installed. Add this to its "
              "pre-commit step:  python3 scripts/eden-audit.py --staged")
        return
    hooks_dir = git(target, "rev-parse", "--git-path", "hooks").stdout.strip()
    hook_path = Path(hooks_dir) if Path(hooks_dir).is_absolute() else target / hooks_dir
    try:
        rel = hook_path.resolve().relative_to(target.resolve()).as_posix() + "/pre-commit"
    except ValueError:
        rel = os.path.relpath(hook_path / "pre-commit", target).replace("\\", "/")
    data = inst.src_bytes("templates/hooks/pre-commit").replace(b"\r\n", b"\n")
    inst.write(rel, data, executable=True, log=False)
    text = _read(target / rel)
    if "eden-audit.py" not in text:
        print("      Your existing hook does not run the audit. Add this line to it:")
        print("      python3 scripts/eden-audit.py --staged || exit 1")
    elif "--staged" not in text:
        print("      Your hook runs the audit without --staged; re-run with --force to install the current hook.")


def plan_text(inst: Installer, mode: str) -> bytes:
    text = inst.src_bytes("templates/eden/PLAN.md").decode("utf-8")
    if mode == "adopt":
        text = re.sub(r"- \[ \] \*\*TASK-01:\*\*.*", "- [ ] **TASK-01:** Finish adopting E.D.E.N.: review the "
                      "EDEN blocks, the detected Commands and `.eden/verify`, `.eden/ARCHITECTURE.md`, and "
                      "the generated registry (skill: `eden-adopt`).", text, count=1)
        text = text.replace("- [x] **TASK-00:** Initialized the E.D.E.N. control plane.",
                            "- [x] **EDEN-ADOPT:** Added the E.D.E.N. control plane to the existing project.")
    return text.encode("utf-8")


def run(args: argparse.Namespace) -> int:
    source = Path(args.source).resolve()
    target = Path(args.target).resolve()
    target.mkdir(parents=True, exist_ok=True)
    if source == target:
        print("ERROR: target is the protocol repo itself. Run this from (or point it at) the repo you "
              "want to initialize.", file=sys.stderr)
        return 1
    tools = {t.strip().lower() for t in args.tools.split(",") if t.strip()}
    unknown = tools - set(ALL_TOOLS)
    if unknown:
        print(f"ERROR: unknown tool(s): {', '.join(sorted(unknown))}. Choose from {', '.join(ALL_TOOLS)}.",
              file=sys.stderr)
        return 2
    mode = args.mode or guess_mode(target)
    name = args.name or target.name
    detect = args.detect if args.detect is not None else (mode == "adopt")
    cmds = detect_commands(target) if detect else {}

    print(f"Initializing E.D.E.N. Protocol in {target} (project: {name}, mode: {mode}, "
          f"tools: {', '.join(t for t in ALL_TOOLS if t in tools)})")
    if cmds:
        print("  Detected commands: " + "; ".join(f"{k}: {v}" for k, v in cmds.items()))
    elif detect:
        print("  No build/test commands detected; fill in the Commands section of AGENTS.md.")

    inst = Installer(source, target, args.force)
    files, hook_configs = files_for_tools(tools, args.legacy)
    for rel in MARKER_FILES:  # adopt: always merge into instruction files the project already has
        if rel not in files and (target / rel).exists():
            files.append(rel)

    # 1. Agent instructions and pointer files
    for rel in files:
        text = inst.src_bytes(rel).decode("utf-8")
        if rel == "AGENTS.md":
            text = fill_commands(text, cmds)
        if rel in MARKER_FILES:
            inst.merge_markdown(rel, text)
        else:
            inst.write(rel, text.encode("utf-8"))

    # 2. Tooling, shared skills, and stop hooks
    for rel in SCRIPTS:
        inst.write(rel, inst.src_bytes(rel), executable=True)
    for rel in SKILLS:
        inst.write(rel, inst.src_bytes(rel))
    for rel in hook_configs:
        inst.merge_hook_config(rel)

    # 3. Control plane (never replaced, even with --force)
    arch = inst.src_bytes("templates/eden/ARCHITECTURE.md").decode("utf-8").replace("{{PROJECT_NAME}}", name)
    inst.write(".eden/ARCHITECTURE.md", arch.encode("utf-8"), keep=True)
    inst.write(".eden/PLAN.md", plan_text(inst, mode), keep=True)
    registry_created = inst.write(".eden/REGISTRY.md", inst.src_bytes("templates/eden/REGISTRY.md"), keep=True)
    inst.write(".eden/LEARNINGS.md", inst.src_bytes("templates/eden/LEARNINGS.md"), keep=True)
    script = verify_script(cmds)
    if script and not (target / ".eden/verify").exists() and not (target / ".eden/verify.py").exists():
        inst.write(".eden/verify", script.encode("utf-8"), executable=True)

    # 4. Git pre-commit hook
    install_git_hook(inst, target)

    # 5. Index existing source files (only into a fresh registry, or when asked)
    if registry_created or args.reindex:
        res = subprocess.run([sys.executable, str(target / "scripts/eden-index.py"), str(target)],
                             capture_output=True, text=True)
        print("  " + (res.stdout.strip() or res.stderr.strip()).replace("\n", "\n  "))
    else:
        print("  [=] .eden/REGISTRY.md kept; run with --reindex (or scripts/eden-index.py) to regenerate section 2")

    # 6. Changelog: record only what this run actually wrote or merged
    changelog = target / ".eden/CHANGELOG_AGENT.jsonl"
    new_log = not changelog.exists() or changelog.stat().st_size == 0
    if inst.written or new_log:
        task = ("EDEN-ADOPT" if mode == "adopt" else "TASK-00") if new_log else "EDEN-SETUP"
        summary = {"TASK-00": "Initialized the E.D.E.N. control plane.",
                   "EDEN-ADOPT": "Adopted the E.D.E.N. control plane into the existing project.",
                   "EDEN-SETUP": "Re-ran init-eden; updated the E.D.E.N. files listed."}[task]
        entry = {"timestamp": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
                 "phase": "Normalize", "task_id": task, "action": "CREATED" if new_log else "MODIFIED",
                 "files": inst.written, "reused_modules": [], "summary": summary}
        prefix = ""
        if not new_log and not changelog.read_bytes().endswith(b"\n"):
            prefix = "\n"
        with open(changelog, "a", encoding="utf-8", newline="\n") as fh:
            fh.write(prefix + json.dumps(entry, separators=(",", ":")) + "\n")
        print(f"  [{'+' if new_log else '*'}] .eden/CHANGELOG_AGENT.jsonl ({task}, {len(inst.written)} file(s))")
    else:
        print("  [=] .eden/CHANGELOG_AGENT.jsonl (nothing changed; no entry added)")

    print("Done. Next:")
    if mode == "adopt":
        print("  1. Review the EDEN blocks, detected Commands, .eden/verify, and .eden/REGISTRY.md (git diff).")
        print("  2. Fill in .eden/ARCHITECTURE.md (or ask your agent to run the eden-adopt skill).")
    else:
        print("  1. Fill in the Commands section of AGENTS.md and .eden/ARCHITECTURE.md.")
        print("  2. Register source files as you add them (scripts/eden-index.py helps).")
    print("  3. python3 scripts/eden-audit.py --doctor   (what each tool loads, what is unfinished)")
    if inst.backups:
        print("Review and delete the *.eden-bak backups before committing.")
    if inst.skipped:
        print("Some files were left unchanged (see [~] above). Use --force to replace them.")
    return 0


def parse_args(argv: list[str]) -> argparse.Namespace:
    p = argparse.ArgumentParser(description="E.D.E.N. Protocol installer")
    p.add_argument("--target", default=".", help="repository to initialize (default: current directory)")
    p.add_argument("--source", default=str(Path(__file__).resolve().parent.parent),
                   help="protocol checkout to copy from (default: the checkout holding this script)")
    p.add_argument("--name", default="", help="project name for .eden/ARCHITECTURE.md")
    mode = p.add_mutually_exclusive_group()
    mode.add_argument("--new", dest="mode", action="store_const", const="new")
    mode.add_argument("--adopt", dest="mode", action="store_const", const="adopt")
    p.add_argument("--tools", default=",".join(DEFAULT_TOOLS),
                   help=f"comma-separated: {','.join(ALL_TOOLS)} (default: {','.join(DEFAULT_TOOLS)})")
    p.add_argument("--legacy", action="store_true", help="also write .cursorrules and .windsurfrules")
    p.add_argument("--force", action="store_true", help="replace E.D.E.N.-managed files (with backups)")
    det = p.add_mutually_exclusive_group()
    det.add_argument("--detect", dest="detect", action="store_const", const=True,
                     help="detect Setup/Build/Test/Lint commands (default in adopt mode)")
    det.add_argument("--no-detect", dest="detect", action="store_const", const=False)
    p.add_argument("--reindex", action="store_true", help="regenerate REGISTRY.md section 2 even if it exists")
    return p.parse_args(argv)


if __name__ == "__main__":
    sys.exit(run(parse_args(sys.argv[1:])))
