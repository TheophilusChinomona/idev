---
name: build-check
description: "Auto-detects the project's build system and runs compile/type-check after file changes, auto-fixing straightforward errors (max 3 attempts). Use after completing a multi-file feature or when asked to build or check compilation."
---

# Build Check Skill

## Purpose
Auto-detect the project's build system and run compilation/type-checking after creating or modifying files. Catches errors (missing imports, type mismatches, DI failures) before the user discovers them at runtime.

## Activation
Run once per logical change set — after completing a multi-file feature or a self-contained modification, NOT after each individual file:
- After completing a multi-file feature (run once at the end)
- After a single-file change that could affect compilation (run once for that change)
- When the user asks to build or check compilation

---

## How It Works

This skill does NOT hardcode build commands. It detects them from the project.

Results cached in `.claude/idev/build-check/cache.json` after first detection.

---

## Phase 1: Detect Build System

Scan for build configuration files. Check ALL — do not assume any stack:

```
.NET:
  Glob for *.sln → dotnet build {solution.sln}
  Glob for *.csproj (if no .sln) → dotnet build {project.csproj}
  Check for specific project to build (API project .csproj for faster builds)

Node.js/TypeScript:
  Read package.json → check scripts section:
    "build" → npm run build / yarn build / pnpm build
    "typecheck" or "tsc" → npm run typecheck (preferred — faster than full build)
    "check" → npm run check (Svelte)
  Detect package manager: look for yarn.lock, pnpm-lock.yaml, or package-lock.json

Python:
  Glob for pyproject.toml → check for build tool (poetry, setuptools, hatch)
  Check for mypy.ini or pyproject.toml [tool.mypy] → mypy for type checking
  Check for ruff.toml or pyproject.toml [tool.ruff] → ruff check

Java:
  Glob for pom.xml → mvn compile
  Glob for build.gradle → gradle compileJava / ./gradlew compileJava

Go:
  Glob for go.mod → go build ./...

Rust:
  Glob for Cargo.toml → cargo check (faster than cargo build)

Ruby:
  Glob for Gemfile → bundle exec ruby -c (syntax check)
  Check for sorbet → srb tc (type check)

PHP:
  Glob for composer.json → check for phpstan or psalm → phpstan analyse / psalm
```

---

## Phase 2: Generate Cache

Write detected build commands to `.claude/idev/build-check/cache.json`:

```json
{
  "generated": "YYYY-MM-DD",
  "projects": [
    {
      "name": "ProjectName",
      "root": "relative/path/to/project",
      "layer": "backend|frontend",
      "buildCommand": "dotnet build path/to/project.csproj",
      "typeCheckCommand": "npm run typecheck (if different from build)",
      "lintCommand": "npm run lint (if available)",
      "workingDirectory": "relative/path (if command must run from specific dir)",
      "timeout": 120000
    }
  ],
  "quickChecks": {
    "backend": "dotnet build path/to/api.csproj --no-restore",
    "frontend": "npx tsc --noEmit"
  }
}
```

---

## Phase 3: When to Run

### Pre-flight: DBScripts check
Before running any build, check for unapplied database migrations:
```
1. Scan for DBScripts/ folder in the project
2. Compare scripts against .claude/idev/db-preflight/applied.json
3. If unapplied scripts exist:
   → WARN: "N unapplied DBScripts found — builds may fail with 'Invalid object name' errors"
   → List the unapplied scripts
   → Ask user: apply first, or proceed with build anyway?
4. This prevents the recurring 500 errors from missing schema changes
```
The db-preflight skill provides the full scanning and error-mapping logic.
build-check invokes it as a lightweight pre-flight, not a full replacement.

### After creating a NEW feature (multi-file):
```
1. Wait until ALL files are created (entity, DTOs, service, controller, etc.)
2. Run db-preflight pre-flight (check for unapplied DBScripts)
3. Run the backend build command
4. If frontend files were also created, run frontend type-check
5. Report results: success or list of errors
```

### After modifying a SINGLE file:
```
1. Determine which project the file belongs to (check file path against project roots)
2. Run ONLY that project's build/type-check
3. Use quick check command (--no-restore, --noEmit) for speed
```

### When NOT to run:
```
- After reading files (no changes made)
- After modifying only .md, .json, .txt, .css files (non-compiled)
- When user explicitly says "don't build" or "skip build"
- When creating skill/config files (not source code)
```

---

## Phase 4: Handle Build Errors

### If build succeeds:
```
Report: "Build passed ✓" (brief, one line)
```

### If build fails:
```
1. Parse error output for:
   - File path and line number
   - Error code and message
   - Missing reference or type
2. Categorize the error:
   - Missing using/import → Add it
   - Missing registration (DI) → Use post-creation-verify skill
   - Type mismatch → Fix the type
   - Missing file → Check if it was created
3. Fix the error automatically if it's straightforward
4. Re-run build to verify fix
5. If fix is unclear, report the error to the user
```

### Error fix limits:
```
- Max 3 auto-fix attempts per build
- If still failing after 3 attempts, report all errors to user
- Never suppress or ignore build errors
```

## Phase 5b: Test Mapping (absorbed from test-map)

After a successful build, optionally run targeted tests for modified files:
```
1. Check if .claude/idev/build-check/test-map.json exists
2. If not, generate it by scanning for test files:
   - .NET: Glob for *.Tests/**/*.cs, map by naming convention
   - JS/TS: Glob for *.test.ts, *.spec.ts, map by import analysis
   - Python: Glob for test_*.py, *_test.py
3. For each modified source file, look up its test files
4. Run only the affected tests (not the full suite)
5. Report: "3/3 tests passed" or "1 test failed: ..."
```

Test map format (`.claude/idev/build-check/test-map.json`):
```json
{
  "generated": "YYYY-MM-DD",
  "sourceToTests": {
    "path/to/Source.cs": ["path/to/SourceTests.cs"]
  },
  "testRunCommand": "dotnet test --filter {TestClassName}"
}
```

This replaces the standalone test-map skill. The map is generated on first use
and updated incrementally when new test files are created.
---

## Phase 5: Usage Commands

The user can trigger builds manually:
- "build" or "check build" → Run all project builds
- "build backend" → Run backend build only
- "build frontend" → Run frontend type-check only
- "skip build" → Suppress auto-build for current task

---

## Integration with Other Skills

```
After creating a new backend feature:
  1. post-creation-verify → Check all registrations exist
  2. build-check → Run dotnet build
  3. If errors → auto-fix → re-build
  4. Report final status

After creating a new frontend feature:
  1. build-check → Run tsc --noEmit
  2. If errors → auto-fix → re-check
  3. Report final status
```

---

## Anti-Patterns

1. Do NOT run build after every single file in a multi-file creation — wait until done
2. Do NOT run full build when a quick check (--noEmit, --no-restore) suffices
3. Do NOT hardcode build commands — always detect from project config
4. Do NOT ignore build failures — always report or fix
5. Do NOT run builds for non-compiled file changes
