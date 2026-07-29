#!/bin/bash
# map-watcher-daemon.sh — Start/stop the project-map watcher as a background daemon.
# Called from the session-start hook. Silent when project has no idev state
# or config is missing.
#
# Usage:
#   map-watcher-daemon.sh start   # start if not running
#   map-watcher-daemon.sh stop    # stop if running
#   map-watcher-daemon.sh status  # check if running

PROJECT_DIR="${CLAUDE_PROJECT_DIR:-.}"
PROJECT_DIR="${PROJECT_DIR//\\//}"
IDEV_DIR="$PROJECT_DIR/.claude/idev"
WATCHER_CONFIG="$IDEV_DIR/project-map/watcher_config.json"
PID_FILE="$IDEV_DIR/project-map/watcher.pid"
LOG_FILE="$IDEV_DIR/project-map/watcher.log"
WATCHER_SCRIPT="${CLAUDE_PLUGIN_ROOT}/skills/project-map/map_watcher.py"

# Silent exit if no idev state or no watcher config
if [ ! -d "$IDEV_DIR" ] || [ ! -f "$WATCHER_CONFIG" ]; then
  exit 0
fi

# Check if config has actual values (not blank)
PROJECT_TYPE=$(python3 -c "import json; c=json.load(open('$WATCHER_CONFIG')); print(c.get('project_type',''))" 2>/dev/null)
if [ -z "$PROJECT_TYPE" ]; then
  exit 0
fi

is_running() {
  if [ -f "$PID_FILE" ]; then
    PID=$(cat "$PID_FILE")
    if kill -0 "$PID" 2>/dev/null; then
      return 0
    fi
    # Stale PID file
    rm -f "$PID_FILE"
  fi
  return 1
}

start_watcher() {
  if is_running; then
    return 0
  fi

  # Ensure log directory exists
  mkdir -p "$(dirname "$PID_FILE")"

  # Start the watcher in background, detached from terminal
  cd "$PROJECT_DIR"
  nohup python3 "$WATCHER_SCRIPT" > "$LOG_FILE" 2>&1 &
  WATCHER_PID=$!

  # Verify it started
  sleep 1
  if kill -0 "$WATCHER_PID" 2>/dev/null; then
    echo "$WATCHER_PID" > "$PID_FILE"
    echo "[map-watcher] Started (PID $WATCHER_PID) — regenerates project.map.md on file changes"
  else
    # Watcher failed to start (e.g. no config, error in script)
    rm -f "$PID_FILE"
  fi
}

stop_watcher() {
  if ! is_running; then
    return 0
  fi

  PID=$(cat "$PID_FILE")
  echo "[map-watcher] Stopping watcher (PID $PID)..."
  kill "$PID" 2>/dev/null
  # Wait briefly for graceful shutdown
  for i in 1 2 3; do
    if ! kill -0 "$PID" 2>/dev/null; then
      break
    fi
    sleep 1
  done
  # Force kill if still running
  kill -9 "$PID" 2>/dev/null
  rm -f "$PID_FILE"
}

status_watcher() {
  if is_running; then
    PID=$(cat "$PID_FILE")
    echo "[map-watcher] Running (PID $PID)"
  else
    echo "[map-watcher] Not running"
  fi
}

case "${1:-start}" in
  start)  start_watcher ;;
  stop)   stop_watcher ;;
  status) status_watcher ;;
  *)      echo "Usage: $0 {start|stop|status}" >&2; exit 1 ;;
esac
