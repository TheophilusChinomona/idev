---
name: env-preflight
description: "Session environment sanity check — verifies cwd is the repo root, git auth is live, DB env vars are present, and reports active sandbox constraints. Use when starting a session, when credentials may have expired, or when the environment feels stale."
---

# Env Preflight Skill

## Purpose
Catch environment problems before they waste a turn: wrong working directory,
expired git credentials, missing DB env vars, or sandbox blocks that will
silently fail later.

## Activation
- Automatically via the SessionStart hook (silent when all checks pass)
- Explicitly: when the session feels stale, credentials may have expired, or after a long pause

---

## Phase 1: Working Directory Check

```bash
git rev-parse --show-toplevel 2>/dev/null
pwd
```

**Pass:** `pwd` output equals `git rev-parse --show-toplevel`.

**Fail — inside subdirectory:**
```bash
cd "$(git rev-parse --show-toplevel)"
```
Report: "Corrected cwd from [was] to [now]."

**Fail — not a git repo:** Report the current directory and stop.
Never continue into deeper subdirectories without surfacing this.

---

## Phase 2: Git Auth Check

```bash
git remote -v 2>/dev/null | head -3
git ls-remote --exit-code origin HEAD 2>&1 | head -3
```

- Exit 0 → auth OK, note the remote URL silently.
- Non-zero → report the error. Do NOT attempt to fix credentials.
  Tell the user exactly which command failed and what the output was.

---

## Phase 3: DB Env Var Check

Detect any DB-related env vars and verify they are set (not empty):

```bash
# Generic detection — check common patterns
for VAR in DATABASE_URL DB_URL CONNECTION_STRING DB_HOST DB_SERVER \
           POSTGRES_URL MYSQL_URL MONGO_URL REDIS_URL \
           ConnectionStrings__DefaultConnection; do
  VAL="${!VAR:-}"
  if [ -n "$VAL" ]; then
    # Mask credentials: show scheme + host only, redact password
    MASKED=$(echo "$VAL" | sed 's|//[^:]*:[^@]*@|//***:***@|g')
    echo "DB_ENV: $VAR=$MASKED"
  fi
done

# .NET-style: check appsettings for ConnectionStrings presence (do not read values)
if ls *.csproj 2>/dev/null | head -1 | grep -q .; then
  grep -l "ConnectionStrings" appsettings*.json 2>/dev/null | head -3
fi
```

**Pass:** At least one DB var is set — report names and masked values.
**No vars found:** Note "No DB env vars detected" (not a failure — project may not use one).
**Never print raw connection strings** — always mask.

---

## Phase 4: Sandbox Report

```bash
echo "SANDBOX: $CLAUDE_SANDBOX_ENABLED"
echo "USER: $(whoami)"
echo "SHELL: $SHELL"
# Report which write targets are sandboxed by checking a canary write
TMPDIR_OK=$(mktemp 2>/dev/null && echo "ok" || echo "blocked")
echo "TMP_WRITE: $TMPDIR_OK"
```

If `CLAUDE_SANDBOX_ENABLED=true`: briefly note which common operations
(rm, git push --force, installs) typically need `dangerouslyDisableSandbox`.
One line each — do not over-explain.

---

## Output Format

Report only failures and notable findings. If everything passes, output:
```
[env-preflight] OK — cwd: /path/to/repo | git: connected | db: <VAR names or none> | sandbox: <on/off>
```

If anything fails, output each issue on its own line prefixed with `[env-preflight] WARN:` or `[env-preflight] FAIL:`.

---

## Anti-Patterns

1. Do NOT fix git auth — report and stop.
2. Do NOT print raw connection strings.
3. Do NOT run this after every prompt — SessionStart only (or explicit user request).
4. Do NOT block the session on warnings — only hard FAIL (e.g., no git repo at all) should stop work.
