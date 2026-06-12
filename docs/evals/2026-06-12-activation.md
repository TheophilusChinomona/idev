# Activation Eval — 2026-06-12 (plugin v0.9.0, 27 skills)

## Methodology

Offline routing simulation, per the skill-benchmark skill's methodology:
five independent judge agents each received the full catalog of 27 skill
name+description pairs (exactly what drives triggering in a session) plus
10 user messages — 7 that SHOULD route to the target skill, 3 that should
NOT — and returned which skill(s) they would invoke per message, blind to
which skill was under test.

**Limitation (stated per anti-fabrication rules):** this measures
description routing by a judge model, not live-session activation. Live
behavior also depends on conversation context and CLAUDE.md guidance.
Treat as a lower-bound sanity check, not a live activation rate.

## Results

| Target skill | Should-trigger | False positives | Verdict |
|---|---|---|---|
| branch-sync | 7/7 | 0/3 | clean |
| browser-test | 7/7 | 0/3 | clean |
| build-check | 7/7 | 0/3 | clean ("Build me a landing page" correctly routed to frontend-patterns) |
| post-creation-verify | 7/7 | 0/3 | clean (one co-activation with feature-completeness — complementary) |
| smart-context | 3/7 strict | 0/3 | see finding |

**Overall: 31/35 strict TP (89%), 0/15 FP (0%).**

## Finding: smart-context ↔ file-index overlap

The four smart-context "misses" ("where is feature X implemented"-style
prompts) all routed to **file-index** — whose stated purpose IS
feature→file lookup. The user lands in the right place either way, so no
task failure; but the two descriptions claimed the same trigger. Fix
applied after this eval: smart-context's description now scopes itself to
session-start loading, context policy, and index generation, and
explicitly defers feature→path lookups to file-index.

## Off-target observations (not failures of the skill under test)

- "Squash my last three commits" → commit-style (borderline; acceptable —
  the squash ends in a commit message).
- "Run the unit tests" → no skill (test-map arguably should fire;
  its description leans on "after modifying source files" — watch in
  field use before changing).

## Not yet measured

Live-session activation, effectiveness A/B (skill vs no skill), and
multi-model pass rates (Haiku/Sonnet/Opus targets) — these need field
sessions; see the evaluation-checklist template in the skill-benchmark
skill.
