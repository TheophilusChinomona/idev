#!/usr/bin/env python3
"""Generate SkillOpt test scenarios from a skill's SKILL.md.

Reads the skill's procedure, activation conditions, anti-patterns, and
domain context to produce train/val/test scenario splits.

Usage:
    python3 generate_scenarios.py <skill-path> [--out-dir DIR]
"""
from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path


def parse_skill(path: Path) -> dict:
    """Parse a SKILL.md into structured sections."""
    text = path.read_text(encoding="utf-8")
    sections = {"raw": text, "frontmatter": {}, "sections": {}}

    # Parse frontmatter
    if text.startswith("---"):
        end = text.find("---", 3)
        if end > 0:
            fm_text = text[3:end].strip()
            for line in fm_text.splitlines():
                if ":" in line:
                    key, val = line.split(":", 1)
                    sections["frontmatter"][key.strip()] = val.strip().strip('"')

    # Parse markdown sections
    current_section = None
    current_lines = []
    for line in text.splitlines():
        if line.startswith("## "):
            if current_section:
                sections["sections"][current_section] = "\n".join(current_lines).strip()
            current_section = line[3:].strip()
            current_lines = []
        elif current_section:
            current_lines.append(line)
    if current_section:
        sections["sections"][current_section] = "\n".join(current_lines).strip()

    return sections


def extract_procedure_steps(sections: dict) -> list[str]:
    """Extract procedure steps from the skill."""
    steps = []
    for key, content in sections.get("sections", {}).items():
        if any(w in key.lower() for w in ["procedure", "steps", "phase", "how"]):
            # Look for numbered steps or bullet points
            for line in content.splitlines():
                line = line.strip()
                if re.match(r"^[\d]+\.\s", line) or re.match(r"^[-*]\s", line):
                    steps.append(line)
    return steps


def extract_anti_patterns(sections: dict) -> list[str]:
    """Extract anti-patterns from the skill."""
    patterns = []
    for key, content in sections.get("sections", {}).items():
        if "anti" in key.lower():
            for line in content.splitlines():
                line = line.strip()
                if line.startswith("-") or line.startswith("*"):
                    patterns.append(line.lstrip("-* ").strip())
    return patterns


def extract_activation(sections: dict) -> list[str]:
    """Extract activation conditions."""
    activations = []
    for key, content in sections.get("sections", {}).items():
        if "activation" in key.lower():
            for line in content.splitlines():
                line = line.strip()
                if line.startswith("-") or line.startswith("*"):
                    activations.append(line.lstrip("-* ").strip())
    return activations


def infer_domain(sections: dict, skill_path: Path) -> str:
    """Infer the skill's domain from its content."""
    name = sections.get("frontmatter", {}).get("name", skill_path.stem)
    raw = sections.get("raw", "").lower()

    domain_keywords = {
        "git": ["git", "branch", "merge", "commit", "push", "pull", "rebase"],
        "database": ["database", "sql", "migration", "schema", "table", "column"],
        "build": ["build", "compile", "typecheck", "lint", "test"],
        "api": ["api", "endpoint", "route", "controller", "service"],
        "frontend": ["component", "react", "vue", "angular", "css", "ui"],
        "backend": ["server", "controller", "service", "repository", "di"],
        "auth": ["auth", "login", "session", "token", "permission"],
        "context": ["cache", "index", "map", "scan", "detect"],
    }

    scores = {}
    for domain, keywords in domain_keywords.items():
        scores[domain] = sum(1 for kw in keywords if kw in raw)

    if scores:
        best = max(scores, key=scores.get)
        if scores[best] > 0:
            return best
    return "general"


def generate_scenarios(skill_path: Path) -> dict:
    """Generate test scenarios from a skill file."""
    sections = parse_skill(skill_path)
    name = sections["frontmatter"].get("name", skill_path.stem)
    domain = infer_domain(sections, skill_path)
    steps = extract_procedure_steps(sections)
    anti_patterns = extract_anti_patterns(sections)
    activations = extract_activation(sections)

    scenarios = []
    scenario_id = 0

    # Generate happy-path scenario
    scenario_id += 1
    scenarios.append({
        "id": f"gen-{scenario_id:03d}",
        "scenario": f"{name}_happy_path",
        "description": f"Standard {name} operation — everything works as expected.",
        "skill_section": "procedure",
        "expected_signals": [s for s in steps[:5]],  # first few steps
        "anti_patterns": anti_patterns[:3],
        "task_type": domain,
        "complexity": "easy",
    })

    # Generate error/edge-case scenarios from anti-patterns
    for i, pattern in enumerate(anti_patterns[:3]):
        scenario_id += 1
        scenarios.append({
            "id": f"gen-{scenario_id:03d}",
            "scenario": f"{name}_avoids_{re.sub(r'[^a-z0-9]+', '_', pattern.lower())[:30]}",
            "description": f"Verify the skill avoids: {pattern}",
            "skill_section": "anti_patterns",
            "expected_signals": [],
            "anti_patterns": [pattern],
            "task_type": domain,
            "complexity": "medium",
        })

    # Generate edge-case scenarios from activation conditions
    for i, activation in enumerate(activations[:3]):
        scenario_id += 1
        scenarios.append({
            "id": f"gen-{scenario_id:03d}",
            "scenario": f"{name}_activation_{i+1}",
            "description": f"Scenario triggering activation: {activation}",
            "skill_section": "activation",
            "expected_signals": [activation],
            "anti_patterns": [],
            "task_type": domain,
            "complexity": "medium",
        })

    # Generate a complex multi-step scenario
    if len(steps) > 3:
        scenario_id += 1
        scenarios.append({
            "id": f"gen-{scenario_id:03d}",
            "scenario": f"{name}_complex",
            "description": f"Complex {name} scenario requiring multiple procedure steps and handling edge cases.",
            "skill_section": "full_procedure",
            "expected_signals": steps,
            "anti_patterns": anti_patterns,
            "task_type": domain,
            "complexity": "hard",
        })

    return {
        "skill_name": name,
        "skill_path": str(skill_path),
        "domain": domain,
        "scenarios": scenarios,
        "stats": {
            "total": len(scenarios),
            "easy": sum(1 for s in scenarios if s.get("complexity") == "easy"),
            "medium": sum(1 for s in scenarios if s.get("complexity") == "medium"),
            "hard": sum(1 for s in scenarios if s.get("complexity") == "hard"),
        },
    }


def split_scenarios(scenarios: list[dict], seed: int = 42) -> dict:
    """Split scenarios into train/val/test."""
    import random
    rng = random.Random(seed)
    shuffled = list(scenarios)
    rng.shuffle(shuffled)

    n = len(shuffled)
    if n <= 3:
        return {"train": shuffled, "val": [], "test": shuffled}
    elif n <= 6:
        split_point = max(1, n // 3)
        return {
            "train": shuffled[:split_point],
            "val": shuffled[split_point:split_point * 2],
            "test": shuffled[split_point * 2:],
        }
    else:
        split_point = max(1, n // 3)
        return {
            "train": shuffled[:split_point],
            "val": shuffled[split_point:split_point * 2],
            "test": shuffled[split_point * 2:],
        }


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("skill_path", type=Path, help="Path to SKILL.md")
    parser.add_argument("--out-dir", type=Path, help="Output directory")
    parser.add_argument("--seed", type=int, default=42)
    args = parser.parse_args()

    if not args.skill_path.exists():
        print(f"Error: {args.skill_path} not found", file=sys.stderr)
        sys.exit(1)

    result = generate_scenarios(args.skill_path)
    splits = split_scenarios(result["scenarios"], seed=args.seed)

    # Output directory
    skill_name = result["skill_name"]
    out_dir = args.out_dir or Path("benchmarks") / skill_name
    data_dir = out_dir / "data"

    for split_name, items in splits.items():
        split_dir = data_dir / split_name
        split_dir.mkdir(parents=True, exist_ok=True)
        (split_dir / "items.json").write_text(
            json.dumps(items, indent=2, ensure_ascii=False),
            encoding="utf-8",
        )

    # Save metadata
    (out_dir / "scenarios.json").write_text(
        json.dumps(result, indent=2, ensure_ascii=False),
        encoding="utf-8",
    )

    print(f"Generated {result['stats']['total']} scenarios for '{skill_name}'")
    print(f"  Domain: {result['domain']}")
    print(f"  Train: {len(splits['train'])} | Val: {len(splits['val'])} | Test: {len(splits['test'])}")
    print(f"  Saved to: {out_dir}")


if __name__ == "__main__":
    main()
