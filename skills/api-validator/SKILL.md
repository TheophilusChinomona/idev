---
name: api-validator
description: Validates FE↔BE API alignment, detects mismatches, broken calls, unused endpoints, and type inconsistencies.
priority: high
auto_trigger: true
user_invocable: true
command: /api-check
model: haiku
integrates_with:
  - smart-context
  - project-map
  - api-docs-sync
config_source: .claude/idev/project-map/watcher_config.json
takes_priority_over:
  - security-reviewer (for API-related security)
generic: true
---

# API Validator

Validates synchronization between Frontend API calls and Backend endpoints. Detects misalignments, broken calls, unused endpoints, and type mismatches.

**IMPORTANT**: This skill is ALWAYS ACTIVE. It performs an initial full scan to establish baseline, then proactively monitors for changes.

**GENERIC**: This skill auto-detects project stack and patterns. Works with any FE/BE combination.

---

## AUTO-DETECTION (GENERIC FOR ANY PROJECT)

This skill automatically detects the project's technology stack and API patterns.

### Stack Detection

```
1. Check package.json → Detect FE framework
   - "react" → React (axios, fetch patterns)
   - "vue" → Vue (axios patterns)
   - "angular" → Angular (HttpClient patterns)
   - "next" → Next.js (fetch, API routes)

2. Check for BE indicators:
   - *.csproj → .NET (Controllers, [Http*] attributes)
   - package.json with "express" → Node/Express (app.get/post)
   - pom.xml or build.gradle → Java Spring (@GetMapping, @PostMapping)
   - requirements.txt with "django/flask/fastapi" → Python

3. If watcher_config.json exists → Use configured paths
4. If not → Auto-detect from project structure
```

### FE API Call Patterns (Auto-Detected)

| Framework | Pattern to Grep | Example |
|-----------|-----------------|---------|
| React/Vue | `axios\.(get\|post\|put\|delete)` | `axios.get('/api/users')` |
| React/Vue | `\.get\(\|\.post\(\|\.put\(` | `api.get('/users')` |
| Angular | `http\.(get\|post\|put\|delete)` | `this.http.get('/api/users')` |
| Next.js | `fetch\(.*\/api` | `fetch('/api/users')` |
| Generic | `\/api\/` | Any API path reference |

### BE Endpoint Patterns (Auto-Detected)

| Framework | Pattern to Grep | Example |
|-----------|-----------------|---------|
| .NET | `\[Http(Get\|Post\|Put\|Delete)` | `[HttpGet("users")]` |
| Express | `\.(get\|post\|put\|delete)\(["']\/` | `app.get('/api/users')` |
| Spring | `@(Get\|Post\|Put\|Delete)Mapping` | `@GetMapping("/users")` |
| FastAPI | `@app\.(get\|post\|put\|delete)` | `@app.get("/users")` |
| Django | `path\(.*,.*view` | `path('users/', views.list)` |

### File Patterns (Auto-Detected)

| Stack | FE Service Files | BE Controller Files |
|-------|------------------|---------------------|
| React + .NET | `*Service.ts`, `*.service.ts` | `*Controller.cs` |
| React + Express | `*Service.ts`, `*Api.ts` | `*Router.js`, `*Controller.js` |
| Vue + .NET | `*Service.ts`, `*Api.ts` | `*Controller.cs` |
| Angular + Spring | `*.service.ts` | `*Controller.java` |
| Next.js + Node | `*Api.ts`, `/api/**/*.ts` | `/api/**/*.ts` (API routes) |

### Auto-Detection Flow

```
IF watcher_config.json exists:
  → Use configured paths
ELSE:
  1. Scan root for package.json, *.csproj, pom.xml, etc.
  2. Detect FE framework from dependencies
  3. Detect BE framework from file patterns
  4. Build pattern list for this stack
  5. Cache detection in index.json for future use
```

### Generic Endpoint Discovery

```
1. Glob for service/controller files using detected patterns
2. Grep for API call patterns using detected framework
3. Extract: method, path, line number
4. Build endpoint map regardless of specific stack
```

---

## INITIALIZATION (FIRST SCAN)

### When First Scan Triggers

The initial full scan happens when **ALL** of these are true:

1. **No validation report exists** (`.claude/idev/api-contracts/validation-report.md` doesn't exist)
2. **watcher_config.json exists** (has FE/BE paths configured)
3. **User makes ANY FE↔BE code change** (triggers initialization check)

### NOT Triggered By

- Just opening a session (no proactive scanning on session start)
- Reading files (only writing/modifying triggers check)
- Non-API changes (CSS, tests, configs)

### First Scan Flow

```
User modifies service/controller file
           ↓
Check: Does validation-report.md exist?
  ├─ YES → Normal proactive monitoring
  └─ NO → Check watcher_config.json
           ├─ EXISTS → RUN FULL INITIALIZATION SCAN
           └─ MISSING → Alert: "Run map_watcher.py first"
```

### Manual Trigger

User can force full scan anytime with:
```
/api-check --init       → Force full initialization scan
/api-check --full       → Complete re-scan of all endpoints
```

---

## INITIALIZATION SCAN PROCESS

### Step 1: Load Configuration

```
1. Load index.json → Get all features
2. Load watcher_config.json → Get FE/BE paths
3. Verify paths exist
```

### Step 2: Discover All Endpoints

```
FE Discovery (Grep-based, low token):
  1. Glob: Find all *Service.ts files in FE path
  2. For each service file:
     a. Grep for api.(get|post|put|delete|patch)
     b. Extract: method, path, line number
     c. Build FE endpoint map

BE Discovery (Grep-based, low token):
  1. Glob: Find all *Controller.cs files in BE path
  2. For each controller file:
     a. Grep for [Http(Get|Post|Put|Delete|Patch)]
     b. Extract: method, route, line number
     c. Build BE endpoint map
```

### Step 3: Cross-Reference & Validate

```
For each FE endpoint:
  1. Find matching BE endpoint (path + method)
  2. If found → Mark as IN SYNC
  3. If not found → Mark as CRITICAL: Missing BE endpoint

For each BE endpoint:
  1. Find matching FE caller
  2. If found → Already marked IN SYNC
  3. If not found → Mark as LOW: Unused endpoint
```

### Step 4: Generate Baseline Report

Create `.claude/idev/api-contracts/validation-report.md`:

```markdown
# API Validation Report (Baseline)

**Generated:** YYYY-MM-DD HH:MM
**Type:** INITIALIZATION SCAN
**FE Path:** [from watcher_config]
**BE Path:** [from watcher_config]

---

## Summary

| Status | Count |
|--------|-------|
| In Sync | XX |
| Missing BE (CRITICAL) | XX |
| Missing FE (Type Mismatch) | XX |
| Unused BE (LOW) | XX |

**Overall Health:** HEALTHY / WARNING / CRITICAL

---

## CRITICAL Issues (Require Immediate Fix)

### Missing Backend Endpoints

| FE Call | Expected BE | Status |
|---------|-------------|--------|
| POST /api/orders/archive | OrdersController | NOT FOUND |
| GET /api/users/preferences | UserController | NOT FOUND |

### Method Mismatches

| Endpoint | FE Method | BE Method | Status |
|----------|-----------|-----------|--------|
| /api/orders/close | POST | PUT | MISMATCH |

---

## HIGH Issues (Fix Soon)

[Type mismatches, auth issues]

---

## LOW Issues (Review)

### Unused Backend Endpoints

| BE Endpoint | Controller | No FE Caller |
|-------------|------------|--------------|
| GET /api/orders/stats | OrdersController:289 | UNUSED |
| POST /api/orders/bulk | OrdersController:312 | UNUSED |

---

## Healthy Endpoints (In Sync)

| Endpoint | FE Service | BE Controller | Status |
|----------|------------|---------------|--------|
| GET /api/orders | OrderService:45 | OrdersController:139 | IN SYNC |
| POST /api/orders/create | OrderService:78 | OrdersController:27 | IN SYNC |
| PUT /api/orders/{id} | OrderService:92 | OrdersController:107 | IN SYNC |

---

## Next Steps

1. Fix CRITICAL issues (missing endpoints cause runtime errors)
2. Review HIGH issues (may cause data problems)
3. Decide on unused endpoints (remove or document as external API)
4. Run `/api-check` after fixes to update report

---

*Baseline established. Proactive monitoring now active.*
*Run `/api-check --full` to regenerate complete report.*
```

### Step 5: Update API Docs

After initialization scan:

```
1. For each CRITICAL (missing BE):
   → Add to pending-backend.md

2. For each unused BE endpoint:
   → Add to pending-frontend.md (if should be used)
   → OR mark as "External/Internal Only" in contract

3. For each IN SYNC endpoint:
   → Create/update contract in contracts/[feature].contract.md
```

### Step 6: Enable Proactive Monitoring

After initialization:
- validation-report.md exists → Proactive mode active
- Future changes → Quick validation only (not full scan)
- Periodic full scan → User runs `/api-check --full`

---

## INITIALIZATION ALERT FORMAT

```
API VALIDATION INITIALIZATION
=============================
Status: RUNNING FIRST SCAN
FE Path: [path]
BE Path: [path]

Discovering endpoints...
  FE Services: XX files, YY endpoints
  BE Controllers: XX files, YY endpoints

Cross-referencing...
  In Sync: XX
  Missing BE: XX (CRITICAL)
  Unused BE: XX (LOW)

Report: .claude/idev/api-contracts/validation-report.md
Tokens used: ~XXX

Proactive monitoring now ACTIVE.
=============================
```

---

## PROACTIVE BEHAVIOR (AUTO-TRIGGER)

### When Claude Automatically Validates

Claude MUST run validation when:

1. **After editing FE service files** - Check if BE endpoint exists
2. **After editing BE controller files** - Check if FE calls are still valid
3. **After adding new API calls** - Verify endpoint exists
4. **After modifying endpoint routes** - Check FE callers still work
5. **After changing request/response types** - Verify type compatibility

### Automatic Actions

```
AFTER any FE↔BE code change:

1. Quick validation (path + method check)
2. If CRITICAL issue found:
   → Alert user immediately
   → Suggest fix
   → Update pending docs if endpoint missing

3. If alignment confirmed:
   → Update api-docs-sync contracts if changed
   → No alert needed (silent success)
```

### Alert Format (Proactive)

```
API VALIDATION ALERT
====================
Status: MISMATCH DETECTED
Change: [what was just modified]
Issue: [what's wrong]
Impact: [runtime error type]
Fix: [how to resolve]
====================
```

### Silent Success (No Alert)

When validation passes after a change:
- Update contract if endpoint signature changed
- No interruption to user
- Log: `API sync verified: [endpoint]`

---

## AUTO-UPDATE DOCUMENTATION

When validation detects changes, Claude MUST update api-docs-sync documentation:

### On New FE API Call (No BE Endpoint)

```
1. Detect: FE added call to non-existent endpoint
2. Action: Add to pending-backend.md
3. Format:

   ## PENDING: [Feature] - [Endpoint]
   **Requested:** [date]
   **FE Call:** [file:line]
   **Endpoint Needed:** [method] [path]
   **Request Type:** [extracted from FE]
   **Response Expected:** [extracted from FE]
```

### On New BE Endpoint (No FE Caller)

```
1. Detect: BE added endpoint with no FE caller
2. Action: Add to pending-frontend.md
3. Format:

   ## AVAILABLE: [Feature] - [Endpoint]
   **Created:** [date]
   **BE Endpoint:** [file:line]
   **Method:** [HTTP method]
   **Path:** [endpoint path]
   **Response Type:** [extracted from BE]
```

### On Endpoint Signature Change

```
1. Detect: Method, path, or types changed
2. Action: Update existing contract in contracts/[feature].contract.md
3. Log:

   API DOCS AUTO-UPDATED
   =====================
   Contract: [feature].contract.md
   Endpoint: [method] [path]
   Changed: [what changed]
   =====================
```

### On Endpoint Removed

```
1. Detect: Endpoint deleted from BE or call removed from FE
2. Action:
   - Mark as DEPRECATED in contract
   - Move to "Recently Removed" section
   - Keep for 7 days before full deletion
3. Log:

   API ENDPOINT DEPRECATED
   =======================
   Endpoint: [method] [path]
   Reason: [BE removed / FE removed]
   Action: Marked deprecated in contract
   =======================
```

---

## Commands

### `/api-check` - Full Validation

Runs complete FE↔BE validation and generates report.

```
/api-check              → Full scan of all endpoints
/api-check jobs         → Scan only jobs feature
/api-check --quick      → Quick scan (signatures only, no types)
```

### `/api-check mismatches` - Show Only Issues

Shows only misaligned or broken endpoints.

### `/api-check unused` - Unused Endpoints

Shows BE endpoints with no FE calls.

### `/api-check missing` - Missing Endpoints

Shows FE calls targeting non-existent BE endpoints.

---

## What Gets Validated

### 1. Endpoint Existence
- FE calls an endpoint → Does BE have it?
- BE has an endpoint → Does FE use it?

### 2. HTTP Method Match
- FE calls `GET /api/orders` → BE must have `[HttpGet]` on `/api/orders`
- FE calls `POST /api/orders` → BE must have `[HttpPost]` on `/api/orders`

### 3. Path Match
- FE path matches BE route exactly
- Path parameters align (`{id}` vs `:id`)

### 4. Type Compatibility
- FE request type matches BE DTO
- FE response type matches BE return type
- Optional/required fields align

### 5. Authentication Requirements
- FE expects auth → BE has `[Authorize]`
- Public FE call → BE has `[AllowAnonymous]`

---

## Validation Workflow

### Step 1: Gather Data (Low Token)

```
1. Load index.json → Get features list
2. Load watcher_config.json → Get FE/BE paths
3. Grep FE services for API calls
4. Grep BE controllers for endpoints
5. Build comparison map
```

### Step 2: Compare Endpoints

```
For each FE API call:
  1. Extract: method, path, request type, response type
  2. Find matching BE endpoint
  3. Compare:
     - Method matches?
     - Path matches?
     - Types compatible?
     - Auth requirements match?
  4. Flag any mismatches
```

### Step 3: Find Orphans

```
FE orphans (broken calls):
  - FE calls endpoint that doesn't exist in BE
  - FE expects response type BE doesn't return

BE orphans (unused endpoints):
  - BE endpoint with no FE caller
  - May be intentional (external API, scheduled jobs)
```

---

## Extraction Patterns

### Frontend (React/TypeScript)

```typescript
// Pattern 1: Direct API calls
await api.get('/api/orders')
await api.post('/api/orders', data)
await api.put(`/api/orders/${id}`)
await api.delete(`/api/orders/${id}`)

// Pattern 2: Axios instance calls
const response = await axios.get<JobDto>('/api/orders')

// Pattern 3: Fetch calls
fetch('/api/orders', { method: 'POST', body: JSON.stringify(data) })

// Extract:
// - HTTP method (get, post, put, delete)
// - Endpoint path (/api/orders, /api/orders/${id})
// - Request type (from second parameter or generic)
// - Response type (from generic <T>)
```

### Backend (.NET/C#)

```csharp
// Pattern 1: Route attributes
[Route("api/[controller]")]  // Base route
[HttpGet]                    // GET /api/orders
[HttpGet("{id}")]           // GET /api/orders/{id}
[HttpPost]                   // POST /api/orders
[HttpPut("{id}")]           // PUT /api/orders/{id}
[HttpDelete("{id}")]        // DELETE /api/orders/{id}

// Pattern 2: Custom routes
[HttpGet("search")]         // GET /api/orders/search
[HttpPost("create")]        // POST /api/orders/create

// Extract:
// - Controller name (OrdersController → /api/orders)
// - HTTP method ([HttpGet], [HttpPost], etc.)
// - Route template ({id}, search, etc.)
// - Auth attribute ([Authorize], [AllowAnonymous])
// - Parameter types ([FromBody] CreateJobDto)
// - Return type (Task<ActionResult<JobDto>>)
```

---

## Mismatch Categories

### CRITICAL - Broken Functionality

| Issue | Description | Impact |
|-------|-------------|--------|
| Missing Endpoint | FE calls endpoint BE doesn't have | Runtime error (404) |
| Method Mismatch | FE uses POST, BE expects GET | Runtime error (405) |
| Path Mismatch | FE path doesn't match BE route | Runtime error (404) |

### HIGH - Data Issues

| Issue | Description | Impact |
|-------|-------------|--------|
| Type Mismatch | FE sends/expects different type than BE | Data loss, errors |
| Missing Required Field | FE doesn't send field BE requires | Validation error (400) |
| Extra Field | FE sends field BE doesn't accept | Ignored or error |

### MEDIUM - Auth Issues

| Issue | Description | Impact |
|-------|-------------|--------|
| Auth Mismatch | FE expects public, BE requires auth | Unauthorized (401) |
| Role Mismatch | FE expects user, BE requires admin | Forbidden (403) |

### LOW - Unused Code

| Issue | Description | Impact |
|-------|-------------|--------|
| Unused BE Endpoint | BE has endpoint FE never calls | Dead code |
| Deprecated FE Call | FE calls old endpoint | May break later |

---

## Report Format

```markdown
# API Validation Report

**Generated:** YYYY-MM-DD HH:MM
**FE Path:** [from watcher_config]
**BE Path:** [from watcher_config]

---

## Summary

| Status | Count |
|--------|-------|
| In Sync | XX |
| Mismatched | XX |
| FE Missing BE | XX |
| BE Unused | XX |

**Overall Status:** HEALTHY / WARNING / CRITICAL

---

## CRITICAL Issues (Fix Immediately)

### 1. Missing Endpoint: POST /api/orders/archive

**FE Call:**
```typescript
// src/services/order.service.ts:145
await api.post('/api/orders/archive', { jobId, reason })
```

**BE Status:** NOT FOUND

**Impact:** FE will get 404 error when calling this endpoint.

**Resolution:**
- Create endpoint in OrdersController.cs
- OR remove FE call if no longer needed
- OR update FE to use correct endpoint

---

### 2. Method Mismatch: /api/orders/{id}/close

**FE Call:**
```typescript
// src/services/order.service.ts:178
await api.post(`/api/orders/${id}/close`)  // POST
```

**BE Endpoint:**
```csharp
// OrdersController.cs:226
[HttpPut("close/{jobKey}")]  // PUT, not POST!
```

**Impact:** FE will get 405 Method Not Allowed.

**Resolution:**
- Change FE to use `api.put()` instead of `api.post()`

---

## HIGH Issues (Fix Soon)

### 1. Type Mismatch: GET /api/orders

**FE Expects:**
```typescript
interface Job {
  jobId: number
  title: string
  status: string  // FE expects string
}
```

**BE Returns:**
```csharp
public class JobDto {
  public int JobId { get; set; }
  public string Title { get; set; }
  public JobStatus Status { get; set; }  // BE returns enum
}
```

**Impact:** FE may not handle enum values correctly.

**Resolution:**
- Update FE type to use enum union: `'Draft' | 'Active' | 'Closed'`
- OR ensure BE serializes enum as string

---

## MEDIUM Issues (Review)

### 1. Auth Mismatch: GET /api/orders/public

**FE Call:** No auth header sent
**BE Endpoint:** Has `[Authorize]` attribute

**Impact:** Unauthenticated users will get 401.

**Resolution:**
- Add `[AllowAnonymous]` to BE if endpoint should be public
- OR add auth to FE call

---

## LOW Issues (Optional)

### Unused BE Endpoints

| Endpoint | Controller | Last Modified |
|----------|------------|---------------|
| GET /api/orders/stats | OrdersController:289 | 2025-12-15 |
| POST /api/orders/bulk-update | OrdersController:312 | 2025-11-20 |

**Recommendation:** Review if these are needed or can be removed.

---

## In Sync (Healthy)

| FE Call | BE Endpoint | Status |
|---------|-------------|--------|
| GET /api/orders | OrdersController.GetAll | IN SYNC |
| GET /api/orders/{id} | OrdersController.GetById | IN SYNC |
| POST /api/orders/create | OrdersController.Create | IN SYNC |
| PUT /api/orders/{id} | OrdersController.Update | IN SYNC |
| DELETE /api/orders/{id} | OrdersController.Delete | IN SYNC |

---

## Recommendations

1. **Fix CRITICAL issues immediately** - These cause runtime errors
2. **Review HIGH issues** - May cause data problems
3. **Consider removing unused endpoints** - Reduces maintenance burden
4. **Update api-docs-sync contracts** - Keep documentation in sync

---

*Report generated by Claude's api-validator skill*
*Run `/api-check` to regenerate*
```

---

## Grep Patterns for Extraction

### FE API Calls (TypeScript)

```bash
# Find all API calls in services
Grep "api\.(get|post|put|delete|patch)\(" --type ts

# Find fetch calls
Grep "fetch\(['\"]" --type ts

# Find axios calls
Grep "axios\.(get|post|put|delete)" --type ts

# Extract endpoint paths
Grep "/api/" --type ts
```

### BE Endpoints (C#)

```bash
# Find all HTTP method attributes
Grep "\[Http(Get|Post|Put|Delete|Patch)" --type cs

# Find route attributes
Grep "\[Route\(" --type cs

# Find controller classes
Grep "class.*Controller" --type cs

# Find authorize attributes
Grep "\[Authorize" --type cs
```

---

## LOW-TOKEN OPERATION (CRITICAL)

This skill follows smart-context principles to minimize token usage while delivering high value.

### Token-Efficient Lookup Order

```
1. Existing contracts     → CHECK FIRST (documented state, ~0 tokens)
2. index.json            → Feature detection (~70 tokens)
3. watcher_config.json   → FE/BE paths (~10 tokens)
4. Grep project-map      → File paths only (~50 tokens)
5. Grep source files     → Signatures only (~100 tokens)
6. Read source files     → LAST RESORT (~500+ tokens)
```

### What NOT to Do (Token Waste)

```
❌ Load full project-map.md
❌ Read all service files to "understand the project"
❌ Re-scan everything on every validation
❌ Read full files when Grep gives enough info
❌ Validate all endpoints when only one changed
```

### Data Source Priority

```
1. Existing contracts    → Already documented, use as baseline
2. index.json           → What features exist (~70 lines)
3. Grep project-map     → File paths only (minimal tokens)
4. Grep source files    → Endpoint signatures only
5. Read source files    → LAST RESORT (only specific lines)
```

---

## INTEGRATION WITH SMART_CONTEXT + PROJECT_MAP

This skill uses a **layered approach** identical to api-docs-sync for minimal token usage.

### Layer 1: index.json (ALWAYS LOAD FIRST)

```json
// .claude/idev/smart-context/index.json (~80 lines)
{
  "features": ["Orders", "Customers", "Reports", "Auth", ...],
  "structure": {
    "controllers": "{{backend_root}}/Controllers",
    "services": "{{frontend_root}}/.../services"
  },
  "docs": {
    "api_contracts": ".claude/idev/api-contracts/contracts/"
  },
  "patterns": {
    "service": "*Service.*",
    "controller": "*Controller.*"
  }
}
```

**Use for:**
- Feature detection (what endpoints might exist)
- Path patterns (where to look)
- Skip features not relevant to current validation

### Layer 2: watcher_config.json (Get Paths)

```json
// .claude/idev/project-map/watcher_config.json
{
  "frontend_path": "{{frontend_root absolute path}}",
  "backend_path": "{{backend_root absolute path}}"
}
```

**Use for:**
- Know exact FE/BE root directories
- Scope Grep searches to correct paths

### Layer 3: Existing Contracts (Check Before Scanning)

```
.claude/idev/api-contracts/contracts/
  └─ If [feature].contract.md exists → USE IT as baseline
  └─ Compare code against documented contract
  └─ Don't rescan what's already validated
```

**Use for:**
- Baseline for comparison
- Avoid redundant validation work

### Layer 4: Grep Project Map (Paths Only)

```bash
# Get file paths without reading content
Grep project.map.md "OrderService" → src/Services/OrderService.ts
Grep project.map.md "OrdersController" → Controllers/OrdersController.cs
```

**Use for:**
- Finding file locations
- No need to search entire codebase

### Layer 5: Grep Source Files (Signatures Only)

```bash
# Get endpoint signatures, not full code
Grep OrderService.ts "api\.(get|post|put|delete)" -A 1
Grep OrdersController.cs "\[Http" -A 1
```

**Use for:**
- Endpoint discovery without full file read
- Extract method + path only

### Layer 6: Read Source (LAST RESORT)

```
Only read specific lines when:
- Validating type compatibility
- Resolving ambiguous mismatches
- User explicitly requests detail
- Need DTO/interface definitions
```

### Token Cost Comparison

| Approach | Tokens | When to Use |
|----------|--------|-------------|
| Use existing contract | ~0 | Baseline comparison |
| index.json | ~70 | Feature detection |
| watcher_config.json | ~10 | Path lookup |
| Grep project-map | ~50 | File paths |
| Grep source | ~100 | Signatures |
| Read full file | ~500-2000 | Type validation |

### Validation Flow Diagram

```
Code change detected
       ↓
Load index.json (features list)
       ↓
Load watcher_config.json (FE/BE paths)
       ↓
Check: Does contract exist for this feature?
  ├─ YES → Use contract as baseline
  └─ NO → Quick Grep scan
       ↓
Grep changed file for endpoints
       ↓
Grep counterpart (FE→BE or BE→FE)
       ↓
Compare: paths + methods match?
  ├─ YES → Silent success, update contract if changed
  └─ NO → Alert user, suggest fix
       ↓
Only read full files if type validation needed
```

---

## PROACTIVE VALIDATION WORKFLOW

### On FE Service File Change

```
1. Detect: File matches *Service.ts pattern
2. Load: index.json → Get feature name
3. Load: watcher_config.json → Get BE path
4. Grep: Changed file for api.* calls
5. For each API call found:
   a. Extract method + path
   b. Grep BE controllers for matching route
   c. If match → Validate method matches
   d. If no match → Flag as MISSING ENDPOINT
6. Update: contracts/[feature].contract.md if needed
7. Alert: Only if issues found
```

### On BE Controller File Change

```
1. Detect: File matches *Controller.cs pattern
2. Load: index.json → Get feature name
3. Load: watcher_config.json → Get FE path
4. Grep: Changed file for [Http*] attributes
5. For each endpoint found:
   a. Extract method + route
   b. Grep FE services for matching API call
   c. If match → Validate method matches
   d. If no match → Flag as UNUSED ENDPOINT (LOW)
6. Update: contracts/[feature].contract.md if needed
7. Alert: Only if CRITICAL/HIGH issues found
```

### Targeted Validation (Single Endpoint)

When only one endpoint changed:

```
1. Extract: endpoint path from changed code
2. Grep: Counterpart for that specific path
3. Validate: Just this one endpoint
4. Skip: All other endpoints (already validated)

Token cost: ~100-150 tokens (vs ~1000 for full scan)
```

---

## Integration with Other Skills

### With smart-context

```
1. ALWAYS load index.json first
2. Use features list to scope validation
3. Use patterns for file detection
4. Use structure paths for targeted search
```

### With project-map

```
1. Get FE/BE paths from watcher_config.json
2. Grep project.map.md for file locations (don't read full map)
3. Use file patterns from index.json
4. Never scan entire codebase
```

### With api-docs-sync

```
1. Load existing contracts as validation baseline
2. After validation, update contracts if changes detected
3. Add to pending-backend.md if FE needs new endpoint
4. Add to pending-frontend.md if BE has unused endpoint
5. Mark endpoints deprecated if removed
```

### Skill Loading Order

```
1. smart-context/index.json  → What features exist
2. watcher_config.json       → Where FE/BE code lives
3. api-contracts/contracts/  → What's already documented
4. project-map (Grep)        → Where specific files are
5. Source files (Grep/Read)  → Actual code (minimize)
```

---

## Quick Validation (Low Token)

For `/api-check --quick`:

```
1. Grep FE for endpoint paths only (no types)
2. Grep BE for route attributes only (no DTOs)
3. Compare paths and methods
4. Report mismatches without type analysis

Token cost: ~200-300 tokens
```

## Full Validation

For `/api-check`:

```
1. Quick validation first
2. For mismatches, read specific files
3. Extract and compare types
4. Generate detailed report

Token cost: ~500-1000 tokens depending on issues
```

---

## Automation Suggestions

### Pre-Commit Hook

```bash
# .husky/pre-commit
claude --skill api-validator --command "/api-check --quick"
# Fails commit if CRITICAL issues found
```

### CI/CD Integration

```yaml
# .github/workflows/api-check.yml
- name: API Validation
  run: claude code "/api-check" --fail-on-critical
```

### Scheduled Check

Run weekly to catch drift:
```
/api-check --full > reports/api-validation-$(date +%Y%m%d).md
```

---

## Error Handling

### If FE Path Not Found

```
ERROR: Frontend path not found
Path: [from watcher_config]

Resolution:
1. Check watcher_config.json has correct frontend_path
2. Run map_watcher.py to update paths
3. Verify frontend directory exists
```

### If BE Path Not Found

```
ERROR: Backend path not found
Path: [from watcher_config]

Resolution:
1. Check watcher_config.json has correct backend_path
2. Run map_watcher.py to update paths
3. Verify backend directory exists
```

### If No Endpoints Found

```
WARNING: No API endpoints detected

Possible causes:
1. Non-standard API patterns
2. Different file structure
3. Incorrect path configuration

Try:
- /api-check --verbose for detailed search
- Check if services use different naming convention
```

---

## Best Practices

1. **Run after major changes** - New features, refactors
2. **Run before releases** - Catch issues before production
3. **Fix CRITICAL first** - These break functionality
4. **Review unused endpoints** - May be intentional or dead code
5. **Keep contracts updated** - Use api-docs-sync after fixes
6. **Automate in CI** - Catch drift early

---

*This skill validates reality against expectations. api-docs-sync documents what should be, api-validator checks what actually is.*
