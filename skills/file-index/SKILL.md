---
name: file-index
description: Compact feature-to-file index mapping feature names to exact file paths. Use when the user mentions a feature and exact file paths are needed, or to refresh the index after files change.
---

# File Index Skill

## Purpose
Compact file index that maps feature names to exact file paths. Eliminates multi-step searching — one read gives you every file for any feature.

## Activation
- **Load**: When user mentions a feature name and you need to find its files
- **Generate**: On first use, or when user says "refresh index"

---

## How It Works

A compact index is maintained at:
`.claude/idev/file-index/index.md`

This file maps every feature to its exact FE and BE file paths (~100-150 lines).
One read replaces 5-10 grep/glob operations.

---

## Index Format

```markdown
# File Index
Generated: YYYY-MM-DD

## [FeatureName]
FE:
  - pages: path/to/Page.tsx
  - containers: path/to/Container1.tsx, path/to/Container2.tsx
  - hooks: path/to/feature.hook.ts
  - service: path/to/feature.service.ts
  - types: path/to/feature.types.ts
  - models: path/to/feature.models.ts
BE:
  - controller: path/to/Controller.cs
  - service: path/to/Service.cs
  - interface: path/to/IService.cs
  - entity: path/to/Entity.cs
  - dtos: path/to/Dto.cs, path/to/CreateDto.cs, path/to/UpdateDto.cs
  - extensions: path/to/DtoExtensions.cs

## [FeatureName2]
...
```

---

## Phase 1: Generate Index

Scan the codebase to build the index. This is technology-agnostic:

```
1. Detect project structure (use architecture-scanner cache if available)
2. For frontend:
   - Glob for feature directories (src/modules/features/*, src/features/*, etc.)
   - For each feature, glob for: pages, containers, hooks, services, types, models
3. For backend:
   - Glob for controller files → extract feature name from class name
   - For each feature, find: service, interface, entity, DTOs
4. Cross-reference FE and BE features by name similarity
5. Write index.md
```

---

## Phase 2: Usage

### Finding files for a feature:
```
User mentions "orders"
  → Read index.md
  → Find "## Orders" section
  → All file paths instantly available
  → No grep needed
```

### Finding a specific layer:
```
User says "update the orders service"
  → Read index.md → Find Orders → service: path
  → Read that file directly
  → One read instead of glob + grep + read
```

---

## Phase 3: Keeping Index Fresh

The index can become stale when files are created/deleted/moved.

### Auto-refresh triggers:
- User says "refresh index" or "update index"
- A new feature is created (add its section)
- Index is older than 14 days

### Incremental updates:
- When you create a new file → add it to the index immediately
- When you delete a file → remove it from the index
- Do NOT rescan everything for a single file change

---

## Integration with Other Skills

```
User asks about "orders":
  1. file-index → get all Order file paths (1 read)
  2. architecture-scanner cache → know FE/BE roots
  3. Read the specific file needed

Total: 2 reads to get any file. No searching.
```

---

## Anti-Patterns

1. Do NOT include node_modules, bin, obj, or build output paths
2. Do NOT include test files in the main index (add separate section if needed)
3. Do NOT include every file — only feature-organized files that are frequently accessed
4. Do NOT let the index exceed ~200 lines
5. Do NOT grep/glob when the index has the answer
