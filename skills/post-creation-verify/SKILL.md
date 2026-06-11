---
name: post-creation-verify
description: Verifies all required registrations (DI, repository, DbContext, routes, exports) after creating new feature files, and auto-fixes missing ones. Run before build-check.
---

# Post-Creation Verification Skill

## Purpose
After creating a new feature (entity, service, controller, component, hook, etc.), automatically verify that ALL required registrations, imports, and wiring are in place. Catches the classic bug class of a missing registration (e.g., a forgotten `IGenericRepository<Entity>` DI entry).

## Activation
Run automatically after creating any new feature file(s). This is a pre-build check — run BEFORE the build-check skill.

---

## How It Works

This skill builds a verification checklist dynamically based on the detected stack. It does NOT hardcode what to check — it discovers what registrations are needed by scanning how existing features are wired.

Results cached in `.claude/idev/post-creation-verify/cache.json` after first detection.

---

## Phase 1: Detect Registration Points

Scan the codebase to find where things get registered/wired. This adapts to any stack:

```
.NET:
  1. Find DI registration files:
     Grep for "AddTransient|AddScoped|AddSingleton" → DI files
  2. Find DbContext:
     Grep for "DbSet<" → DbContext file
  3. Find AutoMapper/Extension profiles:
     Grep for "CreateMap|Profile" → Mapper config files
  4. Catalog what each registration file contains:
     - Service DI: maps IService → Service
     - Data DI: maps IGenericRepository<Entity> → GenericRepository<Entity>
     - DbContext: DbSet<Entity> declarations

Node.js/Express:
  1. Find route registration:
     Grep for "app.use|router.use" → Where routes are mounted
  2. Find module imports:
     Grep for "import.*from" in index/barrel files
  3. Find middleware chain:
     Grep for "app.use(" → Middleware registration

NestJS:
  1. Find module files:
     Glob for *.module.ts → Module declarations
  2. Check providers, controllers, imports arrays

Python/Django:
  1. Find INSTALLED_APPS in settings.py
  2. Find urlpatterns in urls.py
  3. Find admin.site.register in admin.py

Python/FastAPI:
  1. Find app.include_router calls
  2. Find dependency injection (Depends) registrations

Java/Spring:
  1. Find @ComponentScan, @Bean definitions
  2. Find application.properties/yml for config

React/Frontend:
  1. Find route registration:
     Grep for "createBrowserRouter|Routes|Route" → Route config file
  2. Find barrel exports:
     Check index.ts files for re-exports
  3. Find query key registrations (if centralized)
```

---

## Phase 2: Generate Cache

Write detected registration points to `.claude/idev/post-creation-verify/cache.json`:

```json
{
  "generated": "YYYY-MM-DD",
  "registrationPoints": {
    "backend": [
      {
        "type": "service-di",
        "file": "relative/path/to/DI/file",
        "pattern": "services.AddTransient<I{Name}Service, {Name}Service>()",
        "grepCheck": "I{Name}Service",
        "required": true
      },
      {
        "type": "repository-di",
        "file": "relative/path/to/Data/DI/file",
        "pattern": "services.AddTransient<IGenericRepository<{Entity}>, GenericRepository<{Entity}>>()",
        "grepCheck": "IGenericRepository<{Entity}>",
        "required": true
      },
      {
        "type": "dbcontext",
        "file": "relative/path/to/DbContext",
        "pattern": "public virtual DbSet<{Entity}> {Entity} { get; set; }",
        "grepCheck": "DbSet<{Entity}>",
        "required": true
      }
    ],
    "frontend": [
      {
        "type": "route",
        "file": "relative/path/to/Routes.tsx",
        "grepCheck": "path.*{feature-route}",
        "required": false,
        "note": "Only needed if feature has its own page"
      },
      {
        "type": "barrel-export",
        "file": "relative/path/to/hooks/index.ts",
        "grepCheck": "export.*{hookName}",
        "required": false,
        "note": "Only needed if barrel file exists"
      }
    ]
  }
}
```

---

## Phase 3: Verification Process

After creating new feature files, run these checks:

### Step 1: Determine what was created
```
From the files just created, extract:
  - Entity/Model name (e.g., Order)
  - Service name (e.g., OrderService)
  - Controller/Router name (e.g., OrdersController)
  - Frontend component names (if any)
```

### Step 2: Check each registration point
```
For each registration point in cache:
  1. Grep the registration file for the expected pattern
  2. Replace {Name}, {Entity} with actual names
  3. If found → PASS
  4. If NOT found → FAIL (missing registration)
```

### Step 3: Report results
```
Format:
  Registration Verification:
  ✓ Service DI: IOrderService registered
  ✓ DbContext: DbSet<Order> registered
  ✗ Repository DI: IGenericRepository<Order> NOT registered
    → Fix: Add to [file] at line [N]:
      services.AddTransient<IGenericRepository<Order>, GenericRepository<Order>>();
```

### Step 4: Auto-fix missing registrations
```
For each FAIL:
  1. Read the registration file
  2. Find the correct insertion point (same region/section as similar registrations)
  3. Add the missing registration
  4. Report what was added
```

---

## Phase 4: Stack-Specific Checklists

These are auto-generated from cache, not hardcoded. Examples of what gets detected:

### .NET Backend Feature
```
□ Entity created in Entities/{Feature}/
□ DTOs created in ServiceDtos/{Feature}/
□ Extension methods (ToDto, ToEntity) created
□ Interface created in Interfaces/Services/{Feature}/
□ Service created in Services/{Feature}/
□ Controller created in Controllers/
□ Service registered in Services DI file
□ Repository registered in Data DI file  ← THIS IS WHAT WE MISSED
□ DbSet added to DbContext
□ Database change script created (if no-migration rule)
```

### React Frontend Feature
```
□ Types/interfaces created
□ Service functions created
□ Hooks created (useQuery/useMutation)
□ Container component created
□ Presentation component created
□ Route registered (if new page)
□ Barrel export updated (if index.ts exists)
```

### Node.js/Express Backend Feature
```
□ Model/schema created
□ Service created
□ Controller/handler created
□ Routes defined and mounted
□ Validation middleware added (if applicable)
□ Module exported from index
```

---

## Phase 5: Integration

```
Feature creation workflow:
  1. Create all feature files
  2. post-creation-verify → Check registrations (this skill)
  3. Auto-fix any missing registrations
  4. build-check → Compile/type-check
  5. Report final status
```

---

## Anti-Patterns

1. Do NOT skip verification for "simple" changes — always verify
2. Do NOT hardcode registration patterns — detect from existing registrations
3. Do NOT only check one DI file — scan ALL registration points
4. Do NOT silently pass when grep returns no result — report it
5. Do NOT add registrations without finding the correct insertion point (region/section)
