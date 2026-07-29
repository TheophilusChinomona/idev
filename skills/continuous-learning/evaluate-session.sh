#!/bin/bash
# evaluate-session.sh — Extract patterns from the current session.
# Called by the Stop hook. Reads session transcript, extracts patterns.

LEARNED_DIR="${HOME}/.claude/homunculus/instincts/personal"
CONFIG_FILE="${CLAUDE_PLUGIN_ROOT}/skills/continuous-learning/config.json"

# Ensure directory exists
mkdir -p "$LEARNED_DIR"

# Read config
MIN_LENGTH=$(python3 -c "import json; print(json.load(open('$CONFIG_FILE')).get('min_session_length', 10))" 2>/dev/null || echo 10)

# Check if session has enough activity (via observations)
OBS_FILE="${HOME}/.claude/homunculus/observations.jsonl"
if [ ! -f "$OBS_FILE" ]; then
  exit 0
fi

OBS_COUNT=$(wc -l < "$OBS_FILE" 2>/dev/null || echo 0)
if [ "$OBS_COUNT" -lt "$MIN_LENGTH" ]; then
  exit 0
fi

# Signal to the agent that patterns should be extracted
echo "[continuous-learning] Session has $OBS_COUNT observations (threshold: $MIN_LENGTH). Consider extracting patterns."
