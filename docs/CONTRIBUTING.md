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
  `git status` before committing. A CI job (**Personal Data Guard**) also
  checks this automatically on every push/PR touching those paths and will
  fail the build if it finds anything disallowed.
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

## Resolving `update.sh`/`update.ps1` merge conflicts

Since v1.8.0, `User-Profile.md` is protected by a local `merge=ours` git
attribute the update scripts set up automatically — once you've filled it
in, future template changes to that file will never conflict; your local
copy always wins silently. You shouldn't see conflicts on it anymore.

For everything else you've customized locally (most commonly
`.obsidian/appearance.json` or a bundled theme's `theme.css`, e.g. after
adding your own wallpaper or color tweaks), a real 3-way merge conflict can
still happen if the template changes the same lines. To resolve:

```bash
git checkout --ours  <file>   # keep your local version
git checkout --theirs <file>  # take the template's version instead
git add <file>
git commit
```

Then re-run `update.sh`/`update.ps1` — if origin has advanced further since
your last sync, a second pull applies cleanly.
