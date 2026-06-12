---
description: Sync the current feature branch with the team base branch before a PR — merge base in, resolve conflicts with evidence, verify with build/tests, and report.
argument-hint: "[base-branch]"
---

# /idev:sync-branch

Prepare the current branch for a PR by merging the base branch into it.

Arguments: `$ARGUMENTS` (optional base branch; otherwise resolved from
`.claude/idev/project-config.json` `git.baseBranch`, falling back to the
first of developer/develop/main/master on origin).

## Steps

1. Delegate to the **branch-syncer** agent with the resolved base branch
   and a pointer to follow the idev:branch-sync skill.
2. Relay the agent's sync report verbatim — commits merged, per-conflict
   resolutions, verification results, rollback point, PR readiness.
3. If the agent escalated ambiguous conflicts, walk the user through each
   decision before resuming.
4. On SYNCED: offer to create the PR targeting the base branch — only on
   explicit yes. Use the platform from project config / origin URL:
   `az repos pr create` for Azure DevOps remotes, `gh pr create` for
   GitHub. Title and description per the commit-style skill's PR format.
