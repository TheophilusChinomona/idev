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


# NotebookLM accepts these as native file uploads; other extensions (.py, .sh,
# .json, ...) 400 on upload, so they are added as pasted text sources instead.
NATIVE_UPLOAD_EXT = {".md", ".markdown", ".txt", ".pdf", ".docx", ".doc", ".epub"}


def _add_source(runner, path):
    """Add one source, routing by extension: native upload for doc types, else text."""
    ext = os.path.splitext(path)[1].lower()
    if ext in NATIVE_UPLOAD_EXT:
        runner.add_source_file(path)
        return
    with open(path, encoding="utf-8") as fh:
        content = fh.read()
    runner.add_source_text(content, os.path.basename(path))


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
                _add_source(runner, src)
            runner.generate_video(video["instructions"], style)
            # Inside the try so any failure here leaves status non-done, enabling retry on resume.
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
