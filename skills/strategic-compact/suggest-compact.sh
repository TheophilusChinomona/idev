#!/bin/bash
# Strategic Compact Suggester (idev plugin)
#
# PostToolUse hook (matcher: "Edit|Write"). Reads the hook JSON from stdin,
# keeps a per-session counter, and every N Edit/Write calls (default 50,
# override with IDEV_COMPACT_THRESHOLD) emits hookSpecificOutput JSON on
# stdout so Claude sees a reminder to suggest /compact at a logical boundary.
#
# Why manual over auto-compact:
# - Auto-compact happens at arbitrary points, often mid-task
# - Strategic compacting preserves context through logical phases
#   (after exploration/planning/debugging, after a milestone)
#
# See SKILL.md in this folder for the settings.json registration snippet.
# Always exits 0; emits nothing below the threshold.

set -u

input=$(cat)

# Extract session_id from the hook JSON, sanitize to a safe filename token
session_id=$(printf '%s' "$input" | sed -n 's/.*"session_id"[[:space:]]*:[[:space:]]*"\([^"]*\)".*/\1/p' | tr -cd 'A-Za-z0-9._-')
[ -n "$session_id" ] || session_id="default"

threshold=${IDEV_COMPACT_THRESHOLD:-50}
case "$threshold" in
  ''|*[!0-9]*) threshold=50 ;;
esac
[ "$threshold" -ge 1 ] || threshold=50

# Per-session counter (not shared across sessions/projects)
counter_file="${TMPDIR:-/tmp}/claude-idev-compact-${session_id}"

count=0
if [ -f "$counter_file" ]; then
  count=$(cat "$counter_file" 2>/dev/null)
  # Reset if contents are not numeric (corrupt/tampered file)
  case "$count" in
    ''|*[!0-9]*) count=0 ;;
  esac
fi
count=$((count + 1))
printf '%s' "$count" > "$counter_file"

if [ $((count % threshold)) -eq 0 ]; then
  printf '{"hookSpecificOutput":{"hookEventName":"PostToolUse","additionalContext":"[strategic-compact] %s Edit/Write calls this session. If you are at a logical boundary (plan finalized, milestone complete, bug fixed), consider suggesting /compact to the user before continuing. Do not interrupt mid-implementation."}}\n' "$count"
fi

exit 0
