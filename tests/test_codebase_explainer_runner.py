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
    # --use makes the new notebook the active context for the calls that follow.
    assert "--use" in args


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
    # `source add` auto-detects type in 0.7.2; --wait doesn't exist and --type file
    # triggers a 400 on upload, so neither flag is passed.
    assert "--wait" not in args
    assert "--type" not in args


def test_add_source_text_passes_text_type_and_title():
    mod = load_script("ce_runner")
    fake = FakeRun()
    mod.add_source_text("print('hi')\n", "scanner.py", run=fake)
    args = fake.calls[0][0]
    assert "source" in args and "add" in args
    assert "print('hi')\n" in args
    assert "--type" in args and "text" in args
    assert "--title" in args and "scanner.py" in args


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
