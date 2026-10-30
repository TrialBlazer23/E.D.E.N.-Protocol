#!/usr/bin/env python3
"""
E.D.E.N. stop hook for Cursor, Grok Build, VS Code / GitHub Copilot, and Google Antigravity.

When the agent tries to finish, this runs the E.D.E.N. audit (only if source files changed)
and, if it fails, asks the agent to fix the problems before stopping. Each tool sends a
different JSON payload on stdin and expects a different reply on stdout; the caller is
detected from the payload, so one script serves every config:

  .cursor/hooks.json        Cursor `stop` (Grok Build also reads this file)
  .github/hooks/eden.json   Copilot CLI / cloud agent / VS Code `agentStop`
  .agents/hooks.json        Antigravity `Stop`

The agent is forced to continue at most MAX_FORCED_ROUNDS times per turn; with the
original attempt that is the "3 rounds, then stop and report" rule from AGENTS.md.
The hook fails open: any internal error lets the agent stop.

Environment:
  EDEN_HOOK_VERIFY=1    also run .eden/verify (tests/lint) in the hook
  EDEN_HOOK_DISABLE=1   do nothing
"""

from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys
import tempfile
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from eden_common import is_protocol_repo, is_source_file, parse_porcelain_z  # noqa: E402

MAX_FORCED_ROUNDS = 2
AUDIT_TIMEOUT_S = 110
MAX_REASON_CHARS = 6000
STATE_TTL_S = 6 * 3600
TOOLS = ("cursor", "grok", "copilot", "antigravity")


# ------------------------------------------------------------------------------
# Caller detection and per-tool protocol
# ------------------------------------------------------------------------------
def detect_tool(payload: dict, env: dict | None = None) -> str | None:
    env = os.environ if env is None else env
    if env.get("GROK_HOOK_EVENT") or "hookEventName" in payload or "stopHookActive" in payload:
        return "grok"
    if any(k in payload for k in ("executionNum", "terminationReason", "workspacePaths", "fullyIdle")):
        return "antigravity"
    if any(k in payload for k in ("loop_count", "cursor_version", "workspace_roots")):
        return "cursor"
    if any(k in payload for k in ("stopReason", "stop_reason", "stop_hook_active")) or \
            payload.get("hook_event_name") == "Stop":
        return "copilot"
    return None


def is_real_stop(tool: str, payload: dict) -> bool:
    """Gate only genuine completions, not aborts, errors, subagents, or session-end fires."""
    if tool == "cursor":
        return payload.get("status", "completed") == "completed"
    if tool == "grok":
        return payload.get("reason", "end_turn") == "end_turn" and not payload.get("subagentType")
    if tool == "antigravity":
        return (payload.get("terminationReason", "model_stop") == "model_stop"
                and payload.get("fullyIdle", True) is not False)
    if tool == "copilot":
        return (payload.get("stopReason") or payload.get("stop_reason") or "end_turn") == "end_turn"
    return False


def continuing(tool: str, payload: dict) -> bool | None:
    """Whether this stop follows one of our own forced continuations (None = unknown)."""
    if tool == "cursor" and "loop_count" in payload:
        return int(payload.get("loop_count") or 0) > 0
    for key in ("stopHookActive", "stop_hook_active"):
        if key in payload:
            return bool(payload[key])
    return None


def session_key(tool: str, payload: dict) -> str:
    for key in ("conversation_id", "conversationId", "sessionId", "session_id"):
        if payload.get(key):
            return f"{tool}:{payload[key]}"
    return f"{tool}:{os.environ.get('GROK_SESSION_ID', 'default')}"


def allow(tool: str | None) -> dict:
    return {"decision": "allow"} if tool == "antigravity" else {}


def block(tool: str, reason: str) -> dict:
    if tool == "cursor":
        return {"followup_message": reason}
    if tool == "antigravity":
        return {"decision": "continue", "reason": reason}
    if tool == "copilot":
        # Copilot CLI reads the flat fields; the VS Code local runtime reads hookSpecificOutput.
        return {"decision": "block", "reason": reason,
                "hookSpecificOutput": {"hookEventName": "Stop", "decision": "block", "reason": reason}}
    return {"decision": "block", "reason": reason}  # grok (Claude Code-compatible)


# ------------------------------------------------------------------------------
# Repository, state, and audit
# ------------------------------------------------------------------------------
def find_root(payload: dict) -> Path | None:
    candidates: list[str] = []
    for key in ("workspace_roots", "workspacePaths"):
        val = payload.get(key)
        if isinstance(val, list):
            candidates.extend(str(v) for v in val if v)
    for key in ("workspaceRoot", "cwd"):
        if payload.get(key):
            candidates.append(str(payload[key]))
    for key in ("GROK_WORKSPACE_ROOT", "CURSOR_PROJECT_DIR"):
        if os.environ.get(key):
            candidates.append(os.environ[key])
    candidates.append(os.getcwd())
    candidates.append(str(Path(__file__).resolve().parent.parent))
    for cand in candidates:
        path = Path(os.path.expanduser(cand))
        for p in (path, *path.parents):
            if (p / ".eden").is_dir() and (p / "scripts" / "eden-audit.py").is_file():
                return p
    return None


def state_path(root: Path) -> Path:
    try:
        res = subprocess.run(["git", "-C", str(root), "rev-parse", "--git-dir"],
                             capture_output=True, text=True, timeout=10)
        if res.returncode == 0 and res.stdout.strip():
            git_dir = Path(res.stdout.strip())
            return (git_dir if git_dir.is_absolute() else root / git_dir) / "eden-hook-state.json"
    except (OSError, subprocess.SubprocessError):
        pass
    return Path(tempfile.gettempdir()) / "eden-hook-state.json"


def load_state(path: Path) -> dict:
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
        now = time.time()
        return {k: v for k, v in data.items()
                if isinstance(v, dict) and now - float(v.get("t", 0)) < STATE_TTL_S}
    except (OSError, ValueError, TypeError):
        return {}


def save_state(path: Path, state: dict) -> None:
    try:
        path.write_text(json.dumps(state), encoding="utf-8")
    except OSError:
        pass


def changed_source_files(root: Path) -> list[str] | None:
    """Changed project source files, or None if git is unavailable (then audit anyway)."""
    try:
        res = subprocess.run(["git", "-C", str(root), "status", "--porcelain=v1", "-z",
                              "--untracked-files=all"], capture_output=True, timeout=30)
    except (OSError, subprocess.SubprocessError):
        return None
    if res.returncode != 0:
        return None
    include_eden = is_protocol_repo(root)
    return sorted(p for p, s in parse_porcelain_z(res.stdout).items()
                  if s != "D" and is_source_file(p, include_eden=include_eden))


def run_audit(root: Path) -> tuple[bool, str]:
    cmd = [sys.executable, str(root / "scripts" / "eden-audit.py"), "--root", str(root)]
    if os.environ.get("EDEN_HOOK_VERIFY") == "1":
        cmd.append("--verify")
    try:
        res = subprocess.run(cmd, cwd=root, capture_output=True, text=True, timeout=AUDIT_TIMEOUT_S,
                             encoding="utf-8", errors="replace")
    except subprocess.TimeoutExpired:
        return True, "audit timed out; not blocking"
    except OSError as e:
        return True, f"audit could not start ({e}); not blocking"
    return res.returncode == 0, (res.stdout + res.stderr).strip()


def build_reason(output: str, round_no: int) -> str:
    if len(output) > MAX_REASON_CHARS:
        output = output[:MAX_REASON_CHARS] + "\n... (truncated; run the audit yourself for the rest)"
    last = round_no >= MAX_FORCED_ROUNDS
    tail = ("This is the last automatic round. If the audit still fails after this, stop and report "
            "the remaining errors to the human instead of continuing."
            if last else
            "Fix these, then re-run `python3 scripts/eden-audit.py` until it exits 0 before you finish.")
    return ("E.D.E.N. stop hook: the audit failed, so this change is not done yet "
            f"(automatic round {round_no} of {MAX_FORCED_ROUNDS}).\n\n{output}\n\n{tail}")


# ------------------------------------------------------------------------------
# Entry point
# ------------------------------------------------------------------------------
def decide(payload: dict, tool_hint: str | None = None) -> tuple[str | None, dict]:
    tool = detect_tool(payload) or tool_hint
    if tool not in TOOLS or os.environ.get("EDEN_HOOK_DISABLE") == "1":
        return tool, allow(tool)
    if not is_real_stop(tool, payload):
        return tool, allow(tool)
    root = find_root(payload)
    if root is None:
        return tool, allow(tool)

    spath = state_path(root)
    state = load_state(spath)
    key = session_key(tool, payload)
    rounds = int(state.get(key, {}).get("rounds", 0))
    if continuing(tool, payload) is False:
        rounds = 0  # a new user turn starts a fresh budget

    changed = changed_source_files(root)
    if changed == [] and os.environ.get("EDEN_HOOK_VERIFY") != "1":
        state.pop(key, None)
        save_state(spath, state)
        return tool, allow(tool)

    ok, output = run_audit(root)
    if ok or rounds >= MAX_FORCED_ROUNDS:
        if not ok:
            print("[EDEN-HOOK] audit still failing after the automatic rounds; letting the agent stop "
                  "so it can report.", file=sys.stderr)
        state.pop(key, None)
        save_state(spath, state)
        return tool, allow(tool)

    rounds += 1
    state[key] = {"rounds": rounds, "t": time.time()}
    save_state(spath, state)
    return tool, block(tool, build_reason(output, rounds))


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="E.D.E.N. stop hook (reads hook JSON on stdin)")
    parser.add_argument("--tool", choices=TOOLS, help="fallback when the caller cannot be detected")
    args = parser.parse_args(sys.argv[1:] if argv is None else argv)
    tool = args.tool
    try:
        raw = sys.stdin.read() if sys.stdin and not sys.stdin.isatty() else ""
        payload = json.loads(raw) if raw.strip() else {}
        if not isinstance(payload, dict):
            payload = {}
        tool, reply = decide(payload, args.tool)
    except Exception as e:  # fail open: never trap the agent because the hook broke
        print(f"[EDEN-HOOK] internal error, allowing stop: {e}", file=sys.stderr)
        reply = allow(tool)
    sys.stdout.write(json.dumps(reply) + "\n")
    sys.stdout.flush()
    return 0


if __name__ == "__main__":
    sys.exit(main())
