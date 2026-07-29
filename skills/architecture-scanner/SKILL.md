---
name: architecture-scanner
description: "DEPRECATED — Use project-map, backend-patterns, and frontend-patterns instead. This skill is retained for backwards compatibility only; do not invoke directly."
---

# Architecture Scanner — DEPRECATED

**This skill is deprecated.** Its functionality has been distributed to more focused skills:

- **Layer detection** → `project-map` (generates FE/BE file map with layer annotations)
- **Backend conventions** → `backend-patterns` (scans and caches backend code patterns)
- **Frontend conventions** → `frontend-patterns` (scans and caches frontend code patterns)
- **FE↔BE endpoint mapping** → `api-contract-validation` (discovers and validates API routes)

If you need architecture information, use those skills directly. This file is retained only for backwards compatibility with existing per-project caches that reference it.
