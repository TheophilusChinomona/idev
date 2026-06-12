#!/bin/bash
# Auto-Learning - Observation Hook (thin wrapper)
#
# Registered by the plugin's hooks/hooks.json on PreToolUse/PostToolUse for
# ALL plugin users, but OFF by default: it exits immediately unless the
# opt-in flag file exists. Enable/disable with /idev:hooks — no settings.json
# editing needed:
#
#   /idev:hooks enable observer    -> touch ~/.claude/homunculus/enabled
#   /idev:hooks disable observer   -> rm    ~/.claude/homunculus/enabled
#
# When enabled, pipes the hook JSON from stdin to observe.py, the single
# canonical implementation (event parsing, truncation, redaction, append,
# rotation).
#
# Usage: observe.sh [pre|post]

[ -f "$HOME/.claude/homunculus/enabled" ] || exit 0

exec python3 "$(dirname "$0")/observe.py" "$@"
