#!/usr/bin/env bash
# ==============================================================================
# E.D.E.N. Protocol bootstrapper (POSIX shell). Needs Python 3.
#
# Usage:
#   /path/to/E.D.E.N.-Protocol/init-eden.sh [--new | --adopt] [--tools LIST] [--legacy]
#       [--force] [--detect | --no-detect] [--reindex] [--name NAME] [--source DIR] [TARGET_DIR]
#
#   TARGET_DIR   repository to initialize (default: current directory)
#   --new        brand-new project: write the full AGENTS.md and pointer files
#   --adopt      existing project: merge an <!-- EDEN:BEGIN v1 --> ... <!-- EDEN:END -->
#                block into existing AGENTS.md / CLAUDE.md / GEMINI.md /
#                .github/copilot-instructions.md (text outside the markers is kept)
#                and detect Setup/Build/Test/Lint commands.
#                Default: --new if the target has no commits and no source files, else --adopt.
#   --tools      comma-separated: antigravity,cursor,grok,vscode,claude
#                (default: antigravity,cursor,grok,vscode)
#   --legacy     also write .cursorrules and .windsurfrules
#   --force      replace E.D.E.N.-managed files wholesale; each is backed up as
#                <file>.eden-bak. Existing .eden/ state files are always kept.
#   --detect     detect commands in --new mode too (--no-detect turns detection off)
#   --reindex    regenerate section 2 of an existing .eden/REGISTRY.md
#   --source     protocol checkout to copy from (default: the folder holding this script)
#   --name       project name used in .eden/ARCHITECTURE.md (default: target folder name)
#
#   EDEN_RAW_BASE=https://raw.githubusercontent.com/<owner>/E.D.E.N.-Protocol/<commit>
#                download the protocol files from this URL when --source has none.
#   EDEN_SHA256  optional: 64-hex SHA-256 of scripts/eden-install.py, or a path to a
#                sha256sum-format file. A mismatch aborts before the installer runs.
#
# Re-running is safe. The work is done by scripts/eden-install.py.
# ==============================================================================
set -euo pipefail

SOURCE_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
TARGET_DIR="."
ARGS=()

while [ $# -gt 0 ]; do
  case "$1" in
    --new|--adopt|--legacy|--force|--detect|--no-detect|--reindex) ARGS+=("$1") ;;
    --tools|--name) ARGS+=("$1" "${2:?$1 needs a value}"); shift ;;
    --tools=*|--name=*) ARGS+=("$1") ;;
    --source) SOURCE_DIR="$(cd "${2:?--source needs a value}" && pwd)"; shift ;;
    -h|--help) sed -n '2,32p' "$0"; exit 0 ;;
    -*) echo "Unknown option: $1" >&2; exit 2 ;;
    *) TARGET_DIR="$1" ;;
  esac
  shift
done

mkdir -p "$TARGET_DIR"
TARGET_DIR="$(cd "$TARGET_DIR" && pwd)"

# Files the installer reads from the protocol checkout (keep in sync with scripts/eden-install.py).
SOURCE_FILES="AGENTS.md CLAUDE.md GEMINI.md .cursorrules .windsurfrules .cursor/rules/eden.mdc
.github/copilot-instructions.md scripts/eden-audit.py scripts/eden-index.py scripts/eden-hook.py
scripts/eden_common.py scripts/eden-install.py .cursor/hooks.json .github/hooks/eden.json .agents/hooks.json
.agents/skills/eden-normalize/SKILL.md .agents/skills/eden-architect/SKILL.md .agents/skills/eden-adopt/SKILL.md
templates/eden/ARCHITECTURE.md templates/eden/PLAN.md templates/eden/REGISTRY.md templates/eden/LEARNINGS.md
templates/hooks/pre-commit"

# Fetch the protocol files if the source folder does not have them.
if [ ! -f "$SOURCE_DIR/scripts/eden-install.py" ] || [ ! -f "$SOURCE_DIR/templates/hooks/pre-commit" ]; then
  if [ -z "${EDEN_RAW_BASE:-}" ]; then
    echo "ERROR: $SOURCE_DIR is not an E.D.E.N.-Protocol checkout (scripts/ or templates/ missing)." >&2
    echo "       Run this script from a clone of the protocol repo, pass --source DIR, or set EDEN_RAW_BASE." >&2
    exit 1
  fi
  TMP_SRC="$(mktemp -d)"
  trap 'rm -rf "$TMP_SRC"' EXIT
  echo "Downloading protocol files from $EDEN_RAW_BASE"
  for f in $SOURCE_FILES; do
    mkdir -p "$TMP_SRC/$(dirname "$f")"
    if command -v curl >/dev/null 2>&1; then
      curl -fsSL "$EDEN_RAW_BASE/$f" -o "$TMP_SRC/$f"
    else
      wget -q "$EDEN_RAW_BASE/$f" -O "$TMP_SRC/$f"
    fi
  done
  SOURCE_DIR="$TMP_SRC"
fi

eden_sha256() {
  if command -v sha256sum >/dev/null 2>&1; then
    sha256sum "$1" | awk '{print $1}'
  elif command -v shasum >/dev/null 2>&1; then
    shasum -a 256 "$1" | awk '{print $1}'
  else
    python3 -c 'import hashlib,sys; print(hashlib.sha256(open(sys.argv[1],"rb").read()).hexdigest())' "$1"
  fi
}

# Optional integrity check (no-op unless EDEN_SHA256 is set).
if [ -n "${EDEN_SHA256:-}" ]; then
  if [ -f "${EDEN_SHA256}" ]; then
    while read -r expected rel rest; do
      case "$expected" in ""|\#*) continue ;; esac
      rel="${rel#\*}"
      if [ -z "$rel" ]; then
        echo "ERROR: EDEN_SHA256 checksums file has a line without a path." >&2
        exit 1
      fi
      actual="$(eden_sha256 "$SOURCE_DIR/$rel")"
      expected_lc="$(printf '%s' "$expected" | tr 'A-F' 'a-f')"
      actual_lc="$(printf '%s' "$actual" | tr 'A-F' 'a-f')"
      if [ "$actual_lc" != "$expected_lc" ]; then
        echo "ERROR: sha256 mismatch for $rel (EDEN_SHA256 checksums file)." >&2
        exit 1
      fi
    done < "${EDEN_SHA256}"
    echo "EDEN_SHA256: checksums file verified."
  elif printf '%s' "$EDEN_SHA256" | grep -Eq '^[0-9A-Fa-f]{64}$'; then
    actual="$(eden_sha256 "$SOURCE_DIR/scripts/eden-install.py")"
    expected_lc="$(printf '%s' "$EDEN_SHA256" | tr 'A-F' 'a-f')"
    actual_lc="$(printf '%s' "$actual" | tr 'A-F' 'a-f')"
    if [ "$actual_lc" != "$expected_lc" ]; then
      echo "ERROR: sha256 mismatch for scripts/eden-install.py." >&2
      exit 1
    fi
    echo "EDEN_SHA256: scripts/eden-install.py verified."
  else
    echo "ERROR: EDEN_SHA256 must be a 64-digit hex digest of scripts/eden-install.py" >&2
    echo "       or a path to a sha256sum-format file." >&2
    exit 1
  fi
fi

if [ "$SOURCE_DIR" = "$TARGET_DIR" ]; then
  echo "ERROR: target is the protocol repo itself. Run this from (or point it at) the repo you want to initialize." >&2
  exit 1
fi

# Python 3 discovery: python3, then python, then py -3 (Windows launcher, e.g. Git Bash).
PY=()
for cand in "python3" "python" "py -3"; do
  # shellcheck disable=SC2086
  if command -v ${cand%% *} >/dev/null 2>&1 && $cand -c 'import sys; sys.exit(sys.version_info[0] != 3)' >/dev/null 2>&1; then
    read -r -a PY <<< "$cand"
    break
  fi
done
if [ ${#PY[@]} -eq 0 ]; then
  echo "ERROR: Python 3 not found (tried python3, python, py -3). Install Python 3 and re-run." >&2
  exit 1
fi

exec "${PY[@]}" "$SOURCE_DIR/scripts/eden-install.py" --source "$SOURCE_DIR" --target "$TARGET_DIR" ${ARGS[@]+"${ARGS[@]}"}
