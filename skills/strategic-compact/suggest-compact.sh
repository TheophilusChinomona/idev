#!/bin/bash
# Strategic Compact Suggester
# Runs on PreToolUse or periodically to suggest manual compaction at logical intervals
#
# Why manual over auto-compact:
# - Auto-compact happens at arbitrary points, often mid-task
# - Strategic compacting preserves context through logical phases
# - Compact after exploration, before execution
# - Compact after completing a milestone, before starting next
#
# Hook config (in ~/.claude/settings.json):
# {
#   "hooks": {
#     "PreToolUse": [{
#       "matcher": "tool == \"Edit\" || tool == \"Write\"",
#       "hooks": [{
#         "type": "command",
#         "command": "${CLAUDE_PLUGIN_ROOT}/skills/strategic-compact/suggest-compact.sh"
#       }]
#     }]
#   }
# }
#
# Criteria for suggesting compact:
# - Session has been running for extended period
# - Large number of tool calls made
# - Transitioning from research/exploration to implementation
# - Plan has been finalized
#
# NOTE: This script is for Unix/Linux/macOS. Windows users need PowerShell version.

# Track tool call count (fixed filename so it persists across hook invocations)
# Uses date-based reset - counter resets each day for fresh sessions
TODAY=$(date +%Y%m%d)
COUNTER_FILE="/tmp/claude-strategic-compact-${TODAY}"
THRESHOLD=${COMPACT_THRESHOLD:-50}
REMINDER_INTERVAL=${COMPACT_REMINDER_INTERVAL:-25}

# Initialize or increment counter
if [ -f "$COUNTER_FILE" ]; then
  count=$(cat "$COUNTER_FILE")
  count=$((count + 1))
else
  count=1
fi
echo "$count" > "$COUNTER_FILE"

# Suggest compact after threshold tool calls
if [ "$count" -eq "$THRESHOLD" ]; then
  echo "[StrategicCompact] $THRESHOLD tool calls reached - consider /compact if transitioning phases" >&2
fi

# Suggest at regular intervals after threshold
if [ "$count" -gt "$THRESHOLD" ] && [ $((count % REMINDER_INTERVAL)) -eq 0 ]; then
  echo "[StrategicCompact] $count tool calls - good checkpoint for /compact if context is stale" >&2
fi
