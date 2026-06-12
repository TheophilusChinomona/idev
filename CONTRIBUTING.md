# Contributing to idev

Thanks for your interest. A few ground rules keep the plugin maintainable.

## Design principles

1. **Plugin = logic, project = state.** Nothing in the plugin directory is
   mutable at runtime. All caches, indexes, journals, and config live in
   `<project>/.claude/idev/`.
2. **Generic-first.** Skill logic must work on any stack. Stack-specific
   knowledge belongs in per-project caches that skills regenerate by
   scanning, or in clearly-labeled illustrative examples — never as
   hardcoded rules.
3. **Honest capabilities.** Skills trigger via their `description`; they
   cannot be "always active", monitor anything, or grant permissions. Only
   hooks run automatically. Don't document behavior the runtime doesn't
   deliver, and don't reference commands or flags that don't exist.
4. **Token-frugal.** Keep SKILL.md bodies lean (target < 250 lines); move
   heavy reference material to separate files in the skill directory.

## Before you open a PR

- Run `bash scripts/validate.sh` — shell/python/JSON validation, stale-
  reference checks, skill-name consistency, version agreement.
- Run `python3 -m pytest tests/` (needs `pip install pytest`).
- If you add or remove a skill: update the README count and table, and
  check `templates/` for references.
- If you change a script's CLI surface: update the corresponding
  `commands/*.md` so docs match the implementation.
- Frontmatter: skills use `name` + `description` (plus `allowed-tools` /
  `argument-hint` where meaningful); agents use `name`, `description`,
  `tools` (comma-separated string), `model`; commands use `description` +
  `argument-hint`. Unrecognized fields are silently ignored by Claude Code —
  don't add them.

## Versioning

Semver in `.claude-plugin/plugin.json`, mirrored in
`.claude-plugin/marketplace.json` (CI enforces agreement). Add a
`CHANGELOG.md` entry for anything user-visible.
