---
name: context-switching
description: "Switches between development modes (dev, review, research) by loading the appropriate context. Use when the user changes task type or asks to switch modes."
---

# Context Switching Skill

## Purpose
Dynamically adjust Claude's behavior based on the current task mode.

## Modes

| Mode | Context File | Behavior |
|------|-------------|----------|
| dev | `contexts/dev.md` | Write code, run tests, commit often |
| review | `contexts/review.md` | Read thoroughly, find issues, suggest fixes |
| research | `contexts/research.md` | Explore, understand, document findings |

## Activation
- User says "switch to review mode" or "let's review this"
- User says "research how X works" or "investigate Y"
- User says "switch to dev mode" or "let's build this"
- Task type changes mid-session

## Example

```
User: "let's review this PR"
→ Claude loads contexts/review.md
→ Behavior shifts to thorough reading, issue prioritization
→ Output grouped by file, severity first

User: "switch to dev mode, let's build the feature"
→ Claude loads contexts/dev.md
→ Behavior shifts to writing code, running tests
→ Output focuses on implementation
```

## How It Works
1. Read the appropriate context file from `${CLAUDE_PLUGIN_ROOT}/contexts/`
2. Load its behavior rules into working memory
3. Apply those rules until the mode changes

## Anti-Patterns
1. Do NOT stay in research mode when the user wants to build
2. Do NOT switch modes without telling the user
3. Do NOT load multiple modes simultaneously
