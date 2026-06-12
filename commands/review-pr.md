---
description: Review a pull request with the code-reviewer agent — fetches the PR diff (Azure DevOps or GitHub), reviews against project conventions, and returns prioritized findings.
argument-hint: "<pr-id> [--security]"
---

# /idev:review-pr

Review a teammate's PR with prioritized, evidence-based findings.

Arguments: `$ARGUMENTS` (PR id/number; `--security` adds a security-reviewer
pass).

## Steps

1. **Detect platform** from `.claude/idev/project-config.json` `git.platform`
   or `git remote get-url origin` (dev.azure.com / *.visualstudio.com →
   Azure DevOps; github.com → GitHub).

2. **Fetch the PR locally** (the review needs surrounding code, not just
   the diff):

   Azure DevOps (azure-devops `az` extension; org/project auto-detected
   from the remote):
   ```bash
   az repos pr show --id <id> --query "{title:title, source:sourceRefName, target:targetRefName, description:description}"
   git fetch origin <sourceRefName> <targetRefName>
   git diff origin/<target>...FETCH_HEAD --stat   # FETCH_HEAD = source branch
   ```

   GitHub:
   ```bash
   gh pr view <id> --json title,baseRefName,headRefName,body
   gh pr diff <id> --name-only && git fetch origin <headRefName>
   ```

3. **Delegate to the code-reviewer agent** with: the PR title/description,
   the target branch, the changed-file list, and instructions to diff
   `origin/<target>...<source>` and review per its own rules (project
   conventions from `.claude/idev/` caches, blocker/suggestion/nit
   priorities). With `--security`, also run the security-reviewer agent on
   the same range and merge findings.

4. **Relay the report verbatim**, then offer (never auto-post) to publish
   it to the PR:
   - GitHub: `gh pr review <id> --comment --body "<report>"`.
   - Azure DevOps: the az CLI has no first-class PR-comment command;
     posting a thread requires the REST API via `az devops invoke --area git
     --resource pullRequestThreads ...`. Unless the user explicitly wants
     that, hand them the formatted review text to paste into the PR.
   Never use `az repos pr update --description` for this — it overwrites
   the PR description.
