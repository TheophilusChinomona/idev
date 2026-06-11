# Claude Context Rules

## System Instruction
System: Use the combined smart-context + project-map system. Load `.claude/idev/smart-context/index.json` at session start (~70 lines). Use project-map sections on-demand via Grep. Never load the full project-map at once. Follow the idev:smart-context skill for all context loading rules.

---

## SECURITY FIRST (HIGHEST PRIORITY)

**The coding-standards skill is ALWAYS ACTIVE. Security takes highest priority.**

Before writing or modifying ANY code, Claude MUST:
1. Check for security vulnerabilities (injection, XSS, auth bypass, etc.)
2. Alert the user immediately if issues are found
3. Refuse to write insecure code without explicit user override

### Security Alert Format
```
⚠️ SECURITY ALERT: [Vulnerability Type]
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Location: [file:line]
Severity: CRITICAL | HIGH | MEDIUM | LOW
Issue: [Brief description]
Fix: [How to fix it]
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
```

### Quick Security Checks
- [ ] No hardcoded secrets/API keys
- [ ] All user input validated (use Zod)
- [ ] SQL uses parameterized queries
- [ ] No innerHTML with unsanitized user content
- [ ] Auth required on protected routes
- [ ] Sensitive data not exposed in responses
- [ ] CORS restricted to allowed origins

Reference: the idev:coding-standards skill

---

## Data Sources (Hierarchy)

```
1. index.json      → Quick lookup (70 lines) - ALWAYS LOAD
2. Grep            → Find specific paths (fast)
3. project.map.md  → Detailed reference (load sections only)
4. Source files    → Actual code (targeted reads)
```

---

## Loading Rules

### At Session Start
- Load: `.claude/idev/smart-context/index.json`
- DO NOT load: project.map.md

### For Each Task
1. Extract keywords from user message
2. Grep project.map.md OR source files for matches
3. Read only specific files/sections needed
4. Expand only if required

### What NOT to Do
- ❌ Load entire project.map.md
- ❌ Pre-read files "just in case"
- ❌ Read all files in a directory
- ❌ Skip index.json and go straight to map

---

## Quick Reference

### File Patterns
| Type | Pattern |
|------|---------|
| Page | `**/pages/*Page.tsx` |
| Container | `**/containers/*Container.tsx` |
| Hook | `**/hooks/*.hook.ts` |
| Service (FE) | `**/services/*.service.ts` |
| Controller | `**/*Controller.cs` |
| Service (BE) | `**/*Service.cs` |

### Feature Keywords
Examples — derive the real list from the features in index.json:

| Keyword | Search Pattern |
|---------|---------------|
| order | `**/[Oo]rder*` |
| customer | `**/[Cc]ustomer*` |
| invoice | `**/[Ii]nvoice*` |
| report | `**/[Rr]eport*` |
| auth | `**/[Aa]uth*` |
| team | `**/[Tt]eam*` |
| payment | `**/[Pp]ay*` |

---

## File Safety
- Never delete files without explicit permission
- Never perform git operations automatically
- Prefer editing existing files over creating new ones

---

## API Documentation Sync (AUTO-ACTIVE, LOW-TOKEN)

**The api-docs-sync skill is ALWAYS ACTIVE. Uses layered approach for minimal tokens.**

### When First Scan Triggers

First scan happens when ALL true:
1. User modifies FE service or BE controller
2. No contracts exist in `.claude/idev/api-contracts/contracts/`
3. `watcher_config.json` exists (has FE/BE paths)

**NOT triggered by:** Opening session, reading files, non-API changes

### Path Source

FE/BE paths come from project-map's config:
```
.claude/idev/project-map/watcher_config.json
  → frontend_path: [path]
  → backend_path: [path]
```

### Token-Efficient Lookup Order

```
1. Existing contracts     → USE FIRST (0 tokens)
2. index.json            → Feature detection (70 tokens)
3. watcher_config.json   → FE/BE paths (10 tokens)
4. Grep project-map      → File paths only (50 tokens)
5. Grep source files     → Signatures only (100 tokens)
6. Read source files     → LAST RESORT (500+ tokens)
```

### Initialization (Only If No Contracts)

```
IF contracts/ is empty AND watcher_config.json exists:
  → Read watcher_config.json for FE/BE paths
  → Load index.json for features list
  → Grep project-map for file mappings
  → Create skeleton contracts (paths only)
```

### After FE↔BE Code Changes

```
1. Check existing contract first
2. If exists → Update minimally
3. If not → Create skeleton via Grep
4. Never read full files unless detail requested
```

### When to Document

| Change | Action | Token Cost |
|--------|--------|------------|
| New API call | Grep + skeleton | ~150 |
| Endpoint modified | Update contract | ~50 |
| Type changed | Grep signature | ~100 |
| Detail requested | Read specific lines | ~500 |

### Documentation Alert Format
```
API DOCS UPDATED
================
Updated: [file]
Reason: [change description]
Method: [index.json/Grep/Read]
Tokens: ~[estimate]
```

Reference: the idev:api-docs-sync skill

---

## API Validation (AUTO-ACTIVE, PROACTIVE, LOW-TOKEN)

**The api-validator skill is ALWAYS ACTIVE. Performs initial full scan, then proactive monitoring.**

### Initialization (First Scan)

First scan triggers when ALL true:
1. `validation-report.md` doesn't exist (or is pending)
2. `watcher_config.json` exists
3. User makes FE↔BE code change

**NOT triggered by:** Opening session, reading files, non-API changes

### Initialization Process

```
1. Load index.json + watcher_config.json
2. Glob: Find all *Service.ts and *Controller.cs
3. Grep: Extract all endpoints from each file
4. Cross-reference: FE calls ↔ BE endpoints
5. Generate: validation-report.md (baseline)
6. Update: contracts/ and pending docs
7. Enable: Proactive monitoring mode
```

### When Claude Validates (After Init)

After ANY change to:
- FE service files (API calls)
- BE controller files (endpoints)
- Request/response types

### Low-Token Validation Flow

```
1. Load index.json         → Feature detection (~70 tokens)
2. Load watcher_config     → Get FE/BE paths (~10 tokens)
3. Check existing contract → Use as baseline (~0 tokens)
4. Grep changed file       → Extract endpoints (~50 tokens)
5. Grep counterpart        → Find matching code (~50 tokens)
6. Compare paths + methods → Validate alignment
7. Read full file          → ONLY if type check needed
```

### Automatic Actions

```
1. Quick validation (path + method via Grep)
2. If CRITICAL issue → Alert immediately
3. If change detected → Update api-docs-sync contracts
4. If endpoint missing → Add to pending docs
5. If all good → Silent success (no interruption)
```

### Validation Alert Format
```
API VALIDATION ALERT
====================
Status: MISMATCH DETECTED | IN SYNC
Change: [what was modified]
Issue: [problem found]
Fix: [resolution]
Tokens: ~[estimate]
====================
```

### Issue Severity

| Severity | Issue Type | Action |
|----------|------------|--------|
| CRITICAL | Missing endpoint, wrong method | Alert + block |
| HIGH | Type mismatch | Alert + suggest fix |
| MEDIUM | Auth mismatch | Alert |
| LOW | Unused endpoint | Log only |

### Documentation Updates

- New FE call (no BE) → Add to `pending-backend.md`
- New BE endpoint (no FE) → Add to `pending-frontend.md`
- Signature change → Update `contracts/[feature].contract.md`
- Endpoint removed → Mark deprecated in contract

### Integration with smart-context + project-map

Uses same layered approach as api-docs-sync:
```
1. index.json           → Features, patterns
2. watcher_config.json  → FE/BE paths
3. Existing contracts   → Baseline
4. Grep project-map     → File locations
5. Grep source          → Signatures only
6. Read source          → LAST RESORT
```

Reference: the idev:api-validator skill

---

## Project Map (Auto-Updated)
The project-map at `.claude/idev/project-map/project.map.md` is auto-updated by the Python watcher. It contains:
- All frontend files (pages, containers, services)
- All backend files (controllers, services)
- FE → BE mappings (if configured)

Use it as a detailed reference, but always access via Grep first.

---

## Strategic Compact (Context Management)

**The strategic-compact skill suggests optimal `/compact` points.**

### Scripts

| Platform | Script |
|----------|--------|
| Windows | `suggest-compact.ps1` |
| Unix/macOS | `suggest-compact.sh` |

### When to Compact (Hook Suggestions)

The skill suggests compaction at:
- **50 tool calls** - First suggestion
- **Every 25 calls after** - Periodic reminders

### Best Compact Points

| After | Why |
|-------|-----|
| Exploration complete | Research context no longer needed |
| Plan finalized | Fresh context for implementation |
| Bug fixed | Error traces no longer needed |
| Feature complete | Ready for next task |

### What Persists After Compact

- `index.json` - Feature index (~70 lines)
- `api-contracts/` - API documentation
- `project.map.md` - Project structure
- `rules.md` - These rules

Reference: the idev:strategic-compact skill
