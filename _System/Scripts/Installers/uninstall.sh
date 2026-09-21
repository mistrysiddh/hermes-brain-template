#!/usr/bin/env bash
# uninstall.sh — cleanly remove a Hermes Brain vault installation.
# Mirrors install.sh's setup steps in reverse. Works on Linux, macOS, and
# Git Bash/WSL on Windows.
set -euo pipefail

bold()  { printf '\033[1m%s\033[0m\n' "$1"; }
info()  { printf '  %s\n' "$1"; }
warn()  { printf '  \033[33m! %s\033[0m\n' "$1"; }
ok()    { printf '  \033[32m✓ %s\033[0m\n' "$1"; }

echo
bold "Hermes Brain — vault uninstaller"
info "Reverses what install.sh set up: Hermes CLI wiring, then (optionally)"
info "the vault directory itself. Nothing is deleted without confirmation."
echo

# ---------------------------------------------------------------------------
# 1. Ask which vault to uninstall
# ---------------------------------------------------------------------------
DEFAULT_DEST="$HOME/Hermes Brain"
read -rp "Vault path to uninstall [$DEFAULT_DEST]: " DEST
DEST="${DEST:-$DEFAULT_DEST}"
DEST="${DEST/#\~/$HOME}"

if [ ! -e "$DEST" ]; then
  warn "$DEST doesn't exist — nothing to remove there."
fi

# ---------------------------------------------------------------------------
# 2. Unset HERMES_VAULT_PATH if it points at this vault
# ---------------------------------------------------------------------------
echo
bold "Hermes CLI wiring"
if command -v hermes >/dev/null 2>&1; then
  CURRENT=$(hermes config get env.HERMES_VAULT_PATH 2>/dev/null || true)
  if [ -n "$CURRENT" ] && [ "$CURRENT" = "$DEST" ]; then
    read -rp "  Unset env.HERMES_VAULT_PATH (currently set to this vault)? [Y/n]: " UNSET
    if [ "${UNSET,,}" != "n" ]; then
      hermes config unset env.HERMES_VAULT_PATH \
        && ok "Unset env.HERMES_VAULT_PATH" \
        || warn "Couldn't unset automatically — run manually: hermes config unset env.HERMES_VAULT_PATH"
    fi
  elif [ -n "$CURRENT" ]; then
    info "env.HERMES_VAULT_PATH is set to a different vault ($CURRENT) — leaving it alone."
  else
    info "env.HERMES_VAULT_PATH isn't set — nothing to unset."
  fi
else
  warn "Hermes CLI not found on PATH — skipping."
fi

# ---------------------------------------------------------------------------
# 3. Cron job cleanup
# ---------------------------------------------------------------------------
echo
bold "Cron job cleanup"
if command -v hermes >/dev/null 2>&1; then
  if hermes cron list 2>/dev/null | grep -q "hermes-brain-archive-hourly"; then
    read -rp "  Found 'hermes-brain-archive-hourly' cron job. Remove it now? [Y/n]: " RM_CRON
    if [ "${RM_CRON,,}" != "n" ]; then
      hermes cron delete "hermes-brain-archive-hourly" \
        && ok "Removed 'hermes-brain-archive-hourly' cron job." \
        || warn "Could not remove cron job automatically — run: hermes cron delete hermes-brain-archive-hourly"
    fi
  else
    info "No 'hermes-brain-archive-hourly' cron job found."
  fi
else
  info "Hermes CLI not found — if you had an hourly cron job set up, remove it via Hermes chat or CLI."
fi

# ---------------------------------------------------------------------------
# 4. Optionally delete the vault directory
# ---------------------------------------------------------------------------
echo
bold "Vault directory"
if [ -e "$DEST" ]; then
  warn "This will permanently delete: $DEST"
  warn "That includes any real chat archives, Memory-Review candidates, and"
  warn "Research notes you've accumulated — this is NOT recoverable."
  read -rp "  Type the vault path again to confirm deletion, or press Enter to keep it: " CONFIRM
  if [ "$CONFIRM" = "$DEST" ]; then
    rm -rf "$DEST"
    ok "Deleted $DEST"
  else
    info "Skipped — vault directory left in place at $DEST"
  fi
else
  info "Nothing to delete — $DEST doesn't exist."
fi

echo
bold "Done."
info "If you had this vault open in Obsidian, close that window/vault manually."
