# idev plugin — contributor guide

This repo IS the plugin (logic only — nothing here is mutable at runtime;
per-project state lives in each project's `.claude/idev/`).

## Before every commit
- `bash scripts/validate.sh` — shell/python/JSON validation, stale-reference
  grep, skill-name↔dir consistency, plugin/marketplace version agreement,
  hook script existence, and the skill benchmark in `--strict` mode (every
  skill must score 10/10).
- `python3 -m pytest tests/` — keep all tests green.
- Follow `CONTRIBUTING.md`: plugin=logic/project=state, generic-first (no
  stack- or project-specific rules stated as universal), honest capabilities
  (never document behavior the runtime doesn't deliver, no phantom commands
  or flags), token-frugal (SKILL.md target < 250 lines).

## Wiring rules (things that silently break)
- Frontmatter: skills = `name` + `description` (+ `allowed-tools`/
  `argument-hint`); agents = `name`, `description`, `tools` (comma-separated
  string), `model`; commands = `description` + `argument-hint`. Anything
  else is silently ignored — don't add it.
- Skill descriptions need "Use when..." trigger phrasing (benchmark check).
- `${CLAUDE_PLUGIN_ROOT}` expands ONLY in this repo's `hooks/hooks.json` —
  never tell users to put it in their settings.json.
- Optional hooks (observer, compact) are pre-registered in `hooks/hooks.json`
  but flag-guarded; toggles live in `/idev:hooks` (commands/hooks.md).
- If a command documents a CLI flag, `instinct-cli.py` (or the relevant
  script) must actually implement it.

## Adding/removing components
Update ALL of: README counts + tables, `CHANGELOG.md`, version in BOTH
`.claude-plugin/plugin.json` and `.claude-plugin/marketplace.json` (CI
enforces agreement), and `templates/claude-md-snippet.md` if the workflow
chain or delegation map changed. Third-party adaptations keep MIT
attribution in-file, in the README, and in the changelog.

## Releases
Tag `vX.Y.Z` matching plugin.json, push with `--follow-tags`, `gh release
create`. Branch protection on `master` requires the `validate` check for
PRs; admin direct pushes bypass it but CI still runs post-push — check it.
