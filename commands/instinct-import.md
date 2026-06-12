---
description: Import instincts from a teammate's export file or a URL
argument-hint: "<file-or-url> [--dry-run] [--force] [--min-confidence <n>]"
---

# Instinct Import

Import instincts from a file or URL into `~/.claude/homunculus/instincts/inherited/`.

## How to Run

Run the instinct CLI, passing through the user's source and flags:

```bash
python3 "${CLAUDE_PLUGIN_ROOT}/skills/auto-learning/scripts/instinct-cli.py" import $ARGUMENTS
```

## Supported Flags (these are the only ones)

- `--dry-run`: preview what would be imported without writing anything
- `--force`: skip the confirmation prompt
- `--min-confidence <n>`: only import instincts at or above this confidence

Note: when run non-interactively (which is how this command runs), the CLI does not prompt — it proceeds as confirmed. Use `--dry-run` first if the user wants a preview before committing.

## What the CLI Does

1. Fetches the source (local path or http/https URL) and parses its instinct blocks
2. Compares against existing instincts by `id`:
   - New ids are added to a timestamped file in `~/.claude/homunculus/instincts/inherited/`
   - Existing ids with higher imported confidence are updated **in place** in their original file (no duplicate copies)
   - Existing ids with equal/lower confidence are skipped
3. Marks added instincts with `source: inherited` and `imported_from`

## Recommended Flow

1. Run with `--dry-run` first and show the user the NEW/UPDATE/SKIP summary.
2. If the user approves, re-run without `--dry-run`.
3. Afterwards, suggest `/idev:instinct-status` to review the merged set.
4. If the user reports a conflict (an imported instinct contradicts a local one), resolve it manually by editing the relevant files under `~/.claude/homunculus/instincts/` — the CLI does not do conflict detection.
