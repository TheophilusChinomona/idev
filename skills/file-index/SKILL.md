---
name: file-index
description: "DEPRECATED — Use smart-context for feature-to-file lookups. This skill is retained for backwards compatibility only; do not invoke directly."
---

# File Index — DEPRECATED

**This skill is deprecated.** Its functionality has been merged into `smart-context`:

- The smart-context `index.json` already contains feature names and file-naming patterns
- For exact file paths, grep the project-map (which smart-context references)
- The separate file-index was a redundant lookup layer

Use the smart-context skill for feature-to-file lookups. This file is retained only for backwards compatibility with existing per-project caches that reference it.
