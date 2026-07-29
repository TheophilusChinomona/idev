---
name: test-coverage
description: "Measures and reports test coverage for the project. Use when asked about coverage, before PRs, or when coverage drops."
---

# Test Coverage Skill

## Purpose
Measure, report, and enforce test coverage thresholds.

## Activation
- User says "check coverage" or "what's the coverage?"
- Before creating a PR
- When coverage drops below threshold

## How It Works

### 1. Detect Test Framework
```
JavaScript/TypeScript:
  jest.config.* → npx jest --coverage
  vitest.config.* → npx vitest --coverage
  .nycrc → npx nyc report

Python:
  pytest.ini → pytest --cov
  pyproject.toml [tool.pytest] → pytest --cov

.NET:
  *.Tests.csproj → dotnet test /p:CollectCoverage=true
```

### 2. Run Coverage
```bash
# JavaScript/TypeScript
npx jest --coverage --coverageReporters=text-summary

# Python
pytest --cov=src --cov-report=term-missing

# .NET
dotnet test /p:CollectCoverage=true /p:CoverletOutputFormat=lcov
```

### 3. Report
```
Coverage Report
═══════════════
Lines:    85% (120/141)
Branches: 78% (45/58)
Functions: 92% (33/36)

Below 80% threshold:
  src/auth.ts: 65% (missing edge cases)
  src/utils.ts: 72% (missing error paths)
```

## Threshold
- Minimum: 80% line coverage
- Target: 90% line coverage
- Branches: 75% minimum

## Anti-Patterns
1. Do NOT skip coverage on "simple" files
2. Do NOT mock everything — integration tests need real calls
3. Do NOT ignore coverage drops — investigate and fix
