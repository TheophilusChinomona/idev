---
name: strategic-compact
description: "Suggests manual /compact at logical task boundaries (after exploration, planning, milestones) instead of arbitrary auto-compaction. Use when the user wants automatic /compact reminders, asks about managing context size, or when deciding whether to suggest compaction at a phase boundary."
---

# Strategic Compact Skill

Suggests manual `/compact` at strategic points in your workflow rather than relying on arbitrary auto-compaction.

## Why Strategic Compaction?

Auto-compaction triggers at arbitrary points:
- Often mid-task, losing important context
- No awareness of logical task boundaries
- Can interrupt complex multi-step operations

Strategic compaction at logical boundaries:
- **After exploration, before execution** - Compact research context, keep implementation plan
- **After completing a milestone** - Fresh start for next phase
- **Before major context shifts** - Clear exploration context before different task

## What Claude should do when this skill loads

1. At phase boundaries (plan finalized, milestone complete, bug fixed, long exploration finished), suggest the user run `/compact` — briefly, with the reason.
2. When the PostToolUse hook below injects a `[strategic-compact]` reminder, treat it as a prompt to evaluate whether the current moment is a logical boundary; only suggest `/compact` if it is. Never suggest it mid-implementation.
3. Remind the user that durable state survives compaction: `.claude/idev/smart-context/index.json`, `.claude/idev/project-map/project.map.md`, and the other `.claude/idev/` caches.

## How the hook works

`suggest-compact.sh` (Unix) / `suggest-compact.ps1` (Windows) run on **PostToolUse** with matcher `Edit|Write`:

1. Read the hook JSON from stdin and extract `session_id`
2. Increment a per-session counter file in the temp directory
3. Every N calls (default 50), emit `hookSpecificOutput` JSON on stdout, which Claude Code injects as additional context for Claude

## Hook Setup

Add to your `~/.claude/settings.json`. NOTE: `${CLAUDE_PLUGIN_ROOT}` is NOT expanded in user settings — replace `<idev-plugin-root>` below with the absolute path of the installed idev plugin (find it with `claude plugin list` or under `~/.claude/plugins/`):

### Unix/macOS

```json
{
  "hooks": {
    "PostToolUse": [{
      "matcher": "Edit|Write",
      "hooks": [{
        "type": "command",
        "command": "bash \"<idev-plugin-root>/skills/strategic-compact/suggest-compact.sh\""
      }]
    }]
  }
}
```

### Windows (PowerShell)

```json
{
  "hooks": {
    "PostToolUse": [{
      "matcher": "Edit|Write",
      "hooks": [{
        "type": "command",
        "command": "powershell -ExecutionPolicy Bypass -File \"<idev-plugin-root>\\skills\\strategic-compact\\suggest-compact.ps1\""
      }]
    }]
  }
}
```

The matcher is a regex over tool names (`Edit|Write`) — not an expression language.

## Configuration

- `IDEV_COMPACT_THRESHOLD` - Edit/Write calls between suggestions (default: 50)

## Best Practices

1. **Compact after planning** - Once plan is finalized, compact to start fresh
2. **Compact after debugging** - Clear error-resolution context before continuing
3. **Don't compact mid-implementation** - Preserve context for related changes
4. **The hook tells you *when*, you decide *if***

| Phase | Compact After | Why |
|-------|---------------|-----|
| Exploration | Reading 10+ files | Research context no longer needed |
| Planning | Plan finalized | Implementation needs fresh context |
| Debugging | Bug fixed | Error traces no longer needed |
| Feature complete | Tests pass | Ready for next feature |

## Related

- smart-context skill - For context that persists across compaction
- project-map skill - The map survives compaction at `.claude/idev/project-map/project.map.md`
