#!/bin/bash
# pre-compact.sh — Save session state before context compaction.
# Same logic as memory-save.sh but triggered by PreCompact event.

PROJECT_DIR="${CLAUDE_PROJECT_DIR:-.}"
PROJECT_DIR="${PROJECT_DIR//\\//}"
IDEV_DIR="$PROJECT_DIR/.claude/idev"
STATE_FILE="$IDEV_DIR/session-resume/last-session.json"

[ -d "$IDEV_DIR" ] || exit 0
mkdir -p "$(dirname "$STATE_FILE")"

if [ -f "$STATE_FILE" ]; then
  EXISTING=$(cat "$STATE_FILE")
else
  EXISTING='{"lastTask":null,"recentFiles":{"modified":[],"read":[]},"openIssues":[],"savedAt":null}'
fi

TIMESTAMP=$(date '+%Y-%m-%d %H:%M')
echo "$EXISTING" | python3 -c "
import json, sys
data = json.load(sys.stdin)
data['savedAt'] = '$TIMESTAMP'
data['compacted'] = True
json.dump(data, sys.stdout, indent=2)
" > "$STATE_FILE" 2>/dev/null || true
