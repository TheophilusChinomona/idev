---
name: test-map
description: "DEPRECATED — Use build-check for test mapping and targeted test running. This skill is retained for backwards compatibility only; do not invoke directly."
---

# Test Map — DEPRECATED

**This skill is deprecated.** Its functionality has been merged into `build-check`:

- Build-check now includes test-file mapping (source → test files)
- It generates a test map on first use and updates it incrementally
- After a build, it can run only the tests affected by modified files

Use the build-check skill for all build and test verification. This file is retained only for backwards compatibility with existing per-project caches that reference it.
