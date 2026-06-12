#!/usr/bin/env python3
"""Static quality benchmark for Claude Code Agent Skills.

Scans a plugin's skills/*/SKILL.md and scores each against the checks
documented in this skill's SKILL.md. Output: a per-skill scorecard table
plus failure details. Exit 0 unless --strict and any skill scores below
--min-score.

Usage:
    python3 benchmark_skills.py [--plugin-dir DIR] [--strict] [--min-score N]
"""
import argparse
import re
import sys
from pathlib import Path

NAME_RE = re.compile(r"^[a-z0-9]+(-[a-z0-9]+)*$")
RESERVED = ("anthropic", "claude")
FIRST_PERSON_RE = re.compile(r"\b(I can|You can|I will|I'll)\b", re.IGNORECASE)
TRIGGER_RE = re.compile(r"\buse (when|before|after|for)\b", re.IGNORECASE)
PLUGIN_PATH_RE = re.compile(r"\$\{CLAUDE_PLUGIN_ROOT\}/([A-Za-z0-9._/\-]+)")

CHECKS = [
    "desc-present",     # description non-empty, <= 1024 chars
    "desc-triggers",    # contains "Use when/before/after/for"
    "desc-3rd-person",  # no "I can" / "You can"
    "name-kebab",       # ^[a-z0-9]+(-[a-z0-9]+)*$
    "name-length",      # <= 64 chars
    "name-reserved",    # no anthropic/claude in name
    "name-matches-dir", # frontmatter name == directory name
    "body-length",      # SKILL.md <= 500 lines
    "has-examples",     # contains a fenced code block
    "refs-resolve",     # ${CLAUDE_PLUGIN_ROOT}/... paths exist
]


def parse_frontmatter(text):
    lines = text.splitlines()
    if not lines or lines[0].strip() != "---":
        return {}, text
    fm = {}
    for i, line in enumerate(lines[1:], start=1):
        if line.strip() == "---":
            return fm, "\n".join(lines[i + 1:])
        m = re.match(r"^([A-Za-z_-]+):\s*(.*)$", line)
        if m:
            val = m.group(2).strip()
            if len(val) >= 2 and val[0] == val[-1] and val[0] in "\"'":
                val = val[1:-1]
            fm[m.group(1)] = val
    return fm, text


def check_skill(skill_dir, plugin_root):
    path = skill_dir / "SKILL.md"
    text = path.read_text(encoding="utf-8", errors="replace")
    fm, body = parse_frontmatter(text)
    name = fm.get("name", "")
    desc = fm.get("description", "")
    n_lines = len(text.splitlines())

    results = {
        "desc-present": bool(desc) and len(desc) <= 1024,
        "desc-triggers": bool(TRIGGER_RE.search(desc)),
        "desc-3rd-person": not FIRST_PERSON_RE.search(desc),
        "name-kebab": bool(NAME_RE.match(name)),
        "name-length": 0 < len(name) <= 64,
        "name-reserved": not any(w in name.lower() for w in RESERVED),
        "name-matches-dir": name == skill_dir.name,
        "body-length": n_lines <= 500,
        "has-examples": "```" in body,
    }

    missing = []
    for rel in PLUGIN_PATH_RE.findall(text):
        rel = rel.rstrip("`'\").,;:")
        if not (plugin_root / rel).exists():
            missing.append(rel)
    results["refs-resolve"] = not missing

    return {
        "name": name or skill_dir.name,
        "lines": n_lines,
        "results": results,
        "score": sum(results.values()),
        "missing_refs": missing,
        "desc_len": len(desc),
    }


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--plugin-dir", default=None,
                    help="plugin root (default: this script's plugin)")
    ap.add_argument("--strict", action="store_true",
                    help="exit 1 if any skill scores below --min-score")
    ap.add_argument("--min-score", type=int, default=len(CHECKS),
                    help="minimum passing score for --strict (default: all)")
    args = ap.parse_args()

    plugin_root = (Path(args.plugin_dir).resolve() if args.plugin_dir
                   else Path(__file__).resolve().parent.parent.parent)
    skills_dir = plugin_root / "skills"
    if not skills_dir.is_dir():
        sys.exit(f"no skills/ directory under {plugin_root}")

    rows = []
    for d in sorted(skills_dir.iterdir()):
        if d.is_dir() and (d / "SKILL.md").is_file():
            rows.append(check_skill(d, plugin_root))

    total = len(CHECKS)
    name_w = max((len(r["name"]) for r in rows), default=5)
    print(f"{'Skill':<{name_w}}  {'Lines':>5}  {'Desc':>4}  Failures{'':<30}  Score")
    print("-" * (name_w + 60))
    for r in rows:
        fails = [c for c in CHECKS if not r["results"][c]]
        fail_str = ", ".join(fails) if fails else "-"
        print(f"{r['name']:<{name_w}}  {r['lines']:>5}  {r['desc_len']:>4}  "
              f"{fail_str:<38}  {r['score']}/{total}")
        for m in r["missing_refs"]:
            print(f"{'':<{name_w}}         missing ref: {m}")

    n = len(rows)
    perfect = sum(1 for r in rows if r["score"] == total)
    avg = sum(r["score"] for r in rows) / n if n else 0.0
    print(f"\n{n} skills | {perfect} pass all {total} checks | "
          f"average {avg:.1f}/{total}")

    if args.strict and any(r["score"] < args.min_score for r in rows):
        sys.exit(1)


if __name__ == "__main__":
    main()
