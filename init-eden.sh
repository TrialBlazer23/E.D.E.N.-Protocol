#!/usr/bin/env bash
# ==============================================================================
# E.D.E.N. Protocol bootstrapper (POSIX shell)
#
# Usage:
#   /path/to/E.D.E.N-Protocol/init-eden.sh [--force] [--name NAME] [--source DIR] [TARGET_DIR]
#
#   TARGET_DIR   repository to initialize (default: current directory)
#   --source     protocol checkout to copy from (default: the folder holding this script)
#   --name       project name used in .eden/ARCHITECTURE.md (default: target folder name)
#   --force      overwrite existing agent files, scripts, and hook; each is backed up as
#                <file>.eden-bak. Existing .eden/ state files are always kept.
#
#   EDEN_RAW_BASE=https://raw.githubusercontent.com/<owner>/E.D.E.N-Protocol/main
#                download the protocol files from this URL when --source has none.
#
# Existing files (AGENTS.md, pointer files, scripts, .eden/*, pre-commit hook) are
# never overwritten without --force.
# ==============================================================================
set -euo pipefail

FORCE=0
PROJECT_NAME=""
SOURCE_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
TARGET_DIR="."

while [ $# -gt 0 ]; do
  case "$1" in
    --force) FORCE=1 ;;
    --name) PROJECT_NAME="$2"; shift ;;
    --source) SOURCE_DIR="$(cd "$2" && pwd)"; shift ;;
    -h|--help) sed -n '2,19p' "$0"; exit 0 ;;
    -*) echo "Unknown option: $1" >&2; exit 2 ;;
    *) TARGET_DIR="$1" ;;
  esac
  shift
done

mkdir -p "$TARGET_DIR"
TARGET_DIR="$(cd "$TARGET_DIR" && pwd)"
PROJECT_NAME="${PROJECT_NAME:-$(basename "$TARGET_DIR")}"

# Files copied verbatim from the protocol repo (source path -> same target path).
COPY_FILES="AGENTS.md CLAUDE.md GEMINI.md .cursorrules .windsurfrules .cursor/rules/eden.mdc .github/copilot-instructions.md scripts/eden-audit.py scripts/eden-index.py"
TEMPLATE_FILES="templates/eden/ARCHITECTURE.md templates/eden/PLAN.md templates/eden/REGISTRY.md templates/eden/LEARNINGS.md templates/hooks/pre-commit"

# Fetch the protocol files if the source folder does not have them.
if [ ! -f "$SOURCE_DIR/scripts/eden-audit.py" ] || [ ! -f "$SOURCE_DIR/templates/hooks/pre-commit" ]; then
  if [ -z "${EDEN_RAW_BASE:-}" ]; then
    echo "ERROR: $SOURCE_DIR is not an E.D.E.N.-Protocol checkout (scripts/ or templates/ missing)." >&2
    echo "       Run this script from a clone of the protocol repo, pass --source DIR, or set EDEN_RAW_BASE." >&2
    exit 1
  fi
  TMP_SRC="$(mktemp -d)"
  trap 'rm -rf "$TMP_SRC"' EXIT
  echo "Downloading protocol files from $EDEN_RAW_BASE"
  for f in $COPY_FILES $TEMPLATE_FILES; do
    mkdir -p "$TMP_SRC/$(dirname "$f")"
    if command -v curl >/dev/null 2>&1; then
      curl -fsSL "$EDEN_RAW_BASE/$f" -o "$TMP_SRC/$f"
    else
      wget -q "$EDEN_RAW_BASE/$f" -O "$TMP_SRC/$f"
    fi
  done
  SOURCE_DIR="$TMP_SRC"
fi

if [ "$SOURCE_DIR" = "$TARGET_DIR" ]; then
  echo "ERROR: target is the protocol repo itself. Run this from (or point it at) the repo you want to initialize." >&2
  exit 1
fi

cd "$TARGET_DIR"
echo "Initializing E.D.E.N. Protocol in $TARGET_DIR (project: $PROJECT_NAME)"

SKIPPED=0
BACKUPS=0
# install_file SRC DEST [MODE] [keep]   ("keep" = project state; never replaced, even with --force)
install_file() {
  local src="$1" dest="$2" mode="${3:-}" keep="${4:-}"
  mkdir -p "$(dirname "$dest")"
  if [ -e "$dest" ]; then
    if cmp -s "$src" "$dest"; then
      echo "  [=] $dest (already up to date)"
      return 0
    fi
    if [ "$keep" = "keep" ]; then
      echo "  [=] $dest exists (project state; kept)"
      return 0
    fi
    if [ "$FORCE" -ne 1 ]; then
      echo "  [~] $dest exists; skipped (re-run with --force to replace it; a backup is kept)"
      SKIPPED=1
      return 0
    fi
    cp -p "$dest" "$dest.eden-bak"
    BACKUPS=1
    echo "  [!] $dest replaced (backup: $dest.eden-bak)"
  else
    echo "  [+] $dest"
  fi
  cp "$src" "$dest"
  if [ -n "$mode" ]; then chmod "$mode" "$dest"; fi
}

# 1. Agent instructions, pointer files, and tooling
for f in $COPY_FILES; do
  case "$f" in
    scripts/*) install_file "$SOURCE_DIR/$f" "$f" 755 ;;
    *) install_file "$SOURCE_DIR/$f" "$f" ;;
  esac
done

# 2. Control plane templates
TMP_ARCH="$(mktemp)"
sed "s/{{PROJECT_NAME}}/$(printf '%s' "$PROJECT_NAME" | sed 's/[\/&]/\\&/g')/g" \
  "$SOURCE_DIR/templates/eden/ARCHITECTURE.md" > "$TMP_ARCH"
install_file "$TMP_ARCH" ".eden/ARCHITECTURE.md" "" keep
rm -f "$TMP_ARCH"
for f in PLAN.md REGISTRY.md LEARNINGS.md; do
  install_file "$SOURCE_DIR/templates/eden/$f" ".eden/$f" "" keep
done

if [ ! -s .eden/CHANGELOG_AGENT.jsonl ]; then
  TIMESTAMP="$(date -u +"%Y-%m-%dT%H:%M:%SZ")"
  printf '%s\n' "{\"timestamp\":\"${TIMESTAMP}\",\"phase\":\"Normalize\",\"task_id\":\"TASK-00\",\"action\":\"CREATED\",\"files\":[\"AGENTS.md\",\".eden/ARCHITECTURE.md\",\".eden/PLAN.md\",\".eden/REGISTRY.md\",\".eden/LEARNINGS.md\"],\"reused_modules\":[],\"summary\":\"Initialized the E.D.E.N. control plane.\"}" > .eden/CHANGELOG_AGENT.jsonl
  echo "  [+] .eden/CHANGELOG_AGENT.jsonl"
else
  echo "  [=] .eden/CHANGELOG_AGENT.jsonl (kept; append-only)"
fi

# 3. Git pre-commit hook (respects core.hooksPath and worktrees)
if git rev-parse --git-dir >/dev/null 2>&1; then
  HOOKS_DIR="$(git rev-parse --git-path hooks)"
  install_file "$SOURCE_DIR/templates/hooks/pre-commit" "$HOOKS_DIR/pre-commit" 755
  if [ -e "$HOOKS_DIR/pre-commit" ] && ! grep -q "eden-audit.py" "$HOOKS_DIR/pre-commit"; then
    echo "      Your existing hook does not run the audit. Add this line to it:"
    echo "      python3 scripts/eden-audit.py --staged || exit 1"
  elif ! grep -q -- "--staged" "$HOOKS_DIR/pre-commit"; then
    echo "      Your hook runs the audit without --staged; re-run with --force to install the current hook."
  fi
else
  echo "  [-] Not a git repository; pre-commit hook not installed (run 'git init' and re-run)."
fi

# 4. Index existing source files into .eden/REGISTRY.md
PY=""
if command -v python3 >/dev/null 2>&1; then PY=python3; elif command -v python >/dev/null 2>&1; then PY=python; fi
if [ -n "$PY" ]; then
  "$PY" scripts/eden-index.py .
else
  echo "  [-] Python 3 not found; skipped indexing. Install Python 3 to use the audit."
fi

echo "Done. Next: fill in the Commands section of AGENTS.md and .eden/ARCHITECTURE.md, then run:"
echo "  python3 scripts/eden-audit.py"
if [ "$BACKUPS" -eq 1 ]; then
  echo "Review and delete the *.eden-bak backups before committing."
fi
if [ "$SKIPPED" -eq 1 ]; then
  echo "Some files already existed and were left unchanged (see [~] above). Use --force to replace them."
fi
