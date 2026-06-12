#!/bin/bash
# idev SessionStart hook — injects the auto-startup context that used to live
# in CLAUDE.md ("Auto-Startup Sequence"). Reads per-project state from
# .claude/idev/ in the current working directory. Cheap and silent when absent.

IDEV_DIR="${CLAUDE_PROJECT_DIR:-.}/.claude/idev"

# Truly silent when the project has no idev state (see README for /idev:idev-init).
if [ ! -d "$IDEV_DIR" ]; then
  exit 0
fi

echo "[idev] Session startup context (from $IDEV_DIR):"

if [ -f "$IDEV_DIR/session-resume/last-session.json" ]; then
  echo "--- last-session.json ---"
  head -c 4000 "$IDEV_DIR/session-resume/last-session.json"
  echo ""
fi

if [ -f "$IDEV_DIR/task-journal/journal.md" ]; then
  echo "--- task-journal/journal.md (head) ---"
  head -n 60 "$IDEV_DIR/task-journal/journal.md"
fi

if [ -f "$IDEV_DIR/smart-context/index.json" ]; then
  echo "--- smart-context index available: $IDEV_DIR/smart-context/index.json (load it before task work) ---"
else
  echo "--- no smart-context index yet: the idev:smart-context skill will generate it on first scan ---"
fi

echo "[idev] Briefly tell the user what the last task was and any open issues, then ask: continue or start fresh?"
exit 0
