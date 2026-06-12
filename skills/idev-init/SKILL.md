---
name: idev-init
description: "Scaffolds the per-project .claude/idev/ state directory (caches, journal, lessons, config templates) for the idev plugin. Use when starting idev in a new project, when the SessionStart hook reports the state directory is missing, or when the user runs /idev:idev-init or asks to 'set up idev'."
argument-hint: "[--with-claude-md-snippet]"
allowed-tools: ["Bash", "Read", "Write", "Edit", "Glob"]
---

# idev Init — Scaffold Per-Project State

Initialize the `.claude/idev/` state directory in the current project. All idev skills read and write their per-project state (caches, indexes, journal, lessons, session state) here — never inside the plugin install directory.

## Steps

1. **Check for existing state**: If `.claude/idev/` already exists with content, report what's there and ask before overwriting anything. Never overwrite an existing `journal.md`, `lessons.md`, or any cache file.

2. **Create the directory layout**:
   ```bash
   mkdir -p .claude/idev/{smart-context,backend-patterns,frontend-patterns,architecture-scanner,build-check,api-contract-validation,post-creation-verify,file-index,import-graph,test-map,lessons-learned,task-journal,session-resume,project-map,api-contracts/contracts,browser-tests/{scripts,artifacts,reports}}
   ```

3. **Copy templates** (only where the destination does not exist):
   - `${CLAUDE_PLUGIN_ROOT}/templates/journal.md` → `.claude/idev/task-journal/journal.md`
   - `${CLAUDE_PLUGIN_ROOT}/templates/lessons.md` → `.claude/idev/lessons-learned/lessons.md`
   - `${CLAUDE_PLUGIN_ROOT}/templates/project-config.json` → `.claude/idev/project-config.json`
   - `${CLAUDE_PLUGIN_ROOT}/templates/commands.json` → `.claude/idev/commands.json`
   - `${CLAUDE_PLUGIN_ROOT}/templates/watcher_config.json` → `.claude/idev/project-map/watcher_config.json`
   - `${CLAUDE_PLUGIN_ROOT}/templates/rules.md` → `.claude/idev/rules.md`
   - `${CLAUDE_PLUGIN_ROOT}/templates/commit-style.md` → `.claude/idev/commit-style.md`

4. **Initialize session state**: Write `.claude/idev/session-resume/last-session.json` with:
   ```json
   { "lastTask": null, "modifiedFiles": [], "openIssues": [], "savedAt": null }
   ```

5. **Offer the CLAUDE.md snippet** (or do it directly if the user passed `--with-claude-md-snippet`): append the contents of `${CLAUDE_PLUGIN_ROOT}/templates/claude-md-snippet.md` to the project's `CLAUDE.md` (create the file if missing). It contains the idev operating guide (cache-first context rules, skill workflow chain, agent delegation map) plus per-project policies (protected branches, migration policy, API config) — tell the user to review the FILL IN / KEEP ONLY IF sections. If an older idev snippet already exists in CLAUDE.md (look for the `===== idev plugin` marker), replace it instead of appending a duplicate.

6. **Offer the low-prompt permissions preset**: Ask whether to allowlist the plugin's read-only scripts and read-only git commands in the project's `.claude/settings.json`, so they run without permission prompts. If yes: resolve `${CLAUDE_PLUGIN_ROOT}` to its absolute path, then MERGE (never replace existing entries) this into `.claude/settings.json`'s `permissions.allow` array, creating the file if missing:
   ```json
   [
     "Bash(python3 <abs-plugin-root>/skills/smart-context/scanner.py:*)",
     "Bash(python3 <abs-plugin-root>/skills/auto-learning/scripts/instinct-cli.py:*)",
     "Bash(python3 <abs-plugin-root>/skills/project-map/ai_map_updater.py:*)",
     "Bash(git status:*)",
     "Bash(git diff:*)",
     "Bash(git log:*)",
     "Bash(git branch:*)"
   ]
   ```
   These are exact path prefixes — only the plugin's own read-only scripts are covered, nothing broader (never add `Bash(python3:*)`). Note for the user: the bundled agents' Read/Grep/Glob tools never prompt; prompts come from Bash invocations, which is what this preset removes.

7. **Offer team git hooks**: Ask whether to install the commit-message hooks (`prepare-commit-msg` auto-prefixes the ticket from the branch name; `commit-msg` validates the subject format). If yes, follow the `install-git-hooks` procedure in the `/idev:hooks` command (never overwrite non-idev hooks without asking). Point the user at `.claude/idev/commit-style.md` to tune the team format.

8. **Optionally trigger first scans**: Ask whether to run the initial project scans now (smart-context index, file-index, pattern caches). If yes, generate `.claude/idev/smart-context/index.json` first by running the scanner from the project root:
   ```bash
   python3 "${CLAUDE_PLUGIN_ROOT}/skills/smart-context/scanner.py"
   ```
   If `python3` is unavailable, build the index manually per the idev:smart-context skill (detect the stack, feature names, and naming patterns, and write the same JSON shape by hand).

9. **Report**: List what was created, what was skipped (already existed), and remind the user that caches regenerate automatically as the skills run. Mention `/idev:hooks` for enabling the optional observer/compact hooks later.
