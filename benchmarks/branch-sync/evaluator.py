"""Branch-sync evaluator — scores model responses against expected git operations."""
from __future__ import annotations

import re


def _normalize_cmd(cmd: str) -> str:
    """Normalize a git command for comparison."""
    cmd = cmd.strip()
    # Remove trailing semicolons, newlines
    cmd = cmd.rstrip(";").strip()
    # Normalize whitespace
    cmd = re.sub(r"\s+", " ", cmd)
    return cmd.lower()


def _extract_commands(response: str) -> list[str]:
    """Extract git commands from a model response.

    Looks for:
    1. Fenced code blocks containing git commands
    2. Lines starting with 'git ' (not in code blocks)
    """
    commands = []

    # Extract from fenced code blocks
    code_blocks = re.findall(r"```(?:bash|sh|shell)?\n(.*?)```", response, re.DOTALL)
    for block in code_blocks:
        for line in block.splitlines():
            line = line.strip()
            if line.startswith("git ") or line.startswith("$ git "):
                cmd = line.lstrip("$ ").strip()
                commands.append(cmd)

    # Also check for inline git commands (outside fenced code blocks)
    # Remove fenced code blocks first, then search
    cleaned = re.sub(r"```.*?```", "", response, flags=re.DOTALL)
    for line in cleaned.splitlines():
        line = line.strip()
        if line.startswith("git "):
            commands.append(line)

    # Extract from inline code (backtick-wrapped git commands)
    # e.g., "1. `git fetch origin`" or "run `git merge origin/developer`"
    inline_cmds = re.findall(r"`(git [^`]+)`", response)
    for cmd in inline_cmds:
        cmd = cmd.strip()
        if cmd not in commands:
            commands.append(cmd)

    return commands


def _check_expected_commands(
    commands: list[str], expected: list[str]
) -> tuple[float, list[str]]:
    """Check if expected commands appear in the response.

    Returns (score, details) where score is 0.0-1.0.
    """
    if not expected:
        # If no commands expected (e.g., should refuse), check for refusal
        return 1.0, ["No commands expected (refusal scenario)"]

    normalized_cmds = [_normalize_cmd(c) for c in commands]
    matched = []
    missing = []

    for exp in expected:
        exp_norm = _normalize_cmd(exp)
        found = False
        for cmd_norm in normalized_cmds:
            # Check if the expected command is a substring of what the model produced
            # or vice versa (handles minor variations like flag order)
            if exp_norm in cmd_norm or cmd_norm in exp_norm:
                found = True
                break
            # Check key parts (e.g., "git merge origin/developer" matches "git merge origin/developer --no-edit")
            exp_parts = set(exp_norm.split())
            cmd_parts = set(cmd_norm.split())
            if exp_parts.issubset(cmd_parts):
                found = True
                break
        if found:
            matched.append(exp)
        else:
            missing.append(exp)

    score = len(matched) / len(expected) if expected else 1.0
    details = []
    for m in matched:
        details.append(f"  ✓ {m}")
    for m in missing:
        details.append(f"  ✗ MISSING: {m}")

    return score, details


def _check_anti_patterns(
    commands: list[str], response: str, anti_patterns: list[str]
) -> tuple[float, list[str]]:
    """Check that anti-patterns are NOT present.

    Returns (score, details) where score is 1.0 if no anti-patterns found.
    """
    if not anti_patterns:
        return 1.0, []

    violations = []
    for pattern in anti_patterns:
        pattern_lower = pattern.lower()
        # Check in commands
        for cmd in commands:
            if pattern_lower in _normalize_cmd(cmd):
                violations.append(f"  ✗ Anti-pattern found: {cmd.strip()}")
                break
        else:
            # Also check in raw response text
            if pattern_lower in response.lower():
                # But only if it looks like a command context, not just mentioned in prose
                for line in response.splitlines():
                    if pattern_lower in line.lower() and (
                        "git " in line.lower() or "checkout" in line.lower()
                    ):
                        violations.append(
                            f"  ✗ Anti-pattern found in response: {line.strip()[:80]}"
                        )
                        break

    score = 1.0 if not violations else max(0.0, 1.0 - len(violations) * 0.5)
    return score, violations


def _check_behaviors(
    response: str, expected_behaviors: list[str]
) -> tuple[float, list[str]]:
    """Check if expected behaviors are demonstrated in the response.

    This is a keyword-based heuristic — not perfect, but catches the basics.
    """
    if not expected_behaviors:
        return 1.0, []

    response_lower = response.lower()
    matched = []
    missing = []

    behavior_keywords = {
        "fetches before merge": ["fetch"],
        "merges base into feature": ["merge origin/", "merge origin"],
        "pushes after successful merge": ["push"],
        "does not use --ours or --theirs": [],  # checked by anti_patterns
        "detects dirty tree before merge": ["status", "dirty", "uncommitted"],
        "surfaces dirty files to user": ["status", "modified", "uncommitted"],
        "offers commit or stash options": ["commit", "stash"],
        "does not silently stash": [],  # checked by anti_patterns
        "refuses to sync the base branch": ["refuse", "cannot sync", "on the base", "already on"],
        "explains this skill is for feature branches": ["feature branch"],
        "lists conflicted files": ["conflict", "diff --name-only", "unmerged"],
        "understands both sides' intent": ["intent", "both sides", "understand", "purpose"],
        "resolves by integrating both changes": ["integrate", "combine", "both changes"],
        "stages resolved files": ["git add"],
        "commits merge": ["commit"],
        "recognizes lockfile conflict": ["lock", "package-lock", "regenerat"],
        "regenerates lockfile with npm install instead of hand-merging": ["npm install", "regenerat"],
        "detects ambiguous conflict": ["ambiguous", "unclear", "unsure", "conflicting"],
        "stops and asks user for resolution": ["ask", "user", "decision", "which"],
        "shows both diffs to user": ["diff", "show", "both"],
        "does not guess at resolution": [],  # checked by anti_patterns
        "merges even for long-lived branches": ["merge"],
        "does not suggest rebase": [],  # checked by anti_patterns
        "runs build verification after merge": ["build", "compile", "test", "verify"],
        "reports merge results": ["report", "result", "summary", "merged"],
        "hand-merges source files": ["merge", "resolve", "integrate"],
        "recognizes generated migration file": ["generat", "migration", "script"],
        "reads sync_strategy from config": ["config", "strategy", "rebase"],
        "rebases instead of merging": ["rebase"],
        "completes merge and push": ["push"],
        "offers to create PR": ["pr", "pull request"],
        "uses gh pr create for GitHub": ["gh pr create", "gh pr"],
        "aborts merge cleanly": ["merge --abort", "abort"],
        "returns to pre-merge state": ["abort", "rollback", "pre-merge"],
        "reports what was aborted": ["abort", "report"],
    }

    for behavior in expected_behaviors:
        keywords = behavior_keywords.get(behavior, [])
        if not keywords:
            # Can't check this behavior with keywords, count as matched
            matched.append(behavior)
            continue

        found = any(kw in response_lower for kw in keywords)
        if found:
            matched.append(behavior)
        else:
            missing.append(behavior)

    score = len(matched) / len(expected_behaviors) if expected_behaviors else 1.0
    details = []
    for m in matched:
        details.append(f"  ✓ Behavior: {m}")
    for m in missing:
        details.append(f"  ✗ Missing behavior: {m}")

    return score, details


def evaluate(
    response: str,
    expected_commands: list[str],
    expected_behaviors: list[str],
    anti_patterns: list[str],
) -> dict:
    """Evaluate a branch-sync response.

    Returns a dict with:
    - hard: 0 or 1 (pass/fail based on overall score >= 0.6)
    - soft: float 0.0-1.0 (weighted average score)
    - command_score: float (score for correct commands)
    - anti_pattern_score: float (score for avoiding anti-patterns)
    - behavior_score: float (score for expected behaviors)
    - details: list of strings (what passed/failed)
    """
    commands = _extract_commands(response)

    cmd_score, cmd_details = _check_expected_commands(commands, expected_commands)
    anti_score, anti_details = _check_anti_patterns(commands, response, anti_patterns)
    behav_score, behav_details = _check_behaviors(response, expected_behaviors)

    # Weighted average: commands 40%, anti-patterns 30%, behaviors 30%
    soft = cmd_score * 0.4 + anti_score * 0.3 + behav_score * 0.3
    hard = 1 if soft >= 0.6 else 0

    all_details = ["Commands:"] + cmd_details + ["Anti-patterns:"] + anti_details + ["Behaviors:"] + behav_details

    return {
        "hard": hard,
        "soft": soft,
        "command_score": cmd_score,
        "anti_pattern_score": anti_score,
        "behavior_score": behav_score,
        "predicted_commands": commands,
        "details": all_details,
    }
