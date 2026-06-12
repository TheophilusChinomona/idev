---
name: commit-style
description: "Team commit-message conventions. Use when writing a commit message, committing or amending changes, or when asked about the project's commit format. Reads the per-project style from .claude/idev/commit-style.md."
---

# Commit Style — Team Commit Message Conventions

Write commit messages that pass the team's `commit-msg` hook on the first try
and read well in `git log` years later.

## Procedure

1. **Read the project's style file first**: `.claude/idev/commit-style.md`.
   If it exists, its rules override everything below. If it doesn't exist,
   apply the defaults below (and mention that `/idev:hooks install-git-hooks`
   sets up the style file + enforcement hooks).

2. **Derive the ticket ID from the branch name** when the style requires one:
   `git branch --show-current`, extract the first `ABC-123`-shaped token.
   The `prepare-commit-msg` hook does this automatically too — don't add the
   prefix twice.

3. **Write the message**:
   - Subject: `type(scope): imperative summary` — conventional-commit types
     (`feat`, `fix`, `docs`, `refactor`, `perf`, `test`, `build`, `ci`,
     `chore`), ≤ 72 chars, no trailing period.
   - Body (for anything non-trivial): the **why**, not a list of what — the
     diff already shows what. Wrap at ~72 columns.
   - Trailers last, each on its own line (`Co-Authored-By:`, `Refs:`), per
     the team's policy in the style file.

4. **Check before committing**: if `.git/hooks/commit-msg` exists, the message
   must match its pattern (default: optional `ABC-123: ` ticket prefix +
   conventional-commit subject). If the hook rejects a commit, fix the
   message — never bypass with `--no-verify` unless the user explicitly asks.

## Defaults (when no style file exists)

```
feat(auth): add refresh-token rotation

Sessions died after 15 minutes because the access token was never
refreshed. Rotate the refresh token on each renewal per OWASP.

Refs: ABC-123
```

## Anti-patterns

- "fix stuff", "wip", "updates" — the hook rejects these; so should you.
- Restating the diff in the body.
- Bundling unrelated changes to share one message — split the commits.
