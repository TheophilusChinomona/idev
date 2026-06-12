---
description: Run the skill quality benchmark — static scorecard for every skill in this plugin (or a given plugin directory), with category classification and improvement recommendations.
argument-hint: "[plugin-dir]"
---

# /idev:benchmark-skills

Benchmark Agent Skill quality using the idev:skill-benchmark skill.

Arguments: `$ARGUMENTS` (optional plugin directory; default is the idev plugin itself).

## Steps

1. Run the static analysis:
   ```bash
   python3 "${CLAUDE_PLUGIN_ROOT}/skills/skill-benchmark/benchmark_skills.py" $ARGUMENTS
   ```
   (Pass `--plugin-dir <dir>` if the user named another plugin.)

2. Present the scorecard table verbatim, then for each skill that failed any
   check, explain the failure concretely and propose the specific fix (e.g.
   the exact description rewrite, which referenced path is missing).

3. Classify each failing skill as capability-uplift or encoded-preference and
   note what kind of eval would verify a fix (per the skill-benchmark skill's
   methodology).

4. Report only measured results — no invented rates or scores. If the user
   wants activation/effectiveness numbers, offer to build evals from
   `${CLAUDE_PLUGIN_ROOT}/skills/skill-benchmark/evaluation-checklist.md`.
