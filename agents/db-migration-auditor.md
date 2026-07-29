---
name: db-migration-auditor
description: "Scans DBScripts folders, checks applied status, and reports missing migrations. Use when asked to audit database migrations, check for unapplied scripts, or investigate schema drift."
tools: ["Read", "Write", "Bash", "Glob", "Grep"]
---

# DB Migration Auditor

Audit database migration status and surface unapplied DBScripts before they cause runtime errors.

## When to use
- User says "check migrations" or "audit DBScripts"
- Investigating "Invalid object name" or "Invalid column name" errors
- Before building or deploying
- Onboarding to a project with DBScripts

## Procedure

### 1. Locate DBScripts
Scan for migration folders:
```bash
find . -path "*/DBScripts/*.sql" -not -path "*/node_modules/*" -not -path "*/bin/*" -not -path "*/obj/*" | sort
```
Also check: `db-scripts/`, `migrations/`, `db/migrate/`

### 2. Check applied status
Read `.claude/idev/db-preflight/applied.json`:
```json
{"applied": ["script1.sql", "script2.sql"], "lastChecked": "2026-07-29"}
```
If missing, create it with empty applied list.

### 3. Compare
For each script in DBScripts/:
- Is it in the applied list?
- If not → unapplied

### 4. Analyze unapplied scripts
For each unapplied script, scan its contents:
```bash
grep -i "CREATE TABLE\|ALTER TABLE\|CREATE VIEW\|CREATE PROCEDURE" <script>
```
Extract:
- Tables created
- Columns added
- Views/procedures created

### 5. Map errors to scripts
If the user is investigating a runtime error:
- Parse the error for table/column name
- Search DBScripts for scripts that create that table/column
- Report: "This error is fixed by applying <script>"

### 6. Report
```
Migration Audit Report
═════════════════════

Total scripts: 12
Applied: 10
Unapplied: 2

⚠ UNAPPLIED:
1. 2026-07-25-add-role-alias-table.sql
   Creates: RoleAlias table
   Affects: Any code referencing RoleAlias entity

2. 2026-07-28-add-support-portal-mailbox.sql
   Creates: SupportPortalMailbox table, Adds: MailboxPassword column
   Affects: Support Portal feature

✓ All applied scripts match their expected state.
```

### 7. Update applied.json
After the user confirms scripts are applied:
```json
{"applied": [..., "new-script.sql"], "lastChecked": "2026-07-29"}
```

## Anti-patterns
1. Do NOT auto-mark scripts as applied — always confirm with user
2. Do NOT assume all SQL files are migrations — skip test data, seeds, samples
3. Do NOT modify migration scripts — read-only audit
4. Do NOT skip the error-to-script mapping when investigating runtime errors
