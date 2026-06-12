#!/bin/bash
# Auto-Learning - Observation Hook (thin wrapper)
#
# Pipes the hook JSON from stdin to observe.py, the single canonical
# implementation (event parsing, truncation, redaction, append, rotation).
#
# Usage: observe.sh [pre|post]
#
# Hook config (in ~/.claude/settings.json). NOTE: ${CLAUDE_PLUGIN_ROOT} is
# NOT expanded in user settings.json — use the absolute path of the
# installed plugin instead:
# {
#   "hooks": {
#     "PreToolUse": [{
#       "matcher": "*",
#       "hooks": [{ "type": "command", "command": "<idev-plugin-root>/skills/auto-learning/hooks/observe.sh pre" }]
#     }],
#     "PostToolUse": [{
#       "matcher": "*",
#       "hooks": [{ "type": "command", "command": "<idev-plugin-root>/skills/auto-learning/hooks/observe.sh post" }]
#     }]
#   }
# }

exec python3 "$(dirname "$0")/observe.py" "$@"
