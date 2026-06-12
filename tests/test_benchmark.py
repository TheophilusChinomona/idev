"""Tests for the skill-benchmark static checker."""
import subprocess
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
SCRIPT = REPO / "skills" / "skill-benchmark" / "benchmark_skills.py"


def run(*args, cwd=None):
    return subprocess.run(
        [sys.executable, str(SCRIPT), *args],
        capture_output=True, text=True, timeout=30, cwd=cwd or REPO,
    )


def test_own_plugin_all_pass():
    res = run("--strict")
    assert res.returncode == 0, res.stdout + res.stderr
    assert "pass all 10 checks" in res.stdout


def test_detects_bad_skill(tmp_path):
    bad = tmp_path / "skills" / "Bad_Skill"
    bad.mkdir(parents=True)
    (bad / "SKILL.md").write_text(
        "---\n"
        "name: Bad_Skill\n"
        "description: I can do things.\n"
        "---\n"
        "No examples here. See ${CLAUDE_PLUGIN_ROOT}/does/not/exist.py\n"
    )
    res = run("--plugin-dir", str(tmp_path))
    assert res.returncode == 0  # not strict: reports, doesn't fail
    for failure in ("desc-triggers", "desc-3rd-person", "name-kebab",
                    "has-examples", "refs-resolve"):
        assert failure in res.stdout, f"{failure} not flagged:\n{res.stdout}"

    strict = run("--plugin-dir", str(tmp_path), "--strict")
    assert strict.returncode == 1


def test_footprint_mode():
    res = run("--footprint")
    assert res.returncode == 0, res.stdout + res.stderr
    assert "always-loaded metadata" in res.stdout
    assert "estimate" in res.stdout


def test_good_skill_passes(tmp_path):
    good = tmp_path / "skills" / "tidy-skill"
    good.mkdir(parents=True)
    (good / "SKILL.md").write_text(
        "---\n"
        "name: tidy-skill\n"
        'description: "Does a thing. Use when the user asks for the thing."\n'
        "---\n"
        "# Tidy\n\n```bash\necho example\n```\n"
    )
    res = run("--plugin-dir", str(tmp_path), "--strict")
    assert res.returncode == 0, res.stdout
    assert "1 pass all 10 checks" in res.stdout
