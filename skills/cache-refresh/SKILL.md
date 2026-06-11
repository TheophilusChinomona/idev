---
name: cache-refresh
description: Keeps idev skill caches fresh after source files are created, deleted, or renamed. Use after structural file changes or when the user says refresh caches.
---

# Cache Refresh Skill

## Purpose
Keep all skill caches fresh by detecting when source files change and triggering targeted cache updates. Prevents stale data from causing wrong file paths, missing registrations, or outdated function line numbers.

## Activation
- **Incremental**: After Claude creates, deletes, or renames a file during a task
- **Full refresh**: When user says "refresh caches" or when caches are older than 7 days
- **On session start**: Quick staleness check (compare cache date vs recent git changes)

---

## How It Works

This skill does NOT use a file watcher daemon. Instead, it hooks into Claude's own actions — every time Claude creates or modifies a file, this skill updates the relevant caches incrementally.

---

## Phase 1: Track File Changes During Session

After Claude creates, renames, or deletes a source file, determine which caches are affected:

```
File change → Affected caches:

New .cs file (Entity)       → file-index, backend-patterns (function-index), post-creation-verify
New .cs file (Controller)   → file-index, architecture-scanner (apiRoutes), backend-patterns
New .cs file (Service)      → file-index, backend-patterns
New .tsx/.ts file            → file-index, frontend-patterns (function-index)
New .service.ts file         → file-index, architecture-scanner (apiRoutes)
New .hook.ts file            → file-index, frontend-patterns
New route added              → architecture-scanner, file-index
DI registration changed      → post-creation-verify (line numbers may shift)
DbContext changed             → post-creation-verify (line numbers may shift)
Any file deleted              → file-index (remove entry), function-index (remove entry)
```

---

## Phase 2: Incremental Update Rules

### After creating a new feature:
```
1. Add new files to file-index/index.md under the correct feature section
2. Add new API routes to architecture-scanner/cache.json apiRoutes
3. Add new function line numbers to pattern cache Function Index sections
4. Update post-creation-verify line numbers if DI/DbContext files were modified
5. Update session-resume with modified files list
6. Update task-journal with completed task
```

### After modifying an existing file:
```
1. If function was added/removed → update function-index line numbers
2. If DI file was modified → update post-creation-verify insertion line numbers
3. If route was added → update architecture-scanner apiRoutes
```

### After deleting a file:
```
1. Remove from file-index
2. Remove from architecture-scanner apiRoutes (if controller/service)
3. Remove function entries from function-index
```

---

## Phase 3: Staleness Detection

On session start, quick-check if caches are stale:

```
1. Read each cache's "generated" date
2. If older than 7 days → mark for full refresh
3. If git is available: run `git log --since="CACHE_DATE" --name-only --pretty=format:""`
   → Get list of files changed since cache was generated
   → If changed files overlap with cached paths → mark for targeted refresh
4. If no git: compare cache date only
```

### Staleness levels:
```
Fresh (< 1 day old, no conflicting changes): Use as-is
Stale (1-7 days, minor changes): Incremental update
Expired (> 7 days): Full rescan
```

---

## Phase 4: Full Refresh

When triggered by user ("refresh caches") or expiry:

```
1. Regenerate file-index/index.md (scan all features)
2. Regenerate architecture-scanner/cache.json (scan routes)
3. Regenerate backend-patterns function-index (scan key files)
4. Regenerate frontend-patterns function-index (scan key files)
5. Regenerate post-creation-verify/cache.json (rescan DI line numbers)
6. Regenerate build-check/cache.json (rescan build commands)
7. Update all "generated" dates
```

Run these as parallel agents for speed.

---

## Phase 5: Integration

```
After every file creation/modification by Claude:
  1. cache-refresh determines which caches are affected
  2. Updates them incrementally (add/remove entries)
  3. No full rescan needed for single-file changes

On session start:
  1. Staleness check (~1 grep command)
  2. If stale → targeted refresh
  3. If fresh → use as-is
```

---

## Anti-Patterns

1. Do NOT rescan everything after a single file change — use incremental updates
2. Do NOT skip cache updates after creating files — stale caches cause real bugs
3. Do NOT run full refresh on every session start — only when stale
4. Do NOT update caches for non-source file changes (.md, .txt, config)
5. Do NOT block the user's task to refresh — update in the background when possible
