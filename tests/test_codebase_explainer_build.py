"""Tests for skills/codebase-explainer/build_videos.py (loop + resume)."""

import json

from conftest import load_script


def _write_plan(tmp_path):
    plan = {
        "style": "whiteboard",
        "videos": [
            {"key": "overview", "title": "Overview", "notebook_name": "R — Overview",
             "sources": [str(tmp_path / "00.md")], "instructions": "Explain system.",
             "output": str(tmp_path / "videos" / "00.mp4"), "doc": str(tmp_path / "00.md")},
            {"key": "auth", "title": "Auth", "notebook_name": "R — Auth",
             "sources": [str(tmp_path / "01.md")], "instructions": "Explain auth.",
             "output": str(tmp_path / "videos" / "01.mp4"), "doc": str(tmp_path / "01.md")},
        ],
    }
    p = tmp_path / "plan.json"
    p.write_text(json.dumps(plan))
    (tmp_path / "00.md").write_text("# overview")
    (tmp_path / "01.md").write_text("# auth")
    return str(p)


class RecordingRunner:
    """Stand-in for notebooklm_runner; records calls, can fail on a given notebook title."""

    def __init__(self, fail_on=None):
        self.calls = []
        self._fail_on = fail_on
        # Surfaced so build code can `except runner.NotebookLMError`
        self.NotebookLMError = type("NotebookLMError", (RuntimeError,), {})

    def create_notebook(self, title, run=None):
        self.calls.append(("create", title))
        if title == self._fail_on:
            raise self.NotebookLMError("daily limit reached")

    def add_source_file(self, path, run=None):
        self.calls.append(("source", path))

    def add_source_text(self, text, title, run=None):
        self.calls.append(("source_text", title))

    def generate_video(self, instructions, style, run=None):
        self.calls.append(("generate", style))

    def download_video(self, out_path, run=None):
        self.calls.append(("download", out_path))


def test_add_source_routes_by_extension(tmp_path):
    mod = load_script("ce_build")
    runner = RecordingRunner()
    md = tmp_path / "doc.md"
    md.write_text("# doc")
    code = tmp_path / "scanner.py"
    code.write_text("print('hi')\n")
    mod._add_source(runner, str(md))
    mod._add_source(runner, str(code))
    # .md uploads natively; .py is added as a text source titled by basename.
    assert ("source", str(md)) in runner.calls
    assert ("source_text", "scanner.py") in runner.calls


def test_build_all_success_marks_all_done(tmp_path):
    mod = load_script("ce_build")
    state_mod = load_script("ce_state")
    plan_path = _write_plan(tmp_path)
    runner = RecordingRunner()
    result = mod.build_all(plan_path, str(tmp_path / "state.json"),
                           str(tmp_path / "index.md"), runner=runner, state_mod=state_mod)
    assert result["done"] == ["overview", "auth"]
    assert result["failed"] == []
    # index written and reflects both done
    idx = (tmp_path / "index.md").read_text()
    assert "00.mp4" in idx and "01.mp4" in idx


def test_build_all_stops_on_failure_and_records(tmp_path):
    mod = load_script("ce_build")
    state_mod = load_script("ce_state")
    plan_path = _write_plan(tmp_path)
    runner = RecordingRunner(fail_on="R — Auth")
    result = mod.build_all(plan_path, str(tmp_path / "state.json"),
                           str(tmp_path / "index.md"), runner=runner, state_mod=state_mod)
    assert result["done"] == ["overview"]
    assert result["failed"] == ["auth"]
    state = json.loads((tmp_path / "state.json").read_text())
    assert state["videos"]["auth"]["status"] == "failed"
    assert "limit" in state["videos"]["auth"]["error"]


def test_build_all_resumes_skipping_done(tmp_path):
    mod = load_script("ce_build")
    state_mod = load_script("ce_state")
    plan_path = _write_plan(tmp_path)
    # Pre-seed overview as done.
    (tmp_path / "state.json").write_text(json.dumps(
        {"videos": {"overview": {"status": "done", "error": None}}}))
    runner = RecordingRunner()
    result = mod.build_all(plan_path, str(tmp_path / "state.json"),
                           str(tmp_path / "index.md"), runner=runner, state_mod=state_mod)
    assert result["done"] == ["auth"]
    # overview was NOT regenerated
    assert ("create", "R — Overview") not in runner.calls
    assert ("create", "R — Auth") in runner.calls
