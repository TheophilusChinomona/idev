# idev — Token-Optimized Development Workflow Plugin

[![validate](https://github.com/TheophilusChinomona/idev/actions/workflows/validate.yml/badge.svg)](https://github.com/TheophilusChinomona/idev/actions/workflows/validate.yml)

A Claude Code plugin packaging 26 skills, 8 agents, 7 commands, and a session-startup hook built around **generic-first design**: skill logic is universal, project knowledge lives in per-project caches that every skill regenerates by scanning the project it lands in. The scanners are strongest on .NET/React-style projects; other stacks fall back to generic heuristics.

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

`/idev:idev-init` is the one required setup step per project: it creates `.claude/idev/` (caches, task journal, lessons file, config templates) and offers to append the operating-guide snippet (`templates/claude-md-snippet.md`) to the project's `CLAUDE.md` — the always-loaded routing layer that tells Claude the cache-first context rules, the skill workflow chain, the agent delegation map, and your per-project policies. The SessionStart hook stays completely silent in projects where `.claude/idev/` doesn't exist, so nothing happens until you run it.

## How it works

Two ideas drive everything:

- **Plugin = logic, project = state.** The plugin install directory is read-only logic: skills, agents, scripts. Everything mutable lives in `<project>/.claude/idev/` — indexes, pattern caches, journal, lessons, session snapshots. Skills regenerate that state by scanning whatever project they land in, which is what makes the same plugin work across different codebases.
- **Skills load themselves; you mostly just work.** Each skill carries a description telling Claude *when* to use it ("after creating an API endpoint…", "when resuming a session…"). You don't invoke skills by name — you ask for normal dev work and the relevant skill's procedure kicks in. The only always-on piece is the SessionStart hook, which injects last-session context, pending journal tasks, and the smart-context index pointer at the start of every session (and stays silent in projects you haven't initialized).

## How to use

### 1. First session in a project

Run `/idev:idev-init` once. It creates `.claude/idev/` with the journal, lessons file, rules file, and config templates, offers to append the operating-guide snippet to your `CLAUDE.md` (how Claude should drive the plugin in this project, plus your tunable policies), and generates the smart-context index (`scanner.py` detects your stack, features, and conventions). From then on, every session starts with that context injected automatically.

### 2. Day-to-day development

Just describe tasks normally. The skills slot into four phases of the work:

**Finding things** — instead of reading whole files, Claude consults the caches first: the smart-context index for "which files implement feature X", the file index for fast path lookup, the project map (grepped, never loaded whole) for structure, and the Function Index inside the pattern caches for "where is function Y" without reading the file.

**Writing code** — `architecture-scanner` works out which layer a file belongs to; `backend-patterns` / `frontend-patterns` scan your codebase once, cache its conventions (file layout, naming, error handling, DI, API client patterns), and make new code follow *your* style rather than generic style. `coding-standards` adds security checks when code touches user input, auth, secrets, or queries.

**Verifying** — after creating files, `post-creation-verify` checks the wiring (registrations, route tables, DI containers — the stuff that compiles but doesn't run); `build-check` builds once per logical change set; `api-contract-validation` cross-checks frontend calls against backend endpoints (paths, methods, DTO shapes) and can emit contract docs; `feature-completeness` traces a feature end-to-end (UI → service → endpoint → DB) to catch dangling links; `self-review` runs a final invariant check against your project's cached patterns; `test-map` knows which tests cover which files so only the relevant ones run; `browser-test` (+ the browser-tester agent, `/idev:browser-test`) verifies UI flows with real Playwright runs — every verification script is saved to `.claude/idev/browser-tests/scripts/` so the project accumulates an E2E suite as a side effect of normal work.

**Remembering** — `task-journal` tracks in-flight work across sessions; `session-resume` snapshots state so "pick up where we left off" works; `lessons-learned` logs mistakes-with-fixes so they aren't repeated. The SessionStart hook surfaces all three next time.

Useful things to say:

| You say | What happens |
|---------|--------------|
| "continue where we left off" | session-resume + journal restore context |
| "refresh the caches" | cache-refresh re-scans whatever is stale |
| "run a self-review" | checklist pass over the diff against cached patterns |
| "validate the API contracts" | FE↔BE alignment check |
| "log that as a lesson" | appends to the lessons file with the why + fix |

### 3. Agents

For bigger jobs, delegate to the bundled subagents: **planner** (step-by-step implementation plan for a task), **backend-architect** (system/schema/API design specs before building), **frontend-developer** (implements UI following your frontend-patterns cache), **code-reviewer** (general diff review with prioritized findings), **security-reviewer** (security-only deep audit), **refactor-cleaner** (dead-code removal honoring never-remove rules), and **onboarding-guide** (facts-only codebase orientation — "where should I start", "how does a request flow"). All reviewers and the planner/architect/guide are read-only.

### 4. Auto-learning (optional)

The instinct subsystem learns reusable habits from your sessions, stored globally in `~/.claude/homunculus/` (not per-project). Turn it on with `/idev:hooks enable observer` (inputs are secret-redacted, tools filterable via `config.json`), then:

- `/idev:instinct-status` — see learned instincts and confidence levels
- `/idev:evolve` — cluster related instincts into a proposed skill/command
- `/idev:instinct-export` / `/idev:instinct-import` — share instincts between machines or teammates (export sanitizes paths/secrets)

### 5. What lives where

| Path | Contents |
|------|----------|
| `.claude/idev/smart-context/index.json` | stack, features, conventions index |
| `.claude/idev/backend-patterns/cache.md`, `frontend-patterns/cache.md` | convention caches + Function Index |
| `.claude/idev/project-map/project.map.md` | annotated file map (grep it, don't load it) |
| `.claude/idev/file-index/`, `import-graph/`, `test-map/` | lookup indexes |
| `.claude/idev/journal.md`, `lessons.md`, `session-resume/` | cross-session memory |
| `.claude/idev/api-contract-validation/`, `api-contracts/` | API alignment cache + generated docs |
| `.claude/idev/rules.md`, `project-config.json` | per-project policies the skills read |
| `~/.claude/homunculus/` | global auto-learning instincts (all projects) |

Delete any cache and the owning skill regenerates it on next use; `.claude/idev/` is safe to gitignore or commit, whichever your team prefers (committing shares warm caches).

## Components

### Skills (26)
| Group | Skills |
|-------|--------|
| Context | smart-context, project-map, file-index, function-extract, strategic-compact |
| Patterns | backend-patterns, frontend-patterns, architecture-scanner, coding-standards, commit-style |
| Verification | build-check, post-creation-verify, api-contract-validation, feature-completeness, self-review, test-map, browser-test |
| Memory | lessons-learned, task-journal, session-resume, auto-learning |
| Maintenance | cache-refresh, import-graph, auto-approve-policy, idev-init, skill-benchmark |

### Agents (7)
| Agent | Role |
|-------|------|
| planner | read-only implementation planning for a specific task |
| backend-architect | system design specs: decomposition, schemas, API contracts, migrations (advisory, read-only) |
| frontend-developer | UI implementation following the project's frontend-patterns cache |
| code-reviewer | general diff/PR review — correctness, maintainability, performance, tests (read-only) |
| security-reviewer | security-only deep audit (read-only) |
| refactor-cleaner | dead-code removal honoring project never-remove rules |
| onboarding-guide | facts-only codebase orientation and execution-path tracing (read-only) |
| browser-tester | code-as-action browser verification: writes/runs Playwright scripts, reports with screenshot + console evidence |

backend-architect, frontend-developer, code-reviewer, and onboarding-guide are adapted from [agency-agents](https://github.com/msitarzewski/agency-agents) (MIT, © 2025 AgentLand Contributors).

### Commands (7)
`/idev:hooks` — manage the optional hooks and team git hooks (status/enable/disable/install-git-hooks).
`/idev:benchmark-skills` — static quality scorecard for every skill in this (or any) plugin; CI enforces all checks via `--strict`.
`/idev:browser-test` — verify a feature or flow with a real Playwright run; structured report with screenshot/console evidence.
`/idev:evolve`, `/idev:instinct-status`, `/idev:instinct-import`, `/idev:instinct-export` — the auto-learning instinct CLI (state in `~/.claude/homunculus/`).

### Optional hooks — managed by `/idev:hooks`, off by default

The auto-learning observer and the strategic-compact suggester are pre-registered in the plugin's own `hooks/hooks.json`, guarded by opt-in flag files so they cost ~nothing until enabled. No settings.json editing:

```
/idev:hooks                       # status of all toggles
/idev:hooks enable observer       # capture session observations (global)
/idev:hooks enable compact        # /compact suggestions (per project)
/idev:hooks install-git-hooks     # team commit-message hooks (see below)
```

### Team commit messages

`/idev:hooks install-git-hooks` installs two git hooks into the repo: `prepare-commit-msg` (auto-prefixes the ticket ID parsed from the branch name) and `commit-msg` (validates the subject against the team pattern — default: optional `ABC-123:` prefix + conventional commits, configurable via `.claude/idev/commit-pattern` or `git config idev.commitpattern`). The `commit-style` skill reads `.claude/idev/commit-style.md` so Claude writes conforming messages proactively; the git hooks enforce the same format for every teammate, with or without Claude.

### Fewer permission prompts

`/idev:idev-init` offers to add a `permissions.allow` preset to the project's `.claude/settings.json`: exact-path allowances for the plugin's read-only scripts (scanner, instinct CLI, map generator) plus read-only git (`status`, `diff`, `log`, `branch`). Bundled agents' Read/Grep/Glob tools never prompt — prompts come from Bash invocations, which is what the preset removes. Nothing broad is ever added (no blanket `python3` allowance).

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
