#!/bin/bash
# memory-save.sh — Auto-save session state on Stop hook.
# Reads the current session context and writes to last-session.json.

PROJECT_DIR="${CLAUDE_PROJECT_DIR:-.}"
PROJECT_DIR="${PROJECT_DIR//\\//}"
IDEV_DIR="$PROJECT_DIR/.claude/idev"
STATE_FILE="$IDEV_DIR/session-resume/last-session.json"

# Silent when no idev state
[ -d "$IDEV_DIR" ] || exit 0

# Ensure directory exists
mkdir -p "$(dirname "$STATE_FILE")"

# Read existing state or create empty
if [ -f "$STATE_FILE" ]; then
  EXISTING=$(cat "$STATE_FILE")
else
  EXISTING='{"lastTask":null,"recentFiles":{"modified":[],"read":[]},"openIssues":[],"savedAt":null}'
fi

# Update timestamp
TIMESTAMP=$(date '+%Y-%m-%d %H:%M')
echo "$EXISTING" | python3 -c "
import json, sys
data = json.load(sys.stdin)
data['savedAt'] = '$TIMESTAMP'
json.dump(data, sys.stdout, indent=2)
" > "$STATE_FILE" 2>/dev/null || true
