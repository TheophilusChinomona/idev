# Changelog

## 0.7.0 — 2026-06-12

### Added
- `templates/claude-md-snippet.md` upgraded from a policies-only snippet to
  a full per-project operating guide: cache-first context discipline, the
  skill workflow chain (including browser-test), an agent delegation map,
  session-boundary rules, and commit-style pointer — followed by the
  tunable policy sections. idev-init now replaces an existing idev snippet
  instead of appending a duplicate.
- Repo-root `CLAUDE.md` contributor guide (validation gates, frontmatter
  wiring rules, the update-everything checklist for adding/removing
  components, release procedure).

## 0.6.0 — 2026-06-12

### Added
- Code-as-action browser testing, concept adapted from Microsoft's Webwright
  (MIT — https://github.com/microsoft/Webwright): `browser-test` skill
  (write re-runnable Playwright scripts instead of imagining browser
  behavior; scripts accumulate into a per-project E2E library under
  `.claude/idev/browser-tests/`; screenshot/console/network evidence;
  app-bug-vs-script-bug failure discipline), `browser-tester` agent (runs
  the flow end-to-end and returns a structured evidence-backed report), and
  `/idev:browser-test` command. idev-init now scaffolds the browser-tests
  directories. 26 skills, 8 agents, 7 commands.

## 0.5.0 — 2026-06-12

### Added
- Four agents adapted from agency-agents (MIT, © 2025 AgentLand
  Contributors — https://github.com/msitarzewski/agency-agents):
  `backend-architect` (system/schema/API design specs, advisory read-only),
  `frontend-developer` (UI implementation driven by the frontend-patterns
  cache), `code-reviewer` (general prioritized diff review, read-only;
  complements the security-only security-reviewer), and `onboarding-guide`
  (facts-only codebase orientation and execution tracing, read-only).
  Adaptations: kebab-case names, standard frontmatter, idev cache
  integration, source-project residue removed, no fabricated-metric
  reporting. 7 agents total.

## 0.4.0 — 2026-06-12

### Added
- `skill-benchmark` skill + `/idev:benchmark-skills` command: static quality
  scorecard for every skill in a plugin (description triggers, naming rules,
  body length, examples, reference resolution) plus evaluation methodology
  (activation evals, A/B testing, multi-model targets) adapted from
  Anthropic's skill evaluation guidance. `benchmark_skills.py --strict` is
  now part of `scripts/validate.sh`, so CI fails if any skill regresses below
  10/10.

### Fixed
- Findings from the first benchmark run: trigger-bearing descriptions for
  smart-context and task-journal; example added to auto-approve-policy.
  All 25 skills now score 10/10.

## 0.3.0 — 2026-06-12

### Added
- `/idev:hooks` command: one-stop management of the optional hooks. The
  observer and compact-suggester hooks are now pre-registered in the plugin's
  `hooks/hooks.json`, guarded by opt-in flag files (off by default, near-zero
  cost when disabled) — enabling them is `/idev:hooks enable observer|compact`
  instead of hand-editing settings.json with absolute paths.
- Team commit-message tooling: `commit-style` skill (reads
  `.claude/idev/commit-style.md` so Claude writes the team format proactively)
  plus `prepare-commit-msg` / `commit-msg` git hook templates (ticket prefix
  from branch name, configurable subject validation) installed via
  `/idev:hooks install-git-hooks`.
- `/idev:idev-init` now offers a low-prompt permissions preset (exact-path
  `permissions.allow` entries for the plugin's read-only scripts and read-only
  git commands) and the git hooks install.

### Changed
- 24 skills, 5 commands. auto-learning and strategic-compact SKILL.md setup
  sections rewritten around `/idev:hooks`; manual settings wiring demoted to
  a fallback.

## 0.2.0 — 2026-06-12

Full-plugin review and repair. Headline: several advertised features were
silently non-functional and now work.

### Fixed
- `hooks/hooks.json` rewritten in the documented `{"hooks": {...}}` plugin
  format with a `startup|resume` matcher — the SessionStart hook now actually
  registers.
- auto-learning observer reads the real hook payload fields
  (`hook_event_name`, `tool_response`); observations now capture inputs and
  outputs, with secret redaction and `capture_tools`/`ignore_tools` filtering
  from `config.json`. `observe.sh` is a thin wrapper around `observe.py`.
- `instinct-cli.py`: parser no longer drops instinct bodies; import works
  non-interactively and updates in place; export escapes YAML and redacts
  paths/secrets.
- `start-observer.sh` no longer archives observations when analysis fails;
  instinct output is captured from stdout; signals fire promptly.
- strategic-compact works end to end: valid `Edit|Write` matcher, per-session
  counter, emits PostToolUse `additionalContext` JSON instead of invisible
  stderr.
- `scanner.py` prunes `node_modules`/`.git` during traversal; Next.js detected
  before React; backend detection checks one level of subdirectories.
- `ai_map_updater.py` gained a non-interactive argparse CLI; `map_watcher.py`
  skips unchanged rewrites and handles Ctrl-C.
- Function Index added to backend/frontend-patterns cache formats, fixing the
  broken dependency from function-extract and cache-refresh.

### Changed
- Consolidated 26 skills to 23: `api-validator` and `api-docs-sync` merged
  into `api-contract-validation`; `project-map-usage` merged into
  `project-map`.
- `coding-standards` cut to its security-review core; `auto-approve-policy`
  rewritten as a destructive-operation caution protocol that respects
  explicit user requests.
- Agents normalized: comma-separated `tools`, recognized frontmatter only,
  `security-reviewer` is read-only, leftover project-specific rules replaced
  with fill-in templates.
- Commands document only flags the CLI implements, with `argument-hint`.
- All mutable state unified under `<project>/.claude/idev/`.
- `session-start.sh` is silent in projects where idev isn't initialized.

### Added
- MIT `LICENSE`, `.claude-plugin/marketplace.json`, CI validation workflow,
  pytest suite, `CONTRIBUTING.md`, issue templates.

## 0.1.0 — 2026-06-12

Initial release: port of the portable `.claude` skills pack to a Claude Code
plugin (26 skills, 3 agents, 4 commands, SessionStart hook).
