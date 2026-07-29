#!/usr/bin/env bash
# autoresearch.sh — Browser capability benchmark
# Measures gstack browse command latency and compares all idev browser tools
# Primary metric: browse_mean_latency_ms (gstack browse command latency)
set -euo pipefail

FIXTURE_FILE="$(dirname "$0")/benchmarks/browse/fixture.html"
FIXTURE_PATH="$(realpath "$FIXTURE_FILE")"
RESULTS_DIR="$(dirname "$0")/autoresearch-results"
mkdir -p "$RESULTS_DIR"

BROWSE="/home/theo/.claude/skills/gstack/browse/dist/browse"

echo "=== Browse Benchmark ===" >&2
echo "Fixture: $FIXTURE_PATH" >&2

# --------------------------------------------------
# 1. GSTACK BROWSE COLD START
# --------------------------------------------------
echo "--- Phase 1: gstack browse cold start ---" >&2

"$BROWSE" stop > /dev/null 2>&1 || true
sleep 0.3

COLD_START_RAW=$( { time "$BROWSE" goto "file://$FIXTURE_PATH" > /dev/null 2>&1; } 2>&1 || true)
COLD_START_FLOAT=$(echo "$COLD_START_RAW" | grep -oP '\d+\.\d+' | head -1)
COLD_START_FLOAT=${COLD_START_FLOAT:-0}
echo "  Cold start (first goto): ${COLD_START_FLOAT}s" >&2

# --------------------------------------------------
# 2. GSTACK BROWSE WARM COMMAND LATENCY
# --------------------------------------------------
echo "--- Phase 2: gstack browse warm latency ---" >&2

measure() {
  local desc="$1"; shift
  local start=$(date +%s%N)
  "$BROWSE" "$@" > /dev/null 2>&1 || true
  local end=$(date +%s%N)
  local elapsed_ms=$(( (end - start) / 1000000 ))
  echo "  [$desc] ${elapsed_ms}ms" >&2
  echo "$elapsed_ms"
}

"$BROWSE" goto "file://$FIXTURE_PATH" > /dev/null 2>&1

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

ALL_MS=($L1 $L2 $L3 $L4 $L5 $L6 $L7 $L8 $L9 $L10)
TOTAL=0; MIN=99999; MAX=0
for ms in "${ALL_MS[@]}"; do
  TOTAL=$((TOTAL + ms))
  [ "$ms" -lt "$MIN" ] && MIN=$ms
  [ "$ms" -gt "$MAX" ] && MAX=$ms
done
MEAN=$(( TOTAL / ${#ALL_MS[@]} ))
echo "--- Latency: mean=${MEAN}ms min=${MIN}ms max=${MAX}ms total=${TOTAL}ms ---" >&2

# --------------------------------------------------
# 3. SKILL COMPARISON (context cost / capability)
# --------------------------------------------------
echo "--- Phase 3: Skill context comparison ---" >&2

# Files to compare
GSTACK_SKILL="/home/theo/.claude/skills/gstack/.agents/skills/gstack-browse/SKILL.md"
IDEV_BTEST=$(readlink -f "$(dirname "$0")/skills/browser-test/SKILL.md")
IDEV_BROWSE=$(readlink -f "$(dirname "$0")/skills/browse/SKILL.md")

for f in "$GSTACK_SKILL" "$IDEV_BTEST" "$IDEV_BROWSE"; do
  [ -f "$f" ] && echo "  exists: $f" >&2 || echo "  MISSING: $f" >&2
done

# Line counts
GSTACK_LINES=0; IDEV_BTEST_LINES=0; IDEV_BROWSE_LINES=0
[ -f "$GSTACK_SKILL" ] && GSTACK_LINES=$(wc -l < "$GSTACK_SKILL")
[ -f "$IDEV_BTEST" ] && IDEV_BTEST_LINES=$(wc -l < "$IDEV_BTEST")
[ -f "$IDEV_BROWSE" ] && IDEV_BROWSE_LINES=$(wc -l < "$IDEV_BROWSE")

# Word counts
GSTACK_WORDS=0; IDEV_BTEST_WORDS=0; IDEV_BROWSE_WORDS=0
[ -f "$GSTACK_SKILL" ] && GSTACK_WORDS=$(wc -w < "$GSTACK_SKILL")
[ -f "$IDEV_BTEST" ] && IDEV_BTEST_WORDS=$(wc -w < "$IDEV_BTEST")
[ -f "$IDEV_BROWSE" ] && IDEV_BROWSE_WORDS=$(wc -w < "$IDEV_BROWSE")

echo "  gstack browse: ${GSTACK_LINES} lines, ${GSTACK_WORDS} words" >&2
echo "  idev browser-test: ${IDEV_BTEST_LINES} lines, ${IDEV_BTEST_WORDS} words" >&2
echo "  idev browse (new): ${IDEV_BROWSE_LINES} lines, ${IDEV_BROWSE_WORDS} words" >&2

# Context reduction ratio
if [ "$GSTACK_LINES" -gt 0 ] && [ "$IDEV_BROWSE_LINES" -gt 0 ]; then
  CONTEXT_RATIO=$(( (GSTACK_LINES - IDEV_BROWSE_LINES) * 100 / GSTACK_LINES ))
  echo "  Context saved: ${CONTEXT_RATIO}% fewer lines vs gstack" >&2
fi

# Count QA patterns in each skill
GSTACK_PATTERNS=$(grep -c "^## Pattern\|^### Pattern\|^### [0-9]" "$GSTACK_SKILL" 2>/dev/null || echo 0)
IDEV_BROWSE_PATTERNS=$(grep -c "^## Pattern" "$IDEV_BROWSE" 2>/dev/null || echo 0)

GSTACK_CMD_REFS=$(grep -c '`\$B' "$GSTACK_SKILL" 2>/dev/null || echo 0)
IDEV_BROWSE_CMD_REFS=$(grep -c '`\$B\|`tab\.' "$IDEV_BROWSE" 2>/dev/null || echo 0)

echo "  gstack browse patterns: ${GSTACK_PATTERNS} documented patterns" >&2
echo "  idev browse patterns: ${IDEV_BROWSE_PATTERNS} documented patterns" >&2

# Skill efficiency: patterns per 100 lines
if [ "$GSTACK_LINES" -gt 0 ] && [ "$IDEV_BROWSE_LINES" -gt 0 ]; then
  GSTACK_EFF=$(( GSTACK_PATTERNS * 100 / GSTACK_LINES ))
  IDEV_BROWSE_EFF=$(( IDEV_BROWSE_PATTERNS * 100 / IDEV_BROWSE_LINES ))
  echo "  Skill efficiency (patterns/100 lines):" >&2
  echo "    gstack: ${GSTACK_EFF}  idev-browse: ${IDEV_BROWSE_EFF}" >&2
fi

# --------------------------------------------------
# 4. COMMAND SURFACE COVERAGE
# --------------------------------------------------
echo "--- Phase 4: Feature coverage ---" >&2

GSTACK_HELP=$("$BROWSE" --help 2>&1)
GSTACK_CMDS=$(echo "$GSTACK_HELP" | grep -cP '^\w+' || echo 0)
echo "  gstack browse CLI commands: $GSTACK_CMDS" >&2

# Features covered by idev browse skill (xd://browser equivalents)
echo "  ibrowse patterns covers: xd://browser open/run/close, " >&2
echo "    tab.observe/ariaSnapshot, fill/click/select via refs," >&2
echo "    screenshot, extract, evaluate, waitFor, multi-tab" >&2
echo "    viewport, dialog-handling, full QA workflow" >&2

# Features NOT covered by ibrowse (gstack-only)
echo "  gstack-only (not in ibrowse): snapshot-diff, CSS inspector," >&2
echo "    annotated screenshots, cookie-import, page cleanup," >&2
echo "    URL diff, handoff, CDP, chain, state save/load, skill-run" >&2

# --------------------------------------------------
# OUTPUT METRICS
# --------------------------------------------------
echo ""
echo "METRIC browse_mean_latency_ms=${MEAN}"
echo "METRIC browse_min_latency_ms=${MIN}"
echo "METRIC browse_max_latency_ms=${MAX}"
echo "METRIC browse_workflow_total_ms=${TOTAL}"
echo "METRIC browse_cold_start_seconds=${COLD_START_FLOAT}"
echo "METRIC browse_cli_commands=${GSTACK_CMDS}"
echo "METRIC gstack_skill_lines=${GSTACK_LINES}"
echo "METRIC gstack_skill_words=${GSTACK_WORDS}"
echo "METRIC idev_browser_test_lines=${IDEV_BTEST_LINES}"
echo "METRIC idev_browse_lines=${IDEV_BROWSE_LINES}"
echo "METRIC idev_browse_words=${IDEV_BROWSE_WORDS}"
echo "METRIC idev_browse_patterns=${IDEV_BROWSE_PATTERNS}"
