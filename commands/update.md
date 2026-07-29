---
description: "Update the idev plugin to the latest version from GitHub — pulls latest code, reinstalls, and reconciles project state."
argument-hint: "[--check]"
---

# /idev:update

Update the idev plugin itself (not project state — that's `/idev:upgrade`).

Arguments: `$ARGUMENTS` (`--check`: report available update without installing).

## Steps

1. **Check current version**: read from
   `${CLAUDE_PLUGIN_ROOT}/.claude-plugin/plugin.json` → `version`.

2. **Fetch latest from GitHub**:
   ```bash
   cd "${CLAUDE_PLUGIN_ROOT}"
   git fetch origin master
   ```
   Compare `origin/master` HEAD against the current checkout.

3. **Pull if newer**:
   ```bash
   git pull origin master
   ```
   If already at latest, report "idev is up to date (v{version})" and stop.

4. **Reinstall**: if the plugin was installed via marketplace, the next
   session will pick up the new files automatically. For local checkouts,
   the pull is the update.

5. **Run /idev:upgrade**: after updating, automatically run the upgrade
   command to reconcile any new directories, config keys, or CLAUDE.md
   snippet changes with the current project.

6. **Report**: old version → new version, list of changes from the pull,
   and the upgrade reconciliation results.

## With --check

Just report the current version and whether a newer version is available
on GitHub. Do not install anything.

```bash
cd "${CLAUDE_PLUGIN_ROOT}"
git fetch origin master --quiet
LOCAL=$(git rev-parse HEAD)
REMOTE=$(git rev-parse origin/master)
if [ "$LOCAL" = "$REMOTE" ]; then
  echo "idev is up to date (v$(python3 -c "import json; print(json.load(open('.claude-plugin/plugin.json'))['version'])"))"
else
  echo "Update available: $(git log --oneline $LOCAL..$REMOTE | wc -l) new commits"
  git log --oneline $LOCAL..$REMOTE | head -5
fi
```
