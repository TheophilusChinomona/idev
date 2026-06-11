---
name: feature-completeness
description: Traces a feature end-to-end (UI, hook, service, API, controller, database) to verify every link is wired. Use after completing a multi-layer feature or when asked whether a feature is fully connected.
---

# Feature Completeness Skill

## Purpose
Verify that a newly created feature is fully wired end-to-end — from UI component through hooks/services to API endpoint to backend controller/service/database. Catches disconnected pieces that compile but don't actually work together.

## Activation
- After completing a multi-layer feature (FE + BE)
- After creating a new page/container that calls an API
- When user reports "it builds but doesn't work"

---

## How It Works

This skill traces the full request path from UI to database and back, verifying each connection point. It's technology-agnostic — it detects the layers from the architecture-scanner cache.

---

## Phase 1: Identify the Feature Chain

For a full-stack feature, the chain is:

```
Generic chain (adapts to any stack):

  UI Layer         → User sees/clicks something
    ↓
  State/Hook Layer → Manages data fetching/mutation
    ↓
  Service Layer    → Makes HTTP call to API
    ↓
  API Layer        → Receives request, routes to handler
    ↓
  Business Layer   → Processes logic, validates, transforms
    ↓
  Data Layer       → Reads/writes database
    ↓
  Database         → Table exists with correct schema
```

### Stack-specific chains:

```
React + .NET:
  Component → useQuery/useMutation → service.ts → API URL →
  Controller.cs → Service.cs → Repository → DbContext → SQL Table

React + Express:
  Component → useQuery/useMutation → service.ts → API URL →
  router.ts → controller.ts → service.ts → Prisma/Sequelize → SQL Table

React + FastAPI:
  Component → useQuery/useMutation → service.ts → API URL →
  router.py → service.py → SQLAlchemy → SQL Table

Vue + Django:
  Component → composable → api.ts → API URL →
  views.py → serializer.py → model.py → SQL Table
```

---

## Phase 2: Trace Each Link

For each link in the chain, verify it exists and connects correctly:

### Link 1: UI → Hook/State
```
Check: Does the component import and call the hook?
  Grep component file for hook name (e.g., useGetOrders)
  Verify: hook is called, return value is used (data, isLoading, error)
  Fail if: hook is imported but never called, or return values are ignored
```

### Link 2: Hook → Service
```
Check: Does the hook call the service function?
  Read hook file → find queryFn or mutationFn
  Verify: service function is imported and called with correct params
  Fail if: service function doesn't exist or signature doesn't match
```

### Link 3: Service → API URL
```
Check: Does the service make an HTTP call to the correct URL?
  Read service file → find axios/fetch call
  Verify: URL matches a known backend route (check architecture-scanner cache)
  Fail if: URL has no matching backend route (lesson L003)
```

### Link 4: API URL → Controller
```
Check: Does the backend controller have a matching route?
  Grep controllers for the URL path
  Verify: HTTP method matches (GET/POST/PUT/DELETE)
  Fail if: no controller route matches
```

### Link 5: Controller → Service
```
Check: Does the controller call the service method?
  Read controller method → find service call
  Verify: service interface is injected and method exists
  Fail if: service method doesn't exist or parameters don't match
```

### Link 6: Service → Repository/DB
```
Check: Does the service access the database?
  Read service method → find repository/DB calls
  Verify: entity type is correct, query filters are present
  Fail if: repository for this entity isn't registered (lesson L001)
```

### Link 7: Database → Table
```
Check: Does the database table exist?
  Check DbContext for DbSet declaration
  Check for database change script in .claude/docs/database-changes/
  Warn if: DbSet exists but no table creation script found
```

---

## Phase 3: Report Results

```
Feature Completeness: Orders CRUD

  Chain: UI → Hook → Service → API → Controller → Service → DB

  ✓ Link 1: OrdersTabContainer → useGetOrders (called, data used)
  ✓ Link 2: useGetOrders → ordersService.getAll (imported, called)
  ✓ Link 3: getAll → GET api/orders/get-all (URL found in architecture cache)
  ✓ Link 4: api/orders/get-all → OrdersController.GetAll (route match)
  ✓ Link 5: GetAll → _orderService.GetAll (injected, method exists)
  ✓ Link 6: GetAll → _repository.GetAllAsync (IGenericRepository<Order> registered)
  ⚠ Link 7: DbSet<Order> exists, DB table pending DBA execution

  Result: Feature is wired end-to-end. Blocked on: database table creation.
```

---

## Phase 4: Common Disconnection Points

Issues this skill catches that compile but fail at runtime:

```
1. Component renders but shows no data
   → Hook is called but service function returns wrong URL (404)

2. Service call succeeds but data shape is wrong
   → FE type doesn't match BE DTO fields (api-contract-validation catches this)

3. Controller receives request but service throws
   → Service depends on unregistered repository (post-creation-verify catches this)

4. Everything works but wrong data appears
   → Query filter missing ClientId (multi-tenancy leak)
   → Soft delete filter missing RecordStatusId check

5. Feature works for create but not update/delete
   → Only some CRUD operations were wired
   → Missing mutation hooks or service functions

6. Page loads but route doesn't work
   → Component created but route not registered in Routes.tsx
```

---

## Phase 5: Completeness Checklist

Auto-generated based on detected stack:

### Full-Stack CRUD Feature
```
□ FE Types: Request/Response interfaces defined
□ FE Service: All CRUD functions (getAll, getById, create, update, delete)
□ FE Hooks: useQuery for reads, useMutation for writes
□ FE Container: Imports hooks, handles loading/error/empty states
□ FE Route: Page registered in router (if new page)
□ BE Entity: Created with all required fields
□ BE DTOs: Return, Create, Update DTOs + mapping extensions
□ BE Interface: Service interface with all methods
□ BE Service: Implementation with error handling
□ BE Controller: All route handlers
□ BE DI: Service + Repository registered
□ BE DbContext: DbSet declared
□ DB: Table creation script exists
□ Contract: FE types match BE DTOs
□ Chain: All 7 links verified connected
```

---

## Phase 6: Integration

```
Complete feature creation workflow:
  1. lessons-learned → prevention steps
  2. Create BE files (entity, DTOs, service, controller)
  3. post-creation-verify → registrations
  4. build-check → BE compiles
  5. Create FE files (types, service, hooks, container)
  6. build-check → FE compiles
  7. api-contract-validation → FE↔BE types match
  8. feature-completeness → end-to-end chain verified  ← THIS SKILL
  9. self-review → code quality
  10. Report to user
```

---

## Anti-Patterns

1. Do NOT run for single-file changes — only for multi-layer features
2. Do NOT trace into external libraries — stop at the project boundary
3. Do NOT check every CRUD operation individually — check the pattern once
4. Do NOT block on database table not existing — warn and continue
5. Do NOT re-read files already checked by other skills — use cached results
