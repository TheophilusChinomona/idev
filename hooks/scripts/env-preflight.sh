#!/bin/bash
# idev env-preflight hook — runs at SessionStart to catch environment problems
# early: wrong cwd, expired git auth, missing DB env vars, sandbox state.
# Silent on pass; prints [env-preflight] lines on warnings or failures.

PROJECT_DIR="${CLAUDE_PROJECT_DIR:-.}"
PROJECT_DIR="${PROJECT_DIR//\\//}"

PASS=1
ISSUES=()

# ── Phase 1: Working directory ────────────────────────────────────────────────
REPO_ROOT=$(git -C "$PROJECT_DIR" rev-parse --show-toplevel 2>/dev/null)
if [ -z "$REPO_ROOT" ]; then
  echo "[env-preflight] FAIL: Not inside a git repository (cwd: $(pwd)). Verify the project directory."
  exit 0
fi

CWD=$(pwd)
if [ "$CWD" != "$REPO_ROOT" ]; then
  cd "$REPO_ROOT" || true
  echo "[env-preflight] WARN: cwd was '$CWD', corrected to '$REPO_ROOT'."
fi

# ── Phase 2: Git auth ─────────────────────────────────────────────────────────
GIT_AUTH=$(git ls-remote --exit-code origin HEAD 2>&1)
GIT_EXIT=$?
REMOTE=$(git remote get-url origin 2>/dev/null | sed 's|//[^@]*@|//***@|g')

if [ $GIT_EXIT -ne 0 ]; then
  ISSUES+=("[env-preflight] WARN: git auth failed for '$REMOTE'. Push/PR will require credentials.")
  PASS=0
fi

# ── Phase 3: DB env vars ──────────────────────────────────────────────────────
DB_VARS_FOUND=""
for VAR in DATABASE_URL DB_URL CONNECTION_STRING DB_HOST DB_SERVER \
           POSTGRES_URL MYSQL_URL MONGO_URL REDIS_URL \
           "ConnectionStrings__DefaultConnection"; do
  VAL="${!VAR:-}"
  if [ -n "$VAL" ]; then
    MASKED=$(echo "$VAL" | sed 's|//[^:]*:[^@]*@|//***:***@|g' | cut -c1-80)
    DB_VARS_FOUND="$DB_VARS_FOUND $VAR"
  fi
done

# ── Phase 4: Sandbox state ────────────────────────────────────────────────────
SANDBOX="${CLAUDE_SANDBOX_ENABLED:-unknown}"

# ── Output ────────────────────────────────────────────────────────────────────
DB_REPORT="${DB_VARS_FOUND:-none}"
if [ $PASS -eq 1 ]; then
  echo "[env-preflight] OK — cwd: $REPO_ROOT | git: connected | db:$DB_REPORT | sandbox: $SANDBOX"
else
  for ISSUE in "${ISSUES[@]}"; do
    echo "$ISSUE"
  done
  echo "[env-preflight] INFO — cwd: $REPO_ROOT | db:$DB_REPORT | sandbox: $SANDBOX"
fi

exit 0
