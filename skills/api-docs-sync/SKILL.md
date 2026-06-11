---
name: api-docs-sync
description: Auto-generates and maintains FE↔BE API contract documentation
priority: high
auto_trigger: true
model: haiku
integrates_with:
  - smart-context
  - project-map
config_source: .claude/idev/project-map/watcher_config.json
generic: true
---

# API Documentation Sync

Automatically creates and maintains synchronized documentation between Frontend and Backend developers.

**IMPORTANT**: This skill is ALWAYS ACTIVE. After any code change that affects the FE↔BE contract, Claude MUST update the relevant documentation.

**GENERIC**: This skill auto-detects project stack and patterns. Works with any FE/BE combination.

---

## AUTO-DETECTION (GENERIC FOR ANY PROJECT)

This skill automatically detects the project's technology stack and adapts its patterns.

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
   - pom.xml or build.gradle → Java Spring (@GetMapping)
   - requirements.txt with "django/flask/fastapi" → Python
```

### Supported Stacks

| FE Framework | BE Framework | Service Pattern | Controller Pattern |
|--------------|--------------|-----------------|-------------------|
| React | .NET | `*Service.ts` | `*Controller.cs` |
| React | Express | `*Service.ts` | `*Router.js` |
| Vue | .NET | `*Service.ts` | `*Controller.cs` |
| Angular | Spring | `*.service.ts` | `*Controller.java` |
| Next.js | Node | `/api/**/*.ts` | `/api/**/*.ts` |

### Auto-Adapt Documentation

Based on detected stack, adapt documentation format:

- **.NET BE**: Document C# DTOs, `[Authorize]` attributes, ActionResult types
- **Express BE**: Document req.body schemas, middleware, res.json patterns
- **Spring BE**: Document `@RequestBody`, ResponseEntity, annotations
- **FastAPI BE**: Document Pydantic models, Path/Query params

---

## WHEN DOES FIRST SCAN HAPPEN?

### Trigger Conditions

The first scan is triggered when **ALL** of these are true:

1. **User makes a code change** that touches FE↔BE (service file, controller, API call)
2. **Contracts directory is empty** (`.claude/idev/api-contracts/contracts/` has no `.contract.md` files)
3. **watcher_config.json exists** (has FE/BE paths configured)

### NOT Triggered By

- Just opening a session (no proactive scanning)
- Reading files (only writing/modifying triggers check)
- Non-API changes (CSS, tests, configs)

### Path Configuration (FROM PROJECT_MAP)

The skill reads FE/BE paths from:
```
.claude/idev/project-map/watcher_config.json
```

```json
{
  "frontend_path": "{{frontend_root absolute path}}",
  "backend_path": "{{backend_root absolute path}}"
}
```

**If watcher_config.json doesn't exist:**
- Skip initialization
- Alert user: "Run map_watcher.py first to configure paths"

### First Scan Flow

```
User modifies service/controller file
           ↓
Check: Do contracts exist?
  ├─ YES → Normal update flow
  └─ NO → Check watcher_config.json
           ├─ EXISTS → Run initialization
           └─ MISSING → Alert: "Configure paths first"
```

### Manual Trigger

User can force initialization anytime with:
```
/api-docs init
```

---

## LOW-TOKEN OPERATION (CRITICAL)

This skill follows smart-context principles to minimize token usage while delivering high value.

### Token-Efficient Workflow

```
STEP 1: Check index.json (70 lines)
  └─ Get feature list and file patterns

STEP 2: Check existing contracts first
  └─ .claude/idev/api-contracts/contracts/*.contract.md
  └─ If contract exists for feature → USE IT (don't rescan)

STEP 3: Only if needed, Grep project-map
  └─ Grep for specific feature (e.g., "job.service")
  └─ Get file paths only, not content

STEP 4: Only if needed, Read specific files
  └─ Read only the service/controller being modified
  └─ Extract only endpoint signatures, not full code
```

### What NOT to Do (Token Waste)

```
❌ Load full project-map.md
❌ Read all service files to "understand the project"
❌ Re-scan everything on every change
❌ Read source files when contract already exists
❌ Load full controller files for one endpoint
```

### Data Source Priority

```
1. Existing contracts    → FIRST (already documented, 0 extra tokens)
2. index.json           → Feature detection (70 lines)
3. Grep project-map     → File paths only (minimal tokens)
4. Grep source files    → Endpoint signatures only
5. Read source files    → LAST RESORT (only specific lines)
```

---

## Initialization Check (FIRST PRIORITY)

Before any documentation update, Claude MUST check if documentation exists:

### Step 1: Check Documentation Status

```
Check: .claude/idev/api-contracts/contracts/
  - If directory is empty OR no contract files exist → RUN INITIALIZATION
  - If contract files exist → PROCEED with normal updates (low token)
```

### Step 2: If Initialization Required

Use smart-context + project-map integration:

```
1. Load index.json → Get features list
2. For each feature in index.json:
   a. Grep project-map for "[feature].service"
   b. Grep project-map for "[Feature]Controller"
   c. If both found → Create contract skeleton
   d. If only one found → Add to pending docs
3. Generate minimal contracts (don't read full source)
```

### Smart Initialization Process

```markdown
API DOCS INITIALIZATION (Low Token Mode)
========================================
Using: index.json + project-map (Grep only)

Features detected from index.json:
  Orders, Customers, Payments, Auth, Reports...

Grep project-map for mappings:
  ✓ Orders: orders.service.ts ↔ OrdersController.cs
  ✓ Customers: customers.service.ts ↔ CustomersController.cs
  ✓ Payments: payments.service.ts ↔ PaymentsController.cs
  ...

Generating skeleton contracts:
  → contracts/orders.contract.md (paths only, details TBD)
  → contracts/customers.contract.md
  → contracts/payments.contract.md

Token usage: ~200 tokens (vs ~5000 for full scan)
```

### Skeleton Contract (Minimal Token)

```markdown
# [Feature] API Contract

> Auto-generated: [timestamp]
> Status: SKELETON (details added on first use)

## File Mapping

| Side | File | Status |
|------|------|--------|
| FE | `[path from project-map]` | Found |
| BE | `[path from project-map]` | Found |

## Endpoints

*Populated when this feature is accessed or modified*

---
*Run /api-docs detail [feature] to populate*
```

---

## DETAILED DOCUMENTATION FORMAT (CRITICAL)

When documenting API contracts, Claude MUST capture ALL of the following details:

### Frontend API Call Documentation

When FE makes an API call, document:

```markdown
### [Function Name] → [Endpoint]

**Location:** `src/services/[feature].service.ts:[line]`

#### Call Details

| Aspect | Value |
|--------|-------|
| Method | GET / POST / PUT / DELETE / PATCH |
| Endpoint | `/api/[path]` |
| Auth Required | Yes (JWT) / No |
| Content-Type | application/json |

#### Request Payload

```typescript
// TypeScript interface
interface [RequestName] {
  field1: string       // Required - Description
  field2: number       // Required - Description
  field3?: boolean     // Optional - Description (default: false)
}
```

```json
// Example request body
{
  "field1": "example value",
  "field2": 123,
  "field3": true
}
```

#### Query Parameters (if GET)

| Param | Type | Required | Default | Description |
|-------|------|----------|---------|-------------|
| page | number | No | 1 | Page number |
| limit | number | No | 20 | Items per page |
| filter | string | No | - | Filter criteria |

#### Expected Response

```typescript
// TypeScript interface
interface [ResponseName] {
  success: boolean
  data: {
    id: number
    name: string
    // ... all fields
  }
  message?: string
}
```

```json
// Example success response (200 OK)
{
  "success": true,
  "data": {
    "id": 1,
    "name": "Example"
  }
}
```

#### Error Handling

```typescript
// How FE handles errors
try {
  const response = await api.post('/endpoint', payload)
  return response.data
} catch (error) {
  if (error.response?.status === 400) {
    // Validation error
  }
  if (error.response?.status === 401) {
    // Unauthorized - redirect to login
  }
  if (error.response?.status === 403) {
    // Forbidden - show permission error
  }
  throw error
}
```

#### Usage Context

Where this is called in the FE:
- Component: `[ComponentName].tsx`
- Trigger: User clicks "Save" button
- State updates: Sets `loading`, updates `data` on success
```

### Backend Endpoint Documentation

When BE creates/modifies an endpoint, document:

```markdown
### [Action Name] - [HTTP Method] [Path]

**Location:** `Controllers/[Feature]Controller.cs:[line]`

#### Endpoint Details

| Aspect | Value |
|--------|-------|
| Method | [HttpGet] / [HttpPost] / [HttpPut] / [HttpDelete] |
| Route | `[Route("api/[controller]")]` |
| Full Path | `/api/[feature]/[action]` |
| Auth | [Authorize] / [AllowAnonymous] |
| Roles | [Authorize(Roles = "Admin,Manager")] |

#### Request DTO

```csharp
public class [RequestDto]
{
    [Required]
    [StringLength(200)]
    public string Field1 { get; set; }

    [Range(1, 10000)]
    public int Field2 { get; set; }

    public bool? Field3 { get; set; } = false;
}
```

#### Validation Rules

| Field | Rule | Error Message |
|-------|------|---------------|
| Field1 | Required, Max 200 chars | "Field1 is required" |
| Field2 | Range 1-10000 | "Field2 must be between 1 and 10000" |

#### Response DTO

```csharp
public class [ResponseDto]
{
    public bool Success { get; set; }
    public DataDto Data { get; set; }
    public string Message { get; set; }
}

public class DataDto
{
    public int Id { get; set; }
    public string Name { get; set; }
    public DateTime CreatedAt { get; set; }
}
```

#### Controller Implementation

```csharp
[HttpPost]
[Authorize]
public async Task<ActionResult<ResponseDto>> CreateItem([FromBody] RequestDto dto)
{
    // 1. Validate
    if (!ModelState.IsValid)
        return BadRequest(ModelState);

    // 2. Authorization check
    var userId = User.GetUserId();
    if (!await _service.CanCreate(userId))
        return Forbid();

    // 3. Business logic
    var result = await _service.CreateAsync(dto, userId);

    // 4. Return response
    return Ok(new ResponseDto { Success = true, Data = result });
}
```

#### Response Codes

| Status | Condition | Response Body |
|--------|-----------|---------------|
| 200 OK | Success | `{ success: true, data: {...} }` |
| 400 Bad Request | Validation failed | `{ success: false, errors: {...} }` |
| 401 Unauthorized | No/invalid token | `{ message: "Unauthorized" }` |
| 403 Forbidden | No permission | `{ message: "Access denied" }` |
| 404 Not Found | Resource missing | `{ message: "Not found" }` |
| 500 Error | Server error | `{ message: "Internal error" }` |

#### Database Operations

```csharp
// What this endpoint does to the database
- Creates new record in [TableName]
- Updates [RelatedTable] with foreign key
- Triggers: [any triggers or cascades]
```

#### Business Logic Notes

- Only [Role] can perform this action
- [Field] must be unique per [scope]
- [Notification/Email] is sent after success
- [Audit log] entry is created
```

### Pending Backend Documentation Format

When FE needs a BE endpoint that doesn't exist:

```markdown
## PENDING: [Feature] - [Action]

**Requested:** [date]
**Priority:** CRITICAL / HIGH / MEDIUM / LOW
**Requested by:** FE change in `[file:line]`

### What Frontend Needs

The frontend is calling:
```typescript
// Current FE code
const response = await api.post('/api/jobs/archive', {
  jobId: number,
  reason: string,
  notifyApplicants: boolean
})
```

### Required Endpoint Specification

| Aspect | Requirement |
|--------|-------------|
| Method | POST |
| Path | `/api/jobs/archive` or `/api/jobs/{id}/archive` |
| Auth | Required (JWT) |
| Roles | Job Owner, Admin |

### Request Payload

```typescript
interface ArchiveJobRequest {
  jobId: number           // Required - Job to archive
  reason: string          // Required - Reason for archiving (max 500 chars)
  notifyApplicants: boolean // Optional - Send notification emails (default: false)
}
```

### Expected Response

```typescript
interface ArchiveJobResponse {
  success: boolean
  archivedAt: string      // ISO 8601 datetime
  affectedApplicants: number
  message: string
}
```

### Error Cases to Handle

| Status | When | Response |
|--------|------|----------|
| 400 | Missing reason | `{ error: "Reason is required" }` |
| 403 | Not job owner | `{ error: "Permission denied" }` |
| 404 | Job not found | `{ error: "Job not found" }` |
| 409 | Already archived | `{ error: "Job already archived" }` |

### Business Logic Required

1. Verify user owns the job OR is admin
2. Check job is not already archived
3. Update job status to "Archived"
4. Set archivedAt timestamp
5. If notifyApplicants=true:
   - Get all applicants for this job
   - Send email notification to each
   - Return count of notified applicants
6. Create audit log entry

### Database Changes

- Update `Jobs` table: `Status = 'Archived'`, `ArchivedAt = NOW()`
- Insert into `AuditLog`: action, userId, jobId, timestamp
- If notifyApplicants: Insert into `NotificationQueue`

### Frontend Waiting On

- Component: `JobManagementContainer.tsx`
- Function: `handleArchiveJob()`
- User flow: Job list → Archive button → Confirmation modal → This API
```

### Pending Frontend Documentation Format

When BE has an endpoint FE hasn't implemented:

```markdown
## AVAILABLE: [Feature] - [Action]

**Created:** [date]
**Priority:** MEDIUM
**Provided by:** BE change in `[file:line]`

### Endpoint Available

| Aspect | Value |
|--------|-------|
| Method | GET |
| Path | `/api/users/preferences` |
| Auth | Required |

### How to Call

```typescript
// Add to src/services/user.service.ts

export async function getUserPreferences(): Promise<UserPreferences> {
  const response = await api.get<ApiResponse<UserPreferences>>('/api/users/preferences')
  return response.data.data
}

export async function updateUserPreferences(
  prefs: Partial<UserPreferences>
): Promise<UserPreferences> {
  const response = await api.put<ApiResponse<UserPreferences>>(
    '/api/users/preferences',
    prefs
  )
  return response.data.data
}
```

### Response Type to Add

```typescript
// Add to src/types/user.types.ts

export interface UserPreferences {
  theme: 'light' | 'dark' | 'system'
  emailNotifications: boolean
  language: string           // e.g., "en-ZA"
  timezone: string           // e.g., "Africa/Johannesburg"
  dashboardLayout: 'compact' | 'expanded'
}
```

### Example Response

```json
{
  "success": true,
  "data": {
    "theme": "dark",
    "emailNotifications": true,
    "language": "en-ZA",
    "timezone": "Africa/Johannesburg",
    "dashboardLayout": "expanded"
  }
}
```

### Suggested Implementation

1. **Service Layer** (`user.service.ts`)
   - Add `getUserPreferences()` function
   - Add `updateUserPreferences()` function

2. **Custom Hook** (`useUserPreferences.ts`)
   ```typescript
   export function useUserPreferences() {
     const [prefs, setPrefs] = useState<UserPreferences | null>(null)
     const [loading, setLoading] = useState(true)

     useEffect(() => {
       getUserPreferences()
         .then(setPrefs)
         .finally(() => setLoading(false))
     }, [])

     const update = async (changes: Partial<UserPreferences>) => {
       const updated = await updateUserPreferences(changes)
       setPrefs(updated)
       return updated
     }

     return { prefs, loading, update }
   }
   ```

3. **Use in Component** (`SettingsPage.tsx`)
   ```typescript
   const { prefs, loading, update } = useUserPreferences()

   if (loading) return <Spinner />

   return (
     <PreferencesForm
       values={prefs}
       onSave={update}
     />
   )
   ```

### Error Handling

```typescript
try {
  const prefs = await getUserPreferences()
} catch (error) {
  if (error.response?.status === 401) {
    // Redirect to login
    navigate('/login')
  } else {
    toast.error('Failed to load preferences')
  }
}
```
```

---

## Core Behavior

### When to Trigger

Claude MUST update documentation when:

1. **Frontend changes that need Backend support:**
   - New API calls added
   - New data structures expected from API
   - New query parameters used
   - New authentication requirements
   - New file upload/download needs

2. **Backend changes that affect Frontend:**
   - New endpoints created
   - Response structure changed
   - New fields added/removed from DTOs
   - Authentication/authorization changes
   - Error response format changes

### Documentation Files

```
.claude/docs/
├── api-contracts/
│   ├── README.md                    # Overview of all contracts
│   ├── pending-backend.md           # FE needs these BE endpoints
│   ├── pending-frontend.md          # BE provides, FE needs to implement
│   └── contracts/
│       ├── auth.contract.md         # Auth-related APIs
│       ├── orders.contract.md       # Orders feature APIs
│       ├── customers.contract.md    # Customers feature APIs
│       └── [feature].contract.md    # Per-feature contracts
```

---

## Documentation Format

### For Backend Developer (pending-backend.md)

When Frontend needs an API that doesn't exist:

```markdown
# Pending Backend Requirements

> Auto-generated by Claude. Last updated: [timestamp]

## Priority: HIGH

### [Feature Name] - [Endpoint Description]

**Requested by:** Frontend change in `[file:line]`
**Date:** [YYYY-MM-DD]
**Status:** PENDING | IN_PROGRESS | COMPLETED

#### Endpoint Specification

| Method | Path | Auth Required |
|--------|------|---------------|
| POST | /api/jobs/{id}/archive | Yes (JWT) |

#### Request

```typescript
// TypeScript interface (what FE will send)
interface ArchiveJobRequest {
  reason: string           // Required, max 500 chars
  notifyApplicants: boolean // Optional, default false
}
```

```json
// Example request body
{
  "reason": "Position filled",
  "notifyApplicants": true
}
```

#### Expected Response

```typescript
// TypeScript interface (what FE expects)
interface ArchiveJobResponse {
  success: boolean
  archivedAt: string      // ISO 8601 datetime
  affectedApplicants: number
}
```

```json
// Example success response (200 OK)
{
  "success": true,
  "archivedAt": "2026-01-28T10:30:00Z",
  "affectedApplicants": 5
}
```

#### Error Responses

| Status | Code | Description |
|--------|------|-------------|
| 400 | INVALID_REASON | Reason is required |
| 403 | NOT_OWNER | User doesn't own this job |
| 404 | JOB_NOT_FOUND | Job doesn't exist |

```json
// Example error response
{
  "success": false,
  "error": {
    "code": "NOT_OWNER",
    "message": "You don't have permission to archive this job"
  }
}
```

#### Business Logic Notes

- Only job owner or admin can archive
- Archived jobs should not appear in search results
- If `notifyApplicants` is true, send email to all applicants
- Archived jobs can be restored within 30 days

#### Frontend Context

The frontend needs this endpoint for the Job Management page.
User clicks "Archive" button → confirmation modal → calls this endpoint.

See: `src/containers/JobManagementContainer.tsx:145`
```

---

### For Frontend Developer (pending-frontend.md)

When Backend provides an API that Frontend hasn't implemented:

```markdown
# Pending Frontend Implementation

> Auto-generated by Claude. Last updated: [timestamp]

## Priority: HIGH

### [Feature Name] - [Endpoint Description]

**Provided by:** Backend change in `[file:line]`
**Date:** [YYYY-MM-DD]
**Status:** PENDING | IN_PROGRESS | COMPLETED

#### Available Endpoint

| Method | Path | Auth Required |
|--------|------|---------------|
| GET | /api/users/preferences | Yes (JWT) |

#### How to Call

```typescript
// Service method to add
async function getUserPreferences(): Promise<UserPreferences> {
  const response = await api.get<UserPreferences>('/api/users/preferences')
  return response.data
}
```

#### Response Type

```typescript
interface UserPreferences {
  theme: 'light' | 'dark' | 'system'
  emailNotifications: boolean
  language: string
  timezone: string
}
```

#### Example Response

```json
{
  "theme": "dark",
  "emailNotifications": true,
  "language": "en-ZA",
  "timezone": "Africa/Johannesburg"
}
```

#### Error Handling

```typescript
try {
  const prefs = await getUserPreferences()
  setPreferences(prefs)
} catch (error) {
  if (error.response?.status === 401) {
    // Redirect to login
  }
  // Show error toast
}
```

#### Suggested Implementation

1. Add service method in `src/services/user.service.ts`
2. Create hook `useUserPreferences()` in `src/hooks/`
3. Use in Settings page

#### Backend Context

This endpoint was added to support user preference syncing.
Preferences are stored in the UserSettings table.

See: `Controllers/UserController.cs:GetPreferences()`
```

---

### Contract Files (per feature)

For established, synchronized APIs:

```markdown
# [Feature] API Contract

> Last synced: [timestamp]
> Status: SYNCHRONIZED

## Endpoints

### 1. List Jobs

| Aspect | Value |
|--------|-------|
| Method | GET |
| Path | /api/jobs |
| Auth | Required |
| FE Service | `src/services/job.service.ts:getJobs()` |
| BE Controller | `Controllers/JobController.cs:GetJobs()` |

#### Query Parameters

| Param | Type | Required | Default | Description |
|-------|------|----------|---------|-------------|
| page | number | No | 1 | Page number |
| limit | number | No | 20 | Items per page |
| status | string | No | all | Filter by status |
| search | string | No | - | Search term |

#### Request Example

```
GET /api/jobs?page=1&limit=20&status=active&search=developer
Authorization: Bearer <token>
```

#### Response Type

```typescript
interface JobListResponse {
  items: Job[]
  total: number
  page: number
  limit: number
  hasMore: boolean
}

interface Job {
  id: number
  title: string
  status: 'draft' | 'active' | 'closed' | 'archived'
  createdAt: string
  applicantCount: number
}
```

#### Sync Status

| Field | FE Type | BE Type | Synced |
|-------|---------|---------|--------|
| id | number | int | YES |
| title | string | string | YES |
| status | union | enum | YES |
| createdAt | string | DateTime | YES |
| applicantCount | number | int | YES |

---

## Change History

| Date | Change | FE Updated | BE Updated |
|------|--------|------------|------------|
| 2026-01-28 | Added applicantCount field | YES | YES |
| 2026-01-20 | Initial contract | YES | YES |
```

---

## Auto-Update Behavior

### After Frontend Changes

When Claude modifies frontend code that:
- Adds new API calls
- Changes expected response types
- Adds new form submissions

Claude MUST:
1. Check if corresponding backend endpoint exists
2. If NO → Add to `pending-backend.md`
3. If YES → Update contract file to ensure sync
4. Alert user: "Documentation updated for backend developer"

### After Backend Changes

When Claude modifies backend code that:
- Adds new endpoints
- Changes DTO structures
- Modifies response formats

Claude MUST:
1. Check if frontend uses this endpoint
2. If YES but outdated → Add to `pending-frontend.md`
3. If NEW endpoint → Add to `pending-frontend.md`
4. Update contract file
5. Alert user: "Documentation updated for frontend developer"

---

## Documentation Update Alert

After updating documentation, Claude shows:

```
API DOCS UPDATED
================
Updated: pending-backend.md
Reason: New API call added in JobContainer.tsx:89

Summary:
  - POST /api/jobs/{id}/archive
  - Needs: Authorization, validation, email notification

Backend developer should review:
  .claude/idev/api-contracts/pending-backend.md
```

---

## Commands

### /api-docs status

Shows current documentation status:
- Pending backend items
- Pending frontend items
- Last sync time
- Out-of-sync contracts

### /api-docs sync

Scans codebase and regenerates all contract documentation.

### /api-docs validate

Checks if FE calls match BE endpoints and reports mismatches.

---

## Integration with Smart Context + Project Map

This skill uses a **layered approach** for minimal token usage:

### Layer 1: index.json (Always Load First)

```json
// .claude/idev/smart-context/index.json (~70 lines)
{
  "features": ["Orders", "Customers", "Payments", "Auth", ...],
  "patterns": {
    "service": "**/services/*.service.ts",
    "controller": "**/*Controller.cs"
  }
}
```

**Use for:** Feature detection, knowing what exists

### Layer 2: Existing Contracts (Check Before Scanning)

```
.claude/idev/api-contracts/contracts/
  └─ If [feature].contract.md exists → USE IT
  └─ Don't rescan what's already documented
```

**Use for:** Avoid redundant work

### Layer 3: Grep Project Map (Paths Only)

```bash
# Get file paths without reading content
Grep project.map.md "job.service" → src/services/job.service.ts
Grep project.map.md "JobController" → Controllers/JobController.cs
```

**Use for:** Finding file locations

### Layer 4: Grep Source Files (Signatures Only)

```bash
# Get endpoint signatures, not full code
Grep job.service.ts "export.*function|async.*=>" -A 1
Grep JobController.cs "\[Http.*\]" -A 1
```

**Use for:** Endpoint discovery without full file read

### Layer 5: Read Source (Last Resort)

```
Only read specific lines when:
- Creating detailed type documentation
- Resolving ambiguous mappings
- User explicitly requests detail
```

### Token Cost Comparison

| Approach | Tokens | When to Use |
|----------|--------|-------------|
| Use existing contract | 0 | Contract exists |
| index.json | ~70 | Feature detection |
| Grep project-map | ~50 | File paths |
| Grep source | ~100 | Signatures |
| Read full file | ~500-2000 | Detail needed |

### Lookup Flow Diagram

```
User changes code
       ↓
Check: Is this a FE↔BE change?
       ↓ YES
Check: Does contract exist?
  ├─ YES → Update contract (minimal read)
  └─ NO → Create skeleton from project-map
       ↓
Grep for file paths (not content)
       ↓
Update docs with paths
       ↓
Full detail only when user requests /api-docs detail
```

---

## Integration with Other Skills

This skill works with:
- **smart-context**: index.json for feature detection (REQUIRED FIRST)
- **project-map**: File paths via Grep (REQUIRED)
- **coding-standards**: Ensures documentation follows standards
- **auto-learning**: Learns common API patterns

### Skill Loading Order

```
1. smart-context/index.json  → What features exist
2. api-contracts/contracts/  → What's already documented
3. project-map (Grep)        → Where files are
4. Source files (Grep/Read)  → Actual code (minimize)
```

---

## Quick Reference

### FE Developer Needs BE Support

```
1. Claude detects new API call in FE
2. Claude checks if BE endpoint exists
3. If missing → Claude adds to pending-backend.md
4. Claude alerts: "Backend requirement documented"
```

### BE Developer Provides New API

```
1. Claude detects new endpoint in BE
2. Claude checks if FE uses it
3. Claude adds to pending-frontend.md
4. Claude alerts: "Frontend implementation documented"
```

### Both Sides Updated

```
1. Change detected on either side
2. Claude checks contract file exists
3. Claude updates contract with new sync status
4. Claude alerts: "Contract synchronized"
```
