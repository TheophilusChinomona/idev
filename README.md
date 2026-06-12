# idev — Token-Optimized Development Workflow Plugin

[![validate](https://github.com/TheophilusChinomona/idev/actions/workflows/validate.yml/badge.svg)](https://github.com/TheophilusChinomona/idev/actions/workflows/validate.yml)

A Claude Code plugin packaging 23 skills, 3 agents, 4 commands, and a session-startup hook built around **generic-first design**: skill logic is universal, project knowledge lives in per-project caches that every skill regenerates by scanning the project it lands in. The scanners are strongest on .NET/React-style projects; other stacks fall back to generic heuristics.

## Install & Setup

From GitHub (inside Claude Code):

```
/plugin marketplace add TheophilusChinomona/idev
/plugin install idev@idev
```

Or test a local checkout:

```bash
claude --plugin-dir /path/to/idev
```

Then, inside each project, scaffold the per-project state:

```
/idev:idev-init
```

`/idev:idev-init` is the one required setup step per project: it creates `.claude/idev/` (caches, task journal, lessons file, config templates) and offers to append the per-project policy snippet (`templates/claude-md-snippet.md`) to the project's `CLAUDE.md`. The SessionStart hook stays completely silent in projects where `.claude/idev/` doesn't exist, so nothing happens until you run it.

## How it works

- **Plugin = logic** (read-only): skills, agents, scripts under the plugin install dir.
- **Project = state**: everything mutable lives in `<project>/.claude/idev/` — smart-context index, pattern caches, file index, import graph, test map, journal, lessons, session-resume state, project map, API contracts.
- **SessionStart hook** injects last-session context, pending journal tasks, and the smart-context index pointer at every session start (the old CLAUDE.md "Auto-Startup Sequence").

## Components

### Skills (23)
| Group | Skills |
|-------|--------|
| Context | smart-context, project-map, file-index, function-extract, strategic-compact |
| Patterns | backend-patterns, frontend-patterns, architecture-scanner, coding-standards |
| Verification | build-check, post-creation-verify, api-contract-validation, feature-completeness, self-review, test-map |
| Memory | lessons-learned, task-journal, session-resume, auto-learning |
| Maintenance | cache-refresh, import-graph, auto-approve-policy, idev-init |

### Agents (3)
`planner` (read-only planning specialist), `refactor-cleaner` (dead-code removal), `security-reviewer` (deep security audits).

### Commands (4)
`/idev:evolve`, `/idev:instinct-status`, `/idev:instinct-import`, `/idev:instinct-export` — the auto-learning instinct CLI (state in `~/.claude/homunculus/`).

### Optional hooks (not enabled by default)
- **auto-learning observer**: add `skills/auto-learning/hooks/observe.sh` as a PreToolUse/PostToolUse hook in your settings to capture observations.
- **strategic-compact suggester**: add `skills/strategic-compact/suggest-compact.sh` as a PostToolUse hook with matcher `"Edit|Write"` to get /compact suggestions.

Note: `${CLAUDE_PLUGIN_ROOT}` only expands inside the plugin's own `hooks/hooks.json` — it does **not** expand in your user/project `settings.json`. When wiring these up in settings, use the absolute path to the plugin install directory instead.

## Workflow

The canonical feature workflow chained from the skills:

```
lessons-learned → create files → post-creation-verify → build-check
→ api-contract-validation → feature-completeness → self-review → cache-refresh
```

## Philosophy

1. Every prompt starts with the caches — index/map summaries instead of full file reads.
2. Grep before Read — locate, then read only the needed section.
3. Caches regenerate, logic doesn't change — drop into a new project and rescan.
4. If a skill would break in a different stack, that's a bug in the skill — fix the skill, not the cache.
