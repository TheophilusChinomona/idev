---
name: continuous-learning
description: "Automatically extracts reusable patterns from sessions and saves them as learned skills. Use when asked to learn from a session, extract patterns, or review what was learned."
---

# Continuous Learning Skill

## Purpose
Automatically evaluate sessions and extract reusable patterns that improve future sessions.

## How It Works

Runs as a **Stop hook** at session end:
1. Checks if session has enough activity (default: 10+ tool calls)
2. Identifies extractable patterns (error resolutions, user corrections, workarounds)
3. Saves patterns to `~/.claude/homunculus/instincts/personal/`

## Configuration

`config.json` in this skill directory:

```json
{
  "min_session_length": 10,
  "extraction_threshold": "medium",
  "patterns_to_detect": [
    "error_resolution",
    "user_corrections",
    "workarounds",
    "debugging_techniques",
    "project_specific"
  ],
  "ignore_patterns": [
    "simple_typos",
    "one_time_fixes",
    "external_api_issues"
  ]
}
```

## Pattern Types

| Pattern | Description |
|---------|-------------|
| `error_resolution` | How specific errors were resolved |
| `user_corrections` | Patterns from user corrections |
| `workarounds` | Solutions to framework quirks |
| `debugging_techniques` | Effective debugging approaches |
| `project_specific` | Project-specific conventions |

## Integration with Auto-Learning

This skill feeds into the existing auto-learning system:
- Extracted patterns become instincts in `~/.claude/homunculus/instincts/personal/`
- High-confidence instincts can evolve into skills via `/idev:evolve`

## Anti-Patterns
1. Do NOT extract trivial patterns (typos, one-off fixes)
2. Do NOT extract patterns without evidence (must be observed 2+ times)
3. Do NOT overwrite existing instincts — update confidence instead
