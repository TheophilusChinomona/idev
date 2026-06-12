---
name: smart-context
description: "Token-optimized context loading: load the cached project index at session start, then Grep before Read, expanding only as needed. Use at session start and whenever deciding what context to load."
---

# Smart Context Skill

## Purpose
Token-optimized context loading using the project-map as the data source.

## Data Sources (Priority Order)
1. `.claude/idev/smart-context/index.json` - Lightweight index (~70 lines)
2. `.claude/idev/project-map/project.map.md` - Full project map (load sections on demand)

## Activation
This skill is ALWAYS ACTIVE. Apply these rules to every task.

---

## Generating the index

If `index.json` is missing (e.g. the session-start hook reports no index), generate it by running the scanner from the project root:

```bash
python3 "${CLAUDE_PLUGIN_ROOT}/skills/smart-context/scanner.py"
```

This writes `.claude/idev/smart-context/index.json` with the detected stack, structure roots, feature names, and file-naming patterns.

**Fallback (no python3 available):** build the index manually — detect the stack from `package.json` / `*.csproj` / `requirements.txt` / `go.mod`, list feature directory names under `features/` or `modules/`, note naming patterns (e.g. `*Controller.*`, `*.hook.*`), and write the same JSON shape (`stack`, `structure`, `features`, `patterns`) to `.claude/idev/smart-context/index.json`.

---

## Phase 1: Session Start

Load ONLY the lightweight index:
```
.claude/idev/smart-context/index.json
```

This gives you (contents depend on what the scanner detected):
- Tech stack (e.g. React + .NET, Next.js + Python — whatever the project uses)
- Detected feature names (up to 50)
- File-naming patterns (e.g. Page, Container, Service, Controller)
- Project structure roots

**DO NOT load the full project-map yet.**

---

## Phase 2: Task Analysis

### Step 2.1: Extract Keywords
From user message, identify:
- **Feature name**: whatever appears in index.json's features list (e.g. orders, customers, auth)
- **Action type**: fix, add, update, delete, explain, find
- **Layer**: frontend, backend, api, database, full-stack

### Step 2.2: Determine What to Load

| Task Type | What to Load |
|-----------|--------------|
| Feature-specific task | Grep for feature files only |
| "Where is X?" | Grep, don't read full map |
| "List all controllers" | Load project-map backend section only |
| Architecture question | Load project-map structure section |
| Bug fix in specific file | Grep → Read that file only |

---

## Phase 3: Smart Loading from Project Map

When you need the project-map, load ONLY the relevant section:

### Section Loading
```markdown
# To find frontend files for a feature:
Grep "FeatureName" in project.map.md → Get file paths → Read specific files

# To find backend controller:
Grep "OrdersController" in project.map.md → Get path → Read controller

# To understand FE→BE mapping:
Load only the "FE → BE Mappings" section if it exists
```

### Never Do This
❌ Read the entire project.map.md (it can run to thousands of lines)
❌ Load all controllers "to understand the project"
❌ Pre-load map sections not related to current task

### Always Do This
✅ Grep project.map.md for keywords first
✅ Extract only the paths you need
✅ Read actual source files targeted by path

---

## Phase 4: Using Both Systems Together

```
User asks about "orders"
         ↓
Check index.json → "Orders" is a known feature
         ↓
Grep project.map.md for "*Order*" → Get 5 file paths
         ↓
Read only the relevant file (e.g., OrderListContainer.tsx)
         ↓
If needed, follow imports to related files
```

---

## Phase 5: Pattern Reference

Use the `patterns` section of index.json. Illustrative examples (the real globs come from index.json):

| Pattern | Glob |
|---------|------|
| Page | `**/pages/*Page.tsx` |
| Container | `**/containers/*Container.tsx` |
| Service (FE) | `**/services/*.service.ts` |
| Hook | `**/hooks/*.hook.ts` |
| Controller | `**/*Controller.cs` |
| Service (BE) | `**/*Service.cs` |

---

## Feature Keywords → Search Patterns

Illustrative examples ONLY — the real keyword list is the `features` array in index.json; build the same `**/[Xx]keyword*` glob for whatever features that project actually has:

| Keyword | Search |
|---------|--------|
| order, orders | `**/[Oo]rder*` |
| customer | `**/[Cc]ustomer*` |
| invoice | `**/[Ii]nvoice*` |
| auth, login | `**/[Aa]uth*` |
| payment | `**/[Pp]ay*` |
| user | `**/[Uu]ser*` |
| dashboard | `**/[Dd]ashboard*` |

---

## Anti-Patterns (DO NOT DO)

1. ❌ Loading entire project.map.md at session start
2. ❌ Reading all files in a feature folder
3. ❌ Pre-loading "just in case"
4. ❌ Ignoring index.json and going straight to map
5. ❌ Reading files not mentioned by user

---

## Token Budget Guide

| Action | Estimated Tokens |
|--------|------------------|
| Load index.json | ~100 |
| Grep project.map.md | ~50 |
| Read specific section of map | ~200-500 |
| Read one source file | ~200-800 |
| **Target per task** | **< 1,500** |

---

## Summary

```
index.json (always)
      ↓
Grep for keywords (fast)
      ↓
project.map.md section (if needed)
      ↓
Actual source files (targeted)
```

The project-map is your detailed reference. The index.json is your quick lookup. Use them together, but always start minimal.
