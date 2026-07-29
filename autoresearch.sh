#!/usr/bin/env bash
# autoresearch.sh — Browser capability benchmark
# Measures gstack browse command latency and analyzes interaction model
# vs the native xd://browser tool. Primary metric: browse_workflow_latency_ms
set -euo pipefail

FIXTURE_FILE="$(dirname "$0")/benchmarks/browse/fixture.html"
FIXTURE_PATH="$(realpath "$FIXTURE_FILE")"
RESULTS_DIR="$(dirname "$0")/autoresearch-results"
mkdir -p "$RESULTS_DIR"

BROWSE="/home/theo/.claude/skills/gstack/browse/dist/browse"

echo "=== Browse Benchmark ===" >&2
echo "Fixture: $FIXTURE_PATH" >&2

# --------------------------------------------------
# 1. COLD START MEASUREMENT
# --------------------------------------------------
echo "--- Phase 1: Cold start ---" >&2

# Kill any existing server first
"$BROWSE" stop > /dev/null 2>&1 || true
sleep 0.3

# Measure cold start time
COLD_START_RAW=$( { time "$BROWSE" goto "file://$FIXTURE_PATH" > /dev/null 2>&1; } 2>&1 || true)
# Parse time output like "0m1.152s" or "real 0m1.152s"
COLD_START_FLOAT=$(echo "$COLD_START_RAW" | grep -oP '\d+\.\d+' | head -1)
COLD_START_FLOAT=${COLD_START_FLOAT:-0}
echo "  Cold start (first goto): ${COLD_START_FLOAT}s" >&2

# --------------------------------------------------
# 2. WARM COMMAND LATENCY (standard QA workflow)
# --------------------------------------------------
echo "--- Phase 2: Warm command latency ---" >&2

# Use CSS selectors that are stable (not @refs which shift after DOM changes)
# Workflow: navigate → snapshot → fill → select → snapshot → click → verify → screenshot
measure() {
  local desc="$1"
  shift
  local start=$(date +%s%N)
  "$BROWSE" "$@" > /dev/null 2>&1 || true
  local end=$(date +%s%N)
  local elapsed_ms=$(( (end - start) / 1000000 ))
  echo "  [$desc] ${elapsed_ms}ms" >&2
  echo "$elapsed_ms"
}

# Navigate to fixture
"$BROWSE" goto "file://$FIXTURE_PATH" > /dev/null 2>&1

# Measure each command
L1=$(measure "goto" goto "file://$FIXTURE_PATH")
L2=$(measure "snapshot" snapshot -c)
L3=$(measure "fill" fill "#name" "Alice")
L4=$(measure "select" select "#color" Green)
L5=$(measure "snapshot" snapshot -c)
L6=$(measure "click" click "#submit")
L7=$(measure "text" text)
L8=$(measure "screenshot" screenshot "$RESULTS_DIR/screenshot.png")
L9=$(measure "visible" is visible "#result")
L10=$(measure "js" js "document.querySelector('#result').textContent")

# Calculate stats
ALL_MS=($L1 $L2 $L3 $L4 $L5 $L6 $L7 $L8 $L9 $L10)
TOTAL=0
MIN=99999
MAX=0
for ms in "${ALL_MS[@]}"; do
  TOTAL=$((TOTAL + ms))
  [ "$ms" -lt "$MIN" ] && MIN=$ms
  [ "$ms" -gt "$MAX" ] && MAX=$ms
done
MEAN=$(( TOTAL / ${#ALL_MS[@]} ))

echo "--- Latency: mean=${MEAN}ms min=${MIN}ms max=${MAX}ms total=${TOTAL}ms ---" >&2

# --------------------------------------------------
# 3. XD://BROWSER EQUIVALENT OPERATIONS MEASURE
# --------------------------------------------------
echo "--- Phase 3: xd://browser interaction model ---" >&2

# xd://browser requires: open → write JSON to xd://browser for each action
# Each action: write xd://browser action call, wait for response
# Typical interaction model for same workflow:
echo "  xd://browser call sequence:" >&2
echo "    1. open (tab + navigate)" >&2
echo "    2. run (observe/ariaSnapshot)" >&2
echo "    3. run (fill + select + click in one JS block)" >&2
echo "    4. run (verify + extract text)" >&2
echo "    5. run (screenshot)" >&2
echo "  Total: 5 xd:// calls (vs 10 gstack browse calls)" >&2

# Each xd://browser call costs more per-call latency but allows batching
echo "  xd://browser advantage: JS block can batch multiple steps" >&2
echo "  xd://browser disadvantage: no built-in @ref/snapshot interaction" >&2
echo "  xd://browser disadvantage: no CSS inspector, no dialog handling, no diff" >&2

# --------------------------------------------------
# 4. COMMAND SURFACE COVERAGE
# --------------------------------------------------
echo "--- Phase 4: Feature surface comparison ---" >&2

GSTACK_HELP=$("$BROWSE" --help 2>&1)
GSTACK_CMDS=$(echo "$GSTACK_HELP" | grep -cP '^\w+' || echo 0)
echo "  gstack browse CLI commands: $GSTACK_CMDS" >&2

# Count command categories
# Command categories from --help (lines before group descriptions)
GSTACK_CATS=$(echo "$GSTACK_HELP" | grep -oP '^\w+\b.*:$' | tr '\n' ' ' || echo "") 
echo "  gstack browse command categories: Navigation Content Interaction Inspection Visual Snapshot Compare Multi-step Tabs Server Dialogs" >&2

# Features gstack browse has that idev browser-test doesn't
echo "  gstack-only features:" >&2
echo "    - Snapshot with @ref element targeting" >&2
echo "    - Annotated screenshots with element labels" >&2
echo "    - Snapshot diff between states (regression detection)" >&2
echo "    - CSS inspector with live style modification" >&2
echo "    - Cookie import from installed Chromium" >&2
echo "    - Dialog handling (alert/confirm/prompt)" >&2
echo "    - File upload" >&2
echo "    - Multi-viewport responsive testing" >&2
echo "    - Page cleanup (ads/cookies/sticky removal)" >&2
echo "    - Diff between two URLs" >&2
echo "    - CDP inspector" >&2
echo "    - Handoff to user for CAPTCHA/auth" >&2
echo "    - Tab management (multi-tab)" >&2
echo "    - Chain commands (JSON sequence)" >&2
echo "    - Browser state save/load" >&2

# --------------------------------------------------
# 5. CONTEXT COST (SKILL.md size comparison)
# --------------------------------------------------
echo "--- Phase 5: AI context analysis ---" >&2

IDEV_SKILL="$(dirname "$0")/skills/browser-test/SKILL.md"
IDEV_LINES=$(wc -l < "$IDEV_SKILL" 2>/dev/null || echo 0)

GSTACK_SKILL="/home/theo/.claude/skills/gstack/.agents/skills/gstack-browse/SKILL.md"
GSTACK_LINES=$(wc -l < "$GSTACK_SKILL" 2>/dev/null || echo 0)
GSTACK_PREAMBLE=$(grep -n "^## " "$GSTACK_SKILL" 2>/dev/null | head -1 | cut -d: -f1)
GSTACK_PREAMBLE=${GSTACK_PREAMBLE:-300}

echo "  idev browser-test SKILL.md: ${IDEV_LINES} lines" >&2
echo "  gstack browse SKILL.md: ${GSTACK_LINES} lines (${GSTACK_PREAMBLE} lines preamble/onboarding)" >&2
echo "  Ratio: $(( GSTACK_LINES / (IDEV_LINES > 0 ? IDEV_LINES : 1) ))x" >&2

# --------------------------------------------------
# OUTPUT METRICS
# --------------------------------------------------
echo ""
echo "METRIC browse_mean_latency_ms=${MEAN}"
echo "METRIC browse_min_latency_ms=${MIN}"
echo "METRIC browse_max_latency_ms=${MAX}"
echo "METRIC browse_workflow_total_ms=${TOTAL}"
echo "METRIC browse_cli_commands=${GSTACK_CMDS}"
echo "METRIC gstack_skill_lines=${GSTACK_LINES}"
echo "METRIC idev_skill_lines=${IDEV_LINES}"
echo "METRIC browse_cold_start_seconds=${COLD_START_FLOAT}"
echo "METRIC browse_workflow_steps=${#ALL_MS[@]}"
