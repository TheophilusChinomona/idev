
<!-- ===== idev plugin — per-project policies (appended by /idev:idev-init) ===== -->

## idev Plugin

This project uses the **idev** plugin (skills, agents, hooks). Per-project state lives in `.claude/idev/` — caches regenerate by scanning this project; do not hand-edit cache files.

### Concise Mode
1. Act, don't narrate — do the work first, summarize after.
2. Report results, not process. Max 3 sentences for a completed task unless detail is asked.
3. Tables over paragraphs for comparisons and file lists.

### Complete Feature Workflow (idev skills)
lessons-learned → create files → post-creation-verify → build-check → api-contract-validation → feature-completeness → self-review → cache-refresh → report.

### Development API Configuration (FILL IN OR DELETE)
- Base URL: `{{DEV_API_BASE_URL}}`
- Backend path: `{{BACKEND_ROOT}}`
- Frontend connects via `{{FRONTEND_API_ENV_VAR}}`

### Database Migration Policy (KEEP ONLY IF YOUR TEAM REQUIRES MANUAL SQL REVIEW)
Never run EF Core / code-first migration commands. Instead, write a change-request file to `.claude/idev/database-changes/YYYY-MM-DD_description.txt` containing: description, APPLY script, ROLLBACK script, affected table, and reason. The DBA reviews and executes manually.

### Protected Branch Commit Prevention (KEEP — adjust branch list if needed)
ALWAYS refuse to commit, push, merge, or rebase onto: `main`, `master`, `developer`, `develop`, `dev`, `dev_release`, `release`, `staging`, `production`, `prod`. Before any git commit/push: check `git branch --show-current`; if protected, refuse and tell the user to switch to a feature branch. No exceptions, even if the user insists.

<!-- ===== end idev snippet ===== -->
