"""Tests for skills/smart-context/scanner.py, run against tmp project dirs."""

import json

from conftest import load_script


def write_package_json(directory, deps):
    directory.mkdir(parents=True, exist_ok=True)
    (directory / "package.json").write_text(
        json.dumps({"name": "app", "dependencies": deps})
    )


def scan(tmp_path):
    scanner_mod = load_script("scanner")
    scanner = scanner_mod.ProjectScanner(str(tmp_path))
    index = scanner.scan()
    return scanner, index


def test_react_project_detected_and_index_written(tmp_path):
    write_package_json(tmp_path, {"react": "^18.2.0", "react-dom": "^18.2.0"})
    (tmp_path / "src").mkdir()
    (tmp_path / "src" / "App.tsx").write_text("export default function App() {}")

    scanner, index = scan(tmp_path)
    scanner.save()

    index_file = tmp_path / ".claude" / "idev" / "smart-context" / "index.json"
    assert index_file.exists()
    saved = json.loads(index_file.read_text())
    assert saved["stack"]["frontend"] == "react"
    assert index["stack"]["frontend"] == "react"


def test_react_plus_next_detected_as_nextjs(tmp_path):
    # Regression: Next.js apps also depend on react; "next" must win.
    write_package_json(tmp_path, {"next": "^14.0.0", "react": "^18.2.0"})

    _, index = scan(tmp_path)
    assert index["stack"]["frontend"] == "nextjs"


def test_python_backend_in_subdir_detected(tmp_path):
    backend = tmp_path / "backend"
    backend.mkdir()
    (backend / "requirements.txt").write_text("fastapi==0.110.0\n")
    (backend / "main.py").write_text("app = None\n")

    _, index = scan(tmp_path)
    assert index["stack"]["backend"] == "python"
    assert index["structure"]["backend_root"] == "backend"


def test_node_modules_decoy_does_not_pollute_detection(tmp_path):
    # A package.json buried in node_modules must never drive stack detection.
    decoy_dir = tmp_path / "node_modules" / "some-dep"
    write_package_json(decoy_dir, {"vue": "^3.0.0"})
    (tmp_path / "requirements.txt").write_text("flask==3.0.0\n")

    _, index = scan(tmp_path)
    assert "frontend" not in index["stack"]
    assert index["stack"]["backend"] == "python"


def test_decoy_does_not_override_real_root_package(tmp_path):
    write_package_json(tmp_path, {"react": "^18.2.0"})
    decoy_dir = tmp_path / "node_modules" / "nested-next"
    write_package_json(decoy_dir, {"next": "^14.0.0"})

    _, index = scan(tmp_path)
    assert index["stack"]["frontend"] == "react"
