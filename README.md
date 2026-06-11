# idev — Token-Optimized Development Workflow Plugin

A Claude Code plugin packaging 27 skills, 3 agents, 4 commands, and a session-startup hook built around **generic-first design**: skill logic is universal, project knowledge lives in per-project caches that every skill regenerates by scanning whichever project it lands in (.NET/React, Django, Express, Flutter, …).

## Install & Setup

```bash
# test locally
claude --plugin-dir /path/to/idev

# then, inside each project, scaffold the per-project state:
/idev:idev-init
```

`/idev:idev-init` creates `.claude/idev/` (caches, task journal, lessons file, config templates) and offers to append the per-project policy snippet (`templates/claude-md-snippet.md`) to the project's `CLAUDE.md`.

## How it works

- **Plugin = logic** (read-only): skills, agents, scripts under the plugin install dir.
- **Project = state**: everything mutable lives in `<project>/.claude/idev/` — smart-context index, pattern caches, file index, import graph, test map, journal, lessons, session-resume state, project map, API contracts.
- **SessionStart hook** injects last-session context, pending journal tasks, and the smart-context index pointer at every session start (the old CLAUDE.md "Auto-Startup Sequence").

## Components

### Skills (27)
| Group | Skills |
|-------|--------|
| Context | smart-context, project-map, project-map-usage, file-index, function-extract, strategic-compact |
| Patterns | backend-patterns, frontend-patterns, architecture-scanner, coding-standards |
| Verification | build-check, post-creation-verify, api-contract-validation, api-validator, api-docs-sync, feature-completeness, self-review, test-map |
| Memory | lessons-learned, task-journal, session-resume, auto-learning |
| Maintenance | cache-refresh, import-graph, auto-approve-policy, idev-init |

### Agents (3)
`planner` (read-only planning specialist), `refactor-cleaner` (dead-code removal), `security-reviewer` (deep security audits).

### Commands (4)
`/idev:evolve`, `/idev:instinct-status`, `/idev:instinct-import`, `/idev:instinct-export` — the auto-learning instinct CLI (state in `~/.claude/homunculus/`).

### Optional hooks (not enabled by default)
- **auto-learning observer**: add `${CLAUDE_PLUGIN_ROOT}/skills/auto-learning/hooks/observe.sh` as a PreToolUse/PostToolUse hook in your settings to capture observations.
- **strategic-compact suggester**: add `${CLAUDE_PLUGIN_ROOT}/skills/strategic-compact/suggest-compact.sh` as a PreToolUse hook to get /compact suggestions.

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
