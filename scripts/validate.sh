#!/usr/bin/env bash
# Repo-wide static validation. Run from the repo root: bash scripts/validate.sh
# CI runs this on every push/PR; it must stay dependency-free (bash + python3).
set -u
cd "$(dirname "$0")/.."

fail=0
err() { echo "FAIL: $*" >&2; fail=1; }

# Validate only git-tracked files (skips local env files, gitignored junk).
tracked() { git ls-files "*$1"; }

# 1. Shell syntax
while IFS= read -r f; do
  bash -n "$f" || err "bash -n $f"
done < <(tracked .sh)

# 2. Python compiles
while IFS= read -r f; do
  python3 -m py_compile "$f" || err "py_compile $f"
done < <(tracked .py)
find . -name __pycache__ -type d -not -path './.git/*' -exec rm -rf {} + 2>/dev/null

# 3. JSON parses
while IFS= read -r f; do
  python3 -m json.tool "$f" > /dev/null || err "invalid JSON: $f"
done < <(tracked .json)

# 4. No references to deleted skills, phantom commands, or stale paths
#    (CHANGELOG legitimately names the deleted skills; this script names the patterns)
if git ls-files '*.md' '*.json' '*.sh' '*.py' '*.ps1' \
    | grep -v -e '^CHANGELOG.md$' -e '^scripts/validate.sh$' \
    | xargs grep -n -E 'api-validator|api-docs-sync|project-map-usage|/api-check|/api-docs |\.claude/docs/|hook_type'; then
  err "stale references found (see matches above)"
fi

# 5. Every skill dir has a SKILL.md whose name matches the directory
for d in skills/*/; do
  s="$d/SKILL.md"
  [ -f "$s" ] || { err "missing $s"; continue; }
  dir_name=$(basename "$d")
  fm_name=$(sed -n 's/^name:[[:space:]]*//p' "$s" | head -1)
  [ "$fm_name" = "$dir_name" ] || err "$s: name '$fm_name' != dir '$dir_name'"
done

# 6. plugin.json and marketplace.json versions agree
pv=$(python3 -c 'import json; print(json.load(open(".claude-plugin/plugin.json"))["version"])')
mv=$(python3 -c 'import json; print(json.load(open(".claude-plugin/marketplace.json"))["plugins"][0]["version"])')
[ "$pv" = "$mv" ] || err "version mismatch: plugin.json $pv vs marketplace.json $mv"

# 7. Hook scripts referenced in hooks.json exist and are executable
while IFS= read -r cmd; do
  p="${cmd//\$\{CLAUDE_PLUGIN_ROOT\}/.}"
  p="${p%% *}"
  [ -x "$p" ] || err "hooks.json references missing/non-executable: $p"
done < <(python3 -c '
import json
h = json.load(open("hooks/hooks.json"))
for entries in h.get("hooks", {}).values():
    for e in entries:
        for hk in e.get("hooks", []):
            if hk.get("type") == "command":
                toks = [t for t in hk["command"].split() if t.endswith((".sh", ".py", ".ps1"))]
                print(toks[0] if toks else hk["command"].split()[0])
')

if [ "$fail" -eq 0 ]; then
  echo "All validation checks passed."
else
  exit 1
fi
