---
name: idev-init
description: Scaffolds the per-project .claude/idev/ state directory (caches, journal, lessons, config templates) for the idev plugin. Use when starting idev in a new project, when the SessionStart hook reports the state directory is missing, or when the user runs /idev:idev-init or asks to "set up idev".
argument-hint: "[--with-claude-md-snippet]"
allowed-tools: ["Bash", "Read", "Write", "Edit", "Glob"]
---

# idev Init — Scaffold Per-Project State

Initialize the `.claude/idev/` state directory in the current project. All idev skills read and write their per-project state (caches, indexes, journal, lessons, session state) here — never inside the plugin install directory.

## Steps

1. **Check for existing state**: If `.claude/idev/` already exists with content, report what's there and ask before overwriting anything. Never overwrite an existing `journal.md`, `lessons.md`, or any cache file.

2. **Create the directory layout**:
   ```bash
   mkdir -p .claude/idev/{smart-context,backend-patterns,frontend-patterns,architecture-scanner,build-check,api-contract-validation,post-creation-verify,file-index,import-graph,test-map,lessons-learned,task-journal,session-resume,project-map,api-contracts/contracts}
   ```

3. **Copy templates** (only where the destination does not exist):
   - `${CLAUDE_PLUGIN_ROOT}/templates/journal.md` → `.claude/idev/task-journal/journal.md`
   - `${CLAUDE_PLUGIN_ROOT}/templates/lessons.md` → `.claude/idev/lessons-learned/lessons.md`
   - `${CLAUDE_PLUGIN_ROOT}/templates/project-config.json` → `.claude/idev/project-config.json`
   - `${CLAUDE_PLUGIN_ROOT}/templates/commands.json` → `.claude/idev/commands.json`
   - `${CLAUDE_PLUGIN_ROOT}/templates/watcher_config.json` → `.claude/idev/project-map/watcher_config.json`
   - `${CLAUDE_PLUGIN_ROOT}/templates/rules.md` → `.claude/idev/rules.md`

4. **Initialize session state**: Write `.claude/idev/session-resume/last-session.json` with:
   ```json
   { "lastTask": null, "modifiedFiles": [], "openIssues": [], "savedAt": null }
   ```

5. **Offer the CLAUDE.md snippet** (or do it directly if the user passed `--with-claude-md-snippet`): append the contents of `${CLAUDE_PLUGIN_ROOT}/templates/claude-md-snippet.md` to the project's `CLAUDE.md` (create the file if missing). This holds per-project policies (protected branches, migration policy, API config) that the user should review and tune.

6. **Optionally trigger first scans**: Ask whether to run the initial project scans now (smart-context index, file-index, pattern caches). If yes, follow the idev:smart-context skill to generate `.claude/idev/smart-context/index.json` first.

7. **Report**: List what was created, what was skipped (already existed), and remind the user that caches regenerate automatically as the skills run.
