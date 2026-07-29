---
name: project-map
description: "Generates and maintains a detailed project map (all FE/BE files with mappings) at .claude/idev/project-map/project.map.md via Python watcher scripts. Use when generating or refreshing the project map, configuring the map watcher, or when another skill needs the map as a data source."
---

# Project Map Skill

## Purpose
Maintain a detailed, greppable map of the project — every frontend file (pages, containers, services) and every backend file (controllers, services). The map is the data source for the smart-context, file-index, and api-contract-validation skills.

## State (per project)
| File | Purpose |
|------|---------|
| `.claude/idev/project-map/project.map.md` | The generated map (note the filename: `project.map.md`, NOT `project-map.md`) |
| `.claude/idev/project-map/watcher_config.json` | FE/BE paths + project type for the watcher |

## Scripts (in this skill folder)
| Script | Purpose |
|--------|---------|
| `${CLAUDE_PLUGIN_ROOT}/skills/project-map/ai_map_updater.py` | One-shot map generation (CLI + importable `create_project_map`) |
| `${CLAUDE_PLUGIN_ROOT}/skills/project-map/map_watcher.py` | Long-running watcher; regenerates the map only when source files change (run from the project root) |

## Generate the map
```bash
# from the project root — auto-detects split vs unified, safe non-interactively
python3 "${CLAUDE_PLUGIN_ROOT}/skills/project-map/ai_map_updater.py"

# or with explicit options
python3 "${CLAUDE_PLUGIN_ROOT}/skills/project-map/ai_map_updater.py" \
  --root . --mode split --frontend ./frontend --backend ./backend

# or start the watcher (interactive config on first run)
python3 "${CLAUDE_PLUGIN_ROOT}/skills/project-map/map_watcher.py"
```

- Always access the map via Grep — never load the whole file. Grep for the feature or file name (e.g. `Grep "Order" .claude/idev/project-map/project.map.md`), then Read only the source files it points to.
- Load only the relevant section (frontend / backend / a single category) when a section-level view is needed.
- If the map is missing or stale, regenerate it (command above) before trusting it.
- Follow `${CLAUDE_PLUGIN_ROOT}/skills/project-map/map.rules.md` for the full rules.

## Staleness Detection

The map file records a `Generated:` timestamp at the top. Check staleness:
```
1. Read the first 5 lines of project.map.md
2. Extract the "Generated: YYYY-MM-DD" date
3. If older than 14 days → warn: "project-map is N days old — results may be stale"
4. If older than 30 days → fail loudly: "project-map is severely stale — regenerate before trusting"
5. If missing → generate before proceeding
```

The session-start hook also checks file mtime and warns if > 14 days old.
When regenerating, update the `Generated:` timestamp in the output.
