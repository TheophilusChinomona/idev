---
name: skillopt
description: "Benchmarks and optimizes idev skills using Microsoft SkillOpt. Use when asked to test a skill's quality, optimize a skill, benchmark skill performance, or run SkillOpt on a skill."
---

# SkillOpt Skill — Benchmark & Optimize Agent Skills

Use Microsoft SkillOpt to evaluate and improve idev skills through trajectory-driven edits and validation-gated updates.

## Activation

- User says "benchmark this skill" or "test skill quality"
- User says "optimize this skill" or "improve this skill with SkillOpt"
- User runs `/idev:skillopt <skill-path>`
- User wants to know if a skill actually helps the agent succeed (not just static analysis)

## How It Works

SkillOpt treats the skill document as trainable state and uses a separate optimizer model to improve it through scored rollouts. The flow:

1. **Generate scenarios** from the skill's described behavior
2. **Run rollouts** — execute the skill against scenarios using the target model (Codex CLI)
3. **Score results** — check if the skill guided the agent to correct outcomes
4. **Reflect on failures** — analyze what went wrong and why
5. **Propose edits** — bounded add/delete/replace on the skill text
6. **Validate** — only accept edits that improve held-out validation scores

## Prerequisites

- `pip install --break-system-packages skillopt`
- `codex` CLI installed and authenticated (`codex login`)
- Skill file exists at the given path

## Using the Command

```
/idev:skillopt skills/branch-sync/SKILL.md
/idev:skillopt skills/build-check/SKILL.md --optimize
```

## What Gets Generated

For each skill, a benchmark directory is created:

```
benchmarks/<skill-name>/
├── __init__.py
├── dataloader.py      # Loads test scenarios
├── evaluator.py       # Scores responses
├── rollout.py         # Runs skill against scenarios
├── adapter.py         # SkillOpt integration
├── config.yaml        # Training config
├── skills/
│   └── initial.md     # Current skill text (seed)
└── data/
    ├── train/items.json
    ├── val/items.json
    └── test/items.json
```

## Evaluation Dimensions

Each scenario is scored on three dimensions:

| Dimension | Weight | What it checks |
|-----------|--------|----------------|
| Commands | 40% | Correct commands present in response |
| Anti-patterns | 30% | No forbidden patterns (--ours, --theirs, force push, etc.) |
| Behaviors | 30% | Expected behaviors demonstrated |

A scenario passes if the weighted soft score ≥ 0.6.

## After Optimization

If `--optimize` is used, SkillOpt produces `best_skill.md` — the optimized version. Review it before adopting:

1. Read the optimized skill
2. Check that it preserves the original intent
3. Verify it doesn't overfit to the test scenarios
4. Merge improvements into the original skill

## Anti-Patterns

1. Do NOT optimize without test scenarios — you need data to validate against
2. Do NOT blindly adopt optimized skills — review for correctness
3. Do NOT run optimization on skills that are already passing all scenarios
4. Do NOT use a different model for optimization than what the skill targets
