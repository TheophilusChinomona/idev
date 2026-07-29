---
name: post-creation-verify
description: "DEPRECATED — Use build-check for post-creation verification and registration checks. This skill is retained for backwards compatibility only; do not invoke directly."
---

# Post-Creation Verify — DEPRECATED

**This skill is deprecated.** Its verification logic has been merged into `build-check`:

- Build-check now runs pre-flight checks for DI registrations, route tables, and wiring
- The db-preflight skill handles database schema verification
- Registration checks are part of the build error handling phase

Use the build-check skill for all post-creation verification. This file is retained only for backwards compatibility with existing per-project caches that reference it.
