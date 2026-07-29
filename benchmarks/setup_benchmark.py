#!/usr/bin/env python3
"""Set up a SkillOpt benchmark for any skill.

Creates the config, registers the adapter, and prepares for evaluation.

Usage:
    python3 setup_benchmark.py <skill-name> [--skill-path PATH] [--model MODEL]
"""
from __future__ import annotations

import argparse
import sys
import sysconfig
import textwrap
from pathlib import Path


def create_config(skill_name: str, skill_path: str, model: str, out_dir: Path) -> Path:
    """Create a SkillOpt YAML config for the benchmark."""
    config_content = textwrap.dedent(f"""\
        # Auto-generated SkillOpt config for {skill_name}
        # Model: {model} via Codex CLI

        model:
          reasoning_effort: medium

        train:
          train_size: 5
          batch_size: 5
          accumulation: 1

        gradient:
          minibatch_size: 3
          merge_batch_size: 3

        optimizer:
          learning_rate: 4

        evaluation:
          sel_env_num: 0
          test_env_num: 5

        env:
          name: {skill_name}
          skill_init: {skill_path}
          split_mode: split_dir
          split_dir: benchmarks/{skill_name}/data
          data_path: ""
          split_output_dir: ""
          max_completion_tokens: 4096
          workers: 1
          limit: 0
    """)

    config_path = out_dir / "config.yaml"
    config_path.write_text(config_content, encoding="utf-8")
    return config_path


def create_init_skill(skill_path: Path, out_dir: Path) -> Path:
    """Copy the skill as the initial seed."""
    content = skill_path.read_text(encoding="utf-8")
    skills_dir = out_dir / "skills"
    skills_dir.mkdir(parents=True, exist_ok=True)
    init_path = skills_dir / "initial.md"
    init_path.write_text(content, encoding="utf-8")
    return init_path


def register_adapter(skill_name: str) -> bool:
    """Register the skill's adapter with SkillOpt's environment registry."""
    # Check if already registered
    try:
        from skillopt.envs import __init__  # noqa
    except ImportError:
        print("Warning: skillopt not installed. Run: pip install --break-system-packages skillopt")
        return False

    # Check if adapter exists in the installed package
    adapter_path = Path(sysconfig.get_path("purelib")) / "skillopt" / "envs" / skill_name / "adapter.py"
    if not adapter_path.exists():
        print(f"Warning: Adapter not found at {adapter_path}")
        print(f"  Copy the benchmark directory to the skillopt envs package:")
        print(f"  cp -r benchmarks/{skill_name} $(python3 -c 'import skillopt; import os; print(os.path.dirname(skillopt.__file__))')/envs/{skill_name}")
        return False

    return True


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("skill_name", help="Name for the benchmark (e.g., branch-sync)")
    parser.add_argument("--skill-path", required=True, help="Path to the SKILL.md file")
    parser.add_argument("--model", default="gpt-5.4", help="Codex model to use")
    parser.add_argument("--out-dir", type=Path, help="Output directory")
    args = parser.parse_args()

    skill_path = Path(args.skill_path)
    if not skill_path.exists():
        print(f"Error: {skill_path} not found", file=sys.stderr)
        sys.exit(1)

    out_dir = args.out_dir or Path("benchmarks") / args.skill_name
    out_dir.mkdir(parents=True, exist_ok=True)

    # Create config
    config_path = create_config(args.skill_name, args.skill_path, args.model, out_dir)
    print(f"Created config: {config_path}")

    # Copy skill as initial seed
    init_path = create_init_skill(skill_path, out_dir)
    print(f"Created initial skill: {init_path}")

    # Check adapter registration
    if register_adapter(args.skill_name):
        print(f"Adapter registered for {args.skill_name}")
    else:
        print(f"Adapter needs to be registered manually")

    print(f"\nBenchmark ready at: {out_dir}")
    print(f"\nTo run evaluation:")
    print(f"  skillopt-eval \\")
    print(f"    --config {config_path} \\")
    print(f"    --skill {skill_path} \\")
    print(f"    --backend codex_exec \\")
    print(f"    --target_model {args.model} \\")
    print(f"    --split test \\")
    print(f"    --env {args.skill_name}")


if __name__ == "__main__":
    main()
