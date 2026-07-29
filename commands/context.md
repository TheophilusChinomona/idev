---
description: "Switch between development modes: dev, review, or research."
argument-hint: "[dev|review|research]"
---

# /context — Switch Development Mode

Switch Claude's behavior mode for the current task.

## Modes

| Command | Mode | What Changes |
|---------|------|-------------|
| `/context dev` | Development | Write code, run tests, commit often |
| `/context review` | Review | Read thoroughly, find issues, suggest fixes |
| `/context research` | Research | Explore, understand, document findings |

## Usage

```
/context dev       # Switch to development mode
/context review    # Switch to code review mode
/context research  # Switch to research mode
```

## What Happens
Claude loads the corresponding context file from `contexts/` and adjusts its behavior:
- Tool preferences change
- Priorities shift
- Output format adapts
