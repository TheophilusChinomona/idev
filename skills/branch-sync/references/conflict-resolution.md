# Conflict Resolution Playbook

Per-file procedure for merge conflicts during branch-sync. Work one file at
a time; resolve with evidence, never by pattern-matching on the markers.

## 1. Inspect the three-way state

```bash
git diff --name-only --diff-filter=U          # all conflicted files
git show :1:<file>   # base (common ancestor)
git show :2:<file>   # ours (feature branch)
git show :3:<file>   # theirs (incoming base branch)
git diff --base <file>                        # combined view
```

## 2. Understand intent, not just text

What was each side trying to do? Check the commits that touched the file on
each side:

```bash
git log --oneline MERGE_HEAD ^HEAD -- <file>   # their commits (incoming)
git log --oneline HEAD ^MERGE_HEAD -- <file>   # our commits (feature work)
```

Read the commit messages and, when unclear, the full diffs
(`git show <sha> -- <file>`). Resolution should preserve BOTH intents
unless they are genuinely mutually exclusive.

## 3. Resolution by conflict type

**Non-overlapping edits flagged as one hunk** (both added imports, both
added methods to the same class) → integrate both. Watch ordering rules
(import sorting, registration order).

**Same line, different values** (version numbers, config values) → the
*newer intent* usually wins, but verify: a version bump on the base branch
plus a different bump on the feature branch means take the higher/merged
result, not either side verbatim.

**Lockfiles / generated files** (`package-lock.json`, `*.csproj` asset
lists, generated clients, snapshots) → do NOT hand-merge. Take either side
to clear the markers, then regenerate with the owning tool
(`npm install`, `dotnet restore`, regenerate the client, re-run the
snapshot tests) and stage the regenerated result.

**Migrations / sequenced files** (EF migrations, Alembic, numbered SQL) →
both sides adding a migration usually means renumbering/re-scaffolding the
feature branch's migration so it comes AFTER the incoming ones. Honor the
project's migration policy from `.claude/idev/rules.md` — some teams
require DBA change-request files instead.

**Moved/renamed vs edited** (one side renamed the file, the other edited
the old path) → apply the edit at the new location; `git log --follow`
confirms the rename.

**Deleted vs modified** → find out WHY it was deleted
(`git log --diff-filter=D MERGE_HEAD -- <file>` or the rename target). If
the base branch deleted it as obsolete, port the feature edit to wherever
the functionality moved; don't resurrect dead files blindly.

**Same logic, conflicting semantics** (both sides changed the same
function's behavior differently) → this is a decision, not a merge. Stop;
show the user both versions, what each was for (from commit messages), and
a proposed combination. Do not guess.

## 4. After each file

```bash
# remove ALL markers — verify none remain:
grep -n '^<<<<<<<\|^=======\|^>>>>>>>' <file>   # must output nothing
git add <file>
```

## 5. Semantic-conflict sweep (after all files staged)

Conflicts git never flags: side A renamed a function, side B added a new
call to the old name; both sides each added the same route/DI registration
(now duplicated). After staging everything:

- Grep for identifiers that either side renamed/removed:
  `git diff HEAD MERGE_HEAD --stat` shows the hot areas.
- Check registration points (post-creation-verify skill knows the
  project's list) for duplicates.
- Then build + targeted tests — the only reliable detector.
