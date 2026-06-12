---
name: frontend-patterns
description: "Scans the codebase to auto-detect frontend conventions (pages, containers, components, hooks, services) and caches them. Use when creating or modifying frontend code so new files follow existing patterns exactly."
---

# Frontend Pattern Scanner Skill

## Purpose
Auto-detect frontend (React/Vue/Angular/Svelte) code conventions by scanning the codebase. Works on any project.

## Activation
When creating or modifying frontend code and no cached patterns exist yet.

---

## How It Works

This skill does NOT hardcode patterns. Instead, it scans the codebase to discover them.
Results are cached in `.claude/idev/frontend-patterns/cache.md` after first scan.

---

## Phase 1: Detect Frontend Stack

Run these checks to identify the technology:

```
1. Read package.json → detect framework (react, vue, angular, svelte, next, nuxt)
2. Read package.json → detect key libraries:
   - State: redux, zustand, mobx, pinia, @tanstack/react-query
   - UI: antd, @mui/material, chakra-ui, tailwindcss, bootstrap
   - Routing: react-router-dom, vue-router, @angular/router
   - HTTP: axios, fetch wrapper, @tanstack/react-query
   - Forms: react-hook-form, formik, vee-validate
   - Date: dayjs, moment, date-fns, luxon
3. Read tsconfig.json or jsconfig.json → TypeScript or JavaScript
4. Glob for tailwind.config.* → Tailwind CSS
5. Glob for .eslintrc* → Linting rules
```

---

## Phase 2: Discover Project Structure

Scan to find the architecture pattern:

```
1. Read src/ directory structure (ls src/)
2. Detect architecture style:
   - Feature-based: src/features/ or src/modules/
   - Layer-based: src/components/, src/services/, src/hooks/
   - Page-based: src/pages/ or app/ (Next.js/Nuxt)
3. Glob **/*Container*.{tsx,jsx,vue} → Container components
4. Glob **/*Page*.{tsx,jsx,vue} → Page components
5. Glob **/hooks/*.{ts,js} or **/composables/*.{ts,js} → Custom hooks
6. Glob **/services/*.{ts,js} or **/api/*.{ts,js} → API services
7. Glob **/models/*.{ts,js} or **/types/*.{ts,js} → Type definitions
8. Glob **/store/*.{ts,js} or **/slices/*.{ts,js} → State management
9. Grep for "createBrowserRouter|Routes|Route" → Routing setup file
10. Grep for "API_URL|BASE_URL|baseURL" in .env* → API configuration
```

---

## Phase 3: Extract Patterns from Existing Code

For each discovered layer, read ONE representative file and extract the pattern:

### 3.1 Component Pattern
```
Pick one presentation/UI component
Extract: FC typing vs function declaration, props interface pattern, styling approach
Detect: CSS modules, Tailwind, styled-components, inline styles, UI library usage
Note: import ordering convention, export style (default vs named)
```

### 3.2 Container/Smart Component Pattern
```
Pick one container component
Extract: how hooks are used, how data flows to children, callback patterns
Detect: useCallback/useMemo usage, data transformation location, error handling
```

### 3.3 Hook Pattern
```
Pick one custom hook
Extract: return type, query/mutation pattern, error dispatching
Detect: query key pattern, cache invalidation strategy, optimistic updates
Note: query library version (v4 vs v5 differences)
```

### 3.4 Service/API Pattern
```
Pick one service file
Extract: HTTP client (axios instance, fetch wrapper), URL construction, response typing
Detect: interceptors, auth headers, error transformation, base URL config
Note: how API URLs are organized (enum, constants file, inline)
```

### 3.5 Type/Model Pattern
```
Pick one types file
Extract: interface vs type usage, enum style (string enum, const enum, object const)
Detect: DTO types, form data types, API response wrappers
```

### 3.6 State Management Pattern
```
Find store/slice files
Extract: how global state is structured, dispatch patterns
Detect: Redux toolkit, Zustand, Context, or other
```

### 3.7 Routing Pattern
```
Find routing config
Extract: route definition style, route constants, navigation pattern
Detect: lazy loading, guards/middleware, nested routes
```

---

## Phase 4: Generate Cache

After scanning, write all discovered patterns to:
`.claude/idev/frontend-patterns/cache.md`

Format:
```markdown
# Frontend Patterns Cache
## Generated: [date]
## Project: [detected project name]
## Stack: [framework] + [UI lib] + [state mgmt] + [query lib]

### Paths
src root: [path]
Components: [path pattern]
Containers: [path pattern]
Hooks: [path pattern]
Services: [path pattern]
Types: [path pattern]
Routes: [file path]
Store: [path pattern]

### Component Template
[extracted pattern with placeholders]

### Container Template
[extracted pattern with placeholders]

### Hook Templates
Query hook: [pattern]
Mutation hook: [pattern]

### Service Template
[extracted pattern with placeholders]

### Type/Interface Template
[extracted pattern]

### Conventions
- Styling: [Tailwind/CSS Modules/styled-components/etc.]
- Exports: [default/named]
- Props: [interface naming]
- File naming: [kebab-case/PascalCase/camelCase]
- Error handling: [pattern]
- Navigation: [pattern]

### Function Index
[Compact list of exported/public functions, one per line:]
functionName — file:line — one-line purpose
[Cap at ~100 entries, most-used first. Used by function-extract for targeted
reads and by cache-refresh for incremental updates. Update entries whenever
adding or modifying functions.]
```

---

## Phase 5: Usage

On subsequent tasks, load only the cache file instead of rescanning.
Keep the cache under ~250 lines by trimming examples if it grows beyond that.
Rescan if user says "refresh patterns" or if cache is older than 7 days.

---

## Checklist (generic, auto-populated from scan)

When creating a new frontend feature, the scanner detects what files are needed:
- [ ] Types/interfaces in [detected types path]
- [ ] Service methods in [detected services path]
- [ ] API URL entries in [detected URL config]
- [ ] Query/mutation hooks in [detected hooks path]
- [ ] Container component in [detected containers path]
- [ ] Presentation component in [detected presentation path]
- [ ] Route registration in [detected routes file]
- [ ] Hook barrel exports in [detected barrel file] (if applicable)
