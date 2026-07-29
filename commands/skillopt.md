---
description: "Benchmark and optimize an idev skill using Microsoft SkillOpt — generates test scenarios, runs evaluation via your Codex subscription, and reports results. Optionally optimizes the skill text."
argument-hint: "<skill-path> [--optimize] [--split train|val|test]"
---

# SkillOpt — Benchmark & Optimize Skills

Benchmark any idev skill against test scenarios using Microsoft SkillOpt, or optimize the skill text through trajectory-driven edits.

## Usage

```
/idev:skillopt skills/branch-sync/SKILL.md
/idev:skillopt skills/build-check/SKILL.md --optimize
/idev:skillopt skills/db-preflight/SKILL.md --split val
```

## What it does

1. **Reads the skill** at the given path
2. **Generates test scenarios** from the skill's described behavior (edge cases, happy paths, anti-patterns)
3. **Creates a SkillOpt benchmark** (dataloader, evaluator, config)
4. **Runs evaluation** using your Codex CLI subscription (no API keys needed)
5. **Reports results** with per-scenario scores
6. **Optionally optimizes** the skill text (requires OpenAI API key for optimizer)

## Prerequisites

- `skillopt` installed: `pip install --break-system-packages skillopt`
- `codex` CLI installed and authenticated: `codex login`
- Skill file exists at the given path

## Arguments

| Argument | Required | Description |
|----------|----------|-------------|
| `<skill-path>` | Yes | Path to the SKILL.md file (relative to project root) |
| `--optimize` | No | Run SkillOpt training loop to optimize the skill text |
| `--split` | No | Which split to evaluate: `train`, `val`, or `test` (default: `test`) |
| `--model` | No | Codex model to use (default: `gpt-5.4`) |

## Workflow

### Step 1: Generate scenarios

The command reads the skill and generates test scenarios based on:
- The skill's described activation conditions
- The skill's procedure steps
- The skill's anti-patterns
- Edge cases inferred from the skill's domain

Scenarios are saved to `benchmarks/<skill-name>/data/{train,val,test}/items.json`.

### Step 2: Set up benchmark

Creates the SkillOpt adapter, dataloader, evaluator, and config files in `benchmarks/<skill-name>/`.

### Step 3: Run evaluation

```bash
skillopt-eval \
  --config benchmarks/<skill-name>/config.yaml \
  --skill <skill-path> \
  --backend codex_exec \
  --target_model <model> \
  --split test \
  --env <skill-name>
```

### Step 4: Report results

Prints a scorecard with:
- Per-scenario: hard pass/fail, soft score, command/anti-pattern/behavior breakdown
- Overall: pass rate, average soft score
- Failed scenarios: what went wrong and suggested fixes

### Step 5: Optimize (optional)

If `--optimize` is passed and an OpenAI API key is available:

```bash
skillopt-train \
  --config benchmarks/<skill-name>/config.yaml \
  --backend codex_exec \
  --target_model <model> \
  --optimizer_backend openai_chat \
  --optimizer_model gpt-4o \
  --split train
```

Produces `benchmarks/<skill-name>/skills/best_skill.md` — the optimized version.

## Output

Results are saved to `outputs/eval_<skill-name>_<model>_<timestamp>/`:
- `rollouts.json` — full results with predictions and scores
- `predictions/<id>/` — per-scenario artifacts (conversation, eval details)
- `eval_summary.json` — aggregate scores
