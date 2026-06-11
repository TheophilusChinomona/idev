---
name: strategic-compact
description: Suggests manual context compaction at logical intervals to preserve context through task phases rather than arbitrary auto-compaction.
priority: low
auto_trigger: false
user_invocable: false
platform: all
integrates_with:
  - smart-context
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

## How It Works

The script runs on PreToolUse (Edit/Write) and:

1. **Tracks tool calls** - Counts tool invocations in session
2. **Threshold detection** - Suggests at configurable threshold (default: 50 calls)
3. **Periodic reminders** - Reminds every 25 calls after threshold

## Hook Setup

### Windows (PowerShell)

Add to your `%USERPROFILE%\.claude\settings.json`:

```json
{
  "hooks": {
    "PreToolUse": [{
      "matcher": "tool == \"Edit\" || tool == \"Write\"",
      "hooks": [{
        "type": "command",
        "command": "powershell -ExecutionPolicy Bypass -File \"%USERPROFILE%\\.claude\\skills\\strategic-compact\\suggest-compact.ps1\""
      }]
    }]
  }
}
```

### Unix/macOS (Bash)

Add to your `~/.claude/settings.json`:

```json
{
  "hooks": {
    "PreToolUse": [{
      "matcher": "tool == \"Edit\" || tool == \"Write\"",
      "hooks": [{
        "type": "command",
        "command": "${CLAUDE_PLUGIN_ROOT}/skills/strategic-compact/suggest-compact.sh"
      }]
    }]
  }
}
```

## Configuration

Environment variables:
- `COMPACT_THRESHOLD` - Tool calls before first suggestion (default: 50)
- `COMPACT_REMINDER_INTERVAL` - Calls between reminders after threshold (default: 25)

## Best Practices

1. **Compact after planning** - Once plan is finalized, compact to start fresh
2. **Compact after debugging** - Clear error-resolution context before continuing
3. **Don't compact mid-implementation** - Preserve context for related changes
4. **Read the suggestion** - The hook tells you *when*, you decide *if*

## Integration with smart-context

This skill integrates with smart-context to provide context-aware suggestions:

```
When suggesting compact:
1. Check index.json for current session context
2. Note which features have been explored
3. Include in suggestion: "Context explored: [features]"
```

### Compact Preserves

After `/compact`, the following persists:
- `.claude/idev/smart-context/index.json` - Feature index
- `.claude/idev/api-contracts/*` - API documentation
- `.claude/idev/project-map/project.map.md` - Project structure

### Best Compact Points

| Phase | Compact After | Why |
|-------|---------------|-----|
| Exploration | Reading 10+ files | Research context no longer needed |
| Planning | Plan finalized | Implementation needs fresh context |
| Debugging | Bug fixed | Error traces no longer needed |
| Feature complete | Tests pass | Ready for next feature |

## Related

- [The Longform Guide](https://x.com/affaanmustafa/status/2014040193557471352) - Token optimization section
- Memory persistence hooks - For state that survives compaction
- smart-context skill - For context that persists across compaction
