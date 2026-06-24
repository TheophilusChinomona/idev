---
description: Turn this codebase into an onboarding playlist — analysis docs plus NotebookLM explainer videos (overview + per-subsystem), with a doc-review checkpoint before any video is generated.
argument-hint: "[subsystem] [--style <visual-style>]"
---

# /idev:explain-codebase

Invoke the **codebase-explainer** skill to build an onboarding playlist for the
current repository.

Arguments: `$ARGUMENTS`
- optional `subsystem` — limit generation to one subsystem video (still writes
  the overview doc for context).
- optional `--style <visual-style>` — NotebookLM visual style for all videos
  (default `whiteboard`).

Follow the skill's five stages in order. The doc-review checkpoint (Stage 4) is
mandatory — never generate videos before the user approves the docs.
