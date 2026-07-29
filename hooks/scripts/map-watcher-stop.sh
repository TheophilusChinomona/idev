#!/bin/bash
# map-watcher-stop.sh — Stop the project-map watcher when the session ends.
# Called from the Stop hook.

PROJECT_DIR="${CLAUDE_PROJECT_DIR:-.}"
PROJECT_DIR="${PROJECT_DIR//\\//}"
IDEV_DIR="$PROJECT_DIR/.claude/idev"
PID_FILE="$IDEV_DIR/project-map/watcher.pid"

if [ -f "$PID_FILE" ]; then
  PID=$(cat "$PID_FILE")
  if kill -0 "$PID" 2>/dev/null; then
    kill "$PID" 2>/dev/null
    rm -f "$PID_FILE"
  else
    rm -f "$PID_FILE"
  fi
fi
