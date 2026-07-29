# idev — Token-Optimized Development Workflow Plugin

[![validate](https://github.com/TheophilusChinomona/idev/actions/workflows/validate.yml/badge.svg)](https://github.com/TheophilusChinomona/idev/actions/workflows/validate.yml)

A Claude Code plugin packaging 31 skills, 15 agents, 18 commands, and a session-startup hook built around **generic-first design**: skill logic is universal, project knowledge lives in per-project caches that every skill regenerates by scanning the project it lands in. The scanners are strongest on .NET/React-style projects; other stacks fall back to generic heuristics. Includes SkillOpt integration for benchmarking and optimizing skills. Five older skills (architecture-scanner, file-index, import-graph, test-map, post-creation-verify) are deprecated and retained for backwards compatibility only.

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

**Finding things** — instead of reading whole files, Claude consults the caches first: the smart-context index for "which files implement feature X", the project map (grepped, never loaded whole) for structure, and the Function Index inside the pattern caches for "where is function Y" without reading the file.

**Writing code** — `backend-patterns` / `frontend-patterns` scan your codebase once, cache its conventions (file layout, naming, error handling, DI, API client patterns), and make new code follow *your* style rather than generic style. `coding-standards` adds security checks when code touches user input, auth, secrets, or queries.

**Verifying** — `db-preflight` catches unapplied database migrations before builds; `build-check` builds once per logical change set (including targeted test mapping); `api-contract-validation` discovers and validates API endpoint alignment; `feature-completeness` traces a feature end-to-end (UI → service → endpoint → DB) to catch dangling links; `self-review` runs a final invariant check against your project's cached patterns; `browser-test` (+ the browser-tester agent, `/idev:browser-test`) verifies UI flows with real Playwright runs — every verification script is saved…

**Remembering** — `task-journal` tracks in-flight work across sessions (integrating with the remember plugin for session persistence); `session-resume` snapshots state so "pick up where we left off" works (proactively prompts to save at natural stopping points); `lessons-learned` logs mistakes-with-fixes so they aren't repeated. The SessionStart hook surfaces all three next time.

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
| `.claude/idev/db-preflight/applied.json` | tracks applied DBScripts to prevent schema 500s |
| `.claude/idev/task-journal/journal.md`, `lessons-learned/lessons.md` | cross-session task log and gotcha reference |
| `.claude/idev/session-resume/last-session.json` | session snapshot for seamless resumption |
| `.claude/idev/api-contract-validation/cache.json` | API endpoint discovery cache |
| `.claude/idev/rules.md`, `project-config.json` | per-project policies the skills read |
| `~/.claude/homunculus/` | global auto-learning instincts (all projects) |

Delete any cache and the owning skill regenerates it on next use; `.claude/idev/` is safe to gitignore or commit, whichever your team prefers (committing shares warm caches).

## Components
### Skills (33 active + 5 deprecated)
| Group | Active Skills |
|-------|---------------|
| Context | smart-context, project-map, function-extract, strategic-compact, context-switching |
| Patterns | backend-patterns, frontend-patterns, coding-standards, commit-style, branch-sync |
| Verification | build-check (includes test mapping), api-contract-validation, feature-completeness, self-review, browser-test, browse, pre-ship-verify, skillopt, tdd-workflow, eval-harness, test-coverage |
| Memory | lessons-learned, task-journal, session-resume, auto-learning, continuous-learning |
| Maintenance | cache-refresh, auto-approve-policy, idev-init, skill-benchmark, env-preflight, db-preflight |
| Onboarding | codebase-explainer |

**Deprecated** (retained for backwards compatibility): architecture-scanner, file-index, import-graph, test-map, post-creation-verify

### Agents (16)
| Agent | Role |
|-------|------|
| planner | read-only implementation planning for a specific task |
| backend-architect | system design specs: decomposition, schemas, API contracts, migrations (advisory, read-only) |
| frontend-developer | UI implementation following the project's frontend-patterns cache |
| code-reviewer | general diff/PR review — correctness, maintainability, performance, tests (read-only) |
| security-reviewer | security-only deep audit (read-only) |
| refactor-cleaner | dead-code removal honoring project never-remove rules |
| onboarding-guide | facts-only codebase orientation and execution-path tracing (read-only) |
| browser-qa | interactive browser QA via xd://browser — snapshot, interact by @ref, screenshot, console checks. Quick verification without writing scripts |
| browser-tester | code-as-action browser verification: writes/runs Playwright scripts, reports with screenshot + console evidence |
| branch-syncer | merges the base branch into the feature branch before a PR; evidence-based conflict resolution + build/test verification |
| skill-optimizer | runs SkillOpt benchmarks on a skill, analyzes failures, proposes improvements |
| benchmark-runner | executes SkillOpt evals across multiple skills, produces comparative scorecard |
| db-migration-auditor | scans DBScripts, checks applied status, reports missing migrations |
| tdd-guide | test-driven development specialist — enforces write-tests-first workflow |
| build-error-resolver | build and type error resolution — fixes errors with minimal diffs |
| doc-updater | keeps documentation in sync with code changes |

backend-architect, frontend-developer, code-reviewer, and onboarding-guide are adapted from [agency-agents](https://github.com/msitarzewski/agency-agents) (MIT, © 2025 AgentLand Contributors).

### Commands (20)
`/idev:hooks` — manage optional hooks and team git hooks (status/enable/disable/install-git-hooks).
`/idev:benchmark-skills` — static quality scorecard for every skill; CI enforces all checks via `--strict`.
`/idev:browser-test` — verify a feature or flow with a real Playwright run; report with screenshot/console evidence.
`/idev:browse` — open interactive browser QA via xd://browser; snapshot, ref interaction, screenshots.
`/idev:sync-branch` — merge base branch into feature branch before a PR; conflict resolution + verification.
`/idev:upgrade` — reconcile project `.claude/idev/` state with installed plugin version.
`/idev:update` — update the idev plugin from GitHub; pulls code, reinstalls, runs upgrade.
`/idev:skillopt` — benchmark and optimize a skill using Microsoft SkillOpt via Codex.
`/idev:review-pr` — fetch and review a PR with the code-reviewer agent; optional `--security` pass.
`/idev:explain-codebase` — turn a repo into an onboarding playlist with analysis docs and NotebookLM videos.
`/idev:context [dev|review|research]` — switch development modes by loading the appropriate context.
`/idev:eval define|check|report <feature>` — manage capability and regression evals with pass@k metrics.
`/idev:test-coverage [--threshold N]` — measure and report test coverage.
`/idev:update-docs [--check]` — synchronize documentation with current code.
`/idev:orchestrate <workflow> <task>` — chain agents in sequence (feature, bugfix, refactor, security).
`/idev:complete-ticket <ticket-id>` — generate ticket completion report with test steps and DevOps link.
`/idev:evolve` — cluster related instincts into reusable skills or commands.
`/idev:instinct-status` — show learned instincts with confidence levels, grouped by domain.
`/idev:instinct-export [--domain <name>]` — export learned instincts to a shareable file.
`/idev:instinct-import <file-or-url>` — import instincts from a teammate's export.

### Git platform support

PR-touching features (sync-branch, review-pr, PR creation offers) detect the platform from the origin URL — `dev.azure.com`/`*.visualstudio.com` → Azure DevOps (`az repos`, requires the `azure-devops` az extension), `github.com` → GitHub (`gh`) — or set `git.platform` explicitly in `.claude/idev/project-config.json`.
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
db-preflight → lessons-learned → create files → build-check
→ api-contract-validation → feature-completeness → self-review → cache-refresh
```

## Team rollout

To give every teammate idev automatically, commit this to the work repo's `.claude/settings.json` (project scope — verified against the official plugin-marketplaces docs):

```json
{
  "extraKnownMarketplaces": {
    "idev": { "source": { "source": "github", "repo": "TheophilusChinomona/idev" } }
  },
  "enabledPlugins": { "idev@idev": true }
}
```

Behavior: when a teammate opens (and trusts) the project, Claude Code prompts once to install the marketplace, then enables the plugin; declining is remembered per user. Updates ship when this repo's `plugin.json` version bumps — not per commit. Teammates need git access to github.com for the install; if the work network blocks GitHub, vendor a checkout and use `{"source": "directory", "path": "./tools/idev"}` instead.

Per-project setup remains: one person runs `/idev:idev-init` (committing `.claude/idev/` shares the warm caches — add `.claude/idev/browser-tests/artifacts/` to .gitignore either way), and each clone runs `/idev:hooks install-git-hooks` for the commit hooks (git hooks are per-clone).

## Windows support

The hook and git-hook scripts are bash. On Windows, install **Git for Windows** (puts `bash`, `grep`, `awk` on PATH — the SessionStart hook, observer, compact suggester, and commit hooks then work under Git Bash; the compact suggester also ships a native `.ps1`). Two caveats:
- Commands document `python3` — on Windows substitute `python` (or the `py` launcher).
- The auto-learning background analyzer (`start-observer.sh`) is Unix-only (PID files/signals); observation capture itself works everywhere.

## Quality & measurements

- `docs/token-footprint.md` — measured always-loaded cost (~1.7k tokens of skill metadata + ~850 snippet) vs on-demand bodies; re-baseline with `benchmark_skills.py --footprint`.
- `docs/evals/` — activation eval reports (latest: 31/35 strict TP, 0/15 FP across 5 key skills, offline routing simulation).
- CI enforces the 10-check skill benchmark at 10/10 for every skill on every push.

## Philosophy

1. Every prompt starts with the caches — index/map summaries instead of full file reads.
2. Grep before Read — locate, then read only the needed section.
3. Caches regenerate, logic doesn't change — drop into a new project and rescan.
4. If a skill would break in a different stack, that's a bug in the skill — fix the skill, not the cache.
