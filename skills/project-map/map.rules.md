# Project Map Rules

## What the generator emits (`ai_map_updater.py`)

### Split projects (FE + BE)
1. Flat `FRONTEND FILES:` and `BACKEND FILES:` listings (generic source extensions).
2. A `DOMAIN ENTITIES SUMMARY:` count when a `Domain/` folder exists under the backend.

### Unified projects (Blazor Server, MVC)
1. Files categorized into: `PAGES / UI COMPONENTS`, `SERVICES / INTERFACES`,
   `DOMAIN / ENTITIES`, `INFRASTRUCTURE / DATA`, `OTHER FILES`.
2. Referenced projects discovered via `.csproj` `ProjectReference` elements are
   listed under `REFERENCED PROJECTS:` and their files included with a
   `[ProjectName]` prefix.

## General rules
1. Never store raw source code in the map — file paths and counts only.
2. The watcher only rewrites the map when the source tree changes
   (file count / max mtime signature); unchanged ticks are skipped.
3. Consumers must Grep the map for relevant entries — never load it whole.
4. If the map is missing or stale, regenerate it before trusting it.
