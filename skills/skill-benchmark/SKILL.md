---
name: skill-benchmark
description: "Evaluates and benchmarks Agent Skill quality via static analysis and evaluation methodology. Use when assessing or reviewing skill quality, benchmarking skills, measuring skill activation accuracy, optimizing skill descriptions, or running /idev:benchmark-skills."
---

# Skill Benchmark — Evaluate Agent Skill Quality

Evaluate skills through static analysis (automated, run the script) and
evaluation-driven methodology (manual, follow the process below). Adapted from
Anthropic's skill evaluation guidance.

## Static analysis (automated)

Run the checker against any plugin:

```bash
python3 "${CLAUDE_PLUGIN_ROOT}/skills/skill-benchmark/benchmark_skills.py"            # this plugin
python3 "${CLAUDE_PLUGIN_ROOT}/skills/skill-benchmark/benchmark_skills.py" --plugin-dir <dir>
```

It scores every `skills/*/SKILL.md` against these checks:

| Check | Pass criteria |
|-------|---------------|
| desc-present | Description non-empty, ≤ 1024 chars |
| desc-triggers | Contains "Use when/before/after/for" activation triggers |
| desc-3rd-person | No "I can" / "You can" phrasing |
| name-kebab | Matches `^[a-z0-9]+(-[a-z0-9]+)*$` |
| name-length | ≤ 64 chars |
| name-reserved | No "anthropic"/"claude" in the name |
| name-matches-dir | Frontmatter name equals directory name |
| body-length | SKILL.md ≤ 500 lines |
| has-examples | Contains at least one fenced code block |
| refs-resolve | Every `${CLAUDE_PLUGIN_ROOT}/...` path in the file exists |

`--strict --min-score N` makes it exit non-zero below a threshold (CI use).

## Skill categories

Classify each skill before evaluating — the test differs:

- **Capability uplift**: enhances core abilities (analysis, verification,
  code patterns). Stable across model versions. Test by comparing base-model
  output with and without the skill.
- **Encoded preference**: encodes project/team workflows and conventions
  (commit formats, cache layouts). Test by verifying fidelity to the encoded
  workflow, not output quality.

## Evaluation methodology (manual)

For activation accuracy and effectiveness, static checks aren't enough:

1. **Write evals per skill**: 5-10 representative prompts that SHOULD trigger
   it, 3-5 out-of-scope prompts that should NOT, and expected-behavior
   criteria for each. Use `evaluation-checklist.md` in this skill's directory
   as the template.
2. **A/B test**: run agent A with the skill loaded and agent B without; have
   a third agent judge outputs blind. Track pass rate, token usage, time.
3. **Multi-model targets**: Haiku 70%+, Sonnet 85%+, Opus 95%+ pass rate.
   If only Haiku fails, the instructions rely on implicit reasoning — make
   them more explicit.

## Description optimization

The description alone determines activation. Tune for ~90%+ true positives
and <5% false positives:

- Too many false positives → description too broad: add domain-specific terms.
- Too many false negatives → too narrow: add synonyms and adjacent phrasings.

## Iteration

Test → measure → analyze → refine → verify. Stop when eval pass rates meet
the model-tier targets, activation is accurate, and token cost is justified
by the benefit.

## Reporting rules (anti-fabrication)

- Run the script (or the evals) BEFORE making any quality claim; report only
  what was measured.
- Never invent percentages, pass rates, or activation numbers — if unmeasured,
  say "not yet measured".
- No superlatives ("excellent", "comprehensive", "optimal") in assessments;
  state which checks passed and failed.
- Verify files exist (Read/Glob) before claiming they do.
