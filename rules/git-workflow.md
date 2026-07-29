# Git Workflow

## Commit Format

```
<type>(<scope>): <subject>

[optional body]

[optional footer]
```

Types: feat, fix, docs, style, refactor, test, chore

## Branch Strategy

- `master` — production-ready
- `feature/*` — new features
- `fix/*` — bug fixes
- `chore/*` — maintenance

## PR Process

1. Create feature branch from master
2. Make changes, commit frequently
3. Run tests before pushing
4. Create PR with description
5. Request review
6. Address feedback
7. Merge after approval
