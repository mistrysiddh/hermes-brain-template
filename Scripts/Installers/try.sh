#!/usr/bin/env bash
# try.sh — evaluate Hermes Brain in a scratch vault, zero commitment.
#
# Copies the template into a fresh temp directory and opens it in Obsidian
# (if found), leaving your real Obsidian config, vault list, and any
# existing Hermes vault completely untouched. Nothing here is registered
# with the Hermes CLI, no cron jobs are set up — this is look-before-you-
# install only. Run install.sh instead when you're ready to keep it.
set -euo pipefail

SCRIPT_DIR="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" &>/dev/null && pwd)"
TEMPLATE_ROOT="$SCRIPT_DIR"

bold()  { printf '\033[1m%s\033[0m\n' "$1"; }
info()  { printf '  %s\n' "$1"; }
warn()  { printf '  \033[33m! %s\033[0m\n' "$1"; }
ok()    { printf '  \033[32m✓ %s\033[0m\n' "$1"; }

echo
bold "Hermes Brain — try it (scratch vault, no install)"
info "Copies the template to a temp directory you can throw away any time."
info "Doesn't touch your real Obsidian config or register anything with Hermes."
echo

SCRATCH="$(mktemp -d 2>/dev/null || mktemp -d -t 'hermes-brain-try')/Hermes Brain (try)"
mkdir -p "$SCRATCH"

info "Copying template to $SCRATCH ..."
(cd "$TEMPLATE_ROOT" && tar cf - --exclude='.git' .) | (cd "$SCRATCH" && tar xf -)
chmod +x "$SCRATCH/Scripts/"*.sh 2>/dev/null || true
ok "Copied."

echo
bold "Open it"
FOUND_OBSIDIAN=0
OPEN_CMD=""
case "$(uname -s)" in
  Darwin*)
    if [ -d "/Applications/Obsidian.app" ]; then
      FOUND_OBSIDIAN=1
      OPEN_CMD="open -a Obsidian \"$SCRATCH\""
    fi
    ;;
  Linux*)
    if command -v obsidian >/dev/null 2>&1; then
      FOUND_OBSIDIAN=1
      OPEN_CMD="obsidian \"$SCRATCH\""
    fi
    ;;
  MINGW*|MSYS*|CYGWIN*)
    if command -v obsidian >/dev/null 2>&1; then
      FOUND_OBSIDIAN=1
      OPEN_CMD="obsidian \"$SCRATCH\""
    fi
    ;;
esac

if [ "$FOUND_OBSIDIAN" = "1" ]; then
  read -rp "  Open in Obsidian now? [Y/n]: " OPENNOW
  if [ "${OPENNOW,,}" != "n" ]; then
    eval "$OPEN_CMD" &
    ok "Launched."
  fi
else
  warn "Couldn't auto-detect Obsidian on PATH."
  info "Open Obsidian manually and choose \"Open folder as vault\" -> \"$SCRATCH\""
fi

echo
bold "Done."
info "Scratch vault: $SCRATCH"
info "This is a temp copy — delete it any time with: rm -rf \"$SCRATCH\""
info "Liked it? Run ./install.sh from this template to set up a real vault."
