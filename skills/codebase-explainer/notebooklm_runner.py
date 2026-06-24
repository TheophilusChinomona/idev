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
