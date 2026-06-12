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

## Using the map
The map contains flat file listings with annotations: `FRONTEND FILES` / `BACKEND FILES` plus a domain entity count (split mode), or layer categories — Pages/UI, Services, Domain, Infrastructure, Other — with referenced `.csproj` projects labeled (unified mode). It does NOT contain module summaries, pattern documentation, or gotchas — do not expect those sections.

- Always access the map via Grep — never load the whole file. Grep for the feature or file name (e.g. `Grep "Order" .claude/idev/project-map/project.map.md`), then Read only the source files it points to.
- Load only the relevant section (frontend / backend / a single category) when a section-level view is needed.
- If the map is missing or stale, regenerate it (command above) before trusting it.
- Follow `${CLAUDE_PLUGIN_ROOT}/skills/project-map/map.rules.md` for the full rules.
