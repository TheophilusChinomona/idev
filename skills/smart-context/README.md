# Smart Context Skill

A generic, self-configuring context management skill for Claude Code that reduces token usage while maintaining accuracy.

## Features

- **Zero Configuration** - Works on any project out of the box
- **Dynamic Loading** - Loads only relevant context based on the task
- **Tech Agnostic** - Supports React, Vue, Angular, .NET, Node, Python, etc.
- **Self-Learning** - Builds and caches project structure automatically

## Installation

Copy this folder to any project:
```
${CLAUDE_PLUGIN_ROOT}/skills/smart-context/
```

## How It Works

1. **First Run**: Scans project, detects tech stack, creates lightweight index
2. **On Task**: Identifies relevant feature/module from user query
3. **Load Context**: Loads only files related to that feature
4. **Cache**: Stores structure to avoid re-scanning

## Files

- `skill.md` - Main skill instructions for Claude
- `scanner.py` - Project scanner script (optional, for pre-generation)
- `README.md` - This file

## Usage

The skill activates automatically when Claude detects it in `${CLAUDE_PLUGIN_ROOT}/skills/`.
