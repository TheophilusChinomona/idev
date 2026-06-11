#!/usr/bin/env python3
"""
Auto-Learning - Observation Hook (Cross-platform)

Captures tool use events for pattern analysis.
Claude Code passes hook data via stdin as JSON.

Hook config (in ~/.claude/settings.json):
{
  "hooks": {
    "PreToolUse": [{
      "matcher": "*",
      "hooks": [{ "type": "command", "command": "python ${CLAUDE_PLUGIN_ROOT}/skills/auto-learning/hooks/observe.py" }]
    }],
    "PostToolUse": [{
      "matcher": "*",
      "hooks": [{ "type": "command", "command": "python ${CLAUDE_PLUGIN_ROOT}/skills/auto-learning/hooks/observe.py" }]
    }]
  }
}
"""

import sys
import json
import os
from datetime import datetime
from pathlib import Path

# Configuration
CONFIG_DIR = Path.home() / ".claude" / "homunculus"
OBSERVATIONS_FILE = CONFIG_DIR / "observations.jsonl"
MAX_FILE_SIZE_MB = 10

def main():
    # Ensure directory exists
    CONFIG_DIR.mkdir(parents=True, exist_ok=True)

    # Skip if disabled
    if (CONFIG_DIR / "disabled").exists():
        return

    # Read JSON from stdin
    try:
        input_json = sys.stdin.read()
        if not input_json.strip():
            return
        data = json.loads(input_json)
    except (json.JSONDecodeError, Exception) as e:
        # Log parse error
        timestamp = datetime.utcnow().isoformat() + "Z"
        error_entry = {
            "timestamp": timestamp,
            "event": "parse_error",
            "error": str(e)
        }
        with open(OBSERVATIONS_FILE, "a", encoding="utf-8") as f:
            f.write(json.dumps(error_entry) + "\n")
        return

    # Extract fields from Claude Code hook format
    hook_type = data.get("hook_type", "unknown")
    tool_name = data.get("tool_name", data.get("tool", "unknown"))
    tool_input = data.get("tool_input", data.get("input", {}))
    tool_output = data.get("tool_output", data.get("output", ""))
    session_id = data.get("session_id", "unknown")

    # Truncate large inputs/outputs
    if isinstance(tool_input, dict):
        tool_input_str = json.dumps(tool_input)[:5000]
    else:
        tool_input_str = str(tool_input)[:5000]

    if isinstance(tool_output, dict):
        tool_output_str = json.dumps(tool_output)[:5000]
    else:
        tool_output_str = str(tool_output)[:5000]

    # Determine event type
    event = "tool_start" if "Pre" in hook_type else "tool_complete"

    # Archive if file too large
    if OBSERVATIONS_FILE.exists():
        file_size_mb = OBSERVATIONS_FILE.stat().st_size / (1024 * 1024)
        if file_size_mb >= MAX_FILE_SIZE_MB:
            archive_dir = CONFIG_DIR / "observations.archive"
            archive_dir.mkdir(exist_ok=True)
            archive_name = f"observations-{datetime.now().strftime('%Y%m%d-%H%M%S')}.jsonl"
            OBSERVATIONS_FILE.rename(archive_dir / archive_name)

    # Build observation
    timestamp = datetime.utcnow().isoformat() + "Z"
    observation = {
        "timestamp": timestamp,
        "event": event,
        "tool": tool_name,
        "session": session_id
    }

    if event == "tool_start" and tool_input_str:
        observation["input"] = tool_input_str
    if event == "tool_complete" and tool_output_str:
        observation["output"] = tool_output_str

    # Write observation
    with open(OBSERVATIONS_FILE, "a", encoding="utf-8") as f:
        f.write(json.dumps(observation) + "\n")

if __name__ == "__main__":
    main()
