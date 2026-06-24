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


def test_auth_check_uses_auth_check_command():
    mod = load_script("ce_preflight")
    seen = {}

    def spy_run(args, **kwargs):
        seen["args"] = args
        return subprocess.CompletedProcess(args, 0, "ok", "")

    mod.auth_ready(run=spy_run)
    # Reconciled against notebooklm-py 0.7.2: `notebooklm list` exits non-zero
    # when unauthenticated (auth check exits 0 even on failure, so is unusable).
    assert seen["args"] == [mod.NB_BIN, "list", "--limit", "1"]


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
