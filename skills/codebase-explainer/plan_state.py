"""State and index bookkeeping for the codebase-explainer build loop.

Pure stdlib. No NotebookLM or network interaction lives here.
State file shape:  {"videos": {"<key>": {"status": str, "error": str|None}}}
"""

import json
import os

VALID_STATUS = ("pending", "generating", "done", "failed")


def load_json(path):
    with open(path, "r", encoding="utf-8") as fh:
        return json.load(fh)


def load_state(state_path):
    if not os.path.exists(state_path):
        return {"videos": {}}
    with open(state_path, "r", encoding="utf-8") as fh:
        data = json.load(fh)
    data.setdefault("videos", {})
    return data


def save_state(state_path, state):
    os.makedirs(os.path.dirname(os.path.abspath(state_path)), exist_ok=True)
    with open(state_path, "w", encoding="utf-8") as fh:
        json.dump(state, fh, indent=2, sort_keys=True)
        fh.write("\n")


def set_status(state, key, status, error=None):
    if status not in VALID_STATUS:
        raise ValueError(f"invalid status: {status}")
    state.setdefault("videos", {})[key] = {"status": status, "error": error}
    return state


def pending_videos(plan, state):
    videos = state.get("videos", {})
    return [v for v in plan["videos"] if videos.get(v["key"], {}).get("status") != "done"]


def render_index(plan, state):
    videos = state.get("videos", {})
    lines = ["# Codebase Onboarding Playlist", ""]
    for v in plan["videos"]:
        status = videos.get(v["key"], {}).get("status", "pending")
        doc_link = f"[{v['title']} doc]({v['doc']})"
        if status == "done":
            video_link = f"[▶ video]({v['output']})"
        elif status == "failed":
            err = videos.get(v["key"], {}).get("error") or "unknown error"
            video_link = f"_failed: {err}_"
        else:
            video_link = "_pending_"
        lines.append(f"- {doc_link} — {video_link}")
    lines.append("")
    return "\n".join(lines)


def write_index(index_path, content):
    os.makedirs(os.path.dirname(os.path.abspath(index_path)), exist_ok=True)
    with open(index_path, "w", encoding="utf-8") as fh:
        fh.write(content)
