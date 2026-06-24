# Codebase Explainer Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add an `idev` skill + command that turns any codebase into an onboarding playlist — Claude-authored analysis docs plus NotebookLM explainer videos (one overview + one per subsystem).

**Architecture:** Claude does the judgement stages (map the codebase via the existing `onboarding-guide` agent + idev caches, then author docs and emit a build `plan.json`). Four focused Python modules in `skills/codebase-explainer/` do the mechanical stages: `preflight.py` (env/auth), `notebooklm_runner.py` (thin CLI wrapper over `notebooklm-py`), `plan_state.py` (state + index bookkeeping), `build_videos.py` (the resumable per-video loop wiring runner + state together). The `SKILL.md` orchestrates; `commands/explain-codebase.md` is the entry point.

**Tech Stack:** Python 3.12 (stdlib only — `subprocess`, `json`, `pathlib`, `argparse`), `notebooklm-py` (installed at runtime in the target environment, never imported by the plugin or its tests), `pytest` for tests. Spec: `docs/superpowers/specs/2026-06-24-codebase-explainer-design.md`.

## Global Constraints

- **No runtime import of `notebooklm-py` in plugin code or tests.** All interaction is via the `notebooklm` CLI through `subprocess`. Tests mock the `run` callable — they must pass with `notebooklm-py` NOT installed and with NO network.
- **Plugin scripts are stdlib-only.** No third-party imports in `preflight.py`, `notebooklm_runner.py`, `plan_state.py`, `build_videos.py`.
- **All paths in code are absolute.** Functions take base directories / file paths as arguments; never hardcode relative paths.
- **Skill dir name must equal its SKILL.md `name:` frontmatter** — both `codebase-explainer` (enforced by `scripts/validate.sh`).
- **`plugin.json` and `marketplace.json` versions must stay equal** (enforced by `scripts/validate.sh`).
- **Every change must keep `bash scripts/validate.sh` green**, including `python3 skills/skill-benchmark/benchmark_skills.py --strict`.
- Tests live in `tests/` and load scripts via `conftest.load_script(name)` using `SCRIPT_PATHS` entries. Test files: `from conftest import load_script` (and `SCRIPT_PATHS` where needed).
- Project-local artifacts at runtime: deliverables in `docs/onboarding/`; skill state in `.claude/idev/codebase-explainer/`. (These are created in the *target* repo at runtime, not in the plugin repo.)
- Branch: `feature/codebase-explainer` in `/home/theo/Desktop/idev`. Commit after every task. Do NOT touch `.github/` CI files.

---

### Task 1: `plan_state.py` — state & index bookkeeping

**Files:**
- Create: `skills/codebase-explainer/plan_state.py`
- Modify: `tests/conftest.py` (add `SCRIPT_PATHS` entries for all four new scripts)
- Test: `tests/test_codebase_explainer_state.py`

**Interfaces:**
- Consumes: nothing (pure stdlib).
- Produces:
  - `load_json(path: str) -> dict`
  - `load_state(state_path: str) -> dict` → `{"videos": {}}` when file missing
  - `save_state(state_path: str, state: dict) -> None`
  - `set_status(state: dict, key: str, status: str, error: str | None = None) -> dict` (mutates and returns `state`)
  - `pending_videos(plan: dict, state: dict) -> list[dict]` → plan videos whose status != `"done"`
  - `render_index(plan: dict, state: dict) -> str` → Markdown playlist
  - `write_index(index_path: str, content: str) -> None`
  - Plan video shape: `{"key","title","notebook_name","sources":[str],"instructions","output","doc"}`
  - State video shape: `{"status": "pending"|"generating"|"done"|"failed", "error": str|None}`

- [ ] **Step 1: Add conftest SCRIPT_PATHS entries**

In `tests/conftest.py`, extend the `SCRIPT_PATHS` dict with all four new scripts (add now so later tasks need no conftest edits):

```python
    "ce_state": PLUGIN_ROOT / "skills" / "codebase-explainer" / "plan_state.py",
    "ce_runner": PLUGIN_ROOT / "skills" / "codebase-explainer" / "notebooklm_runner.py",
    "ce_build": PLUGIN_ROOT / "skills" / "codebase-explainer" / "build_videos.py",
    "ce_preflight": PLUGIN_ROOT / "skills" / "codebase-explainer" / "preflight.py",
```

- [ ] **Step 2: Write the failing tests**

Create `tests/test_codebase_explainer_state.py`:

```python
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
```

- [ ] **Step 3: Run tests to verify they fail**

Run: `cd /home/theo/Desktop/idev && python3 -m pytest tests/test_codebase_explainer_state.py -v`
Expected: FAIL — `KeyError: 'ce_state'` is resolved by Step 1, then `FileNotFoundError`/`spec` error because `plan_state.py` does not exist yet.

- [ ] **Step 4: Write the implementation**

Create `skills/codebase-explainer/plan_state.py`:

```python
"""State and index bookkeeping for the codebase-explainer build loop.

Pure stdlib. No NotebookLM or network interaction lives here.
State file shape:  {"videos": {"<key>": {"status": str, "error": str|None}}}
"""

import json
import os

VALID_STATUS = ("pending", "generating", "done", "failed")


def load_json(path):
    with open(path, "r", encoding="utf-8") as fh:
        return json.load(fh)


def load_state(state_path):
    if not os.path.exists(state_path):
        return {"videos": {}}
    with open(state_path, "r", encoding="utf-8") as fh:
        data = json.load(fh)
    data.setdefault("videos", {})
    return data


def save_state(state_path, state):
    os.makedirs(os.path.dirname(os.path.abspath(state_path)), exist_ok=True)
    with open(state_path, "w", encoding="utf-8") as fh:
        json.dump(state, fh, indent=2, sort_keys=True)
        fh.write("\n")


def set_status(state, key, status, error=None):
    if status not in VALID_STATUS:
        raise ValueError(f"invalid status: {status}")
    state.setdefault("videos", {})[key] = {"status": status, "error": error}
    return state


def pending_videos(plan, state):
    videos = state.get("videos", {})
    return [v for v in plan["videos"] if videos.get(v["key"], {}).get("status") != "done"]


def render_index(plan, state):
    videos = state.get("videos", {})
    lines = ["# Codebase Onboarding Playlist", ""]
    for v in plan["videos"]:
        status = videos.get(v["key"], {}).get("status", "pending")
        doc_link = f"[{v['title']} doc]({v['doc']})"
        if status == "done":
            video_link = f"[▶ video]({v['output']})"
        elif status == "failed":
            err = videos.get(v["key"], {}).get("error") or "unknown error"
            video_link = f"_failed: {err}_"
        else:
            video_link = "_pending_"
        lines.append(f"- {doc_link} — {video_link}")
    lines.append("")
    return "\n".join(lines)


def write_index(index_path, content):
    os.makedirs(os.path.dirname(os.path.abspath(index_path)), exist_ok=True)
    with open(index_path, "w", encoding="utf-8") as fh:
        fh.write(content)
```

- [ ] **Step 5: Run tests to verify they pass**

Run: `cd /home/theo/Desktop/idev && python3 -m pytest tests/test_codebase_explainer_state.py -v`
Expected: PASS (5 passed)

- [ ] **Step 6: Commit**

```bash
cd /home/theo/Desktop/idev
git add skills/codebase-explainer/plan_state.py tests/test_codebase_explainer_state.py tests/conftest.py
git commit -m "feat(codebase-explainer): state & index bookkeeping module"
```

---

### Task 2: `notebooklm_runner.py` — CLI wrapper

**Files:**
- Create: `skills/codebase-explainer/notebooklm_runner.py`
- Test: `tests/test_codebase_explainer_runner.py`

**Interfaces:**
- Consumes: nothing (stdlib only). All functions accept `run=subprocess.run` for injection.
- Produces:
  - `NotebookLMError(RuntimeError)`
  - `create_notebook(title: str, run=subprocess.run) -> None`
  - `add_source_file(path: str, run=subprocess.run) -> None`
  - `generate_video(instructions: str, style: str, run=subprocess.run) -> None`
  - `download_video(out_path: str, run=subprocess.run) -> None`
  - Module constant `NB_BIN = "notebooklm"` and per-command arg builders centralizing CLI flags.

> **API note for the implementer:** the exact CLI flags come from `notebooklm-py`'s README (`notebooklm create`, `source add`, `generate video --style <s> --wait`, `download video <path>`). Before finishing this task, with `notebooklm-py` installed run `notebooklm generate --help` and `notebooklm source --help` and reconcile the `_ARGS` builders below with the real flags. The flags live in ONE place (the builder functions) so this reconciliation is a one-spot edit. Tests assert the runner *calls `run` with whatever the builders produce* and handles exit codes — they do not hardcode service behavior, so they stay valid after reconciliation.

- [ ] **Step 1: Write the failing tests**

Create `tests/test_codebase_explainer_runner.py`:

```python
"""Tests for skills/codebase-explainer/notebooklm_runner.py.

The `run` callable is always injected with a fake — no real `notebooklm`
binary, no network. Verifies command construction and exit-code handling.
"""

import subprocess

import pytest

from conftest import load_script


class FakeRun:
    """Records subprocess.run-style calls; returns a configurable result."""

    def __init__(self, returncode=0, stdout="ok", stderr=""):
        self.calls = []
        self._rc, self._out, self._err = returncode, stdout, stderr

    def __call__(self, args, **kwargs):
        self.calls.append((args, kwargs))
        return subprocess.CompletedProcess(args, self._rc, self._out, self._err)


def test_create_notebook_invokes_cli_with_title():
    mod = load_script("ce_runner")
    fake = FakeRun()
    mod.create_notebook("My Repo — Overview", run=fake)
    args = fake.calls[0][0]
    assert args[0] == mod.NB_BIN
    assert "create" in args
    assert "My Repo — Overview" in args


def test_generate_video_includes_style_and_instructions():
    mod = load_script("ce_runner")
    fake = FakeRun()
    mod.generate_video("Explain the auth subsystem.", "whiteboard", run=fake)
    args = fake.calls[0][0]
    assert "generate" in args and "video" in args
    assert "whiteboard" in args
    assert "Explain the auth subsystem." in args


def test_add_source_file_passes_path():
    mod = load_script("ce_runner")
    fake = FakeRun()
    mod.add_source_file("/abs/docs/onboarding/00-overview.md", run=fake)
    args = fake.calls[0][0]
    assert "source" in args and "add" in args
    assert "/abs/docs/onboarding/00-overview.md" in args


def test_download_video_passes_output_path():
    mod = load_script("ce_runner")
    fake = FakeRun()
    mod.download_video("/abs/docs/onboarding/videos/00-overview.mp4", run=fake)
    args = fake.calls[0][0]
    assert "download" in args and "video" in args
    assert "/abs/docs/onboarding/videos/00-overview.mp4" in args


def test_nonzero_exit_raises_with_stderr():
    mod = load_script("ce_runner")
    fake = FakeRun(returncode=1, stderr="daily limit reached")
    with pytest.raises(mod.NotebookLMError) as exc:
        mod.generate_video("x", "whiteboard", run=fake)
    assert "daily limit reached" in str(exc.value)
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `cd /home/theo/Desktop/idev && python3 -m pytest tests/test_codebase_explainer_runner.py -v`
Expected: FAIL — module `notebooklm_runner.py` does not exist.

- [ ] **Step 3: Write the implementation**

Create `skills/codebase-explainer/notebooklm_runner.py`:

```python
"""Thin wrapper over the `notebooklm` CLI (from the notebooklm-py package).

Plugin code never imports notebooklm-py; it shells out so the dependency is
only needed at runtime in the target environment. All CLI flags live in the
`*_args` builders below — reconcile them with `notebooklm <cmd> --help`.
"""

import subprocess

NB_BIN = "notebooklm"


class NotebookLMError(RuntimeError):
    """Raised when a `notebooklm` CLI invocation exits non-zero."""


def _create_args(title):
    return ["create", title]


def _add_source_args(path):
    return ["source", "add", path, "--wait"]


def _generate_video_args(instructions, style):
    return ["generate", "video", instructions, "--style", style, "--wait"]


def _download_video_args(out_path):
    return ["download", "video", out_path]


def _invoke(args, run):
    result = run([NB_BIN, *args], capture_output=True, text=True)
    if result.returncode != 0:
        detail = (result.stderr or result.stdout or "").strip()
        raise NotebookLMError(f"notebooklm {args[0]} failed: {detail}")
    return result.stdout


def create_notebook(title, run=subprocess.run):
    _invoke(_create_args(title), run)


def add_source_file(path, run=subprocess.run):
    _invoke(_add_source_args(path), run)


def generate_video(instructions, style, run=subprocess.run):
    _invoke(_generate_video_args(instructions, style), run)


def download_video(out_path, run=subprocess.run):
    _invoke(_download_video_args(out_path), run)
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `cd /home/theo/Desktop/idev && python3 -m pytest tests/test_codebase_explainer_runner.py -v`
Expected: PASS (5 passed)

- [ ] **Step 5: Commit**

```bash
cd /home/theo/Desktop/idev
git add skills/codebase-explainer/notebooklm_runner.py tests/test_codebase_explainer_runner.py
git commit -m "feat(codebase-explainer): notebooklm CLI wrapper"
```

---

### Task 3: `build_videos.py` — resumable build loop

**Files:**
- Create: `skills/codebase-explainer/build_videos.py`
- Test: `tests/test_codebase_explainer_build.py`

**Interfaces:**
- Consumes: `plan_state` (Task 1) functions; `notebooklm_runner` (Task 2) functions. Both injected for tests via `runner=` and `state_mod=` params, defaulting to the real modules loaded by path at call time.
- Produces:
  - `build_all(plan_path, state_path, index_path, runner=None, state_mod=None) -> dict`
    returns `{"done": [keys], "failed": [keys], "remaining": [keys]}`
  - Behavior: iterate `pending_videos`; per video set `generating` → save → create notebook → add each source → generate → download → set `done`; on `NotebookLMError` set `failed` (record error) and **stop** (daily-limit semantics); always re-render index after each state change.
  - `main(argv=None) -> int` CLI: `--plan`, `--state`, `--index`; prints summary JSON.

- [ ] **Step 1: Write the failing tests**

Create `tests/test_codebase_explainer_build.py`:

```python
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

    def generate_video(self, instructions, style, run=None):
        self.calls.append(("generate", style))

    def download_video(self, out_path, run=None):
        self.calls.append(("download", out_path))


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
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `cd /home/theo/Desktop/idev && python3 -m pytest tests/test_codebase_explainer_build.py -v`
Expected: FAIL — module `build_videos.py` does not exist.

- [ ] **Step 3: Write the implementation**

Create `skills/codebase-explainer/build_videos.py`:

```python
"""Resumable build loop: turns a plan.json into NotebookLM videos.

Reads plan.json (authored by Claude) + state.json (progress), and for each
not-yet-done video creates a notebook, uploads its sources, generates the
explainer video, and downloads it. Stops on the first failure (daily-limit
friendly); re-running skips videos already marked done.
"""

import argparse
import importlib.util
import json
import os
import sys

_HERE = os.path.dirname(os.path.abspath(__file__))


def _load_sibling(name):
    path = os.path.join(_HERE, f"{name}.py")
    spec = importlib.util.spec_from_file_location(f"ce_{name}", path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def build_all(plan_path, state_path, index_path, runner=None, state_mod=None):
    if runner is None:
        runner = _load_sibling("notebooklm_runner")
    if state_mod is None:
        state_mod = _load_sibling("plan_state")

    plan = state_mod.load_json(plan_path)
    state = state_mod.load_state(state_path)
    style = plan.get("style", "whiteboard")

    done, failed = [], []

    def flush():
        state_mod.save_state(state_path, state)
        state_mod.write_index(index_path, state_mod.render_index(plan, state))

    for video in state_mod.pending_videos(plan, state):
        key = video["key"]
        state_mod.set_status(state, key, "generating")
        flush()
        try:
            runner.create_notebook(video["notebook_name"])
            for src in video["sources"]:
                runner.add_source_file(src)
            runner.generate_video(video["instructions"], style)
            os.makedirs(os.path.dirname(os.path.abspath(video["output"])), exist_ok=True)
            runner.download_video(video["output"])
        except runner.NotebookLMError as exc:
            state_mod.set_status(state, key, "failed", error=str(exc))
            failed.append(key)
            flush()
            break
        state_mod.set_status(state, key, "done")
        done.append(key)
        flush()

    remaining = [v["key"] for v in state_mod.pending_videos(plan, state)
                 if v["key"] not in failed]
    return {"done": done, "failed": failed, "remaining": remaining}


def main(argv=None):
    parser = argparse.ArgumentParser(description="Build NotebookLM videos from a plan.")
    parser.add_argument("--plan", required=True)
    parser.add_argument("--state", required=True)
    parser.add_argument("--index", required=True)
    args = parser.parse_args(argv)
    result = build_all(args.plan, args.state, args.index)
    print(json.dumps(result, indent=2))
    return 1 if result["failed"] else 0


if __name__ == "__main__":
    sys.exit(main())
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `cd /home/theo/Desktop/idev && python3 -m pytest tests/test_codebase_explainer_build.py -v`
Expected: PASS (3 passed)

- [ ] **Step 5: Commit**

```bash
cd /home/theo/Desktop/idev
git add skills/codebase-explainer/build_videos.py tests/test_codebase_explainer_build.py
git commit -m "feat(codebase-explainer): resumable video build loop"
```

---

### Task 4: `preflight.py` — environment & auth check

**Files:**
- Create: `skills/codebase-explainer/preflight.py`
- Test: `tests/test_codebase_explainer_preflight.py`

**Interfaces:**
- Consumes: stdlib only; injectable `which=shutil.which` and `run=subprocess.run`.
- Produces:
  - `cli_available(which=shutil.which) -> bool` — True iff `notebooklm` on PATH
  - `auth_ready(run=subprocess.run) -> bool` — True iff `AUTH_CHECK_ARGS` invocation exits 0
  - `preflight(which=shutil.which, run=subprocess.run) -> dict` → `{"cli": bool, "auth": bool, "ready": bool, "messages": [str]}`
  - `main(argv=None) -> int` — prints JSON; exit 0 iff ready
  - Module constant `AUTH_CHECK_ARGS = ["notebooks", "list"]` (reconcile with `notebooklm --help`)

- [ ] **Step 1: Write the failing tests**

Create `tests/test_codebase_explainer_preflight.py`:

```python
"""Tests for skills/codebase-explainer/preflight.py (no real binary/network)."""

import subprocess

from conftest import load_script


def _ok_run(args, **kwargs):
    return subprocess.CompletedProcess(args, 0, "ok", "")


def _fail_run(args, **kwargs):
    return subprocess.CompletedProcess(args, 1, "", "not logged in")


def test_cli_available_true_when_on_path():
    mod = load_script("ce_preflight")
    assert mod.cli_available(which=lambda name: "/usr/bin/notebooklm") is True


def test_cli_available_false_when_missing():
    mod = load_script("ce_preflight")
    assert mod.cli_available(which=lambda name: None) is False


def test_auth_ready_reflects_exit_code():
    mod = load_script("ce_preflight")
    assert mod.auth_ready(run=_ok_run) is True
    assert mod.auth_ready(run=_fail_run) is False


def test_preflight_ready_when_cli_and_auth():
    mod = load_script("ce_preflight")
    out = mod.preflight(which=lambda name: "/usr/bin/notebooklm", run=_ok_run)
    assert out["ready"] is True


def test_preflight_not_ready_lists_install_hint_when_cli_missing():
    mod = load_script("ce_preflight")
    out = mod.preflight(which=lambda name: None, run=_ok_run)
    assert out["ready"] is False
    assert any("pip install" in m for m in out["messages"])


def test_preflight_not_ready_lists_login_hint_when_unauthed():
    mod = load_script("ce_preflight")
    out = mod.preflight(which=lambda name: "/usr/bin/notebooklm", run=_fail_run)
    assert out["ready"] is False
    assert any("notebooklm login" in m for m in out["messages"])
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `cd /home/theo/Desktop/idev && python3 -m pytest tests/test_codebase_explainer_preflight.py -v`
Expected: FAIL — module `preflight.py` does not exist.

- [ ] **Step 3: Write the implementation**

Create `skills/codebase-explainer/preflight.py`:

```python
"""Preflight checks for the codebase-explainer skill.

Verifies the `notebooklm` CLI is installed and authenticated. Never imports
notebooklm-py; uses PATH lookup + a cheap CLI call. All externals injectable.
"""

import argparse
import json
import shutil
import subprocess
import sys

NB_BIN = "notebooklm"
AUTH_CHECK_ARGS = ["notebooks", "list"]
INSTALL_HINT = 'install it with:  pip install "notebooklm-py[browser]"  (then: notebooklm login)'
LOGIN_HINT = "not authenticated — run:  notebooklm login"


def cli_available(which=shutil.which):
    return which(NB_BIN) is not None


def auth_ready(run=subprocess.run):
    try:
        result = run([NB_BIN, *AUTH_CHECK_ARGS], capture_output=True, text=True)
    except FileNotFoundError:
        return False
    return result.returncode == 0


def preflight(which=shutil.which, run=subprocess.run):
    messages = []
    cli = cli_available(which=which)
    if not cli:
        messages.append(f"notebooklm CLI not found — {INSTALL_HINT}")
        return {"cli": False, "auth": False, "ready": False, "messages": messages}
    auth = auth_ready(run=run)
    if not auth:
        messages.append(LOGIN_HINT)
    return {"cli": True, "auth": auth, "ready": auth, "messages": messages}


def main(argv=None):
    parser = argparse.ArgumentParser(description="Codebase-explainer preflight.")
    parser.parse_args(argv)
    status = preflight()
    print(json.dumps(status, indent=2))
    return 0 if status["ready"] else 1


if __name__ == "__main__":
    sys.exit(main())
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `cd /home/theo/Desktop/idev && python3 -m pytest tests/test_codebase_explainer_preflight.py -v`
Expected: PASS (6 passed)

- [ ] **Step 5: Commit**

```bash
cd /home/theo/Desktop/idev
git add skills/codebase-explainer/preflight.py tests/test_codebase_explainer_preflight.py
git commit -m "feat(codebase-explainer): preflight env & auth check"
```

---

### Task 5: `SKILL.md` orchestrator + `/idev:explain-codebase` command

**Files:**
- Create: `skills/codebase-explainer/SKILL.md`
- Create: `commands/explain-codebase.md`

**Interfaces:**
- Consumes: the four scripts from Tasks 1–4 (referenced via `${CLAUDE_PLUGIN_ROOT}/skills/codebase-explainer/...`), the `onboarding-guide` agent, and idev caches.
- Produces: Claude-facing orchestration; the runtime `plan.json` contract that `build_videos.py` consumes (keys: `style`, `videos[].{key,title,notebook_name,sources,instructions,output,doc}`).

- [ ] **Step 1: Write `SKILL.md`**

Create `skills/codebase-explainer/SKILL.md` (frontmatter `name` MUST be `codebase-explainer`):

````markdown
---
name: codebase-explainer
description: "Turn a codebase into an onboarding playlist — Claude-authored analysis docs plus NotebookLM explainer videos (one overview + one per subsystem). Use when asked to explain a codebase, onboard onto a repo, make explainer/walkthrough videos of the code, or 'help me understand how this whole thing works'."
---

# Codebase Explainer

Produces an onboarding playlist for a repository: narration-friendly Markdown
docs plus NotebookLM **explainer videos** (one overview + one per subsystem).
Claude does the judgement stages (map, author docs); Python scripts do the
mechanical stages (preflight, build). Built on `notebooklm-py` via its CLI.

## Outputs (in the target repo)
- `docs/onboarding/00-overview.md`, `NN-<subsystem>.md` — analysis docs
- `docs/onboarding/videos/*.mp4` — generated videos
- `docs/onboarding/index.md` — playlist linking each doc → its video
- `.claude/idev/codebase-explainer/plan.json` — build plan (you author this)
- `.claude/idev/codebase-explainer/state.json` — resumable progress

## Stage 1 — Preflight
Run and read the JSON:
```bash
python3 "${CLAUDE_PLUGIN_ROOT}/skills/codebase-explainer/preflight.py"
```
If `ready` is false, surface each `messages` line to the user (install /
`notebooklm login`) and STOP until resolved. Auth is an interactive Google
login the user performs once.

## Stage 2 — Map the codebase
Read existing idev caches first when present (they are a head start):
`.claude/idev/smart-context/index.json`, `.claude/idev/project-map/project.map.md`,
`.claude/idev/architecture-scanner/cache.json`. Then dispatch the
`onboarding-guide` agent to identify: tech stack, entry points, and the major
**subsystems** (name, purpose, boundary paths, key files, dependencies, primary
data flow). If few/no subsystems are detected (tiny repo), plan an overview
video only.

## Stage 3 — Author docs + build plan
Write to `docs/onboarding/`:
- `00-overview.md` — architecture, how the pieces fit, main end-to-end flows.
- `NN-<subsystem>.md` — one per subsystem: purpose, how it works, key files,
  dependencies, data flow. Write **prose that explains concepts**, not code dumps.

Then write `.claude/idev/codebase-explainer/plan.json`:
```json
{
  "style": "whiteboard",
  "videos": [
    {"key": "overview", "title": "Overview",
     "notebook_name": "<repo> — Overview",
     "sources": ["docs/onboarding/00-overview.md", "<1-2 key entry files>"],
     "instructions": "Explain how this system works for a new developer: architecture and main flows.",
     "output": "docs/onboarding/videos/00-overview.mp4",
     "doc": "docs/onboarding/00-overview.md"},
    {"key": "<subsystem-key>", "title": "<Subsystem>",
     "notebook_name": "<repo> — <Subsystem>",
     "sources": ["docs/onboarding/01-<subsystem>.md", "docs/onboarding/00-overview.md", "<key raw file>"],
     "instructions": "Explain the <subsystem> for a new developer: responsibilities, key files, main data flow.",
     "output": "docs/onboarding/videos/01-<subsystem>.mp4",
     "doc": "docs/onboarding/01-<subsystem>.md"}
  ]
}
```
- `sources` are file paths (docs + a few key raw files for grounding — hybrid).
- `style` applies to every video for a consistent look; expose the user's choice
  if they named one, else default `whiteboard`.

## Stage 4 — CHECKPOINT (mandatory)
STOP. Tell the user the docs are in `docs/onboarding/` and ask them to review/edit
before any videos are generated. Nothing has been sent to NotebookLM yet. Only
continue on explicit approval.

## Stage 5 — Build & generate
```bash
python3 "${CLAUDE_PLUGIN_ROOT}/skills/codebase-explainer/build_videos.py" \
  --plan .claude/idev/codebase-explainer/plan.json \
  --state .claude/idev/codebase-explainer/state.json \
  --index docs/onboarding/index.md
```
Generates sequentially (overview first), polling and downloading each video.
On a failure (e.g. NotebookLM daily limit) it records progress and stops — tell
the user which videos remain and that **re-running the same command resumes**,
skipping completed videos. Report the final playlist at `docs/onboarding/index.md`.
````

- [ ] **Step 2: Write the command**

Create `commands/explain-codebase.md`:

```markdown
---
description: Turn this codebase into an onboarding playlist — analysis docs plus NotebookLM explainer videos (overview + per-subsystem), with a doc-review checkpoint before any video is generated.
argument-hint: "[subsystem] [--style <visual-style>]"
---

# /idev:explain-codebase

Invoke the **codebase-explainer** skill to build an onboarding playlist for the
current repository.

Arguments: `$ARGUMENTS`
- optional `subsystem` — limit generation to one subsystem video (still writes
  the overview doc for context).
- optional `--style <visual-style>` — NotebookLM visual style for all videos
  (default `whiteboard`).

Follow the skill's five stages in order. The doc-review checkpoint (Stage 4) is
mandatory — never generate videos before the user approves the docs.
```

- [ ] **Step 3: Run validation**

Run: `cd /home/theo/Desktop/idev && bash scripts/validate.sh`
Expected: `All validation checks passed.` (skill dir/name match, JSON valid, skill-benchmark strict passes). If the benchmark scorecard flags the new skill, read its output and fix `SKILL.md` (usually description length/format) until `--strict` passes.

- [ ] **Step 4: Run the full test suite**

Run: `cd /home/theo/Desktop/idev && python3 -m pytest tests/ -q`
Expected: all tests pass (existing + the 4 new test files).

- [ ] **Step 5: Commit**

```bash
cd /home/theo/Desktop/idev
git add skills/codebase-explainer/SKILL.md commands/explain-codebase.md
git commit -m "feat(codebase-explainer): orchestrator skill + /idev:explain-codebase command"
```

---

### Task 6: Version bump, changelog, final validation

**Files:**
- Modify: `.claude-plugin/plugin.json` (version)
- Modify: `.claude-plugin/marketplace.json` (version — must match)
- Modify: `CHANGELOG.md`
- Modify: `README.md` (add the skill/command to the feature list, matching existing style)

- [ ] **Step 1: Bump versions (keep them equal)**

In `.claude-plugin/plugin.json` and `.claude-plugin/marketplace.json` change `"version": "0.10.0"` → `"version": "0.11.0"` (both files).

- [ ] **Step 2: Update CHANGELOG**

Add a top entry to `CHANGELOG.md` following the existing format:

```markdown
## 0.11.0

- Add `codebase-explainer` skill and `/idev:explain-codebase` command: turns a
  repo into an onboarding playlist — analysis docs plus NotebookLM explainer
  videos (overview + per-subsystem), with a doc-review checkpoint and a
  resumable, daily-limit-friendly build loop. Built on `notebooklm-py`.
```

- [ ] **Step 3: Update README**

Add `codebase-explainer` / `/idev:explain-codebase` to the README's skill or command list, matching the surrounding wording and table/list format already used there.

- [ ] **Step 4: Final full validation**

Run: `cd /home/theo/Desktop/idev && bash scripts/validate.sh && python3 -m pytest tests/ -q`
Expected: `All validation checks passed.` and all tests green.

- [ ] **Step 5: Commit**

```bash
cd /home/theo/Desktop/idev
git add .claude-plugin/plugin.json .claude-plugin/marketplace.json CHANGELOG.md README.md
git commit -m "chore(codebase-explainer): bump to 0.11.0, changelog, readme"
```

---

## Self-Review

**Spec coverage:**
- Preflight/install/auth → Task 4 (`preflight.py`) + SKILL Stage 1. ✅
- Map via onboarding-guide + idev caches → SKILL Stage 2 (reuse, no new code). ✅
- Hybrid sources (docs + key raw files) → `plan.json` `sources` arrays, SKILL Stage 3. ✅
- Doc-review checkpoint → SKILL Stage 4 (mandatory stop). ✅
- One notebook per video, explainer format, consistent style → `build_videos.py` + runner + `plan.json` `style`. ✅
- Resumability / daily-limit handling → `build_videos.py` stop-and-resume + `state.json` (Tasks 1, 3). ✅
- Deliverables in `docs/onboarding/`, state in `.claude/idev/codebase-explainer/` → SKILL + script CLI args. ✅
- `index.md` playlist always reflects reality → `plan_state.render_index` (Task 1), re-rendered each step (Task 3). ✅
- Video-only scope (YAGNI) → only video functions in runner; no audio/quiz code. ✅
- idev conventions (skill/command/tests/validate/version) → Tasks 5, 6. ✅
- Two spec open questions (default style, capping subsystem count): default style `whiteboard` is set in `plan.json`/SKILL and reconciled in the Task 2 API note; capping is handled by Claude at Stage 3 (and the optional `subsystem` arg) rather than a hardcoded limit — acceptable for v1.

**Placeholder scan:** No TBD/TODO; every code step shows complete code; the Task 2 API note is a real reconciliation step against `--help`, not a deferred implementation. ✅

**Type consistency:** `plan.json`/`state.json` shapes and function names (`load_state`, `save_state`, `set_status`, `pending_videos`, `render_index`, `write_index`, `create_notebook`, `add_source_file`, `generate_video`, `download_video`, `NotebookLMError`, `build_all`) are used identically across Tasks 1–5 and the tests. ✅
