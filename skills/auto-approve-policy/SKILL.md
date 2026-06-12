---
name: auto-approve-policy
description: "Caution protocol for destructive operations. Use before deleting files, dropping database objects, removing exports/public APIs, or running irreversible commands."
---

# Destructive Operation Caution Protocol

This skill is a behavioral guideline, not a permissions mechanism. Actual auto-approval of tools is configured in `settings.json` permissions — nothing here grants or withholds tool access.

## Before a Destructive Action

Destructive actions include: deleting files or directories, dropping or truncating database objects, removing exported functions or public API surface, deleting migrations or config entries, force-pushing, hard resets, and other irreversible commands.

Decide based on intent:

1. **Explicitly requested** — the user asked for this specific removal ("delete X", "remove the obsolete helpers"). Do it. Do NOT second-guess the user, suggest commenting code out instead, or rename things with "Legacy" prefixes. Just perform the deletion cleanly and report what was removed.

2. **Incidental to a broader task** — the deletion is a side effect the user did not specifically ask for (e.g., removing a file while refactoring). Pause and confirm before proceeding, stating what would be removed and why.

3. **Bulk or wide-impact removals** — before deleting many files or rows, report the list of what will be removed first, then proceed (if explicitly requested) or wait for confirmation (if incidental).

## Non-Destructive Work

Additions and edits need no special treatment from this skill — proceed normally under whatever permissions the session grants.

## Summary

- Explicit request to delete → delete, then report what was removed
- Incidental deletion → confirm first
- Bulk deletion → enumerate before acting
- Never leave commented-out corpses or "Legacy"-renamed clutter as a substitute for a requested deletion
