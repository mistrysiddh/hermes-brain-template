#!/usr/bin/env bash
# install.sh — interactive installer for the Hermes Brain vault template.
# Works on Linux, macOS, and Git Bash/WSL on Windows.
set -euo pipefail

# Reopen /dev/tty for interactive input if running via curl | bash
if [ ! -t 0 ]; then
  if (exec </dev/tty) 2>/dev/null; then
    exec </dev/tty
  fi
fi

REPO_URL="https://github.com/mistrysiddh/hermes-brain-template.git"
ZIP_URL="https://github.com/mistrysiddh/hermes-brain-template/archive/refs/heads/main.zip"

SCRIPT_DIR="$(cd -- "$(dirname -- "${BASH_SOURCE[0]:-$0}")" &>/dev/null && pwd || true)"
CANDIDATE_ROOT="$(cd "$SCRIPT_DIR/../../.." 2>/dev/null && pwd || true)"

if [ -n "$CANDIDATE_ROOT" ] && [ -d "$CANDIDATE_ROOT/_System" ]; then
  TEMPLATE_ROOT="$CANDIDATE_ROOT"
  IS_REMOTE=false
else
  TEMPLATE_ROOT=""
  IS_REMOTE=true
fi

# Parse command line arguments
DEST_ARG=""
BACKEND_ARG=""
TEST_MODE=false

while [ $# -gt 0 ]; do
  case "$1" in
    --dest|-d)
      DEST_ARG="$2"
      shift 2
      ;;
    --backend|-b)
      BACKEND_ARG="$2"
      shift 2
      ;;
    --test)
      TEST_MODE=true
      shift
      ;;
    --help|-h)
      echo "Usage: $0 [--dest <path>] [--backend <ollama|python|skip>] [--test] [--help]"
      echo "  --dest     Destination directory for the vault (default: ~/Hermes Brain)"
      echo "  --backend  Trend-digest embedding backend: ollama, python, or skip"
      echo "  --test     Run self-test after installation (validates scripts, manifest, dashboard)"
      echo "  --help     Show this help"
      exit 0
      ;;
    *)
      shift
      ;;
  esac
done


bold()  { printf '\033[1m%s\033[0m\n' "$1"; }
info()  { printf '  %s\n' "$1"; }
warn()  { printf '  \033[33m! %s\033[0m\n' "$1"; }
ok()    { printf '  \033[32m✓ %s\033[0m\n' "$1"; }

to_native_path() {
  if command -v cygpath >/dev/null 2>&1; then
    cygpath -w "$1" 2>/dev/null || echo "$1"
  else
    echo "$1"
  fi
}

find_python() {
  for candidate in python3 python py; do
    if command -v "$candidate" >/dev/null 2>&1; then
      if "$candidate" -c "import sys" >/dev/null 2>&1; then
        echo "$candidate"
        return 0
      fi
    fi
  done
  return 1
}


echo
bold "Hermes Brain — vault installer"
info "Sets up a personal Obsidian memory vault for a Hermes agent."
echo

# ---------------------------------------------------------------------------
# 1. Detect OS
# ---------------------------------------------------------------------------
OS="unknown"
case "$(uname -s)" in
  Linux*)  OS="linux" ;;
  Darwin*) OS="mac" ;;
  MINGW*|MSYS*|CYGWIN*) OS="windows-bash" ;;
esac
info "Detected platform: $OS"

# ---------------------------------------------------------------------------
# 2. Ask where the vault should live
# ---------------------------------------------------------------------------
DEFAULT_DEST="$HOME/Hermes Brain"
if [ -n "$DEST_ARG" ]; then
  DEST="$DEST_ARG"
else
  echo
  read -rp "Where should the vault live? [$DEFAULT_DEST]: " DEST
fi
DEST="${DEST:-$DEFAULT_DEST}"
DEST="${DEST/#\~/$HOME}"

if [ "$IS_REMOTE" = true ]; then
  if [ -e "$DEST" ] && [ -n "$(ls -A "$DEST" 2>/dev/null)" ] && [ "$TEST_MODE" = false ]; then
    warn "$DEST already exists and is not empty."
    read -rp "  Overwrite/merge into it? [y/N]: " CONFIRM
    [ "${CONFIRM,,}" = "y" ] || { echo "Aborted."; exit 1; }
  fi
  mkdir -p "$DEST"
  if command -v git >/dev/null 2>&1; then
    info "Cloning template from GitHub ($REPO_URL)..."
    git clone "$REPO_URL" "$DEST"
    ok "Cloned."
  else
    info "Downloading template archive from GitHub..."
    TMP_ZIP="$(mktemp -t hermes-brain.XXXXXX.zip 2>/dev/null || mktemp /tmp/hermes-brain.XXXXXX.zip)"
    TMP_EXTRACT="$(mktemp -d -t hermes-brain-extract.XXXXXX 2>/dev/null || mktemp -d /tmp/hermes-brain-extract.XXXXXX)"
    curl -fsSL "$ZIP_URL" -o "$TMP_ZIP"
    unzip -q "$TMP_ZIP" -d "$TMP_EXTRACT"
    cp -R "$TMP_EXTRACT/hermes-brain-template-main/"* "$DEST/"
    rm -rf "$TMP_ZIP" "$TMP_EXTRACT"
    ok "Downloaded and extracted."
  fi
else
  if [ -e "$DEST" ] && [ "$(cd "$DEST" 2>/dev/null && pwd || true)" = "$TEMPLATE_ROOT" ]; then
    info "Configuring in place at $DEST"
  else
    if [ -e "$DEST" ] && [ -n "$(ls -A "$DEST" 2>/dev/null)" ] && [ "$TEST_MODE" = false ]; then
      warn "$DEST already exists and is not empty."
      read -rp "  Overwrite/merge into it? [y/N]: " CONFIRM
      [ "${CONFIRM,,}" = "y" ] || { echo "Aborted."; exit 1; }
    fi
    mkdir -p "$DEST"
    info "Copying template to $DEST ..."
    (cd "$TEMPLATE_ROOT" && tar cf - --exclude='.git' .) | (cd "$DEST" && tar xf -)
    ok "Copied."
  fi
fi

chmod +x "$DEST/_System/Scripts/"*.sh 2>/dev/null || true
chmod +x "$DEST/_System/Scripts/Installers/"*.sh 2>/dev/null || true


# ---------------------------------------------------------------------------
# 3. Ask about the trend-digest embedding backend
# ---------------------------------------------------------------------------
echo
bold "Optional: trend-digest embeddings"
info "_System/Scripts/pipeline.sh uses Ollama (local, no Python deps beyond stdlib)."
info "_System/Scripts/trend_digest.sh uses sentence-transformers (pure Python, no Ollama)."
if [ -n "$BACKEND_ARG" ]; then
  BACKEND="$BACKEND_ARG"
else
  read -rp "Which do you want to set up now? [ollama/python/skip] (skip): " BACKEND
fi
BACKEND="${BACKEND:-skip}"

case "$BACKEND" in
  ollama)
    if command -v ollama >/dev/null 2>&1; then
      ok "Ollama found."
      if ! ollama list 2>/dev/null | grep -q nomic-embed-text; then
        read -rp "  Pull the nomic-embed-text model now? [Y/n]: " PULL
        if [ "${PULL,,}" != "n" ]; then
          ollama pull nomic-embed-text || warn "Pull failed — run 'ollama pull nomic-embed-text' manually later."
        fi
      fi
    else
      warn "Ollama not found. Install it from https://ollama.com then run:"
      info "  ollama pull nomic-embed-text"
    fi
    ;;
  python)
    PY=$(find_python || true)
    if [ -z "$PY" ]; then
      warn "No python3/python found on PATH — install Python 3 first."
    else
      if "$PY" -c "import sentence_transformers" >/dev/null 2>&1; then
        ok "sentence-transformers already installed."
      else
        read -rp "  Install sentence-transformers + numpy now via pip? [Y/n]: " PIPINSTALL
        if [ "${PIPINSTALL,,}" != "n" ]; then
          "$PY" -m pip install --quiet sentence-transformers numpy && ok "Installed." \
            || warn "pip install failed — try manually: $PY -m pip install sentence-transformers numpy"
        fi
      fi
    fi
    ;;
  *)
    info "Skipping — you can run either script manually later." ;;
esac

# ---------------------------------------------------------------------------
# 4. Obsidian check (best-effort, informational only)
# ---------------------------------------------------------------------------
echo
bold "Obsidian"
FOUND_OBSIDIAN=0
if [ "$OS" = "mac" ] && [ -d "/Applications/Obsidian.app" ]; then FOUND_OBSIDIAN=1; fi
if command -v obsidian >/dev/null 2>&1; then FOUND_OBSIDIAN=1; fi
if [ "$FOUND_OBSIDIAN" = "1" ]; then
  ok "Obsidian appears to be installed."
else
  warn "Couldn't confirm Obsidian is installed — get it from https://obsidian.md"
fi
info "Open \"$DEST\" as a vault in Obsidian, then enable: Dataview, Smart Connections,"
info "Local REST API (and brain-atlas if present) under Settings → Community Plugins."

# ---------------------------------------------------------------------------
# 5. Hermes CLI wiring (best-effort)
# ---------------------------------------------------------------------------
echo
bold "Hermes integration"
if command -v hermes >/dev/null 2>&1; then
  ok "Hermes CLI found."
  if [ "$TEST_MODE" = false ]; then
    read -rp "  Record this vault path in Hermes env as HERMES_VAULT_PATH now? [Y/n]: " SETENV
    if [ "${SETENV,,}" != "n" ]; then
      hermes config set env.HERMES_VAULT_PATH "$DEST" \
        && ok "Set env.HERMES_VAULT_PATH" \
        || warn "Couldn't set it automatically — run manually: hermes config set env.HERMES_VAULT_PATH \"$DEST\""
    fi
    echo
    bold "Hourly session-archiving cron job"
    read -rp "  Set up hourly session archiving cron job in Hermes now? [Y/n]: " SETUP_CRON
    if [ "${SETUP_CRON,,}" != "n" ]; then
      if hermes cron list 2>/dev/null | grep -q "hermes-brain-archive-hourly"; then
        ok "Cron job 'hermes-brain-archive-hourly' is already registered."
      else
        ARCHIVE_PROMPT="Run the Hermes Brain hourly session archiver. Execute: python3 \"$DEST/_System/Scripts/hourly_archive.py\". This exports Hermes chat sessions from the last hour as redacted markdown into the vault's 04-Archives/Daily/YYYY/MM/DD/ folder structure, updates 04-Archives/Daily/manifest.jsonl, extracts token usage, and appends to 04-Archives/Audit-Reports/Token-Usage.log. Report the output briefly."
        hermes cron create "0 * * * *" "$ARCHIVE_PROMPT" --name "hermes-brain-archive-hourly" \
          && ok "Created hourly archiving cron job 'hermes-brain-archive-hourly'." \
          || warn "Could not create cron job automatically — see INSTALL_PROMPT.md."
      fi
    fi
  else
    info "Test mode: skipping Hermes env and cron configuration prompts."
  fi
else
  warn "Hermes CLI not found on PATH — skipping auto-config."
  info "Once installed, run: hermes config set env.HERMES_VAULT_PATH \"$DEST\""
fi

# ---------------------------------------------------------------------------
# 6. Optional: run consolidate_memory.py once to sanity-check
# ---------------------------------------------------------------------------
if [ "$TEST_MODE" = false ]; then
  echo
  read -rp "Run _System/Scripts/consolidate_memory.py once now to verify it works? [y/N]: " RUNCONS
  if [ "${RUNCONS,,}" = "y" ]; then
    PY=$(find_python || true)
    if [ -n "$PY" ]; then
      CONS_SCRIPT="$DEST/_System/Scripts/consolidate_memory.py"
      [ -f "$CONS_SCRIPT" ] || CONS_SCRIPT="$DEST/Scripts/consolidate_memory.py"
      "$PY" "$CONS_SCRIPT" "$DEST" || warn "consolidate_memory.py reported an issue — check output above."
    else
      warn "No python3/python found — skipping."
    fi
  fi
fi

# ---------------------------------------------------------------------------
# 7. Self-test (if --test flag provided)
# ---------------------------------------------------------------------------
if [ "$TEST_MODE" = true ]; then
  echo
  bold "Running self-test..."
  
  # Test 1: Validate hourly_archive.py syntax
  PY=$(find_python || true)
  if [ -n "$PY" ]; then
    info "Test 1: Python script syntax validation..."
    SCRIPTS_DIR="$DEST/_System/Scripts"
    [ -d "$SCRIPTS_DIR" ] || SCRIPTS_DIR="$DEST/Scripts"
    NATIVE_SCRIPTS="$(to_native_path "$SCRIPTS_DIR")"
    "$PY" -c "import py_compile, sys; [py_compile.compile(f) for f in sys.argv[1:]]" \
      "$NATIVE_SCRIPTS/hourly_archive.py" "$NATIVE_SCRIPTS/consolidate_memory.py" \
      "$NATIVE_SCRIPTS/skill_forecast.py" "$NATIVE_SCRIPTS/session_tagger.py" 2>/dev/null \
      && ok "All Python scripts compile cleanly" \
      || warn "Some Python scripts have syntax errors"
    
    # Test 2: Validate manifest.jsonl structure (if exists)
    info "Test 2: Manifest structure validation..."
    MANIFEST_FILE="$DEST/04-Archives/Daily/manifest.jsonl"
    [ -f "$MANIFEST_FILE" ] || MANIFEST_FILE="$DEST/Daily/manifest.jsonl"
    if [ -f "$MANIFEST_FILE" ]; then
      if [ ! -s "$MANIFEST_FILE" ]; then
        ok "Manifest.jsonl exists (empty, ready for session archives)"
      else
        NATIVE_MANIFEST="$(to_native_path "$MANIFEST_FILE")"
        "$PY" -c "
import json, sys
errors = 0
with open(sys.argv[1], encoding='utf-8') as f:
    for i, line in enumerate(f, 1):
        line = line.strip()
        if not line:
            continue
        try:
            rec = json.loads(line)
            if 'session_id' not in rec:
                print(f'Line {i}: missing session_id')
                errors += 1
            if 'path' not in rec:
                print(f'Line {i}: missing path')
                errors += 1
        except json.JSONDecodeError as e:
            print(f'Line {i}: JSON decode error: {e}')
            errors += 1
if errors == 0:
    print('Manifest structure OK')
else:
    print(f'Manifest has {errors} errors')
    sys.exit(1)
" "$NATIVE_MANIFEST" 2>/dev/null && ok "Manifest.jsonl structure valid" || warn "Manifest.jsonl has issues"
      fi
    else
      # Test with empty manifest - just verify the file can be created
      mkdir -p "$(dirname "$MANIFEST_FILE")"
      touch "$MANIFEST_FILE"
      ok "Manifest file created (empty)"
    fi
    
    # Test 3: Check Dashboard.md exists
    info "Test 3: Dashboard file validation..."
    if [ -f "$DEST/Dashboard.md" ]; then
      ok "Dashboard.md exists"
    else
      warn "Dashboard.md not found"
    fi
    
    # Test 4: Verify required directories exist
    info "Test 4: Required directories..."
    for dir in "01-Projects" "02-Areas" "03-Resources" "04-Archives" "_System" "assets"; do
      if [ -d "$DEST/$dir" ]; then
        ok "  $dir/"
      else
        warn "  $dir/ missing"
      fi
    done
    
    # Test 5: Verify key files
    info "Test 5: Key files..."
    for file in "Welcome.md" "MOC.md" "README.md" "SETUP.md" "Dashboard.md" "INSTALL_PROMPT.md"; do
      if [ -f "$DEST/$file" ]; then
        ok "  $file"
      else
        warn "  $file missing"
      fi
    done
    
    echo
    bold "Self-test complete."
  else
    warn "No Python found — limited self-test only"
    # Basic checks without Python
    if [ -f "$DEST/Dashboard.md" ]; then ok "Dashboard.md exists"; else warn "Dashboard.md missing"; fi
    for dir in "01-Projects" "02-Areas" "03-Resources" "04-Archives" "_System"; do
      [ -d "$DEST/$dir" ] && ok "  $dir/" || warn "  $dir/ missing"
    done
  fi
fi


echo
bold "Done."
info "Vault: $DEST"
info "Read $DEST/SETUP.md and $DEST/Welcome.md for the rest."
