---
description: "Update documentation to match current code."
argument-hint: "[--check]"
---

# /update-docs — Sync Docs with Code

Update README, ARCHITECTURE, and other docs to reflect current code state.

## Usage

```
/update-docs           # Update all docs
/update-docs --check   # Check what needs updating (dry run)
```

## What Gets Updated
- README.md: component counts, feature descriptions
- CHANGELOG.md: new entries for significant changes
- templates/claude-md-snippet.md: workflow chain updates

## Anti-Patterns
1. Do NOT auto-update CHANGELOG — that's manual
2. Do NOT remove user-added content — only add/update
