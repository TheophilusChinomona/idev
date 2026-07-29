# Performance Guidelines

## Model Selection

| Task | Model | Why |
|------|-------|-----|
| Simple edits | Sonnet | Fast, cheap |
| Complex reasoning | Opus | Better judgment |
| Bulk operations | Sonnet | Throughput |

## Context Management

- Load only what's needed (Grep before Read)
- Use caches (smart-context, project-map)
- Compact aggressively when context grows
- Prefer sections over full files

## Token Budget

- Session start: < 2,000 tokens
- Per task: < 5,000 tokens
- Total session: monitor via /status
