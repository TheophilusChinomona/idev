"""Tests for skills/codebase-explainer/plan_state.py (pure file/state logic)."""

import json

from conftest import load_script


def _plan():
    return {
        "style": "whiteboard",
        "videos": [
            {"key": "overview", "title": "Overview", "notebook_name": "Repo — Overview",
             "sources": ["docs/onboarding/00-overview.md"], "instructions": "Explain the system.",
             "output": "docs/onboarding/videos/00-overview.mp4", "doc": "docs/onboarding/00-overview.md"},
            {"key": "auth", "title": "Auth", "notebook_name": "Repo — Auth",
             "sources": ["docs/onboarding/01-auth.md"], "instructions": "Explain auth.",
             "output": "docs/onboarding/videos/01-auth.mp4", "doc": "docs/onboarding/01-auth.md"},
        ],
    }


def test_load_state_missing_returns_empty(tmp_path):
    mod = load_script("ce_state")
    state = mod.load_state(str(tmp_path / "nope.json"))
    assert state == {"videos": {}}


def test_save_then_load_roundtrip(tmp_path):
    mod = load_script("ce_state")
    p = str(tmp_path / "state.json")
    state = {"videos": {"overview": {"status": "done", "error": None}}}
    mod.save_state(p, state)
    assert mod.load_state(p) == state
    # valid JSON on disk
    assert json.loads((tmp_path / "state.json").read_text())["videos"]["overview"]["status"] == "done"


def test_set_status_mutates_and_returns(tmp_path):
    mod = load_script("ce_state")
    state = {"videos": {}}
    out = mod.set_status(state, "auth", "failed", error="limit reached")
    assert out is state
    assert state["videos"]["auth"] == {"status": "failed", "error": "limit reached"}


def test_pending_videos_excludes_done(tmp_path):
    mod = load_script("ce_state")
    state = {"videos": {"overview": {"status": "done", "error": None}}}
    pending = mod.pending_videos(_plan(), state)
    assert [v["key"] for v in pending] == ["auth"]


def test_render_index_marks_done_and_pending():
    mod = load_script("ce_state")
    state = {"videos": {"overview": {"status": "done", "error": None}}}
    md = mod.render_index(_plan(), state)
    assert "videos/00-overview.mp4" in md          # done → links the video
    assert "_pending_" in md                         # auth not generated yet
    assert "00-overview.md" in md and "01-auth.md" in md  # docs always linked
