---
name: eval-harness
description: "Evaluation framework for capability and regression evals with pass@k metrics. Use when asked to define evals, run evals, or check eval status."
---

# Eval Harness Skill

## Purpose
Define, run, and track evaluations for features — the "unit tests of AI development."

## Eval Types

### Capability Evals
Test if Claude can do something:
```markdown
[CAPABILITY EVAL: feature-name]
Task: Description of what Claude should accomplish
Success Criteria:
  - [ ] Criterion 1
  - [ ] Criterion 2
Expected Output: Description of expected result
```

### Regression Evals
Ensure changes don't break existing functionality:
```markdown
[REGRESSION EVAL: feature-name]
Baseline: SHA or checkpoint name
Tests:
  - existing-test-1: PASS/FAIL
  - existing-test-2: PASS/FAIL
Result: X/Y passed (previously Y/Y)
```

## Metrics

### pass@k
"At least one success in k attempts"
- pass@1: First attempt success rate
- pass@3: Success within 3 attempts
- Typical target: pass@3 > 90%

## Workflow

### 1. Define (Before Coding)
```bash
/eval define feature-name
```
Creates `.claude/evals/feature-name.md`

### 2. Check (During Implementation)
```bash
/eval check feature-name
```
Runs current evals and reports status

### 3. Report (After Implementation)
```bash
/eval report feature-name
```
Generates full eval report

## Storage

```
.claude/evals/
├── feature-xyz.md      # Eval definition
├── feature-xyz.log     # Eval run history
└── baseline.json       # Regression baselines
```

## Anti-Patterns
1. Do NOT define evals after coding — define BEFORE
2. Do NOT skip regression evals
3. Do NOT use slow evals — keep them fast
4. Do NOT fully automate security checks — human review required
