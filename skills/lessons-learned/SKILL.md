---
name: lessons-learned
description: Persistent memory of past mistakes, fixes, and gotchas with prevention steps. Load before creating new features; append a lesson after fixing any bug or discovering non-obvious behavior.
---

# Lessons Learned Skill

## Purpose
Persistent memory of mistakes, fixes, and gotchas discovered during development. Prevents repeating the same errors across sessions. Acts as a project-specific "do/don't" reference.

## Activation
- **Write**: After fixing a bug, discovering a gotcha, or learning something non-obvious
- **Read**: Before creating new features (check for relevant lessons)

---

## How It Works

A rolling log is maintained at:
`.claude/idev/lessons-learned/lessons.md`

Each entry records: what went wrong, why, and how to prevent it next time.

---

## Lesson Format

```markdown
# Lessons Learned
Last updated: YYYY-MM-DD

## Category: [DI/Registration]

### L001: Missing repository DI registration
- **Date**: 2026-01-29
- **Symptom**: Runtime DI error: "Unable to resolve IGenericRepository<Order>"
- **Root cause**: Created entity + service + controller but forgot to register IGenericRepository<Entity> in Data DI file
- **Fix**: Added `services.AddTransient<IGenericRepository<Order>, GenericRepository<Order>>();` to Data/DependancyInjectionExtentions.cs
- **Prevention**: After creating any new entity, ALWAYS check BOTH DI files:
  1. Services DI → IService registration
  2. Data DI → IGenericRepository<Entity> registration
- **Applies to**: Any new backend entity in this project
- **Tags**: backend, di, entity, registration

## Category: [Frontend/Hooks]

### L002: ...

## Category: [Database]

### L003: ...
```

---

## Phase 1: When to Write a Lesson

Write a new lesson when ANY of these occur:

```
1. A build/runtime error was caused by something Claude created
2. A registration, import, or wiring was missed
3. A pattern was followed incorrectly (wrong namespace, wrong convention)
4. User corrected Claude's approach
5. A workaround was needed for a framework quirk
6. Something took multiple attempts to get right
7. A type mismatch or API contract mismatch was discovered
```

### What NOT to log:
```
- Typos or simple syntax errors (not recurring)
- User preference changes (those go in CLAUDE.md)
- One-time debugging steps
```

---

## Phase 2: When to Read Lessons

### Before creating a new backend feature:
```
1. Load lessons.md
2. Filter by tags: "backend, entity, di, registration"
3. Check each relevant lesson's "Prevention" section
4. Apply all prevention steps
```

### Before creating a new frontend feature:
```
1. Load lessons.md
2. Filter by tags: "frontend, hooks, types, imports"
3. Apply prevention steps
```

### When a build error occurs:
```
1. Load lessons.md
2. Search for matching "Symptom" text
3. If found → apply the known fix immediately
4. If not found → fix it, then write a NEW lesson
```

---

## Phase 3: Lesson Categories

Organize by area for fast lookup:

```
- DI/Registration: Missing service/repo registrations, wrong lifetime
- Database: Schema issues, migration gotchas, query patterns
- Frontend/Components: React patterns, Ant Design quirks, state issues
- Frontend/Hooks: TanStack Query patterns, cache invalidation
- Frontend/Types: Type mismatches, missing exports, DTO alignment
- API/Integration: FE↔BE contract mismatches, endpoint URL issues
- Build/Config: Build failures, config issues, environment problems
- Testing: Test setup, mocking patterns, coverage gaps
```

---

## Phase 4: Maintenance

```
- Max 50 lessons (archive older ones to lessons-archive.md)
- Review and merge similar lessons quarterly
- Remove lessons that are no longer relevant (framework upgraded, etc.)
- Keep most impactful lessons at the top of each category
```

---

## Integration with Other Skills

```
Feature creation workflow:
  1. Load lessons-learned → Check prevention steps
  2. Create files
  3. post-creation-verify → Verify registrations
  4. build-check → Compile
  5. If new error found → Write new lesson
  6. cache-refresh → Update caches

This closes the learning loop:
  Make mistake → Learn → Prevent → Never repeat
```

---

## Anti-Patterns

1. Do NOT log every minor issue — only recurring or high-impact ones
2. Do NOT write vague lessons — include exact symptoms and exact fixes
3. Do NOT skip reading lessons before feature creation
4. Do NOT let the file grow beyond 50 entries — archive old ones
5. Do NOT duplicate lessons — check if a similar one exists first
