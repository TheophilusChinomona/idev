---
name: api-contract-validation
description: "Discovers and validates API endpoints between frontend and backend. Use after creating or modifying API endpoints, or when investigating FE-BE contract mismatches. Simplified to endpoint discovery; full contract comparison deferred to dedicated tools."
---

# API Contract Validation — Simplified

## Purpose
Discover API endpoints on both frontend and backend, and flag obvious mismatches (missing endpoints, wrong HTTP methods, broken URL patterns). This is a lightweight discovery tool, not a full contract comparison engine.

## Activation
- After creating a new API endpoint (backend) or service function (frontend)
- When user reports a 404 or data mismatch between FE and BE
- When asked to "validate API contracts" or "check endpoint alignment"

---

## How It Works

### Endpoint Discovery

**Backend** — scan for route definitions:
```
.NET:     grep for [Route("api/"] or [Http*("  in *.cs
Express:  grep for "app.get|app.post|router.get|router.post" in *.ts/*.js
FastAPI:  grep for "@app.get|@app.post|@router" in *.py
Django:   grep for "path(" in urls.py
Spring:   grep for "@GetMapping|@PostMapping|@RequestMapping" in *.java
Go:       grep for "HandleFunc|Handle|r.GET|r.POST" in *.go
```

**Frontend** — scan for API calls:
```
TS/JS: grep for "api/|/api" in *.service.ts, *.api.ts, api/*.ts
Python: grep for "requests.get|requests.post|httpx" 
Flutter: grep for "http.get|http.post|dio"
```

### Quick Validation
For each discovered endpoint:
1. Check if the backend route exists
2. Check if the frontend has a corresponding service call
3. Flag: missing backend route, missing frontend call, HTTP method mismatch
4. Report results in a compact table

---

## Phase 1: Discover Endpoints

Scan both sides and build a mapping:
```json
{
  "generated": "YYYY-MM-DD",
  "endpoints": [
    {
      "path": "api/orders/get-all",
      "method": "GET",
      "backend": "path/to/OrdersController.cs",
      "frontend": "path/to/orders.service.ts",
      "status": "aligned|missing-backend|missing-frontend"
    }
  ]
}
```

Write to `.claude/idev/api-contract-validation/cache.json`.

---

## Phase 2: Report

```
API Endpoint Discovery: 12 endpoints found

  ✓ GET  api/orders/get-all      → aligned
  ✓ POST api/orders/create        → aligned
  ✗ GET  api/orders/get-by-key    → missing frontend call
  ✗ POST api/customers/import     → missing backend route

  Summary: 10 aligned, 1 missing-frontend, 1 missing-backend
```

---

## When to Use Full Contract Comparison

For detailed type/field validation (request/response shapes, DTO alignment), use a dedicated OpenAPI/Swagger tool or generate contracts from code. This skill focuses on URL and method alignment — the most common source of runtime 404s.

---

## Anti-Patterns
1. Do NOT assume casing matches — check JSON serializer config
2. Do NOT flag Guid→string as a type error — it serializes fine
3. Do NOT run full validation after every single file change — run after feature completion
4. Do NOT try to validate response shapes — focus on URL and method alignment
