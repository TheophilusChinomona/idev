---
name: pre-ship-verify
description: "Migration-aware pre-ship gate — diffs the migration/schema state against code changes, runs build/type-check, and smoke-tests changed API routes against a live DB before allowing a PR. Use before opening a PR when DB-backed code changed."
---

# Pre-Ship Verify Skill

## Purpose
Prevent the 'still not working' loop caused by missing migrations, wrong
credentials, or broken routes that only surface after pushing. Gate the PR on
a full green run: schema ↔ code ↔ routes.

## Activation
- Before opening any PR that touches DB schema, models, or API routes
- When asked to "verify before PR", "pre-flight the deploy", or "check migrations"

---

## Phase 1: Detect Migration System

Scan for the project's migration tool. Check all — do not assume a stack.

```bash
# .NET / Entity Framework Core
ls migrations/ Migrations/ */Migrations/ 2>/dev/null | head -3
ls *.csproj */*.csproj 2>/dev/null | head -1 && dotnet ef migrations list 2>/dev/null | tail -20

# Prisma
ls prisma/migrations/ 2>/dev/null && npx prisma migrate status 2>/dev/null

# Alembic (Python)
ls alembic/versions/ 2>/dev/null && alembic current 2>/dev/null && alembic heads 2>/dev/null

# Flyway
ls db/migration/ src/main/resources/db/migration/ 2>/dev/null | head -3

# Knex
ls knex/ migrations/ db/migrations/ 2>/dev/null | head -3

# Rails / Active Record
ls db/migrate/ 2>/dev/null | tail -5 && bin/rails db:migrate:status 2>/dev/null | tail -20

# Django
python manage.py showmigrations 2>/dev/null | grep "\[ \]" | head -10
```

Record: migration tool name, pending count, last applied.

---

## Phase 2: Schema ↔ Code Diff Check

Get the list of files changed on this branch:
```bash
BASE=$(git rev-parse --abbrev-ref --symbolic-full-name @{u} 2>/dev/null \
  || git rev-parse --abbrev-ref HEAD@{upstream} 2>/dev/null \
  || echo "main")
git diff "$BASE"...HEAD --name-only
```

For each changed file, determine if it touches DB-backed logic:
- Models / entities / schema files (any ORM model, `@Entity`, `DbSet<>`, `models.py`, `schema.prisma`)
- Migration files (any file under a migration directory)
- Repository / data-access layer files

**If model/schema files changed but NO new migration exists:**
```
[pre-ship-verify] FAIL: Model changes detected but no pending migration found.
  Changed: <file list>
  Run the appropriate migration generate command before shipping.
```
Stop. Do not proceed to Phase 3.

**If migration files changed:** Confirm they have been applied or are pending
(not already applied and modified). Report status.

**If no DB-related files changed:** Skip Phase 2 and note it.

---

## Phase 3: Build / Type-Check

Detect and run the project's build (reuse `build-check` skill logic if active):

```bash
# .NET
dotnet build --no-restore 2>&1 | tail -20

# Node/TS
[ -f pnpm-lock.yaml ] && pnpm run typecheck 2>&1 | tail -20 \
  || [ -f bun.lockb ] && bun run typecheck 2>&1 | tail -20 \
  || npm run typecheck --silent 2>&1 | tail -20

# Python
[ -f mypy.ini ] || grep -q "tool.mypy" pyproject.toml 2>/dev/null \
  && mypy . 2>&1 | tail -20

# Go
go build ./... 2>&1 | tail -20
```

**Pass:** Proceed.
**Fail:** Report errors, stop. Do not open a PR with a broken build.

---

## Phase 4: API Route Smoke Tests

Only run if a `BASE_URL` or `APP_URL` env var is set, or the app is already
running locally (detect via `curl -s --max-time 2 http://localhost:3000/health`
or the port from package.json / launchSettings.json).

Get changed route files:
```bash
git diff "$BASE"...HEAD --name-only | grep -E "(controller|router|route|endpoint|handler)" -i
```

For each changed route file, extract the HTTP method + path pattern and
construct a minimal smoke-test request:

```bash
# Example: GET /api/health → expect non-500
curl -s -o /dev/null -w "%{http_code}" \
  -H "Authorization: Bearer $TEST_TOKEN" \
  "${BASE_URL:-http://localhost:3000}/api/health"
```

**Pass (2xx or 401):** Route is reachable.
**Fail (500 or connection refused):** Report which route failed and the
response body (first 500 chars). Stop — do not open a PR.

If no app is reachable: note "Smoke tests skipped — no running app detected"
and continue to Phase 5.

---

## Phase 5: Gate Decision

All checks must pass before allowing a PR:

| Check | Result | Action |
|---|---|---|
| Migration ↔ model sync | PASS | Continue |
| Migration ↔ model sync | FAIL | STOP — run migrations |
| Build / type-check | PASS | Continue |
| Build / type-check | FAIL | STOP — fix errors |
| Route smoke tests | PASS | Continue |
| Route smoke tests | SKIPPED | Continue with note |
| Route smoke tests | FAIL | STOP — investigate 500s |

**All green:** Output a single line:
```
[pre-ship-verify] PASS — migrations synced, build clean, routes OK. Safe to open PR.
```
Then hand off to the `/ship` or PR creation workflow.

---

## Anti-Patterns

1. Do NOT skip Phase 2 because migrations "look fine" — always run the status command.
2. Do NOT open a PR if Phase 2 or Phase 3 fails.
3. Do NOT run smoke tests against production — only localhost or staging.
4. Do NOT expose DB credentials in output — mask them (Phase 4 uses env vars, not raw strings).
5. Do NOT block on smoke-test skips — a missing app is a warning, not a hard failure.
