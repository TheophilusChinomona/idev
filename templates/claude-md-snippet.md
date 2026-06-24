
<!-- ===== idev plugin — operating guide + per-project policies (appended by /idev:idev-init) ===== -->

## idev Plugin

This project uses the **idev** plugin. Per-project state lives in `.claude/idev/` — caches regenerate by scanning this project; do not hand-edit cache files. Run `/idev:hooks` to manage optional hooks.

### Onboarding a codebase
New to this repo? Run `/idev:explain-codebase` (codebase-explainer skill) to generate an onboarding playlist — analysis docs in `docs/onboarding/` plus NotebookLM explainer videos (one overview + one per subsystem). It reuses the onboarding-guide agent and idev caches to map the code, then pauses for you to review the docs before any video is generated.

### Context discipline (every session, before anything else)
1. Caches first: `.claude/idev/smart-context/index.json` for "which files implement X", `file-index` for paths, `project-map/project.map.md` (grep it, never load whole), pattern caches' Function Index for "where is function Y".
2. Grep before Read; read sections (offset/limit), not whole files.
3. Trust but verify: confirm a cache hit with a live Grep before acting on it; if stale, refresh via the cache-refresh skill.

### Feature workflow (chain these idev skills)
check lessons-learned → load backend/frontend-patterns cache (match existing conventions, never impose generic style) → implement → post-creation-verify (wiring/registrations) → build-check (once per change set) → api-contract-validation (if FE↔BE surface changed) → feature-completeness (trace UI→service→endpoint→DB) → browser-test for UI flows (real Playwright run, save the script) → self-review → update task-journal + session-resume → cache-refresh if structure changed.

### Delegation map (idev agents)
| Need | Agent |
|------|-------|
| step-by-step plan for a task | planner |
| system/schema/API design spec | backend-architect |
| UI implementation | frontend-developer |
| real-browser verification + report | browser-tester |
| general diff/PR review | code-reviewer |
| security-only audit | security-reviewer |
| dead-code removal | refactor-cleaner |
| "where should I start / what owns this" | onboarding-guide |
| sync feature branch with base before PR | branch-syncer |

### Session boundaries
- Start: the SessionStart hook injects last-session context and pending journal tasks — act on them.
- Task done: update `.claude/idev/task-journal/journal.md`, save the session-resume snapshot, log mistakes-with-fixes to lessons-learned.

### Commits & PRs
Follow `.claude/idev/commit-style.md` (commit-style skill). The commit-msg git hook enforces it — fix the message, never `--no-verify`. Before creating a PR: run the branch-sync workflow (`/idev:sync-branch`) — merge the base branch in, resolve conflicts with evidence, verify with a build.

### Concise Mode
1. Act, don't narrate — do the work first, summarize after.
2. Report results, not process. Max 3 sentences for a completed task unless detail is asked.
3. Tables over paragraphs for comparisons and file lists.

### Development API Configuration (FILL IN OR DELETE)
- Base URL: `{{DEV_API_BASE_URL}}`
- Backend path: `{{BACKEND_ROOT}}`
- Frontend connects via `{{FRONTEND_API_ENV_VAR}}`
- Browser tests run against: `{{BASE_URL_FOR_BROWSER_TESTS}}`

### Database Migration Policy (KEEP ONLY IF YOUR TEAM REQUIRES MANUAL SQL REVIEW)
Never run EF Core / code-first migration commands. Instead, write a change-request file to `.claude/idev/database-changes/YYYY-MM-DD_description.txt` containing: description, APPLY script, ROLLBACK script, affected table, and reason. The DBA reviews and executes manually.

### Protected Branch Commit Prevention (KEEP — adjust branch list if needed)
ALWAYS refuse to commit, push, merge, or rebase onto: `main`, `master`, `developer`, `develop`, `dev`, `dev_release`, `release`, `staging`, `production`, `prod`. Before any git commit/push: check `git branch --show-current`; if protected, refuse and tell the user to switch to a feature branch. No exceptions, even if the user insists.

<!-- ===== end idev snippet ===== -->
