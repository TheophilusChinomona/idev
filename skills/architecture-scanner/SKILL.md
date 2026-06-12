---
name: architecture-scanner
description: "Detects which architectural layer (frontend or backend) a file or task belongs to and routes to the matching pattern skill. Use when a task spans frontend and backend, or when determining which layer a file belongs to."
---

# Architecture Scanner Skill

## Purpose
Unified layer detection that connects frontend and backend pattern skills with the project map. Works on ANY project by auto-detecting which directories are FE vs BE and what technologies are used.

## Activation
When a task spans multiple layers (frontend + backend) or when Claude needs to determine which layer a file belongs to.

---

## How It Works

This skill bridges three systems:
1. **Backend Patterns** (`${CLAUDE_PLUGIN_ROOT}/skills/backend-patterns/`)
2. **Frontend Patterns** (`${CLAUDE_PLUGIN_ROOT}/skills/frontend-patterns/`)
3. **Project Map** (`.claude/idev/project-map/project.map.md`) — if available

It auto-detects project types, which directories are frontend vs backend, and provides FE-to-BE endpoint mappings.

---

## Phase 1: Detect Project Type

Scan the workspace root using technology-agnostic detection. Check for ALL of these — do not assume any specific stack.

### 1.1 Detect All Project Roots
```
Glob for these marker files (exclude dependency folders like node_modules, vendor, bin, obj):

Frontend markers:
  package.json         → Read to detect: react, vue, angular, svelte, next, nuxt, solid, qwik
  pubspec.yaml         → Flutter/Dart
  Podfile              → iOS (Swift/ObjC)
  build.gradle + /app  → Android

Backend markers:
  *.sln / *.csproj     → .NET (C#)
  go.mod               → Go
  Cargo.toml           → Rust
  pom.xml / build.gradle (no /app) → Java/Kotlin (Spring Boot, etc.)
  requirements.txt / pyproject.toml / setup.py → Python (Django, Flask, FastAPI)
  Gemfile              → Ruby (Rails)
  composer.json        → PHP (Laravel)
  package.json (with express/fastify/nest/koa) → Node.js backend

Monorepo markers:
  lerna.json / nx.json / turbo.json / pnpm-workspace.yaml → Monorepo
```

### 1.2 Classify Each Root
```
For each detected project root:
1. Read the marker file to determine exact framework
2. Classify as: "frontend", "backend", "fullstack", "shared/lib", or "mobile"
3. Detect language: TypeScript, JavaScript, C#, Python, Go, Java, Rust, etc.
4. Record the root directory path
```

### 1.3 Use Project Map (if available)
```
If .claude/idev/project-map/project.map.md exists:
1. Grep for section headers to find FE/BE groupings
2. Cross-reference detected roots with map sections
3. Use map to fill in any missing feature-to-directory mappings
```

---

## Phase 2: Map FE-to-BE Connections

Discover how frontend calls backend. Detection varies by stack:

### 2.1 Find API Base Configuration
```
Search FE project for API base URL config:
  React/Vue/Angular: grep for "baseURL|BASE_URL|API_URL|VITE_API|NEXT_PUBLIC_API"
  Flutter: grep for "baseUrl|apiUrl"
  Any: grep for environment variable files (.env, .env.local, .env.development)
```

### 2.2 Collect Frontend API Calls
```
Search FE service/api files for endpoint paths:
  TypeScript/JS: grep for "api/|/api" in *.service.ts, *.api.ts, api/*.ts
  Python: grep for "requests.get|requests.post|httpx"
  Flutter: grep for "http.get|http.post|dio"
```

### 2.3 Collect Backend API Routes
```
Search BE project for route definitions:
  .NET:     grep for [Route("api/"] or [Http*("  in *.cs
  Express:  grep for "app.get|app.post|router.get|router.post" in *.ts/*.js
  FastAPI:  grep for "@app.get|@app.post|@router" in *.py
  Django:   grep for "path(" in urls.py
  Spring:   grep for "@GetMapping|@PostMapping|@RequestMapping" in *.java
  Go:       grep for "HandleFunc|Handle|r.GET|r.POST" in *.go
  Rails:    read config/routes.rb
  Laravel:  read routes/api.php
  NestJS:   grep for "@Get|@Post|@Controller" in *.ts
```

### 2.4 Match Endpoints
```
1. Normalize FE endpoint paths and BE route definitions
2. Match them by URL pattern
3. Build FE→BE mapping table
```

---

## Phase 3: Generate Layer Index

Write to `.claude/idev/architecture-scanner/cache.json`:

```json
{
  "generated": "YYYY-MM-DD",
  "projectType": "monorepo|single-app|multi-repo",
  "layers": {
    "frontend": {
      "root": "relative/path/to/fe",
      "framework": "react|vue|angular|svelte|next|nuxt|flutter",
      "language": "typescript|javascript|dart",
      "patternsSkill": "frontend-patterns",
      "apiConfigFile": "relative/path/to/api/config",
      "serviceFilesPattern": "**/*.service.ts"
    },
    "backend": {
      "root": "relative/path/to/be",
      "framework": ".net|express|fastapi|django|spring|rails|laravel|nestjs|go",
      "language": "csharp|typescript|python|java|go|ruby|php|rust",
      "patternsSkill": "backend-patterns",
      "routesLocation": "relative/path/to/controllers-or-routes"
    }
  },
  "apiRoutes": {
    "api/example/get-all": "ExampleController.cs (or example.routes.ts, etc.)"
  },
  "featureMapping": {
    "FeatureName": {
      "feRoot": "path/to/fe/feature",
      "beControllers": ["Controller.cs"],
      "feServices": ["service.ts"]
    }
  },
  "filePatterns": {
    "*.tsx": "frontend",
    "*.cs": "backend"
  }
}
```

---

## Phase 4: Usage

### Determine Layer for a File
```
Given a file path:
1. Check if path contains any known layer root
2. Fall back to file extension check against filePatterns
3. Return: "frontend" or "backend"
4. Load the corresponding patterns skill
```

### Find BE Endpoint for FE Service Call
```
Given a frontend API call (e.g., "api/jobs/get-all"):
1. Look up apiRoutes for matching endpoint
2. Return the BE route handler file and method name
3. Read that specific method for implementation details
```

### Find FE Service for BE Route
```
Given a backend route/controller method:
1. Look up apiRoutes in reverse
2. Grep FE service files for the endpoint URL
3. Follow imports to find the hook/composable and component using it
```

---

## Phase 5: Full-Stack Task Workflow

When user asks for a full-stack feature:

```
1. Load architecture-scanner cache
2. Determine which layers are affected
3. Load backend-patterns cache → Create BE files following detected conventions
4. Load frontend-patterns cache → Create FE files following detected conventions
5. Update apiRoutes with new endpoint mapping
6. Use the Checklist from both pattern skills
```

---

## Anti-Patterns

1. Do NOT assume any specific technology — always detect first
2. Do NOT load both pattern caches unless the task truly spans both layers
3. Do NOT re-scan if cache exists and is < 7 days old
4. Do NOT load the full project map; grep it for specific keywords only
5. Do NOT guess which layer a file belongs to; check the cache
6. Do NOT hardcode file extensions — derive them from detected language

---

## Rescan Triggers

- User says "refresh architecture" or "rescan layers"
- Cache is older than 7 days
- New directories are added to the workspace
- FE-to-BE mapping is missing for a known endpoint
- Project type cannot be determined from cache alone
