---
description: "Define, check, or report on feature evals."
argument-hint: "define|check|report <feature-name>"
---

# /eval — Feature Evaluation

Manage capability and regression evaluations.

## Usage

```
/eval define auth    # Create eval definition for auth feature
/eval check auth     # Run evals and report status
/eval report auth    # Generate full eval report
```

## Define
Creates `.claude/evals/<feature>.md` with:
- Capability eval criteria
- Regression eval baseline
- Success metrics (pass@3 > 90%)

## Check
Runs evals and reports:
- Which criteria pass/fail
- Current pass@k metrics
- Regressions from baseline

## Report
Generates full report with:
- Per-criterion results
- pass@k metrics
- Recommendation: SHIP / NEEDS WORK / BLOCKED
