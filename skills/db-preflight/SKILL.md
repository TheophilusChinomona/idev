---
name: db-preflight
description: "Scans DBScripts/ folder for unapplied database migrations and surfaces them before builds or at session start. Prevents 'Invalid object name' 500s caused by hand-applied DBScript migrations being missed. Use when starting a session, before building, or when a runtime DB error mentions a missing table/column."
---

# DB Preflight Skill

## Purpose
Catch unapplied database migrations before they cause runtime 500 errors. Scans the project's `DBScripts/` folder, compares against a list of known-applied scripts, and reports which ones are missing. Maps runtime DB errors back to the specific DBScript that fixes them.

## Activation
- **Session start**: SessionStart hook surfaces unapplied scripts
- **Before build**: build-check runs this as a pre-flight step
- **On DB error**: When a runtime error mentions "Invalid object name", "Invalid column name", or similar schema errors

## How It Works

### State (per project)
| File | Purpose |
|------|---------|
| `.claude/idev/db-preflight/applied.json` | List of scripts the user has confirmed are applied |
| `.claude/idev/db-preflight/known-errors.json` | Maps DB error patterns to their fixing DBScript |

### Scan Process
```
1. Glob for DBScripts/**/*.sql (or DBScripts/**/*.ps1, DBScripts/**/*.sh)
2. Extract script names (sort by date prefix if present: YYYY-MM-DD-*.sql)
3. Compare against applied.json
4. Report unapplied scripts with their date and description
```

### Detection Patterns
The skill detects DBScript folders using these conventions:
```
DBScripts/
DBScripts/YYYY-MM-DD/
db-scripts/
migrations/
```

### Script Naming Convention
Most DBScript folders follow: `YYYY-MM-DD-description.sql`
The date prefix determines execution order.

## Phase 1: Scan for DBScripts

```bash
# Find all SQL scripts in DBScripts folders
find . -path "*/DBScripts/*.sql" -not -path "*/node_modules/*" -not -path "*/bin/*" -not -path "*/obj/*" | sort
```

Or use Glob: `**/DBScripts/**/*.sql`

## Phase 2: Compare Against Applied

Read `.claude/idev/db-preflight/applied.json`:
```json
{
  "applied": [
    "2026-01-15-add-orders-table.sql",
    "2026-01-20-add-customer-column.sql"
  ],
  "lastChecked": "2026-07-29"
}
```

Scripts in DBScripts/ NOT in the `applied` list are unapplied.

## Phase 3: Report

### At session start (brief):
```
[db-preflight] 2 unapplied DBScripts:
  - 2026-07-25-add-role-alias-table.sql
  - 2026-07-28-add-support-portal-mailbox.sql
Run these before building or expect "Invalid object name" errors.
```

### Before build (detailed):
```
DB Preflight Check:
  Total DBScripts: 12
  Applied: 10
  Unapplied: 2
  
  ⚠ UNAPPLIED:
  1. 2026-07-25-add-role-alias-table.sql
     Creates: RoleAlias table
     Affects: Any code referencing RoleAlias entity
     
  2. 2026-07-28-add-support-portal-mailbox.sql
     Creates: SupportPortalMailbox table, Adds: MailboxPassword column
     Affects: Support Portal feature
     
  Apply these scripts to the dev database before building.
```

## Phase 4: Error Mapping

When a runtime DB error occurs, map it to the fixing script:

### Error Pattern Matching
```
"Invalid object name 'RoleAlias'" 
  → Grep DBScripts for "CREATE TABLE.*RoleAlias" or "RoleAlias"
  → Found: 2026-07-25-add-role-alias-table.sql
  → Report: "This error is fixed by applying 2026-07-25-add-role-alias-table.sql"

"Invalid column name 'MailboxPassword'"
  → Grep DBScripts for "MailboxPassword" or "ALTER TABLE.*ADD.*MailboxPassword"
  → Found: 2026-07-28-add-support-portal-mailbox.sql
  → Report: "This error is fixed by applying 2026-07-28-add-support-portal-mailbox.sql"
```

### Building the Error Map
On first run (or when DBScripts change), scan all scripts and extract:
- Tables created (`CREATE TABLE`)
- Columns added (`ALTER TABLE.*ADD`)
- Views created (`CREATE VIEW`)
- Stored procedures (`CREATE PROCEDURE`)

Write to `.claude/idev/db-preflight/known-errors.json`:
```json
{
  "generated": "2026-07-29",
  "mappings": [
    {
      "script": "2026-07-25-add-role-alias-table.sql",
      "creates": ["table:RoleAlias"],
      "description": "Creates RoleAlias table for user role aliasing"
    },
    {
      "script": "2026-07-28-add-support-portal-mailbox.sql",
      "creates": ["table:SupportPortalMailbox"],
      "adds": ["column:SupportPortalMailbox.MailboxPassword"],
      "description": "Adds SupportPortalMailbox table with encrypted password"
    }
  ]
}
```

## Phase 5: Mark as Applied

When the user confirms a script has been applied (manually or via migration tool):
```json
{
  "applied": [
    "2026-01-15-add-orders-table.sql",
    "2026-07-25-add-role-alias-table.sql"
  ],
  "lastChecked": "2026-07-29"
}
```

The user can also bulk-mark: "mark all DBScripts as applied" or "mark 2026-07-25 as applied".

## Integration with Other Skills

```
Session start:
  1. db-preflight → scan for unapplied scripts
  2. If unapplied → warn user before they start coding
  
Before build:
  1. db-preflight → check for unapplied scripts
  2. If unapplied → warn and offer to skip build (user may be mid-development)
  
On DB error:
  1. Parse error for table/column name
  2. db-preflight known-errors.json → find fixing script
  3. Report: "Apply X to fix this error"
```

## Anti-Patterns
1. Do NOT auto-apply scripts — always let the user confirm
2. Do NOT assume all SQL files are migrations (skip test data, seeds)
3. Do NOT fail the build for unapplied scripts — warn and let user decide
4. Do NOT store connection strings or credentials in applied.json
5. Do NOT scan node_modules, bin, obj, or vendor directories
