---
name: project-map
description: Generates and maintains a detailed project map (all FE/BE files with mappings) at .claude/idev/project-map/project.map.md via Python watcher scripts. Use when generating or refreshing the project map, configuring the map watcher, or when another skill needs the map as a data source.
---

# Project Map Skill

## Purpose
Maintain a detailed, greppable map of the project — every frontend file (pages, containers, services), every backend file (controllers, services), and FE→BE mappings. The map is the data source for the smart-context, file-index, and api-validator skills.

## State (per project)
| File | Purpose |
|------|---------|
| `.claude/idev/project-map/project.map.md` | The generated map (PRIMARY CONTEXT once generated) |
| `.claude/idev/project-map/watcher_config.json` | FE/BE paths + project type for the watcher |

## Scripts (in this skill folder)
| Script | Purpose |
|--------|---------|
| `${CLAUDE_PLUGIN_ROOT}/skills/project-map/ai_map_updater.py` | One-shot map generation (`create_project_map`) |
| `${CLAUDE_PLUGIN_ROOT}/skills/project-map/map_watcher.py` | Long-running watcher that regenerates the map every 60s (run from the project root) |

## Generate the map
```bash
# from the project root — interactive config on first run
python3 "${CLAUDE_PLUGIN_ROOT}/skills/project-map/map_watcher.py"
```
Or one-shot from Claude: read `watcher_config.json` for paths and call `create_project_map(config=...)`.

## Usage rules
Follow `${CLAUDE_PLUGIN_ROOT}/skills/project-map/map.rules.md` and the idev:project-map-usage skill:
- Always access the map via Grep first — never load it whole
- Load only the relevant section (frontend / backend / mappings)
- If the map is missing or stale, regenerate before trusting it
