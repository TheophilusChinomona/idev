"""Tests for skills/auto-learning/hooks/observe.py.

The hook reads a JSON payload from stdin and appends events to
~/.claude/homunculus/observations.jsonl. Tests run main() in-process
with HOME pointed at a tmp dir and a controlled plugin config.
"""

import io
import json
import sys


def run_hook(observe_mod, monkeypatch, tmp_path, payload, argv=(), config=None):
    """Drive observe.main() with a given payload and plugin config."""
    config_file = tmp_path / "plugin-config.json"
    config_file.write_text(json.dumps(config if config is not None else {}))
    monkeypatch.setattr(observe_mod, "PLUGIN_CONFIG_FILE", config_file)
    monkeypatch.setattr(sys, "argv", ["observe.py", *argv])
    monkeypatch.setattr(sys, "stdin", io.StringIO(json.dumps(payload)))
    observe_mod.main()


def read_events(observe_mod):
    if not observe_mod.OBSERVATIONS_FILE.exists():
        return []
    lines = observe_mod.OBSERVATIONS_FILE.read_text().splitlines()
    return [json.loads(line) for line in lines if line.strip()]


def test_post_tool_use_payload_captures_output(observe_mod, monkeypatch, tmp_path):
    # Regression: event/phase must come from `hook_event_name` and the data
    # from `tool_name`/`tool_input`/`tool_response` (the actual Claude Code
    # hook payload field names), not legacy field names.
    payload = {
        "hook_event_name": "PostToolUse",
        "tool_name": "Bash",
        "tool_input": {"command": "ls -la"},
        "tool_response": "file1.txt\nfile2.txt",
        "session_id": "sess-123",
    }
    run_hook(observe_mod, monkeypatch, tmp_path, payload)

    events = read_events(observe_mod)
    assert len(events) == 1
    event = events[0]
    assert event["event"] == "tool_complete"
    assert event["tool"] == "Bash"
    assert event["session"] == "sess-123"
    assert "file1.txt" in event["output"]


def test_pre_tool_use_payload_captures_input(observe_mod, monkeypatch, tmp_path):
    payload = {
        "hook_event_name": "PreToolUse",
        "tool_name": "Write",
        "tool_input": {"file_path": "/tmp/x.txt", "content": "hello"},
        "session_id": "sess-123",
    }
    run_hook(observe_mod, monkeypatch, tmp_path, payload)

    events = read_events(observe_mod)
    assert len(events) == 1
    assert events[0]["event"] == "tool_start"
    assert "/tmp/x.txt" in events[0]["input"]


def test_secret_in_tool_input_is_redacted(observe_mod, monkeypatch, tmp_path):
    payload = {
        "hook_event_name": "PreToolUse",
        "tool_name": "Bash",
        "tool_input": {"command": "mysql -u root password=hunter2"},
        "session_id": "sess-123",
    }
    run_hook(observe_mod, monkeypatch, tmp_path, payload)

    raw = observe_mod.OBSERVATIONS_FILE.read_text()
    assert "hunter2" not in raw
    events = read_events(observe_mod)
    assert "[REDACTED]" in events[0]["input"]


def test_ignore_tools_filtering_produces_no_event(observe_mod, monkeypatch, tmp_path):
    config = {"observation": {"ignore_tools": ["TodoWrite"]}}
    payload = {
        "hook_event_name": "PostToolUse",
        "tool_name": "TodoWrite",
        "tool_input": {"todos": []},
        "tool_response": "ok",
        "session_id": "sess-123",
    }
    run_hook(observe_mod, monkeypatch, tmp_path, payload, config=config)
    assert read_events(observe_mod) == []

    # Sanity: a non-ignored tool with the same config IS captured
    payload["tool_name"] = "Bash"
    run_hook(observe_mod, monkeypatch, tmp_path, payload, config=config)
    events = read_events(observe_mod)
    assert len(events) == 1
    assert events[0]["tool"] == "Bash"
