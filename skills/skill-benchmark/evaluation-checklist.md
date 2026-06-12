# Skill Evaluation Checklist — <skill-name>

Category: capability-uplift | encoded-preference
Date: <YYYY-MM-DD>   Models tested: <haiku|sonnet|opus>

## Activation evals

Should-trigger prompts (5-10) — expected: skill activates:

| # | Prompt | Activated? |
|---|--------|------------|
| 1 |        |            |

Should-NOT-trigger prompts (3-5) — expected: skill stays cold:

| # | Prompt | Activated? |
|---|--------|------------|
| 1 |        |            |

True positive rate: __ / __    False positive rate: __ / __
(targets: ≥90% TP, <5% FP)

## Effectiveness evals (A/B)

| # | Task prompt | With skill | Without skill | Blind judge verdict |
|---|-------------|------------|----------------|---------------------|
| 1 |             |            |                |                     |

Pass rate with skill: __    without: __    Token delta: __

## Verdict

- [ ] Activation accurate (or description change proposed: ...)
- [ ] Skill output beats baseline (or revision proposed: ...)
- [ ] Token cost justified
