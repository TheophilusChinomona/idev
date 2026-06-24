# Codebase Explainer — Design Spec

**Date:** 2026-06-24
**Status:** Approved design, pre-implementation
**Target:** `idev` plugin (v0.10.0+)

## Summary

A reusable `idev` feature that turns any codebase into an **onboarding playlist**:
Claude-authored analysis docs plus a set of NotebookLM **explainer videos** — one
high-level overview video and one focused video per major subsystem — so a
developer can *watch* how the code works rather than only read it.

Built on the unofficial [`notebooklm-py`](https://github.com/teng-lin/notebooklm-py)
library, which can create notebooks, upload sources, and generate/download video
overviews via Python/CLI (Playwright-based Google auth).

## Goals

- Produce a **codebase onboarding playlist**: overview video + per-subsystem drill-down videos.
- Maximize narration quality by feeding NotebookLM **prose that explains concepts**, with key real files attached for grounding (hybrid sources).
- Package as a first-class, reusable `idev` skill + command, consistent with idev conventions.
- Be **resumable** so NotebookLM daily limits or timeouts don't force a full restart.

## Non-Goals (v1 — YAGNI)

- No audio overviews, quizzes, flashcards, mind maps, or slide decks (library supports them; deferred).
- No automatic upload/hosting of the resulting videos anywhere; they download locally.
- No CI integration or scheduled regeneration.
- No fully-unattended mode that skips the doc-review checkpoint.

## Key Decisions

| Decision | Choice | Rationale |
|----------|--------|-----------|
| Granularity | Overview video **+** per-subsystem videos | Bird's-eye view plus real drill-down onboarding |
| Source material | **Hybrid** — Claude-authored docs + key raw files | Docs drive explanatory narration; raw files ground it |
| Deliverable | **Reusable skill** in `idev` plugin | Works across all Speccon repos, version-controlled |
| Checkpoints | **Review docs, then auto-generate** | Docs are where quality is won; videos are slow/limited |
| Notebook strategy | **One notebook per video** | NotebookLM generates from *all* a notebook's sources; isolation keeps each video on-topic |
| v1 artifact type | **Video only** | Focused scope; other artifact types are trivial to add later |

## Architecture

### Pipeline (5 stages)

1. **Preflight** — ensure `notebooklm-py` + Playwright browser installed and NotebookLM auth is valid. First run guides interactive `notebooklm login`; later runs skip.
2. **Map** — build the codebase model. Read existing idev caches first
   (`.claude/idev/smart-context/index.json`, `project-map/project.map.md`,
   `architecture-scanner/cache.json`) when present, then dispatch the existing
   `onboarding-guide` agent to fill gaps. Output: a **subsystem inventory**
   (name, purpose, boundaries/paths, key files, dependencies, primary data flow).
3. **Author docs (hybrid sources)** — write narration-friendly Markdown to `docs/onboarding/`:
   - `00-overview.md` — architecture, how pieces fit, main end-to-end flows.
   - `NN-<subsystem>.md` (one per subsystem) — purpose, how it works, key files, dependencies, data flow. Prose that explains, not code dumps.
   - Select a shortlist of **key raw files** per subsystem (entry points, schemas) to attach as grounding sources.
4. **🛑 CHECKPOINT** — stop. User reviews/edits docs in `docs/onboarding/`. Nothing has been sent to Google yet. On approval, continue.
5. **Build & generate** — for each planned video (overview first, then subsystems):
   create its notebook, upload its sources, generate the explainer video with
   focus instructions, poll until ready, download to `docs/onboarding/videos/`,
   mark done in state. Regenerate `index.md` playlist each run.

### Components (new files in the plugin)

| File | Role |
|------|------|
| `skills/codebase-explainer/SKILL.md` | Orchestrator — the 5-stage pipeline and its rules |
| `skills/codebase-explainer/preflight.py` | Verify/install `notebooklm-py` + Playwright; check auth |
| `skills/codebase-explainer/notebooklm_runner.py` | Wrapper over `notebooklm-py`: create notebook, upload sources, generate/poll/download video. Importable + CLI, invoked via `${CLAUDE_PLUGIN_ROOT}` |
| `commands/explain-codebase.md` | Entry point `/idev:explain-codebase [subsystem]` |

### Reuse (not rebuilt)

- `onboarding-guide` agent — read-only codebase mapper (Stage 2).
- `smart-context`, `project-map`, `architecture-scanner` caches — head-start data for Stage 2.

### NotebookLM build details

- **One notebook per video:**
  - *Overview notebook* ← all `*.md` docs + a couple of top-level entry files.
  - *Per-subsystem notebook* ← that subsystem's `NN-<subsystem>.md` + its key raw files + `00-overview.md` for context.
- **Generation:** format `explainer`; a single visual style applied to all videos for a consistent playlist look. Style is a skill arg with a sensible clean/technical default.
- **Focus instructions** per video derived from its doc intro, e.g. *"Explain how the X subsystem works for a new developer; cover responsibilities, key files, and the main data flow."*

### State & outputs (per project)

- **Deliverables (committable):** `docs/onboarding/` → `00-overview.md`, `NN-<subsystem>.md`, `videos/*.mp4`, `index.md`.
- **Skill state (idev convention):** `.claude/idev/codebase-explainer/state.json` → notebook IDs + per-video status (`pending` / `generating` / `done` / `failed`).

## Data Flow

```
codebase
  └─(Stage 2: onboarding-guide + idev caches)→ subsystem inventory
        └─(Stage 3)→ docs/onboarding/*.md  + key-file shortlist
              └─🛑 user review/edit
                    └─(Stage 5, per video)→ NotebookLM notebook
                          → upload sources → generate explainer video
                          → poll → download → docs/onboarding/videos/*.mp4
                          → update state.json → regenerate index.md
```

## Error Handling & Resumability

- **Auth invalid/expired:** preflight detects it and prompts the user to re-run `notebooklm login`; pipeline does not proceed past preflight.
- **NotebookLM daily limit / generation failure:** record `failed`/`pending` in `state.json`, finish any in-flight downloads, and report which videos remain. Re-running the command **skips `done` videos** and resumes the rest.
- **Timeout while polling:** treat as `pending`; the notebook + generation may still complete server-side, so resume re-checks status before regenerating.
- **No subsystems detected / tiny repo:** fall back to overview video only.
- **Partial success:** `index.md` always reflects reality — completed videos linked, others marked pending.

## Testing

- **preflight.py:** unit test the detection/branching (installed vs missing, auth present vs absent) with mocked environment; no real Google calls.
- **notebooklm_runner.py:** unit test argument construction and state transitions against a mocked `notebooklm-py` client; one optional, manually-run integration smoke test against a real account (not in CI).
- **Skill flow:** dry-run on a small sample repo through the checkpoint (Stages 1–4) verifying docs + inventory are produced and no network calls happen before approval.
- Follow existing idev test conventions (`tests/`, `scripts/validate.sh`).

## Open Questions (resolve during planning)

- Exact default visual style name once verified against the installed `notebooklm-py` API surface.
- Whether to cap the number of subsystem videos by default (e.g. top-N by size/importance) to stay under NotebookLM daily limits, with an arg to override.
