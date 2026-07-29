"""Branch-sync rollout — supports both chat and exec (Codex) backends."""
from __future__ import annotations

import json
import os
from pathlib import Path

from skillopt.envs.branch_sync.evaluator import evaluate
from skillopt.model import chat_target, is_target_exec_backend
from skillopt.model.codex_harness import prepare_workspace, render_skill_md, run_target_exec


def _build_system(skill_content: str) -> str:
    """Build the system prompt from the skill document."""
    return (
        "You are a git workflow assistant that follows the branch-sync skill "
        "to safely merge the base branch into a feature branch before creating a PR.\n\n"
        "## Skill\n"
        f"{skill_content.strip()}\n\n"
        "## Rules\n"
        "- Always follow the skill's procedure step by step\n"
        "- Never use --ours or --theirs wholesale\n"
        "- Never rebase unless the config explicitly says so\n"
        "- Always verify the merge with a build\n"
        "- If the tree is dirty, surface it to the user — never stash silently\n"
    )


def _build_user(item: dict) -> str:
    """Build the user prompt for a branch-sync scenario."""
    git_state = item.get("git_state", {})
    scenario = item.get("description", "")

    parts = [f"## Scenario\n{scenario}\n"]

    parts.append("## Current Git State")
    parts.append(f"- Current branch: `{git_state.get('current_branch', 'unknown')}`")
    parts.append(f"- Base branch: `{git_state.get('base_branch', 'developer')}`")
    parts.append(
        f"- Remote base ahead by: {git_state.get('remote_base_ahead', 0)} commits"
    )
    parts.append(
        f"- Local feature ahead by: {git_state.get('local_commits_ahead', 0)} commits"
    )
    parts.append(
        f"- Working tree clean: {git_state.get('working_tree_clean', True)}"
    )

    if not git_state.get("working_tree_clean", True):
        dirty = git_state.get("dirty_files", [])
        parts.append(f"- Dirty files: {', '.join(dirty)}")

    if git_state.get("conflicts"):
        parts.append("- Merge conflicts: YES")
        conflicts = git_state.get("conflict_files", [])
        for c in conflicts:
            parts.append(f"  - `{c['file']}`: base did '{c.get('base_change', '')}', feature did '{c.get('feature_change', '')}'")
        if git_state.get("ambiguous"):
            parts.append("  - NOTE: This conflict is AMBIGUOUS — the correct resolution is unclear.")
    else:
        parts.append("- Merge conflicts: NO")

    if git_state.get("sync_strategy"):
        parts.append(f"- Sync strategy (from config): {git_state['sync_strategy']}")

    if git_state.get("push_fails"):
        parts.append(f"- Push failed: {git_state.get('push_error', 'unknown error')}")

    if git_state.get("user_wants_abort"):
        parts.append("- User wants to abort the merge.")

    if git_state.get("platform"):
        parts.append(f"- Git platform: {git_state['platform']}")

    parts.append(
        "\n## Task\n"
        "Produce the exact git commands needed to sync this branch. "
        "Follow the skill's procedure. For each command, explain briefly why."
    )

    return "\n".join(parts)


def _build_codex_skill(skill_content: str) -> str:
    """Render skill as a Codex workspace skill."""
    return render_skill_md(
        skill_content,
        description="Branch-sync skill for safely merging the base branch into a feature branch.",
        preamble=(
            "Use this skill when syncing a feature branch with the base branch.\n"
            "Follow the skill's procedure step by step.\n"
            "Produce the exact git commands needed."
        ),
    )


def _run_codex_once(
    *,
    pred_dir: str,
    skill_content: str,
    item: dict,
    model: str,
    timeout: int,
) -> tuple[str, str, str, str]:
    """Run one scenario via Codex exec backend."""
    user = _build_user(item)
    task_text = user
    skill_md = _build_codex_skill(skill_content)
    work_dir = os.path.join(pred_dir, "codex_exec")
    prepare_workspace(
        work_dir=work_dir,
        skill_md=skill_md,
        task_text=task_text,
    )
    prompt = (
        "Use the `skillopt-target` skill available in this workspace.\n"
        "Read `task.md` and produce the git commands for the branch-sync scenario.\n"
        "For each command, explain briefly why."
    )
    final_message, raw = run_target_exec(
        work_dir=work_dir,
        prompt=prompt,
        model=model,
        timeout=timeout,
    )
    return final_message or raw, raw, skill_md, task_text


def _rollout_one(
    item: dict,
    skill_content: str,
    *,
    prediction_dir: Path,
    max_completion_tokens: int,
    exec_timeout: int = 120,
) -> dict:
    """Run a single branch-sync scenario."""
    item_id = str(item["id"])

    result = {
        "id": item_id,
        "scenario": item.get("scenario", ""),
        "hard": 0,
        "soft": 0.0,
        "command_score": 0.0,
        "anti_pattern_score": 0.0,
        "behavior_score": 0.0,
        "predicted_answer": "",
        "task_description": item.get("description", ""),
        "target_system_prompt": "",
        "target_user_prompt": "",
        "n_turns": 1,
    }

    try:
        task_dir = prediction_dir / item_id
        task_dir.mkdir(parents=True, exist_ok=True)

        if is_target_exec_backend():
            from skillopt.model import azure_openai as _llm

            system = ""
            user = ""
            response, raw, system, user = _run_codex_once(
                pred_dir=str(task_dir),
                skill_content=skill_content,
                item=item,
                model=_llm.TARGET_DEPLOYMENT,
                timeout=exec_timeout,
            )
            prediction = response
            result["target_system_prompt"] = system
            result["target_user_prompt"] = user

            # Save artifacts
            with open(os.path.join(str(task_dir), "target_system_prompt.txt"), "w") as f:
                f.write(system)
            with open(os.path.join(str(task_dir), "target_user_prompt.txt"), "w") as f:
                f.write(user)
            conversation = [
                {"type": "message", "turn": 1, "content": response},
                {"type": "raw", "content": raw},
            ]
            with open(os.path.join(str(task_dir), "conversation.json"), "w") as f:
                json.dump(conversation, f, ensure_ascii=False, indent=2)
        else:
            system = _build_system(skill_content)
            user = _build_user(item)
            result["target_system_prompt"] = system
            result["target_user_prompt"] = user

            prediction, _usage = chat_target(
                system=system,
                user=user,
                max_completion_tokens=max_completion_tokens,
            )

            # Save conversation
            conversation = [
                {"role": "system", "content": system},
                {"role": "user", "content": user},
                {"role": "assistant", "content": prediction},
            ]
            (task_dir / "conversation.json").write_text(
                json.dumps(conversation, ensure_ascii=False, indent=2),
                encoding="utf-8",
            )

        eval_result = evaluate(
            response=prediction,
            expected_commands=item.get("expected_commands", []),
            expected_behaviors=item.get("expected_behaviors", []),
            anti_patterns=item.get("anti_patterns", []),
        )

        result["hard"] = eval_result["hard"]
        result["soft"] = eval_result["soft"]
        result["command_score"] = eval_result["command_score"]
        result["anti_pattern_score"] = eval_result["anti_pattern_score"]
        result["behavior_score"] = eval_result["behavior_score"]
        result["predicted_answer"] = prediction

        # Save eval details
        (task_dir / "eval.json").write_text(
            json.dumps(
                {k: v for k, v in eval_result.items() if k != "details"},
                ensure_ascii=False,
                indent=2,
            ),
            encoding="utf-8",
        )

    except Exception as e:
        result["predicted_answer"] = f"ERROR: {e}"

    return result


def run_batch(
    *,
    items: list[dict],
    skill_content: str,
    out_root: str,
    workers: int = 4,
    max_completion_tokens: int = 4096,
    exec_timeout: int = 120,
) -> list[dict]:
    """Run a batch of branch-sync scenarios."""
    os.makedirs(out_root, exist_ok=True)
    prediction_dir = Path(out_root, "predictions")
    results = [
        _rollout_one(
            item,
            skill_content,
            prediction_dir=prediction_dir,
            max_completion_tokens=max_completion_tokens,
            exec_timeout=exec_timeout,
        )
        for item in items
    ]
    Path(out_root, "rollouts.json").write_text(
        json.dumps(results, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    return results
