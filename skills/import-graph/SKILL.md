---
name: import-graph
description: "DEPRECATED — Use LSP tools (lsp references, lsp definition) for dependency tracking. This skill is retained for backwards compatibility only; do not invoke directly."
---

# Import Graph — DEPRECATED

**This skill is deprecated.** Modern language servers (TypeScript LSP, Python LSP, etc.) provide superior import/dependency tracking via their `references` and `definition` capabilities.

Use the LSP tools instead:
- `lsp references` — find all usages of a symbol across the codebase
- `lsp definition` — navigate to where a symbol is defined
- `lsp implementation` — find all implementations of an interface

These are always up-to-date (no staleness issues) and handle renaming, shadowing, and re-exports correctly — something a static graph cannot.

This file is retained only for backwards compatibility with existing per-project caches that reference it.
