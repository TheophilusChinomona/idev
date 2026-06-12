"""Tests for skills/auto-learning/scripts/instinct-cli.py."""

import argparse
import io
import sys

INSTINCT_FILE = '''\
---
id: prefer-tests-first
trigger: "when user says \\"deploy\\" to prod"
confidence: 0.8
domain: workflow
---

## Action

Always run the test suite before deploying.
Check CI status as a second line of defense.

## Evidence

Observed 4 times in session logs.
'''


def test_parse_instinct_file_round_trip(instinct_cli, tmp_path):
    path = tmp_path / "instinct.md"
    path.write_text(INSTINCT_FILE)

    instincts = instinct_cli.parse_instinct_file(path.read_text())

    assert len(instincts) == 1
    inst = instincts[0]
    assert inst["id"] == "prefer-tests-first"
    # The double quote inside the trigger must survive parsing
    assert inst["trigger"] == 'when user says "deploy" to prod'
    assert inst["confidence"] == 0.8
    assert inst["domain"] == "workflow"
    # Regression: the markdown body must be attached as `content`
    # (older versions dropped the body entirely)
    assert "## Action" in inst["content"]
    assert "Always run the test suite before deploying." in inst["content"]
    assert "Observed 4 times" in inst["content"]


def test_serialize_parse_round_trip_is_lossless(instinct_cli):
    original = {
        "id": "quote-heavy",
        "trigger": 'when the user types "rm -rf" anywhere',
        "confidence": 0.65,
        "domain": "safety",
        "source": "personal",
        "content": "## Action\n\nWarn loudly.\n\n## Notes\nMulti-line body, kept verbatim.",
    }

    text = instinct_cli.serialize_instinct(original)
    parsed = instinct_cli.parse_instinct_file(text)

    assert len(parsed) == 1
    out = parsed[0]
    for key in ("id", "trigger", "confidence", "domain", "source", "content"):
        assert out[key] == original[key], f"field {key} not preserved"


def test_export_sanitizes_paths_and_secrets(instinct_cli, tmp_path, capsys):
    leaky = {
        "id": "leaky-instinct",
        "trigger": "when configuring deploys",
        "confidence": 0.9,
        "domain": "devops",
        "content": (
            "## Action\n\n"
            "Read /home/someone/secret/path before connecting\n"
            "and set api_key=abc123 in the environment."
        ),
    }
    src = instinct_cli.PERSONAL_DIR / "leaky.md"
    src.write_text(instinct_cli.serialize_instinct(leaky))

    out_file = tmp_path / "export.md"
    args = argparse.Namespace(output=str(out_file), domain=None, min_confidence=None)
    assert instinct_cli.cmd_export(args) == 0

    exported = out_file.read_text()
    assert "abc123" not in exported
    assert "api_key=[REDACTED]" in exported
    assert "/home/someone/secret/path" not in exported
    assert "<path>" in exported


def test_import_non_interactive_updates_in_place(instinct_cli, tmp_path, monkeypatch):
    # Existing personal instinct, lower confidence
    existing = {
        "id": "use-pathlib",
        "trigger": "when manipulating file paths",
        "confidence": 0.5,
        "domain": "python",
        "content": "## Action\n\nOld guidance.",
    }
    personal_file = instinct_cli.PERSONAL_DIR / "use-pathlib.md"
    personal_file.write_text(instinct_cli.serialize_instinct(existing))

    # Incoming import: same id with higher confidence, plus one new instinct
    updated = dict(existing, confidence=0.9, content="## Action\n\nNew guidance.")
    brand_new = {
        "id": "brand-new",
        "trigger": "when writing tests",
        "confidence": 0.7,
        "domain": "testing",
        "content": "## Action\n\nUse pytest fixtures.",
    }
    import_file = tmp_path / "incoming.md"
    import_file.write_text(
        instinct_cli.serialize_instinct(updated)
        + instinct_cli.serialize_instinct(brand_new)
    )

    # stdin is not a TTY: import must proceed without input() (no EOFError)
    monkeypatch.setattr(sys, "stdin", io.StringIO(""))
    args = argparse.Namespace(
        source=str(import_file), dry_run=False, force=False, min_confidence=None
    )
    assert instinct_cli.cmd_import(args) == 0

    all_instincts = instinct_cli.load_all_instincts()
    by_id = {}
    for inst in all_instincts:
        by_id.setdefault(inst["id"], []).append(inst)

    # Updated in place: exactly one copy, new confidence/content, same file
    assert len(by_id["use-pathlib"]) == 1, "import created a duplicate instinct"
    merged = by_id["use-pathlib"][0]
    assert merged["confidence"] == 0.9
    assert "New guidance." in merged["content"]
    assert merged["_source_file"] == str(personal_file)

    # New instinct landed in the inherited directory
    assert len(by_id["brand-new"]) == 1
    assert by_id["brand-new"][0]["_source_type"] == "inherited"
