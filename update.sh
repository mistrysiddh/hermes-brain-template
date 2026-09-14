#!/usr/bin/env bash
# update.sh — pull template updates into an already-installed Hermes Brain vault.
#
# install.sh/.ps1 do a one-shot copy with no `.git` in the destination, so
# there was previously no safe way to pull in template changes (a new
# Dashboard note, an updated bundled plugin, a fixed script) without blindly
# overwriting hand-edited files. This turns the vault into a local git repo
# tracking the template as a read-only remote, then fetches + merges —
# git's own 3-way merge surfaces conflicts on anything you edited yourself
# instead of silently clobbering it.
#
# Your personal content (Daily/, Memory-Review/*, Projects/* beyond README,
# plugin data.json, etc.) is protected the same way it always was: this
# vault's own .gitignore already excludes it, so it's never part of the
# diff/merge in the first place.
set -euo pipefail

VAULT_ROOT="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" &>/dev/null && pwd)"
TEMPLATE_URL="${1:-https://github.com/mistrysiddh/hermes-brain-template.git}"
TEMPLATE_BRANCH="${2:-main}"
REMOTE_NAME="template"

bold()  { printf '\033[1m%s\033[0m\n' "$1"; }
info()  { printf '  %s\n' "$1"; }
warn()  { printf '  \033[33m! %s\033[0m\n' "$1"; }
ok()    { printf '  \033[32m✓ %s\033[0m\n' "$1"; }

cd "$VAULT_ROOT"

echo
bold "Hermes Brain — template update"
info "Vault: $VAULT_ROOT"
info "Template: $TEMPLATE_URL (branch: $TEMPLATE_BRANCH)"
echo

# ---------------------------------------------------------------------------
# 1. First run: turn this vault into a git repo tracking the template.
# ---------------------------------------------------------------------------
if [ ! -d .git ]; then
  bold "No .git found here yet — setting one up."
  git init -q
  git checkout -b "$TEMPLATE_BRANCH" -q 2>/dev/null || git branch -m "$TEMPLATE_BRANCH"

  # Baseline commit so the merge below has something to diff against.
  # Respects the vault's existing .gitignore, so personal content never
  # enters this local history.
  git add -A
  if ! git diff --cached --quiet; then
    git commit -q -m "Snapshot before first template update"
    ok "Committed a local snapshot of your current vault state."
  else
    info "Nothing to snapshot (empty vault)."
  fi
else
  # Already a repo (either a prior run of this script, or the user cloned
  # the template directly instead of using install.sh — in that case just
  # use plain git pull, don't set up a redundant remote pointing at itself).
  EXISTING_URL="$(git remote get-url origin 2>/dev/null || true)"
  if [ "$EXISTING_URL" = "$TEMPLATE_URL" ]; then
    warn "This vault's 'origin' already IS the template repo — just run 'git pull' directly."
    exit 0
  fi

  if [ -n "$(git status --porcelain)" ]; then
    warn "You have uncommitted changes."
    read -rp "  Commit them now before updating? [Y/n]: " DOCOMMIT
    if [ "${DOCOMMIT,,}" != "n" ]; then
      git add -A
      git commit -q -m "Snapshot before template update"
      ok "Committed."
    else
      warn "Proceeding with uncommitted changes — they may conflict with the merge."
    fi
  fi
fi

# ---------------------------------------------------------------------------
# 2. Point a dedicated, read-only remote at the template.
# ---------------------------------------------------------------------------
if git remote get-url "$REMOTE_NAME" >/dev/null 2>&1; then
  git remote set-url "$REMOTE_NAME" "$TEMPLATE_URL"
else
  git remote add "$REMOTE_NAME" "$TEMPLATE_URL"
fi
# Disable push on this remote on purpose: this vault's local git history can
# contain personal-content commits even though the *files* stay gitignored
# (e.g. commit metadata, timing). Never let 'git push template' send that
# anywhere by accident.
git remote set-url --push "$REMOTE_NAME" DISABLED-see-update.sh

# ---------------------------------------------------------------------------
# 2.5. Protect user-facing scaffold files from future merge conflicts.
#
# Files like User-Profile.md ship in the template as a blank fill-in-the-blank
# note, but the moment you fill it in it becomes personal content -- same
# category as Daily/ or Memory-Review/*. Unlike those folders, this file has
# to be delivered by the template at least once (so new vaults get the blank
# scaffold), which rules out .gitignore -- an ignored path can't be added by
# a future merge either.
#
# Instead, register a local-only "ours" merge driver for these paths (see
# issue #5): on the FIRST pull the file doesn't exist locally yet, so it's
# added cleanly from the template as normal. On every pull AFTER that, if
# you've edited it (you always will, once you fill it in) and the template
# also changes its copy, git resolves the conflict by silently keeping your
# local version instead of stopping with conflict markers. This is local
# vault config only (.git/info/attributes, never synced anywhere) so it
# doesn't touch the template repo itself.
# ---------------------------------------------------------------------------
PERSONAL_SCAFFOLD_FILES=("User-Profile.md")
git config merge.ours.driver true
mkdir -p .git/info
for f in "${PERSONAL_SCAFFOLD_FILES[@]}"; do
  if ! grep -qxF "$f merge=ours" .git/info/attributes 2>/dev/null; then
    printf '%s merge=ours\n' "$f" >> .git/info/attributes
    info "Protected '$f' from future template merge conflicts (keeps your local edits)."
  fi
done

# ---------------------------------------------------------------------------
# 3. Fetch + merge.
# ---------------------------------------------------------------------------
bold "Fetching template updates..."
git fetch "$REMOTE_NAME" "$TEMPLATE_BRANCH" -q

bold "Merging..."
if git merge "$REMOTE_NAME/$TEMPLATE_BRANCH" --allow-unrelated-histories \
    -m "Merge template update ($TEMPLATE_BRANCH)"; then
  ok "Updated cleanly — no conflicts."
else
  echo
  warn "Merge produced conflicts. Resolve them, then:"
  info "  git add <resolved files>"
  info "  git commit"
  echo
  info "Conflicting files:"
  git diff --name-only --diff-filter=U | sed 's/^/    /'
  echo
  info "Tip: for files you've customized locally (e.g. .obsidian/themes/*/theme.css,"
  info ".obsidian/appearance.json), 'git checkout --ours <file>' keeps your version;"
  info "'git checkout --theirs <file>' takes the template's. See CONTRIBUTING.md."
  exit 1
fi

echo
bold "Done."
info "Re-run this script any time to pull future template updates."
