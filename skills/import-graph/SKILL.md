---
name: import-graph
description: "Lightweight dependency graph of which files import which, for path-based-import languages (TS/JS, Python, Go). Use before modifying a shared type, interface, service, or export to find dependent files that might break."
---

# Import Graph Skill

## Purpose
Lightweight dependency tracking that maps which files import from which other files. When you change a type, interface, or export, instantly know what else might break — without grepping the entire codebase.

## Activation
- **Generate**: On first use or when user says "refresh graph"
- **Query**: When modifying a shared type, interface, service, or export
- **Update**: Incrementally after creating new files

---

## How It Works

A compact import/dependency graph is maintained at:
`.claude/idev/import-graph/graph.json`

This maps: `file → [files that import from it]` (reverse dependency map).
Focus on shared/core files that are imported by many others.

---

## Scope: Path-Based-Import Languages Only

This skill applies to languages whose imports reference file paths, so an import line maps directly to a file:

```
TypeScript/JavaScript:
  import { X } from "./path"
  import X from "./path"
  require("./path")

Python:
  from module import X
  import module

Go:
  import "package/path"

Ruby:
  require "path"
  require_relative "path"
```

Do NOT build an import graph for C# or Java: `using Namespace;` / `import package.Class;` reference namespaces, not files, so they don't map to a file graph. For those languages, grep for the type name directly (e.g., `Grep "OrderService"`) to find dependents.

---

## Phase 2: Build the Graph

### What to track (high-value files only):
```
DO track reverse dependencies for:
  - Type/interface definition files (*.types.ts, *.interfaces.ts)
  - Service files (*.service.ts)
  - Hook files (*.hook.ts)
  - Model/entity files (*.models.ts)
  - Shared utility files (helpers, constants, enums)
  - Core/shared components

DO NOT track:
  - Node modules / NuGet packages (external)
  - CSS/style imports
  - Asset imports (images, fonts)
  - Test file imports
```

### Scanning process:
```
1. Identify high-value shared files (types, interfaces, services, models)
2. For each shared file, grep the codebase for files that import from it
3. Build reverse map: shared_file → [dependent_files]
4. Record import count for prioritization
```

---

## Phase 3: Graph Format

Write to `.claude/idev/import-graph/graph.json`:

```json
{
  "generated": "YYYY-MM-DD",
  "graph": {
    "src/modules/features/Orders/models/order.types.ts": {
      "importedBy": [
        "src/modules/features/Orders/hooks/orders.hook.ts",
        "src/modules/features/Orders/services/orders.service.ts",
        "src/modules/features/Orders/containers/OrdersTableContainer/OrdersTableContainer.tsx"
      ],
      "importCount": 3
    },
    "src/modules/core/models/enums/url.enums.ts": {
      "importedBy": ["... many files ..."],
      "importCount": 25
    }
  },
  "highImpactFiles": [
    {
      "file": "relative/path",
      "importCount": N,
      "description": "What this file exports"
    }
  ]
}
```

---

## Phase 4: Usage

### Staleness rule
Before acting on a graph hit, confirm it with a live Grep (e.g., grep for the import path or exported name). If the live result disagrees with the graph, regenerate the graph before proceeding.

### When modifying a type/interface:
```
Before changing Order type:
  1. Load graph.json
  2. Look up "order.types.ts"
  3. See 3 files depend on it
  4. Confirm with a live Grep that those files still import it
  5. Check each dependent file for breaking changes
  6. Update dependents if needed
```

### When renaming an export:
```
Before renaming useGetOrders:
  1. Grep graph for files importing from orders.hook.ts
  2. Update all import statements in dependent files
```

### When deleting a file:
```
Before deleting a service file:
  1. Check if anything imports from it
  2. If importCount > 0 → warn before deleting
  3. Update or remove imports in dependent files
```

---

## Phase 5: Incremental Updates

### After creating a new file:
```
1. Parse the new file's imports
2. For each import, add the new file to that import target's "importedBy" list
3. If the new file exports shared types, add it to the graph as a new entry
```

### After deleting a file:
```
1. Remove the file from all "importedBy" lists
2. Remove its own entry from the graph
```

---

## Scope Control

To keep the graph lightweight (~100-200 lines):

```
Only track files with importCount >= 2 (imported by 2+ files)
Exception: Always track type/interface files regardless of count
Exclude: test files, config files, build scripts
Max entries: 100 files
```

---

## Anti-Patterns

1. Do NOT track every file — only shared/high-value ones
2. Do NOT include external package imports
3. Do NOT rebuild the full graph for a single file change — use incremental updates
4. Do NOT let the graph exceed 200 entries
5. Do NOT skip checking the graph when modifying shared types
