---
name: api-contract-validation
description: "Verifies frontend API calls match backend endpoints (URL paths, HTTP methods, request/response types). Use after creating or modifying API endpoints, service functions, or DTOs, or when asked to validate API alignment, check FE-BE contracts, or generate API contract docs."
---

# API Contract Validation Skill

## Purpose
Verify that frontend API calls and backend API endpoints agree on URL paths, HTTP methods, request/response shapes, and field types. Catches type mismatches, missing fields, and wrong URLs before runtime.

## Activation
- After creating a new API endpoint (backend) or service function (frontend)
- After modifying a DTO, type, or API response shape
- When user reports a data mismatch between FE and BE

---

## How It Works

This skill compares frontend service calls against backend controller signatures to find mismatches. It does NOT assume any specific stack — it detects how each side defines its contracts.

---

## Phase 1: Extract Frontend Contract

Detect how the frontend defines API calls:

```
TypeScript/JavaScript (Axios/Fetch):
  Grep service files for HTTP calls:
    axios.get<ResponseType>("api/endpoint")
    axios.post<ResponseType>("api/endpoint", requestBody)
    fetch("api/endpoint", { method: "POST", body: ... })
  Extract: URL, HTTP method, request body type, response type

React Query hooks:
  Find useQuery/useMutation calls that wrap service functions
  Extract: query key, service function reference

Vue/Angular:
  Similar pattern — grep for HttpClient or $http calls

Extract per endpoint:
  - URL path (e.g., "api/orders/get-all")
  - HTTP method (GET, POST, PUT, DELETE)
  - Request body type (TypeScript interface/type)
  - Response type (TypeScript interface/type)
  - Field names and types from the request/response interfaces
```

---

## Phase 2: Extract Backend Contract

Detect how the backend defines API routes:

```
.NET:
  [Route("api/orders")]
  [HttpGet("get-all")] → full path: api/orders/get-all
  Method signature: Task<IActionResult> GetAll()
  [FromBody] OrderCreateDto dto → request body type
  Return type: wrapped in GetResultDtoAsync → extract inner DTO

Express/NestJS:
  router.get("/api/endpoint", handler)
  @Get("/endpoint") → extract path
  Request body: req.body typed or validated by schema

FastAPI:
  @app.get("/api/endpoint", response_model=ResponseType)
  Request body: Pydantic model

Django:
  urlpatterns path("api/endpoint", view)
  Serializer class defines request/response shape

Spring:
  @GetMapping("/api/endpoint")
  @RequestBody CreateDto dto → request body
  Return type: ResponseEntity<Dto>

Extract per endpoint:
  - URL path
  - HTTP method
  - Request body DTO (field names and types)
  - Response DTO (field names and types)
```

---

## Phase 3: Compare Contracts

For each endpoint, compare FE and BE:

### URL Match
```
FE: "api/orders/get-all" (GET)
BE: [Route("api/orders")] + [HttpGet("get-all")] → "api/orders/get-all" (GET)
Result: ✓ Match
```

### Field Name Match
```
FE type: { templateId: number, templateKey: string, templateName: string }
BE DTO:  { TemplateId: int, TemplateKey: Guid, TemplateName: string }
Check: Do FE field names match BE field names (accounting for casing)?
  templateId ↔ TemplateId → ✓ (camelCase ↔ PascalCase, auto-converted by JSON serializer)
  templateKey ↔ TemplateKey → ✓
```

### Field Type Match
```
FE: templateKey: string
BE: TemplateKey: Guid
Question: Does Guid serialize to string in JSON? → Yes ✓

FE: createdDate: string
BE: CreatedDate: DateTime
Question: Does DateTime serialize to string (ISO format)? → Yes ✓

FE: templateId: number
BE: TemplateId: int
Question: Does int serialize to number? → Yes ✓

FE: isDefault: boolean
BE: IsDefault: bool
Question: Does bool serialize to boolean? → Yes ✓
```

### Common Type Mappings (auto-detected per stack)
```
.NET → TypeScript:
  int, long → number
  decimal, double, float → number
  string → string
  bool → boolean
  DateTime → string (ISO 8601)
  Guid → string
  List<T> → T[]
  IList<T> → T[]
  T? (nullable) → T | null | undefined

Python → TypeScript:
  int, float → number
  str → string
  bool → boolean
  datetime → string
  uuid → string
  List[T] → T[]
  Optional[T] → T | null

Java → TypeScript:
  int, long, Integer, Long → number
  String → string
  boolean, Boolean → boolean
  LocalDateTime → string
  UUID → string
  List<T> → T[]
```

---

## Phase 4: Report Results

```
API Contract Validation: api/orders

  ✓ GET  /get-all          → URL match, response types match
  ✓ GET  /get-by-id/{id}   → URL match, response types match
  ✓ POST /create           → URL match, request body match, response match
  ✗ PUT  /update/{key}     → FE sends templateKey as string, BE expects Guid
    Fix: Guid auto-parses from string — OK at runtime, but FE type should be string
  ✓ DELETE /delete/{key}   → URL match

  Missing in FE: GET /get-by-key/{key} (BE endpoint exists, no FE service call)
  Missing in BE: (none)
```

---

## Phase 5: Auto-Fix Common Issues

### Missing FE service function for existing BE endpoint:
```
→ Generate the service function following the project's detected conventions
  (see the frontend-patterns skill cache at .claude/idev/frontend-patterns/cache.md)
```

### Missing BE endpoint for existing FE service call:
```
→ Flag as error — this causes 404 at runtime
  (see the lessons-learned skill log if present for past instances)
```

### Type mismatch:
```
→ If auto-serializable (Guid→string, DateTime→string): warn but pass
→ If incompatible (number↔string, boolean↔string): fail and suggest fix
```

### Field name mismatch:
```
→ Check if JSON serializer handles casing (camelCase ↔ PascalCase)
→ If custom serialization: flag for manual review
```

---

## Phase 6: Cache Format

Write to `.claude/idev/api-contract-validation/cache.json`:

```json
{
  "generated": "YYYY-MM-DD",
  "contracts": [
    {
      "endpoint": "api/orders/get-all",
      "httpMethod": "GET",
      "feService": "relative/path/to/service.ts",
      "feFunction": "getOrders",
      "feResponseType": "Order[]",
      "beController": "relative/path/to/Controller.cs",
      "beMethod": "GetAll",
      "beResponseType": "IList<OrderDto>",
      "status": "valid|mismatch|missing-fe|missing-be",
      "issues": []
    }
  ],
  "typeMapping": {
    "serializationFormat": "System.Text.Json|Newtonsoft|json",
    "casingConversion": "camelCase (auto)"
  }
}
```

---

## Phase 7: Documentation Output (Optional)

When asked to generate API contract docs (or after validating a full feature), write one compact doc per feature to `.claude/idev/api-contracts/<feature>.md`:

```markdown
# Orders API Contract
> Updated: YYYY-MM-DD | Source: api-contract-validation

| Method | Endpoint              | FE function   | Request        | Response       | Status |
|--------|-----------------------|---------------|----------------|----------------|--------|
| GET    | api/orders/get-all    | getOrders     | —              | OrderDto[]     | valid  |
| POST   | api/orders/create     | createOrder   | OrderCreateDto | OrderDto       | valid  |
| PUT    | api/orders/update/{k} | updateOrder   | OrderUpdateDto | OrderDto       | type mismatch: key string↔Guid |

Notes:
- Auth: all endpoints require [Authorize]
- Casing: camelCase ↔ PascalCase (auto via System.Text.Json)
```

Rules:
- Keep each doc under ~40 lines — a table plus brief notes, not prose
- Update the existing doc in place; do not duplicate
- Derive entries from the validation cache (Phase 6) rather than re-scanning source
- Paths: cache lives at `.claude/idev/api-contract-validation/cache.json`; generated docs live in `.claude/idev/api-contracts/`

---

## Anti-Patterns

1. Do NOT assume casing matches — check JSON serializer config
2. Do NOT flag Guid→string as a type error — it serializes fine
3. Do NOT skip validation for "simple" endpoints — validate all
4. Do NOT run full validation after every single file change — run after feature completion
5. Do NOT hardcode type mappings — detect serializer and derive them
