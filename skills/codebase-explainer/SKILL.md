---
name: codebase-explainer
description: "Turn a codebase into an onboarding playlist — Claude-authored analysis docs plus NotebookLM explainer videos (one overview + one per subsystem). Use when asked to explain a codebase, onboard onto a repo, make explainer/walkthrough videos of the code, or 'help me understand how this whole thing works'."
---

# Codebase Explainer

Produces an onboarding playlist for a repository: narration-friendly Markdown
docs plus NotebookLM **explainer videos** (one overview + one per subsystem).
Claude does the judgement stages (map, author docs); Python scripts do the
mechanical stages (preflight, build). Built on `notebooklm-py` via its CLI.

## Outputs (in the target repo)
- `docs/onboarding/00-overview.md`, `NN-<subsystem>.md` — analysis docs
- `docs/onboarding/videos/*.mp4` — generated videos
- `docs/onboarding/index.md` — playlist linking each doc → its video
- `.claude/idev/codebase-explainer/plan.json` — build plan (you author this)
- `.claude/idev/codebase-explainer/state.json` — resumable progress

## Stage 1 — Preflight
Run and read the JSON:
```bash
python3 "${CLAUDE_PLUGIN_ROOT}/skills/codebase-explainer/preflight.py"
```
If `ready` is false, surface each `messages` line to the user (install /
`notebooklm login`) and STOP until resolved. Auth is an interactive Google
login the user performs once.

## Stage 2 — Map the codebase
Read existing idev caches first when present (they are a head start):
`.claude/idev/smart-context/index.json`, `.claude/idev/project-map/project.map.md`,
`.claude/idev/architecture-scanner/cache.json`. Then dispatch the
`onboarding-guide` agent to identify: tech stack, entry points, and the major
**subsystems** (name, purpose, boundary paths, key files, dependencies, primary
data flow). If few/no subsystems are detected (tiny repo), plan an overview
video only.

## Stage 3 — Author docs + build plan
Write to `docs/onboarding/`:
- `00-overview.md` — architecture, how the pieces fit, main end-to-end flows.
- `NN-<subsystem>.md` — one per subsystem: purpose, how it works, key files,
  dependencies, data flow. Write **prose that explains concepts**, not code dumps.

Then write `.claude/idev/codebase-explainer/plan.json`:
```json
{
  "style": "whiteboard",
  "videos": [
    {"key": "overview", "title": "Overview",
     "notebook_name": "<repo> — Overview",
     "sources": ["docs/onboarding/00-overview.md", "<1-2 key entry files>"],
     "instructions": "Explain how this system works for a new developer: architecture and main flows.",
     "output": "docs/onboarding/videos/00-overview.mp4",
     "doc": "docs/onboarding/00-overview.md"},
    {"key": "<subsystem-key>", "title": "<Subsystem>",
     "notebook_name": "<repo> — <Subsystem>",
     "sources": ["docs/onboarding/01-<subsystem>.md", "docs/onboarding/00-overview.md", "<key raw file>"],
     "instructions": "Explain the <subsystem> for a new developer: responsibilities, key files, main data flow.",
     "output": "docs/onboarding/videos/01-<subsystem>.mp4",
     "doc": "docs/onboarding/01-<subsystem>.md"}
  ]
}
```
- `sources` are file paths (docs + a few key raw files for grounding — hybrid).
- `style` applies to every video for a consistent look; set it to the `--style <visual-style>` value from `$ARGUMENTS` (default `whiteboard` if omitted).
- If a `subsystem` positional argument was given in `$ARGUMENTS`, limit `videos` to the overview entry plus that one subsystem's entry only (still write the overview doc for context, but omit all other subsystem docs from plan.json).
- If few/no subsystems were detected (tiny repo, same as Stage 2), omit the per-subsystem `NN-<subsystem>.md` docs and include only the overview video in plan.json.

## Stage 4 — CHECKPOINT (mandatory)
STOP. Tell the user the docs are in `docs/onboarding/` and ask them to review/edit
before any videos are generated. Nothing has been sent to NotebookLM yet. Only
continue on explicit approval.

## Stage 5 — Build & generate
```bash
python3 "${CLAUDE_PLUGIN_ROOT}/skills/codebase-explainer/build_videos.py" \
  --plan .claude/idev/codebase-explainer/plan.json \
  --state .claude/idev/codebase-explainer/state.json \
  --index docs/onboarding/index.md
```
Generates sequentially (overview first), polling and downloading each video.
On a failure (e.g. NotebookLM daily limit) it records progress and stops — tell
the user which videos remain and that **re-running the same command resumes**,
skipping completed videos. Report the final playlist at `docs/onboarding/index.md`.
