"""Tests for skills/project-map/ai_map_updater.py (non-interactive runs)."""

import io
import subprocess
import sys

from conftest import SCRIPT_PATHS, load_script


def make_project(tmp_path):
    proj = tmp_path / "proj"
    (proj / "src").mkdir(parents=True)
    (proj / "src" / "app.py").write_text("def main():\n    pass\n")
    (proj / "index.ts").write_text("export const x = 1;\n")
    (proj / "util.ts").write_text("export const y = 2;\n")
    return proj


def test_cli_run_with_piped_stdin_writes_map(tmp_path):
    proj = make_project(tmp_path)

    result = subprocess.run(
        [sys.executable, str(SCRIPT_PATHS["ai_map_updater"]), "--root", str(proj)],
        cwd=proj,
        stdin=subprocess.DEVNULL,
        capture_output=True,
        text=True,
        timeout=15,
    )
    assert result.returncode == 0, result.stderr

    map_file = proj / ".claude" / "idev" / "project-map" / "project.map.md"
    assert map_file.exists()
    content = map_file.read_text()
    assert "PROJECT MAP" in content
    assert "src/app.py" in content.replace("\\", "/")
    # index.ts is on the ignore list; util.ts should be present
    assert "util.ts" in content


def test_create_project_map_no_args_non_interactive(tmp_path, monkeypatch):
    # With no paths and stdin not a TTY, create_project_map() must not
    # prompt (no input()/EOFError hang) and falls back to a unified scan.
    proj = make_project(tmp_path)
    monkeypatch.chdir(proj)
    monkeypatch.setattr(sys, "stdin", io.StringIO(""))

    mod = load_script("ai_map_updater")
    mod.create_project_map()

    map_file = proj / ".claude" / "idev" / "project-map" / "project.map.md"
    assert map_file.exists()
    assert "Project Type: unified" in map_file.read_text()
