#!/bin/bash
# idev SessionStart hook — injects the auto-startup context that used to live
# in CLAUDE.md ("Auto-Startup Sequence"). Reads per-project state from
# .claude/idev/ in the current working directory. Cheap and silent when absent.

# Normalize Windows-style backslashes (Git Bash on Windows) to forward slashes.
PROJECT_DIR="${CLAUDE_PROJECT_DIR:-.}"
PROJECT_DIR="${PROJECT_DIR//\\//}"
IDEV_DIR="$PROJECT_DIR/.claude/idev"

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

# ── DB Preflight: surface unapplied DBScripts ─────────────────────────────────
DBSCRIPTS_DIR=""
for CANDIDATE in "$PROJECT_DIR/DBScripts" "$PROJECT_DIR/db-scripts" "$PROJECT_DIR/migrations"; do
  if [ -d "$CANDIDATE" ]; then
    DBSCRIPTS_DIR="$CANDIDATE"
    break
  fi
done
if [ -n "$DBSCRIPTS_DIR" ]; then
  TOTAL=$(find "$DBSCRIPTS_DIR" -name "*.sql" 2>/dev/null | wc -l)
  if [ "$TOTAL" -gt 0 ]; then
    APPLIED_FILE="$IDEV_DIR/db-preflight/applied.json"
    if [ -f "$APPLIED_FILE" ]; then
      UNAPPLIED=$(find "$DBSCRIPTS_DIR" -name "*.sql" -printf "%f\n" 2>/dev/null | while read -r f; do
        grep -q "\"$f\"" "$APPLIED_FILE" 2>/dev/null || echo "$f"
      done | wc -l)
    else
      UNAPPLIED=$TOTAL
    fi
    if [ "$UNAPPLIED" -gt 0 ]; then
      echo "[db-preflight] WARNING: $UNAPPLIED of $TOTAL DBScripts appear unapplied in $DBSCRIPTS_DIR"
      echo "  Run 'idev:db-preflight' or check $IDEV_DIR/db-preflight/applied.json before building."
    fi
  fi
fi

# ── Staleness check: project-map and smart-context ────────────────────────────
MAP_FILE="$IDEV_DIR/project-map/project.map.md"
if [ -f "$MAP_FILE" ]; then
  MAP_AGE=$(( ($(date +%s) - $(stat -c %Y "$MAP_FILE" 2>/dev/null || echo 0)) / 86400 ))
  if [ "$MAP_AGE" -gt 14 ]; then
    echo "[staleness] project-map is ${MAP_AGE} days old — consider running 'idev:project-map' to refresh."
  fi
fi
INDEX_FILE="$IDEV_DIR/smart-context/index.json"
if [ -f "$INDEX_FILE" ]; then
  INDEX_AGE=$(( ($(date +%s) - $(stat -c %Y "$INDEX_FILE" 2>/dev/null || echo 0)) / 86400 ))
  if [ "$INDEX_AGE" -gt 14 ]; then
    echo "[staleness] smart-context index is ${INDEX_AGE} days old — consider running 'idev:smart-context' to refresh."
  fi
fi

echo "[idev] Briefly tell the user what the last task was and any open issues, then ask: continue or start fresh?"
exit 0
