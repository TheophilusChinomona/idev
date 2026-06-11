---
name: backend-patterns
description: Scans the codebase to auto-detect backend code conventions (controllers, services, entities, DTOs, DI registration) and caches them. Use when creating or modifying backend code so new files follow existing patterns exactly.
---

# Backend Pattern Scanner Skill

## Purpose
Auto-detect backend code conventions by scanning the codebase. Works on ANY backend stack — .NET, Node.js, Python, Java, Go, Ruby, PHP, Rust, etc.

## Activation
When creating or modifying backend code and no cached patterns exist yet.

---

## How It Works

This skill does NOT hardcode patterns or assume any technology. Instead, it:
1. Detects the backend stack from marker files
2. Scans for the project's specific conventions
3. Caches discovered patterns for reuse

Results are cached in `.claude/idev/backend-patterns/cache.md` after first scan.

---

## Phase 1: Detect Backend Stack

Run these checks to identify the backend technology. Check ALL — do not assume:

```
Marker File Detection:
  *.sln / *.csproj           → .NET (C#)
  go.mod                     → Go
  Cargo.toml                 → Rust
  pom.xml                    → Java (Maven)
  build.gradle (no /app dir) → Java/Kotlin (Gradle)
  requirements.txt / pyproject.toml / setup.py → Python
  Gemfile                    → Ruby
  composer.json              → PHP
  package.json (with express/fastify/nest/koa/hapi) → Node.js

Framework Detection (read marker file contents):
  .NET:    grep *.csproj for "Microsoft.AspNetCore" → ASP.NET Core
  Python:  grep for "django|flask|fastapi|starlette" in requirements/pyproject
  Java:    grep pom.xml for "spring-boot|quarkus|micronaut"
  Ruby:    grep Gemfile for "rails|sinatra|grape"
  PHP:     grep composer.json for "laravel|symfony|slim"
  Node.js: grep package.json for "express|fastify|nestjs|koa|hapi"
  Go:      grep go.mod for "gin|echo|fiber|chi|mux"

ORM/Database Detection:
  .NET:    grep for "DbContext|EntityFramework" → EF Core
  Python:  grep for "django.db|sqlalchemy|tortoise" → ORM
  Java:    grep for "JpaRepository|@Entity" → JPA/Hibernate
  Node.js: grep for "prisma|typeorm|sequelize|mongoose|knex" → ORM
  Ruby:    grep for "ActiveRecord" → Rails ORM
  Go:      grep for "gorm|sqlx|ent" → ORM
```

---

## Phase 2: Discover Project Structure

Based on detected stack, scan for key directories. The scan adapts to the technology:

### Generic Scans (run regardless of stack)
```
1. Find route/controller files → API layer location
2. Find service/business logic files → Service layer location
3. Find model/entity files → Data layer location
4. Find DTO/schema/serializer files → Data transfer layer
5. Find dependency injection/module registration → DI setup
6. Find database config/context → DB layer
7. Find middleware files → Middleware layer
8. Find test files → Test location and framework
```

### Stack-Specific File Patterns
```
.NET:
  Controllers: **/*Controller.cs
  Services: **/*Service.cs (exclude I*Service.cs)
  Interfaces: **/I*Service.cs
  Entities: **/Entities/**/*.cs
  DTOs: **/*Dto.cs
  DI: file containing "AddTransient|AddScoped"
  DB: file containing "DbSet<"

Node.js/Express:
  Routes: **/routes/*.ts or **/*.routes.ts
  Controllers: **/controllers/*.ts or **/*.controller.ts
  Services: **/services/*.ts or **/*.service.ts
  Models: **/models/*.ts or **/*.model.ts
  Middleware: **/middleware/*.ts
  DB: file containing "prisma|mongoose.model|sequelize"

Python/Django:
  Views: **/views.py or **/views/*.py
  Models: **/models.py or **/models/*.py
  Serializers: **/serializers.py
  URLs: **/urls.py
  Admin: **/admin.py

Python/FastAPI:
  Routers: **/routers/*.py or **/*_router.py
  Services: **/services/*.py
  Models: **/models/*.py or **/schemas/*.py
  DB: file containing "SessionLocal|create_engine"

Java/Spring:
  Controllers: **/*Controller.java
  Services: **/*Service.java or **/*ServiceImpl.java
  Repositories: **/*Repository.java
  Entities: **/entity/*.java or **/model/*.java
  DTOs: **/dto/*.java

Go:
  Handlers: **/handlers/*.go or **/*handler.go
  Services: **/services/*.go
  Models: **/models/*.go
  Routes: file containing "HandleFunc|router.GET"

Ruby/Rails:
  Controllers: app/controllers/**/*_controller.rb
  Models: app/models/**/*.rb
  Serializers: app/serializers/**/*.rb
  Routes: config/routes.rb
```

---

## Phase 3: Extract Patterns from Existing Code

For each discovered layer, read ONE representative file and extract the exact pattern:

### 3.1 Route/Controller Pattern
```
Pick one route handler (not base/abstract)
Extract: namespace/module, routing decorator/attribute, base class/mixin,
         constructor/DI params, response wrapper, auth middleware
Detect: how request params are parsed, how responses are formatted,
        how errors are returned, how auth context is accessed
```

### 3.2 Service/Business Logic Pattern
```
Pick one service implementation
Extract: constructor/init DI params, error handling pattern, repository/DB usage
Detect: transaction handling, logging pattern, exception types,
        how service methods are structured (async/sync, return types)
```

### 3.3 Model/Entity Pattern
```
Pick one data model
Extract: base class, primary key pattern, common fields (timestamps, soft delete, etc.)
Detect: audit fields, multi-tenancy fields, relationship patterns,
        naming conventions (PascalCase, camelCase, snake_case)
```

### 3.4 DTO/Schema/Serializer Pattern
```
Find data transfer objects (DTOs, schemas, serializers, validators)
Extract: naming convention, validation approach, field types
Detect: mapping methods (manual, AutoMapper, extension methods, serializer classes)
        separate Create/Update/Response types or unified
```

### 3.5 Dependency Injection / Module Registration
```
Find where services are registered/configured
Extract: registration method (DI container, module imports, middleware chain)
Detect: grouping convention, insertion point for new registrations
Note: exact file path and line number
```

### 3.6 Database Configuration
```
Find database setup (DbContext, Prisma schema, models.py, etc.)
Extract: how models are registered, connection config
Detect: migration approach, seeding pattern
Note: exact file path and insertion point for new models
```

---

## Phase 4: Generate Cache

After scanning, write all discovered patterns to:
`.claude/idev/backend-patterns/cache.md`

Format:
```markdown
# Backend Patterns Cache
## Generated: [date]
## Project: [detected project name]
## Stack: [framework] + [language] + [ORM] + [other key libs]

### Paths
[All discovered paths with descriptions]

### Route/Controller Template
[extracted pattern with {{PLACEHOLDERS}}]

### Service Template
[extracted pattern with {{PLACEHOLDERS}}]

### Model/Entity Template
[extracted pattern with {{PLACEHOLDERS}}]

### DTO/Schema Templates
[extracted patterns - create, update, response]

### Registration Points
DI/Module File: [path] → Insert at line [N]
DB Config: [path] → Insert after line [N]

### Conventions
- Language: [detected]
- Naming: [PascalCase/camelCase/snake_case]
- Soft delete: [pattern or "not used"]
- Multi-tenancy: [pattern or "not used"]
- Audit fields: [list or "not used"]
- Error handling: [pattern]
- Response wrapper: [pattern]
- Auth context: [how user identity is accessed]
- Testing: [framework and pattern]
```

---

## Phase 5: Usage

On subsequent tasks, load ONLY the cache file (~200 lines) instead of rescanning.
Rescan if user says "refresh patterns" or if cache is older than 7 days.

---

## Checklist (generic, auto-populated from scan)

When creating a new backend feature, the scanner detects what files are needed:
- [ ] Model/Entity in [detected path]
- [ ] DTOs/Schemas in [detected path]
- [ ] Interface/Abstract (if applicable) in [detected path]
- [ ] Service in [detected path]
- [ ] Route/Controller in [detected path]
- [ ] DI/Module registration in [detected file] at line [N]
- [ ] DB registration in [detected file] at line [N]
- [ ] Database change file (if migration-free rule exists)
- [ ] Tests in [detected test path]
