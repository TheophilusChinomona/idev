# Branch Sync

Sync the current feature branch with the team base branch before creating a PR.

## Steps

1. Check current branch — must not be the base branch
2. Check working tree — must be clean
3. Fetch origin
4. Merge origin/<base> --no-edit
5. If conflicts: resolve carefully, understanding both sides' intent
6. Build and test to verify merge
7. Push and report
