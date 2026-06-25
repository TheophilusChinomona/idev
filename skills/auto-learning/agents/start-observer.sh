#!/bin/bash
# Continuous Learning v2 - Observer Agent Launcher
#
# Starts the background observer agent that analyzes observations
# and creates instincts. Uses Haiku model for cost efficiency.
#
# Usage:
#   start-observer.sh        # Start observer in background
#   start-observer.sh stop   # Stop running observer
#   start-observer.sh status # Check if observer is running

set -e

CONFIG_DIR="${HOME}/.claude/homunculus"
PID_FILE="${CONFIG_DIR}/.observer.pid"
LOG_FILE="${CONFIG_DIR}/observer.log"
OBSERVATIONS_FILE="${CONFIG_DIR}/observations.jsonl"
INSTINCTS_DIR="${CONFIG_DIR}/instincts/personal"
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
PLUGIN_CONFIG="${SCRIPT_DIR}/../config.json"

# Minimum observations before an analysis run (from config.json, default 20)
MIN_OBS=$(python3 -c "import json,sys; print(int(json.load(open(sys.argv[1]))['observer']['min_observations_to_analyze']))" "$PLUGIN_CONFIG" 2>/dev/null || echo 20)

mkdir -p "$CONFIG_DIR"

case "${1:-start}" in
  stop)
    if [ -f "$PID_FILE" ]; then
      pid=$(cat "$PID_FILE")
      if kill -0 "$pid" 2>/dev/null; then
        echo "Stopping observer (PID: $pid)..."
        kill "$pid"
        rm -f "$PID_FILE"
        echo "Observer stopped."
      else
        echo "Observer not running (stale PID file)."
        rm -f "$PID_FILE"
      fi
    else
      echo "Observer not running."
    fi
    exit 0
    ;;

  status)
    if [ -f "$PID_FILE" ]; then
      pid=$(cat "$PID_FILE")
      if kill -0 "$pid" 2>/dev/null; then
        echo "Observer is running (PID: $pid)"
        echo "Log: $LOG_FILE"
        echo "Observations: $(wc -l < "$OBSERVATIONS_FILE" 2>/dev/null || echo 0) lines"
        exit 0
      else
        echo "Observer not running (stale PID file)"
        rm -f "$PID_FILE"
        exit 1
      fi
    else
      echo "Observer not running"
      exit 1
    fi
    ;;

  start)
    # Check if already running
    if [ -f "$PID_FILE" ]; then
      pid=$(cat "$PID_FILE")
      if kill -0 "$pid" 2>/dev/null; then
        echo "Observer already running (PID: $pid)"
        exit 0
      fi
      rm -f "$PID_FILE"
    fi

    echo "Starting observer agent..."

    # The observer loop
    (
      analyze_observations() {
        # Only analyze if we have enough observations
        obs_count=$(wc -l < "$OBSERVATIONS_FILE" 2>/dev/null || echo 0)
        if [ "$obs_count" -lt "$MIN_OBS" ]; then
          return 0
        fi

        echo "[$(date)] Analyzing $obs_count observations..." >> "$LOG_FILE"

        # Headless `claude --print` cannot write files; ask it to OUTPUT the
        # instinct markdown on stdout and write the file ourselves.
        if ! command -v claude > /dev/null 2>&1; then
          echo "[$(date)] 'claude' CLI not found; skipping analysis, keeping observations." >> "$LOG_FILE"
          return 0
        fi

        # Analyze a bounded tail, not the whole file. These observation lines
        # are multi-KB each; feeding the entire (growing) file makes `claude`
        # exhaust its turn budget just reading it and every run fails. A small
        # recent sample is enough to spot recurring patterns.
        local sample_file
        sample_file=$(mktemp)
        tail -n 50 "$OBSERVATIONS_FILE" > "$sample_file"

        local analysis_output
        if ! analysis_output=$(claude --model haiku --max-turns 6 --print \
          "Read $sample_file and identify recurring patterns. If you find a pattern with 3+ occurrences, output ONE instinct as markdown to stdout, in exactly this format: a YAML frontmatter block delimited by '---' lines containing id, trigger (quoted), confidence (0.3-0.9), domain, and source: session-observation; followed by a markdown body with '## Action' and '## Evidence' sections. Output ONLY the instinct markdown — no preamble, no code fences. Do NOT attempt to write any files. If there is no clear repeated pattern, output nothing. Be conservative." \
          2>> "$LOG_FILE"); then
          rm -f "$sample_file"
          echo "[$(date)] Analysis run failed; keeping observations for retry." >> "$LOG_FILE"
          return 0
        fi
        rm -f "$sample_file"

        # Only persist output that looks like an instinct (has frontmatter)
        if [ -n "$analysis_output" ] && printf '%s\n' "$analysis_output" | grep -q '^---'; then
          mkdir -p "$INSTINCTS_DIR"
          instinct_file="${INSTINCTS_DIR}/instinct-$(date +%Y%m%d-%H%M%S).md"
          printf '%s\n' "$analysis_output" > "$instinct_file"
          echo "[$(date)] Created instinct: $instinct_file" >> "$LOG_FILE"

          # Archive processed observations only after a successful analysis
          # that produced output — never throw data away on failure.
          if [ -f "$OBSERVATIONS_FILE" ]; then
            archive_dir="${CONFIG_DIR}/observations.archive"
            mkdir -p "$archive_dir"
            mv "$OBSERVATIONS_FILE" "$archive_dir/processed-$(date +%Y%m%d-%H%M%S).jsonl"
            touch "$OBSERVATIONS_FILE"
          fi
        else
          echo "[$(date)] No instinct produced; keeping observations." >> "$LOG_FILE"
        fi
      }

      # Register traps before the loop so they are honored from the start.
      trap 'rm -f "$PID_FILE"; exit 0' TERM INT
      # Handle SIGUSR1 for on-demand analysis
      trap 'analyze_observations' USR1

      # Record the SUBSHELL's own PID ($BASHPID), not the parent script's
      # ($$). The parent exits right after launching this loop, so writing $$
      # would leave the PID file pointing at a dead process — breaking
      # stop/status/USR1 and letting orphaned loops accumulate.
      echo "$BASHPID" > "$PID_FILE"
      echo "[$(date)] Observer started (PID: $BASHPID, threshold: $MIN_OBS observations)" >> "$LOG_FILE"

      while true; do
        # Check every 5 minutes. Run sleep in the background and `wait` on it
        # so signal traps (USR1/TERM) fire promptly instead of being deferred
        # until the sleep finishes.
        sleep 300 &
        wait $! || true

        analyze_observations
      done
    ) &

    disown

    # Wait a moment for PID file
    sleep 1

    if [ -f "$PID_FILE" ]; then
      echo "Observer started (PID: $(cat "$PID_FILE"))"
      echo "Log: $LOG_FILE"
    else
      echo "Failed to start observer"
      exit 1
    fi
    ;;

  *)
    echo "Usage: $0 {start|stop|status}"
    exit 1
    ;;
esac
