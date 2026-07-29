---
description: "Measure and report test coverage for the project."
argument-hint: "[--threshold N]"
---

# /test-coverage — Coverage Report

Measure test coverage and report results.

## Usage

```
/test-coverage              # Run coverage with default 80% threshold
/test-coverage --threshold 90  # Custom threshold
```

## What Happens
1. Detects test framework (Jest, Vitest, pytest, dotnet test)
2. Runs coverage collection
3. Reports line/branch/function coverage
4. Flags files below threshold
5. Suggests which tests to add

## Output
```
Coverage: 85% lines, 78% branches, 92% functions
Threshold: 80% ✓ PASS

Files below threshold:
  src/auth.ts: 65% — add edge case tests
```
