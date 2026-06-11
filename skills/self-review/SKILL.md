---
name: self-review
description: Code-quality checklist run on Claude's own output before reporting done: unused imports, missing error handling, naming consistency, security issues. Use after completing any code changes.
---

# Self-Review Skill

## Purpose
Automated code review checklist that Claude runs on its own output before reporting "done." Catches unused imports, missing null checks, inconsistent naming, and other common issues that a human reviewer would flag.

## Activation
- After completing any code creation or modification task
- Before reporting to the user that work is done
- Run AFTER build-check passes (no point reviewing code that doesn't compile)

---

## How It Works

This is a checklist-based technique, not a scanner. After writing code, Claude re-reads its own output and checks each item. No cache needed.

---

## Phase 1: Universal Checks (All Languages)

Run these on every file created or modified:

```
□ No unused imports/usings — every import is used in the file
□ No unused variables — every declared variable is referenced
□ No hardcoded strings that should be constants — magic numbers, URLs, messages
□ No console.log/print statements left from debugging
□ No commented-out code blocks left behind
□ No TODO/FIXME/HACK comments added without being tracked in task-journal
□ Consistent naming — follows project convention (PascalCase, camelCase, snake_case)
□ File naming matches project convention
□ Exports match project convention (default vs named)
□ No duplicate code — if same logic exists elsewhere, consider shared utility
```

---

## Phase 2: Backend Checks (.NET / API)

```
□ Controller methods use correct HTTP verb (GET for reads, POST for creates, PUT for updates, DELETE for deletes)
□ Route paths follow project convention (kebab-case, consistent with existing routes)
□ All controller methods have authorization attribute (or inherit from base)
□ Service methods have try-catch with error logging (matches project pattern)
□ Entity has all required audit fields (CreatedDate, CreatedBy, UpdatedDate, UpdatedBy, RecordStatusId)
□ Soft delete uses RecordStatusId, NOT physical delete (unless explicitly requested)
□ Multi-tenancy: ClientId is checked in all queries (no cross-tenant data leaks)
□ DTOs don't expose internal fields (RecordStatusId, CreatedBy unless needed)
□ Extension method names are consistent (ToDto, ToEntity, ToReturnDto)
□ No N+1 query patterns (loading related entities in a loop)
```

---

## Phase 3: Frontend Checks (React / TypeScript)

```
□ Components use FC typing (or match project convention)
□ Props interfaces are defined (not inline anonymous types)
□ Hooks follow naming convention (use* prefix)
□ useQuery/useMutation have proper query keys
□ Error states are handled (isError, error display)
□ Loading states are handled (isLoading, skeleton/spinner)
□ Empty states are handled (no data → show empty message)
□ Event handlers are memoized with useCallback where needed
□ No direct state mutation (always use setter functions)
□ Ant Design components follow project patterns (size, styling)
□ Tailwind classes are consistent with project style
□ No inline styles when Tailwind class exists
□ Types match the API response shape (check api-contract-validation)
```

---

## Phase 4: Security Checks

```
□ No secrets/credentials in source code
□ No SQL injection vectors (parameterized queries only)
□ No XSS vectors (user input is sanitized before rendering)
□ No command injection (user input not passed to exec/system calls)
□ Auth checks present on all endpoints that need them
□ CORS is not overly permissive
□ No sensitive data in URL query parameters (use POST body)
□ No sensitive data logged to console or error logs
```

---

## Phase 5: How to Run

After completing code changes:

```
1. For each file created/modified, re-read it
2. Run through applicable checklists (universal + language-specific)
3. If issues found:
   a. Fix automatically if straightforward (unused import → remove)
   b. Flag to user if judgment needed (naming choice, architecture decision)
4. Report: "Self-review: N files checked, M issues found and fixed"
   Or: "Self-review: clean, no issues"
```

### When to SKIP self-review:
```
- Quick one-line fixes (typo, single property change)
- Non-code files (.md, .json, .txt, config)
- User explicitly says "skip review"
```

### Depth levels:
```
Quick review: Universal checks only (~30 seconds)
Standard review: Universal + language-specific (~1 minute)
Deep review: All checks including security (~2 minutes)

Default: Standard review
Use deep review for: new features, auth changes, data handling changes
```

---

## Phase 6: Integration

```
Feature creation workflow:
  1. Load lessons-learned → prevention steps
  2. Create files
  3. post-creation-verify → registration checks
  4. build-check → compile
  5. api-contract-validation → FE↔BE match
  6. self-review → code quality check  ← THIS SKILL
  7. Report to user
```

---

## Anti-Patterns

1. Do NOT review every line — focus on the checklist items
2. Do NOT re-read files that weren't changed
3. Do NOT block on style preferences — only flag objective issues
4. Do NOT add features during review (scope creep)
5. Do NOT report trivial issues — fix them silently
