# Contributing

Thanks for considering a contribution to this template.

## What's welcome

- Fixes to `install.sh` / `install.ps1` for platforms/edge cases they don't
  handle yet (different shells, package managers, Obsidian install paths)
- New or improved Obsidian plugin recipes documented in `SETUP.md`
- Additional automation scripts (equivalent additions belong in both
  PowerShell and bash where practical — see `Scripts/` for the current pairs)
- Documentation clarity fixes

## What NOT to contribute

- **Never** open a PR containing real vault content — chat exports, personal
  `Memory-Review` entries, populated `Research/` notes, `.smart-env/` caches,
  or any `.obsidian/plugins/*/data.json`. These are git-ignored on purpose;
  if your local vault has diverged and picked any of these up, check
  `git status` before committing.
- API keys, tokens, or credentials of any kind, even example/placeholder
  ones that look real enough to be reused by mistake.

## Before submitting

1. Test both the Linux/macOS and Windows install paths if you touched
   `install.sh`/`install.ps1` or anything in `Scripts/`.
2. For shell scripts: `bash -n script.sh` to catch syntax errors.
3. For PowerShell scripts: run them through the PowerShell parser
   (`[System.Management.Automation.Language.Parser]::ParseFile(...)`) or just
   execute with `-WhatIf`/dry-run where applicable.
4. Keep the folder skeleton generic — no hardcoded personal paths (use
   `$PSScriptRoot`/`$(dirname "${BASH_SOURCE[0]}")`-relative resolution, as
   the existing scripts do).

## Questions first?

Use [Discussions](../../discussions) instead of an issue if you're not sure
something is a bug versus a design choice.
