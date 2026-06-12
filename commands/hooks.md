---
description: Manage idev's optional hooks without editing settings — show status, enable/disable the auto-learning observer and compact suggester, and install the team git commit hooks.
argument-hint: "[status|enable|disable|install-git-hooks] [observer|compact]"
---

# /idev:hooks — Hook Manager

Manage the plugin's optional hooks. They are pre-registered in the plugin's
`hooks/hooks.json` but **off by default** — each script exits instantly unless
its opt-in flag exists. Toggling a flag takes effect immediately (no restart,
no settings.json editing).

Arguments: `$ARGUMENTS`

## The toggles

| Hook | Flag file | Scope |
|------|-----------|-------|
| `observer` (auto-learning capture) | `~/.claude/homunculus/enabled` | global, all projects |
| `compact` (/compact suggestions) | `<project>/.claude/idev/compact-suggestions-enabled` | per project |

## Subcommands

### `status` (default when no arguments)

Check both flag files and report each hook as ENABLED/DISABLED, plus:
- observer: number of lines in `~/.claude/homunculus/observations.jsonl` if present, and whether the background analyzer is running (`bash "${CLAUDE_PLUGIN_ROOT}/skills/auto-learning/agents/start-observer.sh" status`)
- compact: current counter value for this session's file in the temp dir, threshold (`IDEV_COMPACT_THRESHOLD`, default 50)
- git hooks: whether `.git/hooks/commit-msg` and `.git/hooks/prepare-commit-msg` are the idev versions (check for the `# idev` marker line)

### `enable observer` / `disable observer`

```bash
mkdir -p ~/.claude/homunculus && touch ~/.claude/homunculus/enabled   # enable
rm -f ~/.claude/homunculus/enabled                                    # disable
```
On enable, remind the user: observations capture tool inputs/outputs
(secret-redacted) to `~/.claude/homunculus/`; tools can be filtered via the
plugin's `skills/auto-learning/config.json`.

### `enable compact` / `disable compact`

```bash
mkdir -p .claude/idev && touch .claude/idev/compact-suggestions-enabled   # enable
rm -f .claude/idev/compact-suggestions-enabled                            # disable
```
Run from the project root. Requires `.claude/idev/` (run `/idev:idev-init` first).

### `install-git-hooks`

Installs the team commit-message hooks into the current repo:

1. Verify this is a git repo (`git rev-parse --git-dir`); find the hooks dir
   (respect `core.hooksPath` if set).
2. For each of `prepare-commit-msg` and `commit-msg`: if a hook already exists
   and is NOT an idev hook (no `# idev` marker), do not overwrite — show the
   user both and ask how to proceed (chain it, replace it, or skip).
3. Copy from `${CLAUDE_PLUGIN_ROOT}/templates/git-hooks/` and `chmod +x` both.
4. If `.claude/idev/commit-style.md` doesn't exist, copy
   `${CLAUDE_PLUGIN_ROOT}/templates/commit-style.md` there and tell the user to
   tune it (it's the source of truth the commit-style skill reads).
5. Remind: git hooks are per-clone — teammates run `/idev:hooks install-git-hooks`
   too, or the team commits the hooks dir and sets `core.hooksPath`.

## After any change

Report the new state of all toggles (a compact status table).
