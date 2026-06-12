---
description: Export learned instincts to a shareable file for teammates or other machines
argument-hint: "[--domain <name>] [--min-confidence <n>] [--output <file>]"
---

# Instinct Export

Export instincts to a shareable YAML-frontmatter file. Useful for sharing with teammates, transferring to a new machine, or contributing to project conventions.

## How to Run

Run the instinct CLI, passing through any user arguments:

```bash
python3 "${CLAUDE_PLUGIN_ROOT}/skills/auto-learning/scripts/instinct-cli.py" export $ARGUMENTS
```

## Supported Flags (these are the only ones)

- `--domain <name>`: export only the specified domain
- `--min-confidence <n>`: minimum confidence threshold
- `--output <file>` / `-o <file>`: write to a file instead of stdout

## What the CLI Does

1. Loads instincts from `~/.claude/homunculus/instincts/{personal,inherited}/`
2. Applies the domain/confidence filters
3. Sanitizes output: absolute filesystem paths are replaced with `<path>` and secret-looking values (api keys, tokens, passwords) are replaced with `[REDACTED]`
4. Writes each instinct as a `---` frontmatter block (id, trigger, confidence, domain, source) followed by its markdown body

## After Running

- If `--output` was used, confirm the file path to the user.
- If output went to stdout, offer to save it to a file the user names.
- Skim the export for anything sensitive the regex-based sanitizer may have missed (project names, internal URLs) and warn the user before they share it.
