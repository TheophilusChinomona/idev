"""Branch-sync task dataloader."""
from __future__ import annotations

import json
from pathlib import Path

from skillopt.datasets.base import SplitDataLoader


def _load_items(path: str) -> list[dict]:
    """Load items from JSON file."""
    p = Path(path)
    if p.is_dir():
        json_files = sorted(p.glob("*.json"))
        if not json_files:
            raise FileNotFoundError(f"No .json file found in {path}")
        p = json_files[0]
    with p.open(encoding="utf-8") as f:
        data = json.load(f)
    if isinstance(data, list):
        return data
    if isinstance(data, dict):
        return data.get("data") or list(data.values())
    return []


class BranchSyncDataLoader(SplitDataLoader):
    """Branch-sync dataloader.

    Each split directory (train/, val/, test/) contains an items.json
    file — a JSON array of scenario items.
    """

    def load_split_items(self, split_path: str) -> list[dict]:
        items = _load_items(split_path)
        normalized = []
        for item in items:
            normalized.append({
                "id": str(item.get("id", "")),
                "scenario": item.get("scenario", ""),
                "description": item.get("description", ""),
                "git_state": item.get("git_state", {}),
                "expected_commands": item.get("expected_commands", []),
                "expected_behaviors": item.get("expected_behaviors", []),
                "anti_patterns": item.get("anti_patterns", []),
                "task_type": item.get("task_type", "branch_sync"),
            })
        return normalized
