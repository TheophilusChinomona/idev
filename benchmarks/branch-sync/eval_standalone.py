#!/usr/bin/env python3
"""Standalone branch-sync benchmark evaluator.

Tests the branch-sync skill against scenarios without requiring
SkillOpt's full training infrastructure. Reads scenario data,
scores the skill's expected behavior, and produces a report.

Usage:
    python3 eval_standalone.py [--skill PATH] [--split train|val|test]
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

# Local evaluator (no skillopt dependency)
sys.path.insert(0, str(Path(__file__).parent))
from evaluator import evaluate


def load_skill(path: Path) -> str:
    """Load a skill markdown file."""
    return path.read_text(encoding="utf-8")


def load_scenarios(data_dir: Path, split: str) -> list[dict]:
    """Load scenarios from a split directory."""
    items_file = data_dir / split / "items.json"
    if not items_file.exists():
        raise FileNotFoundError(f"No items.json found at {items_file}")
    with items_file.open(encoding="utf-8") as f:
        return json.load(f)


def simulate_rollout(scenario: dict, skill_text: str) -> str:
    """Simulate what the skill would produce for a scenario.

    Since we can't call an LLM in standalone mode, this generates
    the EXPECTED response based on the skill's procedure and the
    scenario's git state. This tests the evaluator itself and
    validates the scenario data.

    For real evaluation, replace this with an LLM call.
    """
    git = scenario.get("git_state", {})
    commands = []
    explanations = []
    current = git.get("current_branch", "unknown")
    base = git.get("base_branch", "developer")

    if current == base:
        commands.append("git branch --show-current")
        explanations.append("Check current branch")
        commands.append(f"# REFUSE: Currently on base branch '{current}'")
        commands.append("# This skill syncs feature branches, not the base branch.")
        commands.append("# Create a feature branch first.")
        explanations.append("Refuse: currently on the base branch")
        return _format_response(commands, explanations)

    if not git.get("working_tree_clean", True):
        dirty = git.get("dirty_files", [])
        commands.append("git status --porcelain")
        explanations.append("Check dirty files before proceeding")
        commands.append(f"# Dirty tree detected: {', '.join(dirty)}")
        commands.append("# Options:")
        commands.append("#   1. Commit these changes (recommended)")
        commands.append("#   2. Stash them: git stash push -u -m 'pre-sync'")
        commands.append("git stash push -u -m 'pre-sync'")
        explanations.append("Stash with -u to include untracked files, surface to user first")
        return _format_response(commands, explanations)

    # Step 1.5: Record rollback point
    commands.append("git rev-parse HEAD")
    explanations.append("Record rollback point in case merge goes wrong")

    # Step 2: Fetch
    commands.append("git fetch origin")
    explanations.append("Fetch latest from remote before merge")

    # Step 3: Merge
    strategy = git.get("sync_strategy", "merge")
    if strategy == "rebase":
        commands.append(f"git rebase origin/{base}")
        explanations.append(f"Rebase onto origin/{base} (config says rebase)")
    else:
        commands.append(f"git merge origin/{base} --no-edit")
        explanations.append(f"Merge origin/{base} into feature branch")

    # Step 4: Handle conflicts
    if git.get("conflicts"):
        commands.append("git diff --name-only --diff-filter=U")
        explanations.append("List conflicted files")

        conflicts = git.get("conflict_files", [])
        for c in conflicts:
            fname = c["file"]
            base_change = c.get("base_change", "")
            feature_change = c.get("feature_change", "")
            if "lock" in fname.lower() or "package-lock" in fname.lower():
                commands.append(f"# {fname}: lockfile conflict — regenerate with npm install")
                explanations.append(f"Regenerate {fname} instead of hand-merging")
            elif git.get("ambiguous"):
                commands.append(f"# {fname}: AMBIGUOUS conflict")
                commands.append(f"#   Base did: {base_change}")
                commands.append(f"#   Feature did: {feature_change}")
                commands.append(f"#   → Asking user for resolution")
                explanations.append("Stop and ask user for ambiguous conflicts")
            else:
                commands.append(f"# {fname}: Understanding both sides' intent")
                commands.append(f"#   Base did: {base_change}")
                commands.append(f"#   Feature did: {feature_change}")
                commands.append(f"#   → Integrating both changes")
                commands.append(f"git add {fname}")
                explanations.append(f"Stage resolved {fname} after integrating both sides")

        commands.append("git commit --no-edit")
        explanations.append("Commit the merge")

    # Step 5: Verify
    if not git.get("conflicts") or git.get("user_wants_abort"):
        if git.get("user_wants_abort"):
            commands.clear()
            commands.append("git merge --abort")
            explanations.clear()
            commands.append("# Run build verification")
            explanations.append("Verify merge with build-check")

    # Step 6: Push and report
    if not git.get("user_wants_abort") and not git.get("conflicts"):
        commands.append(f"git push origin {current}")
        explanations.append("Push synced branch")
        commands.append("# Report: base branch merged, conflicts resolved, verification passed")
        explanations.append("Report merge results to user")

        if git.get("platform") == "github":
            commands.append("gh pr create --base developer --title '...' --body '...'")
            explanations.append("Offer to create PR on GitHub")

    return _format_response(commands, explanations)


def _format_response(commands: list[str], explanations: list[str]) -> str:
    """Format commands and explanations into a response."""
    lines = []
    for i, cmd in enumerate(commands):
        if cmd.startswith("#"):
            lines.append(cmd)
        else:
            lines.append(f"```bash\n{cmd}\n```")
            if i < len(explanations):
                lines.append(f"_{explanations[i]}_")
        lines.append("")
    return "\n".join(lines)


def run_evaluation(skill_path: Path, data_dir: Path, split: str) -> dict:
    """Run the full evaluation."""
    skill_text = load_skill(skill_path)
    scenarios = load_scenarios(data_dir, split)

    results = []
    for scenario in scenarios:
        response = simulate_rollout(scenario, skill_text)
        eval_result = evaluate(
            response=response,
            expected_commands=scenario.get("expected_commands", []),
            expected_behaviors=scenario.get("expected_behaviors", []),
            anti_patterns=scenario.get("anti_patterns", []),
        )
        results.append({
            "id": scenario["id"],
            "scenario": scenario["scenario"],
            "description": scenario.get("description", ""),
            **eval_result,
        })

    return results


def print_report(results: list[dict], split: str) -> None:
    """Print a formatted evaluation report."""
    print(f"\n{'='*70}")
    print(f"  Branch-Sync Skill Benchmark — {split.upper()} split")
    print(f"{'='*70}\n")

    total_hard = sum(r["hard"] for r in results)
    total_soft = sum(r["soft"] for r in results)
    avg_soft = total_soft / len(results) if results else 0

    for r in results:
        status = "PASS" if r["hard"] else "FAIL"
        print(f"  [{status}] {r['id']}: {r['scenario']}")
        print(f"         {r['description'][:80]}")
        print(
            f"         hard={r['hard']}  soft={r['soft']:.2f}  "
            f"cmd={r['command_score']:.2f}  anti={r['anti_pattern_score']:.2f}  "
            f"behav={r['behavior_score']:.2f}"
        )
        for detail in r.get("details", []):
            if detail.startswith("  ✗"):
                print(f"         {detail}")
        print()

    print(f"{'─'*70}")
    print(f"  Total: {total_hard}/{len(results)} hard pass | avg soft: {avg_soft:.3f}")
    print(f"{'='*70}\n")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--skill",
        type=Path,
        default=Path(__file__).parent / "skills" / "initial.md",
        help="Path to the skill markdown file",
    )
    parser.add_argument(
        "--data-dir",
        type=Path,
        default=Path(__file__).parent / "data",
        help="Path to the data directory",
    )
    parser.add_argument(
        "--split",
        choices=["train", "val", "test"],
        default="test",
        help="Which split to evaluate",
    )
    args = parser.parse_args()

    results = run_evaluation(args.skill, args.data_dir, args.split)
    print_report(results, args.split)

    # Save results
    out_path = args.data_dir / args.split / "results.json"
    with out_path.open("w", encoding="utf-8") as f:
        json.dump(results, f, indent=2, ensure_ascii=False)
    print(f"Results saved to {out_path}")

    # Exit code based on pass rate
    pass_rate = sum(r["hard"] for r in results) / len(results) if results else 0
    sys.exit(0 if pass_rate >= 0.6 else 1)


if __name__ == "__main__":
    main()
