---
description: Cluster related instincts and evolve them into skills, commands, or agents
---

# Evolve

Evolve accumulated instincts into higher-level structures. This is a two-step flow: the CLI finds and prints clusters of related instincts; you (Claude) then read that output and write the evolved files yourself.

## Step 1: Run the Cluster Analysis

```bash
python3 "${CLAUDE_PLUGIN_ROOT}/skills/auto-learning/scripts/instinct-cli.py" evolve
```

The CLI loads all instincts from `~/.claude/homunculus/instincts/`, groups them by normalized trigger, and prints:

- **Skill candidates**: clusters of 3+ instincts with similar triggers
- **Command candidates**: workflow-domain instincts with confidence >= 0.7
- **Agent candidates**: clusters of 3+ instincts with average confidence >= 0.75

The only flag is `--generate`, which just prints the target directories — the CLI never writes evolved files itself. There are no other flags.

## Step 2: Create the Evolved Files

For each cluster the user wants to evolve, read the underlying instinct files, then write the evolved file to `~/.claude/homunculus/evolved/{skills,commands,agents}/`. Decide the type:

- **Command** (user-invoked): instincts describe actions a user explicitly requests, e.g. a repeatable "when adding a database table..." sequence
- **Skill** (auto-triggered): instincts describe behaviors that should apply automatically, e.g. code-style or error-handling patterns
- **Agent** (needs depth/isolation): instincts describe complex multi-step processes such as debugging or refactoring workflows

## Format to Produce

Write each evolved file as markdown with frontmatter linking back to its source instincts:

```markdown
---
name: <kebab-case-name>
description: <one line, trigger-oriented>
evolved_from:
  - <instinct-id-1>
  - <instinct-id-2>
  - <instinct-id-3>
---

# <Title>

<Synthesized instructions combining the clustered instincts: when to apply,
the steps to follow, and any evidence-backed caveats.>
```

## Flow Summary

1. Run the CLI and show the user the cluster output.
2. Ask which clusters to evolve (or proceed if the user already said).
3. Read the source instinct files for each chosen cluster.
4. Write the evolved file(s) under `~/.claude/homunculus/evolved/`.
5. Tell the user what was created and suggest reviewing before adopting the evolved files into their real plugin/skills setup.
