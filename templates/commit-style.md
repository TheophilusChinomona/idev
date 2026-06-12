# Commit Style — <PROJECT NAME>

The commit-style skill reads this file when writing commit messages, and the
`commit-msg` git hook enforces the subject pattern. Tune both together.

## Subject

- Format: `TICKET-ID: type(scope): imperative summary`
  - Ticket prefix: <required | optional | not used> — auto-added from the
    branch name by the `prepare-commit-msg` hook.
  - Types: feat, fix, docs, style, refactor, perf, test, build, ci, chore
  - Scope: <list your modules, e.g. auth, api, ui — or free-form>
- Max 72 characters, imperative mood ("add", not "added"), no trailing period.

## Body

- Required for anything beyond trivial changes.
- Explain **why** the change was needed; the diff shows what changed.
- Wrap at 72 columns.

## Trailers

- `Refs: TICKET-ID` when the subject has no ticket prefix.
- Co-author policy: <e.g. "Always credit pairing partners with Co-Authored-By"
  | "AI co-author trailers allowed/not allowed">

## Enforcement

- Pattern checked by `.git/hooks/commit-msg` (installed via
  `/idev:hooks install-git-hooks`).
- Custom pattern: put a POSIX ERE on line 1 of `.claude/idev/commit-pattern`,
  or set `git config idev.commitpattern '<ERE>'`.
- Ticket regex for branch-name extraction: `git config idev.ticketregex '<ERE>'`
  (default `[A-Z][A-Z0-9]+-[0-9]+`); disable auto-prefixing with
  `git config idev.ticketprefix false`. If you set a custom commit pattern,
  either allow the ticket prefix in it or disable prefixing.
