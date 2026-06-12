---
description: Show all learned instincts with their confidence levels, grouped by domain
---

# Instinct Status

Show the user the current state of the auto-learning instinct store.

## How to Run

Run the instinct CLI and relay its output:

```bash
python3 "${CLAUDE_PLUGIN_ROOT}/skills/auto-learning/scripts/instinct-cli.py" status
```

The `status` subcommand takes no flags.

## What It Prints

- Total instinct count, split into personal (auto-learned) and inherited (imported)
- Instincts grouped by domain, each with a confidence bar, trigger, and action summary
- Observation stats from `~/.claude/homunculus/observations.jsonl`

## After Running

1. Present the CLI output to the user (verbatim or lightly summarized).
2. If the user wants filtering (by domain, confidence, or source), apply it yourself by reading the relevant instinct files under `~/.claude/homunculus/instincts/{personal,inherited}/` — the CLI does not support filter flags.
3. If there are no instincts yet, point the user to the hook setup in the `auto-learning` skill (observation hooks must be enabled for instincts to accumulate).
