---
name: branch-sync
description: "Syncs the current feature branch with the team base branch (merge base into feature) before creating a PR, resolving merge conflicts safely with build/test verification. Use when preparing a branch for a PR, when asked to sync with or merge in the base/developer branch, when a PR shows conflicts, or before pushing a long-lived feature branch."
---

# Branch Sync — Merge Base Into Feature Before PR

Team workflow: everyone works on their own branch; before a PR into the base
branch, merge the base branch INTO the feature branch so the PR contains
everything current. The risky part is conflict resolution — do it with
evidence, then prove the merge with a build.

## Configuration

Base branch resolution order:
1. Explicit argument from the user
2. `.claude/idev/project-config.json` → `git.baseBranch`
3. First of `developer`, `develop`, `main`, `master` that exists on
   `origin` (`git ls-remote --heads origin <name>`)

Strategy: `git.syncStrategy` in project config — `merge` (default) or
`rebase`. Never rebase unless the project config says so.

## Procedure

### 1. Pre-flight (abort if any fails)
```bash
git branch --show-current     # must NOT be the base/protected branch
git status --porcelain        # must be clean
git fetch origin
```
- On the base branch itself → stop; this skill syncs feature branches.
- Dirty tree → surface the uncommitted files to the user: commit them
  (commit-style skill) or stash (`git stash push -u -m "pre-sync"`) per
  their choice — never silently stash.
- Record the rollback point: `git rev-parse HEAD`.

### 2. Merge
```bash
git merge origin/<base> --no-edit
```
- Clean merge → go to step 4.
- Conflicts → step 3. Never `git checkout --ours/--theirs` wholesale.

### 3. Resolve conflicts (the careful part)
List them: `git diff --name-only --diff-filter=U`. For each file follow
`${CLAUDE_PLUGIN_ROOT}/skills/branch-sync/references/conflict-resolution.md`
— three-way inspection, intent analysis of both sides, special cases
(lockfiles, migrations, generated files). Core rules:
- Understand BOTH sides' intent before resolving (what was each change
  for?), integrate both unless they are genuinely exclusive.
- Generated/lock files: don't hand-merge — regenerate with the tool.
- If both sides changed the same logic and the correct combination is
  ambiguous → stop and ask the user; show both diffs and the options.
- Stage each resolved file; when all staged: `git commit --no-edit`
  (keep the default merge message).

### 4. Verify the merge (mandatory)
A compiling merge can still be semantically broken (both sides "won").
- Build once (build-check skill conventions).
- Run the tests relevant to conflicted/changed files (test-map skill).
- Failures introduced by the merge → fix before declaring the sync done;
  failures that pre-date the sync → report, don't hide.

### 5. Push and report
```bash
git push origin <feature-branch>    # plain push; merge never needs force
```
Report: base branch + commits merged in (`git log --oneline <old-head>..HEAD`
summary), conflicts resolved per file with one-line rationale, verification
results (actual output), and PR readiness. Offer to create the PR — don't
create it unasked. Platform from `git.platform` in project config, or detect
from `git remote get-url origin`:

```bash
# Azure DevOps (dev.azure.com / *.visualstudio.com) — needs the azure-devops
# az extension; org/project/repo auto-detected from the git remote:
az repos pr create --source-branch <feature> --target-branch <base> \
  --title "<commit-style title>" --description "<PR body per commit-style skill>"

# GitHub:
gh pr create --base <base> --title "..." --body "..."
```

## Recovery

- Mid-merge mess: `git merge --abort` returns to the pre-merge state.
- Post-merge regret (not pushed): `git reset --hard <recorded-rollback-sha>`
  — destructive; confirm with the user first.
- NEVER force-push to recover; ask the user when in doubt.

## Anti-patterns

- Resolving by accepting one whole side ("ours/theirs") to make the
  conflict markers go away — silently discards teammates' work.
- Syncing with a dirty tree, or stashing without telling the user.
- Declaring the sync done without a post-merge build/test run.
- Rebasing a shared branch when team policy is merge (rewrites pushed
  history → force-push → breaks teammates).
