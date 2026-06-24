"""Thin wrapper over the `notebooklm` CLI (from the notebooklm-py package).

Plugin code never imports notebooklm-py; it shells out so the dependency is
only needed at runtime in the target environment. All CLI flags live in the
`*_args` builders below — reconciled against notebooklm-py 0.7.2.

Notebook-context model: `create --use` makes the new notebook the active
context, so the subsequent `source add` / `generate video` / `download video`
calls operate on it without threading an id. This run is sequential
(one notebook fully built before the next), so the shared active context is safe.
"""

import subprocess

NB_BIN = "notebooklm"


class NotebookLMError(RuntimeError):
    """Raised when a `notebooklm` CLI invocation exits non-zero."""


def _create_args(title):
    # --use sets the new notebook as the active context for the calls that follow.
    return ["create", title, "--use"]


def _add_source_args(path):
    # `source add` has no --wait flag in 0.7.2; --type file pins local-file handling.
    return ["source", "add", path, "--type", "file"]


def _generate_video_args(instructions, style):
    # --format defaults to "explainer"; --style is one of the 9 visual styles.
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
