"""Shared helpers for the E.D.E.N. smoke tests: temp git repos initialized with init-eden.sh."""

import json
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

PROTOCOL_ROOT = Path(__file__).resolve().parent.parent


def run(cmd, cwd, check=True):
    return subprocess.run(cmd, cwd=cwd, capture_output=True, text=True, check=check)


def make_repo() -> Path:
    """Creates an empty git repo with a committer identity."""
    path = Path(tempfile.mkdtemp(prefix="eden-test-"))
    run(["git", "init", "-q"], path)
    run(["git", "config", "user.email", "test@example.com"], path)
    run(["git", "config", "user.name", "EDEN Test"], path)
    run(["git", "config", "commit.gpgsign", "false"], path)
    return path


def init_repo() -> Path:
    """Creates a repo, runs init-eden.sh, and commits the scaffold."""
    path = make_repo()
    run(["bash", str(PROTOCOL_ROOT / "init-eden.sh")], path)
    run(["git", "add", "-A"], path)
    run(["git", "commit", "-q", "-m", "init"], path)
    return path


def audit(repo: Path, *args: str) -> subprocess.CompletedProcess:
    return run([sys.executable, "scripts/eden-audit.py", *args], repo, check=False)


def register(repo: Path, rel: str) -> None:
    reg = repo / ".eden" / "REGISTRY.md"
    text = reg.read_text(encoding="utf-8")
    header = "| File Path | Exported Symbols / Key API | Responsibility | Consumers |\n| :--- | :--- | :--- | :--- |\n"
    text = text.replace(header, header + f"| `{rel}` | - | test | - |\n", 1)
    reg.write_text(text, encoding="utf-8")


def log_change(repo: Path, files: list[str]) -> None:
    entry = {"timestamp": "2026-01-01T00:00:00Z", "phase": "Normalize", "action": "MODIFIED",
             "files": files, "summary": "test"}
    with open(repo / ".eden" / "CHANGELOG_AGENT.jsonl", "a", encoding="utf-8") as fh:
        fh.write(json.dumps(entry) + "\n")


def cleanup(path: Path) -> None:
    shutil.rmtree(path, ignore_errors=True)
