#!/usr/bin/env python3
"""
Auto-Learning - Observation Hook (single canonical implementation)

Captures tool use events for pattern analysis. Claude Code passes hook data
via stdin as JSON. observe.sh is a thin wrapper that execs this script.

Usage: observe.py [pre|post]
  The optional positional argument indicates the hook phase. When omitted,
  the `hook_event_name` field from the payload is used ("PreToolUse" or
  "PostToolUse").

Hook config (in ~/.claude/settings.json). NOTE: ${CLAUDE_PLUGIN_ROOT} is NOT
expanded in user settings.json — use the absolute path of the installed
plugin instead:
{
  "hooks": {
    "PreToolUse": [{
      "matcher": "*",
      "hooks": [{ "type": "command", "command": "<idev-plugin-root>/skills/auto-learning/hooks/observe.sh pre" }]
    }],
    "PostToolUse": [{
      "matcher": "*",
      "hooks": [{ "type": "command", "command": "<idev-plugin-root>/skills/auto-learning/hooks/observe.sh post" }]
    }]
  }
}
"""

import json
import os
import re
import signal
import sys
from datetime import datetime, timezone
from pathlib import Path

# Configuration
CONFIG_DIR = Path.home() / ".claude" / "homunculus"
OBSERVATIONS_FILE = CONFIG_DIR / "observations.jsonl"
PLUGIN_CONFIG_FILE = Path(__file__).resolve().parent.parent / "config.json"
DEFAULT_MAX_FILE_SIZE_MB = 10
TRUNCATE_AT = 5000

# Cheap redaction of common secret patterns (e.g. secrets typed into Bash
# commands) before anything is written to disk.
SECRET_RE = re.compile(
    r"(api[_-]?key|token|secret|password|authorization)(\s*[=:]\s*)\S+",
    re.IGNORECASE,
)


def utc_timestamp() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def redact(text: str) -> str:
    return SECRET_RE.sub(r"\1\2[REDACTED]", text)


def load_plugin_config() -> dict:
    """Load the plugin's config.json. Fail open (capture) if missing/corrupt."""
    try:
        with open(PLUGIN_CONFIG_FILE, encoding="utf-8") as f:
            config = json.load(f)
        return config if isinstance(config, dict) else {}
    except Exception:
        return {}


def should_capture(tool_name: str, observation_cfg: dict) -> bool:
    """Apply capture_tools / ignore_tools filtering. Fail open on bad config."""
    try:
        ignore_tools = observation_cfg.get("ignore_tools") or []
        if tool_name in ignore_tools:
            return False
        capture_tools = observation_cfg.get("capture_tools") or []
        if capture_tools and tool_name not in capture_tools:
            return False
    except Exception:
        return True
    return True


def archive_if_too_large(max_file_size_mb: float) -> None:
    if not OBSERVATIONS_FILE.exists():
        return
    file_size_mb = OBSERVATIONS_FILE.stat().st_size / (1024 * 1024)
    if file_size_mb >= max_file_size_mb:
        archive_dir = CONFIG_DIR / "observations.archive"
        archive_dir.mkdir(exist_ok=True)
        archive_name = f"observations-{datetime.now().strftime('%Y%m%d-%H%M%S')}.jsonl"
        OBSERVATIONS_FILE.rename(archive_dir / archive_name)


def signal_observer() -> None:
    """Nudge the background observer (if running) for on-demand analysis."""
    if not hasattr(signal, "SIGUSR1"):
        return
    pid_file = CONFIG_DIR / ".observer.pid"
    try:
        pid = int(pid_file.read_text().strip())
        os.kill(pid, signal.SIGUSR1)
    except Exception:
        pass


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
    except Exception as e:
        error_entry = {
            "timestamp": utc_timestamp(),
            "event": "parse_error",
            "error": str(e),
        }
        with open(OBSERVATIONS_FILE, "a", encoding="utf-8") as f:
            f.write(json.dumps(error_entry) + "\n")
        return

    config = load_plugin_config()
    observation_cfg = config.get("observation") or {}
    if isinstance(observation_cfg, dict) and observation_cfg.get("enabled") is False:
        return

    # Extract fields from the Claude Code hook payload
    tool_name = data.get("tool_name", "unknown")
    tool_input = data.get("tool_input", {})
    tool_response = data.get("tool_response", "")
    session_id = data.get("session_id", "unknown")

    # capture_tools / ignore_tools filtering
    if not should_capture(tool_name, observation_cfg if isinstance(observation_cfg, dict) else {}):
        return

    # Phase: prefer the explicit pre/post argument (passed by the hook
    # config), fall back to hook_event_name from the payload.
    phase_arg = sys.argv[1].lower() if len(sys.argv) > 1 else ""
    if phase_arg in ("pre", "post"):
        event = "tool_start" if phase_arg == "pre" else "tool_complete"
    else:
        hook_event = data.get("hook_event_name", "")
        event = "tool_start" if "Pre" in hook_event else "tool_complete"

    # Truncate and redact large inputs/outputs
    if isinstance(tool_input, (dict, list)):
        tool_input_str = json.dumps(tool_input)[:TRUNCATE_AT]
    else:
        tool_input_str = str(tool_input)[:TRUNCATE_AT]
    tool_input_str = redact(tool_input_str)

    if isinstance(tool_response, (dict, list)):
        tool_response_str = json.dumps(tool_response)[:TRUNCATE_AT]
    else:
        tool_response_str = str(tool_response)[:TRUNCATE_AT]
    tool_response_str = redact(tool_response_str)

    # Size-based archive rotation
    try:
        max_mb = float(observation_cfg.get("max_file_size_mb", DEFAULT_MAX_FILE_SIZE_MB))
    except Exception:
        max_mb = DEFAULT_MAX_FILE_SIZE_MB
    archive_if_too_large(max_mb)

    # Build observation
    observation = {
        "timestamp": utc_timestamp(),
        "event": event,
        "tool": tool_name,
        "session": session_id,
    }
    if event == "tool_start" and tool_input_str:
        observation["input"] = tool_input_str
    if event == "tool_complete" and tool_response_str:
        observation["output"] = tool_response_str

    # Write observation
    with open(OBSERVATIONS_FILE, "a", encoding="utf-8") as f:
        f.write(json.dumps(observation) + "\n")

    # Signal observer if running
    signal_observer()


if __name__ == "__main__":
    main()
