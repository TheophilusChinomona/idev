# Project Map Skill (idev plugin)

Generates and maintains a greppable map of a project's source files at:

```
<project>/.claude/idev/project-map/project.map.md
```

This skill ships with the idev plugin — nothing is copied into your project
except the generated state under `.claude/idev/project-map/`.

## Scripts

| Script | Purpose |
|--------|---------|
| `ai_map_updater.py` | One-shot map generation (importable `create_project_map`, plus a CLI) |
| `map_watcher.py` | Long-running watcher; regenerates the map only when source files change |

Both are run via the plugin install path, from the project root:

```bash
# One-shot (auto-detects split vs unified layout; non-interactive safe)
python3 "${CLAUDE_PLUGIN_ROOT}/skills/project-map/ai_map_updater.py"

# Explicit options
python3 "${CLAUDE_PLUGIN_ROOT}/skills/project-map/ai_map_updater.py" \
  --root . --mode split --frontend ./frontend --backend ./backend

# Watcher (interactive config on first run; saved to watcher_config.json)
python3 "${CLAUDE_PLUGIN_ROOT}/skills/project-map/map_watcher.py"
```

## Project types

- **Split** — separate frontend + backend trees; the map lists frontend and
  backend files (generic source extensions) plus a domain entity count.
- **Unified** — single project (e.g. Blazor Server, MVC); files are categorized
  into Pages/UI, Services, Domain, Infrastructure, Other. Referenced `.csproj`
  projects are discovered and included.

## State (per project, under `.claude/idev/project-map/`)

| File | Purpose |
|------|---------|
| `project.map.md` | The generated map (grep it; never load it whole) |
| `watcher_config.json` | Saved paths/project type for the watcher |

See `SKILL.md` for the usage policy and `map.rules.md` for generator rules.
