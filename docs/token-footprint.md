# Token Footprint Baseline — 2026-06-12 (v0.9.0, 27 skills)

Measured with `benchmark_skills.py --footprint` (estimate: chars ÷ 4).
Re-run after adding/removing skills and compare against this baseline.

## Always-loaded cost (every session, every project)

| Component | Est. tokens |
|---|---|
| 27 skill name+description pairs | ~1,668 |
| CLAUDE.md operating-guide snippet (initialized projects) | ~850 |
| SessionStart hook injection (varies with journal/session size, bounded) | ≤ ~1,100 |

Total fixed overhead in an initialized project: **roughly 3.5k tokens per
session** — the budget the cache-first savings must beat. One avoided
whole-file read of a 1,000-line file (~10k tokens) pays for it ~3×.

## On-demand cost (only when a skill triggers)

- All 27 bodies summed: ~34k tokens — but bodies load individually.
- Heaviest: backend-patterns (~2.1k), auto-learning (~2.1k),
  api-contract-validation (~2.0k). All under the 500-line/~2.5k-token cap
  the benchmark enforces.
- branch-sync demonstrates the cheaper pattern: ~1.0k body + a
  references/ playbook that loads only on actual merge conflicts.

## Watch items

1. Description budget grows ~60 tokens per new skill — at 27 skills it's
   still cheap; revisit if the pack passes ~40.
2. The four heaviest bodies are candidates for the references/ split if
   they grow further.
3. Unmeasured: real-session savings of cache-first vs vanilla behavior.
   Needs field data from dogfooding — record a before/after token usage
   comparison on the same task when possible.
