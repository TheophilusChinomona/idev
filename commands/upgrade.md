---
description: Reconcile this project's .claude/idev/ state with the currently installed plugin version — add missing directories and config keys, refresh the CLAUDE.md snippet, and update stale idev git hooks, without touching caches or user content.
argument-hint: "[--dry-run]"
---

# /idev:upgrade

Bring a project initialized under an older idev version up to date with the
installed plugin. Never touches caches, journal, lessons, or any
user-authored content.

Arguments: `$ARGUMENTS` (`--dry-run`: report drift, change nothing).

## Steps

1. **Versions**: read the installed version from
   `${CLAUDE_PLUGIN_ROOT}/.claude-plugin/plugin.json` and the project's
   `.claude/idev/.idev-version` (treat missing as "pre-0.9.0"). If equal,
   report "up to date" and stop.

2. **Directory drift**: run the `mkdir -p` from idev-init step 2 — it is
   idempotent and only creates what's missing. Report which directories
   were added.

3. **Config drift** (merge, never overwrite values):
   - `.claude/idev/project-config.json`: add keys that exist in
     `${CLAUDE_PLUGIN_ROOT}/templates/project-config.json` but not in the
     project's copy (e.g. the `git` section). Preserve every existing
     value. List added keys and tell the user which need filling in.
   - `.claude/idev/commit-style.md` missing → copy from templates.

4. **CLAUDE.md snippet**: if the project's CLAUDE.md contains the
   `===== idev plugin` marker, compare against
   `${CLAUDE_PLUGIN_ROOT}/templates/claude-md-snippet.md`. If the guide
   sections differ, replace the snippet block — but first extract any
   user-tuned policy values (API config, branch list, migration policy)
   from the old block and re-apply them to the new one. Show the diff
   before writing.

5. **Git hooks**: for `prepare-commit-msg` and `commit-msg` in the repo's
   hooks dir that carry the `# idev` marker, diff against
   `${CLAUDE_PLUGIN_ROOT}/templates/git-hooks/`. If stale, reinstall
   (chmod +x). Never touch non-idev hooks.

6. **Stamp**: write the installed version to `.claude/idev/.idev-version`.

7. **Report**: table of component → action taken (added / merged /
   replaced / up-to-date / skipped), plus anything needing user input.
   With `--dry-run`, the same table with proposed actions only.
