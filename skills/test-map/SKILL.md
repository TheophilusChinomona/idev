---
name: test-map
description: Maps source files to their test files so only relevant tests run after a change. Use after modifying source files or when asked which tests cover a file.
---

# Test Map Skill

## Purpose
Map test files to source features so Claude can run targeted tests after modifying code, instead of running the full test suite or guessing which tests are relevant.

## Activation
- **Generate**: On first use or when user says "refresh test map"
- **Query**: After modifying source files, to find which tests to run
- **Update**: Incrementally when new test files are created

---

## How It Works

A compact test-to-feature mapping is maintained at:
`.claude/idev/test-map/map.json`

This maps: `feature/source file → [test files that cover it]`

---

## Phase 1: Detect Test Framework

Auto-detect the testing setup:

```
JavaScript/TypeScript:
  package.json scripts containing "test" → detect runner
  jest.config.* → Jest
  vitest.config.* → Vitest
  .mocharc.* → Mocha
  karma.conf.* → Karma
  playwright.config.* → Playwright (E2E)
  cypress.config.* → Cypress (E2E)

.NET:
  Glob for *.Tests.csproj or *.Test.csproj → xUnit/NUnit/MSTest
  Read .csproj for <PackageReference Include="xunit|NUnit|MSTest">

Python:
  pytest.ini or pyproject.toml [tool.pytest] → pytest
  Glob for test_*.py or *_test.py

Java:
  src/test/ directory → JUnit
  Glob for *Test.java or *Tests.java

Go:
  Glob for *_test.go → built-in testing

Ruby:
  spec/ directory → RSpec
  test/ directory → Minitest
```

---

## Phase 2: Discover Test Files

Scan for test files using detected patterns:

```
.NET:
  Glob: **/*.Tests/**/*Test*.cs
  Glob: **/*.Test/**/*Test*.cs
  Convention: {Service}Tests.cs tests {Service}.cs

JavaScript/TypeScript:
  Glob: **/*.test.ts, **/*.test.tsx, **/*.spec.ts, **/*.spec.tsx
  Glob: **/__tests__/**/*.ts
  Convention: {Component}.test.tsx tests {Component}.tsx

Python:
  Glob: **/test_*.py, **/*_test.py
  Glob: tests/**/*.py

Go:
  Glob: **/*_test.go
  Convention: {file}_test.go tests {file}.go
```

---

## Phase 3: Map Tests to Features

### By naming convention:
```
OrderServiceTests.cs → tests OrderService.cs → feature: Orders
OrdersDashboard.test.tsx → tests OrdersDashboard.tsx → feature: Orders
```

### By import analysis:
```
Read test file imports:
  import { OrderService } from "../../services/OrderService"
  → This test covers OrderService
  → Feature: Orders
```

### By directory structure:
```
Tests in same feature folder:
  features/Orders/__tests__/ → covers Orders feature

Tests in parallel test project:
  Services.Test/Orders/ → covers Services/Orders/
```

---

## Phase 4: Map Format

Write to `.claude/idev/test-map/map.json`:

```json
{
  "generated": "YYYY-MM-DD",
  "testFrameworks": {
    "backend": {
      "framework": "xunit|nunit|mstest",
      "testProject": "relative/path/to/test/project",
      "runCommand": "dotnet test path/to/Tests.csproj",
      "runFilteredCommand": "dotnet test --filter {TestClassName}",
      "runSingleCommand": "dotnet test --filter FullyQualifiedName~{TestName}"
    },
    "frontend": {
      "framework": "jest|vitest",
      "runCommand": "npm test -- --watchAll=false",
      "runFilteredCommand": "npm test -- --testPathPattern={pattern} --watchAll=false",
      "runSingleCommand": "npm test -- {testFile} --watchAll=false"
    },
    "e2e": {
      "framework": "playwright|cypress",
      "runCommand": "npx playwright test",
      "runFilteredCommand": "npx playwright test {testFile}"
    }
  },
  "featureToTests": {
    "Orders": {
      "backend": [
        {
          "testFile": "relative/path/to/OrderServiceTests.cs",
          "covers": ["OrderService.cs"],
          "testCount": 12
        }
      ],
      "frontend": [
        {
          "testFile": "relative/path/to/OrdersDashboard.test.tsx",
          "covers": ["OrdersDashboard.tsx"],
          "testCount": 8
        }
      ]
    }
  },
  "sourceToTests": {
    "relative/path/to/OrderService.cs": ["relative/path/to/OrderServiceTests.cs"],
    "relative/path/to/OrdersDashboard.tsx": ["relative/path/to/OrdersDashboard.test.tsx"]
  },
  "untestedFiles": [
    "relative/path/to/file/with/no/tests.ts"
  ]
}
```

---

## Phase 5: Usage

### After modifying a source file:
```
1. Load test-map
2. Look up sourceToTests for the modified file
3. If tests exist → run them with the filtered command
4. Report: "3/3 tests passed" or "1 test failed: ..."
```

### After creating a new feature:
```
1. Check if test files should be created
2. Suggest test file names following project convention
3. If user wants tests → create them using detected patterns
```

### When user says "run tests":
```
1. Determine scope:
   - "run tests" → run all tests
   - "run tests for Orders" → use featureToTests mapping
   - "run tests for OrderService" → use sourceToTests mapping
2. Use the appropriate run command from testFrameworks
3. Report results
```

---

## Phase 6: Targeted Test Running

### Run only affected tests after a change:
```
Modified: OrderService.cs
  → sourceToTests → OrderServiceTests.cs
  → Command: dotnet test --filter OrderServiceTests
  → Result in ~10 seconds instead of full suite (~2 minutes)
```

### Run feature tests after multi-file change:
```
Modified: 5 files in Orders
  → featureToTests.Orders → all test files
  → Command: dotnet test --filter "Namespace~Orders"
  → Result in ~30 seconds instead of full suite
```

---

## Anti-Patterns

1. Do NOT run the full test suite when targeted tests are available
2. Do NOT skip tests after modifying code — always check
3. Do NOT track test-to-test dependencies (only source-to-test)
4. Do NOT include test helper/fixture files in the map
5. Do NOT run E2E tests for unit-level changes
