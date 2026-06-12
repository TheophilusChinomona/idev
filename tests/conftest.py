"""Shared fixtures and script loaders for the idev plugin test suite.

The plugin's Python scripts live in non-package directories (and
instinct-cli.py has a hyphen in its name), so they are loaded by file
path with importlib. Scripts that resolve ~/.claude/homunculus at import
time must be loaded *after* HOME has been pointed at a tmp dir, which is
what the fake_home-dependent fixtures below guarantee.
"""

import importlib.util
import itertools
from pathlib import Path

import pytest

PLUGIN_ROOT = Path(__file__).parent.parent

SCRIPT_PATHS = {
    "instinct_cli": PLUGIN_ROOT / "skills" / "auto-learning" / "scripts" / "instinct-cli.py",
    "observe": PLUGIN_ROOT / "skills" / "auto-learning" / "hooks" / "observe.py",
    "scanner": PLUGIN_ROOT / "skills" / "smart-context" / "scanner.py",
    "ai_map_updater": PLUGIN_ROOT / "skills" / "project-map" / "ai_map_updater.py",
}

_counter = itertools.count()


def load_script(name):
    """Import one of the plugin scripts by file path, as a fresh module.

    A fresh module each call means import-time constants (e.g. paths
    derived from Path.home()) pick up the current HOME.
    """
    path = SCRIPT_PATHS[name]
    module_name = f"idev_{name}_{next(_counter)}"
    spec = importlib.util.spec_from_file_location(module_name, path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


@pytest.fixture
def fake_home(tmp_path, monkeypatch):
    """Point HOME at a tmp dir so ~/.claude/homunculus never touches the real home."""
    home = tmp_path / "home"
    home.mkdir()
    monkeypatch.setenv("HOME", str(home))
    monkeypatch.setenv("USERPROFILE", str(home))  # harmless on POSIX
    return home


@pytest.fixture
def instinct_cli(fake_home):
    """instinct-cli.py loaded with HOMUNCULUS_DIR under the fake HOME."""
    mod = load_script("instinct_cli")
    assert str(mod.HOMUNCULUS_DIR).startswith(str(fake_home))
    mod.ensure_dirs()
    return mod


@pytest.fixture
def observe_mod(fake_home):
    """observe.py loaded with CONFIG_DIR under the fake HOME."""
    mod = load_script("observe")
    assert str(mod.CONFIG_DIR).startswith(str(fake_home))
    return mod
