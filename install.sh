#!/usr/bin/env bash
# install.sh — interactive installer for the Hermes Brain vault template.
# Works on Linux, macOS, and Git Bash/WSL on Windows.
set -euo pipefail

SCRIPT_DIR="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" &>/dev/null && pwd)"
TEMPLATE_ROOT="$SCRIPT_DIR"

bold()  { printf '\033[1m%s\033[0m\n' "$1"; }
info()  { printf '  %s\n' "$1"; }
warn()  { printf '  \033[33m! %s\033[0m\n' "$1"; }
ok()    { printf '  \033[32m✓ %s\033[0m\n' "$1"; }

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
echo
read -rp "Where should the vault live? [$DEFAULT_DEST]: " DEST
DEST="${DEST:-$DEFAULT_DEST}"
DEST="${DEST/#\~/$HOME}"

if [ -e "$DEST" ] && [ "$(cd "$DEST" 2>/dev/null && pwd || true)" = "$TEMPLATE_ROOT" ]; then
  info "Installing in place at $DEST"
else
  if [ -e "$DEST" ]; then
    warn "$DEST already exists."
    read -rp "  Overwrite/merge into it? [y/N]: " CONFIRM
    [ "${CONFIRM,,}" = "y" ] || { echo "Aborted."; exit 1; }
  fi
  mkdir -p "$DEST"
  info "Copying template to $DEST ..."
  # Copy everything except this installer's own working artifacts.
  (cd "$TEMPLATE_ROOT" && tar cf - --exclude='.git' .) | (cd "$DEST" && tar xf -)
  ok "Copied."
fi

chmod +x "$DEST/Scripts/"*.sh 2>/dev/null || true

# ---------------------------------------------------------------------------
# 3. Ask about the trend-digest embedding backend
# ---------------------------------------------------------------------------
echo
bold "Optional: trend-digest embeddings"
info "Scripts/pipeline.sh uses Ollama (local, no Python deps beyond stdlib)."
info "Scripts/trend_digest.sh uses sentence-transformers (pure Python, no Ollama)."
read -rp "Which do you want to set up now? [ollama/python/skip] (skip): " BACKEND
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
    PY=$(command -v python3 || command -v python || true)
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
  read -rp "  Record this vault path in Hermes env as HERMES_VAULT_PATH now? [Y/n]: " SETENV
  if [ "${SETENV,,}" != "n" ]; then
    hermes config set env.HERMES_VAULT_PATH "$DEST" \
      && ok "Set env.HERMES_VAULT_PATH" \
      || warn "Couldn't set it automatically — run manually: hermes config set env.HERMES_VAULT_PATH \"$DEST\""
  fi
  info "Next: point your session-archive cron job's output root at this path,"
  info "and see SETUP.md step 4 for the Daily/ export convention it expects."
else
  warn "Hermes CLI not found on PATH — skipping auto-config."
  info "Once installed, run: hermes config set env.HERMES_VAULT_PATH \"$DEST\""
fi

# ---------------------------------------------------------------------------
# 6. Optional: run consolidate_memory.py once to sanity-check
# ---------------------------------------------------------------------------
echo
read -rp "Run Scripts/consolidate_memory.py once now to verify it works? [y/N]: " RUNCONS
if [ "${RUNCONS,,}" = "y" ]; then
  PY=$(command -v python3 || command -v python || true)
  if [ -n "$PY" ]; then
    "$PY" "$DEST/Scripts/consolidate_memory.py" "$DEST" || warn "consolidate_memory.py reported an issue — check output above."
  else
    warn "No python3/python found — skipping."
  fi
fi

echo
bold "Done."
info "Vault: $DEST"
info "Read $DEST/SETUP.md and $DEST/Welcome.md for the rest."
