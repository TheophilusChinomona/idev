# Smart Context Skill (idev plugin)

Token-optimized context loading for Claude Code: a lightweight per-project
index is generated once, then context is loaded incrementally (Grep before
Read) instead of re-scanning or bulk-reading files.

## How it works

1. **Index generation**: `scanner.py` detects the tech stack, structure roots,
   feature names, and file-naming patterns, and writes them to
   `<project>/.claude/idev/smart-context/index.json`.
2. **On task**: Claude reads the small index, identifies the relevant
   feature/layer, and greps the project map for exact paths.
3. **Targeted reads**: only the source files actually needed are read.

## Generating the index

From the project root:

```bash
python3 "${CLAUDE_PLUGIN_ROOT}/skills/smart-context/scanner.py"
```

Tech agnostic: detects React/Next.js/Vue/Angular frontends and
.NET/Python/Go/Rust/Java backends (root or one level of subdirectories).

## Files

- `SKILL.md` - Skill instructions for Claude (loading policy)
- `scanner.py` - Index generator
- `README.md` - This file

This skill ships with the idev plugin; the only per-project artifact is the
generated `index.json` under `.claude/idev/smart-context/`.
