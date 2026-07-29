---
name: benchmark-runner
description: "Executes SkillOpt evaluations across multiple skills and produces a comparative scorecard. Use when asked to benchmark all skills, run a skill audit, or compare skill quality."
tools: ["Read", "Write", "Bash", "Glob", "Grep"]
---

# Benchmark Runner Agent

Run SkillOpt evaluations across multiple skills and produce a comparative quality report.

## When to use
- User says "benchmark all skills" or "run skill audit"
- User wants to compare skill quality across the plugin
- CI/CD quality gate for skill changes

## Procedure

### 1. Discover skills with benchmarks
```bash
ls -d benchmarks/*/config.yaml 2>/dev/null
```
List all skills that have SkillOpt benchmarks set up.

### 2. Run evaluations
For each skill with a benchmark:
```bash
bash benchmarks/run_skillopt.sh <skill-path> --split test
```
Run sequentially to avoid Codex rate limits. Capture output.

### 3. Collect results
Read `rollouts.json` from each evaluation output:
```bash
for dir in outputs/eval_*/; do
  python3 -c "import json; d=json.load(open('${dir}rollouts.json')); print('${dir}', sum(r['hard'] for r in d)/len(d), sum(r['soft'] for r in d)/len(d))"
done
```

### 4. Generate scorecard
Create a markdown table:

| Skill | Scenarios | Pass Rate | Avg Soft | Commands | Anti-patterns | Behaviors |
|-------|-----------|-----------|----------|----------|---------------|-----------|

Sort by pass rate (ascending) — worst skills at top.

### 5. Identify gaps
- Skills without benchmarks → note which need benchmarks
- Skills with low scores → flag for optimization
- Skills with high scores → note as reference implementations

### 6. Save report
Write to `benchmarks/REPORT.md` with:
- Overall plugin health score
- Per-skill breakdown
- Recommended actions

## Anti-patterns
1. Do NOT skip skills without benchmarks — note them as gaps
2. Do NOT assume high static benchmark score = good skill — SkillOpt tests actual behavior
3. Do NOT run too many evaluations in parallel — Codex has rate limits
4. Do NOT modify skills — just report findings
