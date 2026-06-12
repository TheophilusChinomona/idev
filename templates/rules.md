# Claude Context Rules

## System Instruction
System: Use the combined smart-context + project-map system. Load `.claude/idev/smart-context/index.json` at session start (~70 lines). Use project-map sections on-demand via Grep. Never load the full project-map at once. Follow the idev:smart-context skill for all context loading rules.

---

## SECURITY FIRST (HIGHEST PRIORITY)

When writing or reviewing code that handles user input, auth, secrets, file uploads, or database queries, apply the security review from the idev:coding-standards skill:
1. Check for security vulnerabilities (injection, XSS, auth bypass, secrets exposure, etc.)
2. Alert the user immediately if issues are found
3. Do not write insecure code without explicit user override

### Security Alert Format
```
SECURITY ALERT: [Vulnerability Type]
Location: [file:line]
Severity: CRITICAL | HIGH | MEDIUM | LOW
Issue: [Brief description]
Fix: [How to fix it]
```

### Quick Security Checks
- [ ] No hardcoded secrets/API keys
- [ ] All user input validated at the boundary
- [ ] SQL uses parameterized queries
- [ ] No raw HTML rendering of unsanitized user content
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

## API Contract Validation (LOW-TOKEN)

After creating or modifying API endpoints, service functions, or DTOs, run the idev:api-contract-validation skill to verify FE calls and BE endpoints agree on URLs, methods, and types. It can also generate per-feature contract docs on request.

### When to Validate

- After a feature's FE service or BE controller/DTO changes (run at feature completion, not after every file edit)
- When the user reports a FE↔BE data mismatch
- When asked to validate API alignment or generate API contract docs

### Token-Efficient Lookup Order

```
1. Existing cache/docs    → USE FIRST (0 tokens)
   .claude/idev/api-contract-validation/cache.json
   .claude/idev/api-contracts/*.md
2. index.json            → Feature detection (~70 tokens)
3. Grep project-map      → File paths only (~50 tokens)
4. Grep source files     → Endpoint signatures only (~100 tokens)
5. Read source files     → LAST RESORT (specific lines only)
```

### Issue Severity

| Severity | Issue Type | Action |
|----------|------------|--------|
| CRITICAL | Missing endpoint, wrong method | Alert + fix |
| HIGH | Incompatible type mismatch | Alert + suggest fix |
| MEDIUM | Auth mismatch | Alert |
| LOW | Unused endpoint, auto-serializable type drift | Log only |

### Outputs

- Validation cache: `.claude/idev/api-contract-validation/cache.json`
- Optional per-feature contract docs: `.claude/idev/api-contracts/<feature>.md`

Reference: the idev:api-contract-validation skill

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
