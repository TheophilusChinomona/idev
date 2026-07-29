#!/usr/bin/env bash
# run_skillopt.sh — One-command SkillOpt benchmark for any idev skill.
#
# Usage:
#   benchmarks/run_skillopt.sh <skill-path> [--optimize] [--split test] [--model gpt-5.4]
#
# Examples:
#   benchmarks/run_skillopt.sh skills/branch-sync/SKILL.md
#   benchmarks/run_skillopt.sh skills/build-check/SKILL.md --optimize
#   benchmarks/run_skillopt.sh skills/db-preflight/SKILL.md --split val
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
REPO_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"
cd "$REPO_ROOT"

# ── Parse arguments ──────────────────────────────────────────────────────────
SKILL_PATH=""
OPTIMIZE=false
SPLIT="test"
MODEL="gpt-5.4"

while [[ $# -gt 0 ]]; do
  case $1 in
    --optimize) OPTIMIZE=true; shift ;;
    --split) SPLIT="$2"; shift 2 ;;
    --model) MODEL="$2"; shift 2 ;;
    -*) echo "Unknown option: $1" >&2; exit 1 ;;
    *) SKILL_PATH="$1"; shift ;;
  esac
done

if [[ -z "$SKILL_PATH" ]]; then
  echo "Usage: $0 <skill-path> [--optimize] [--split train|val|test] [--model MODEL]" >&2
  exit 1
fi

if [[ ! -f "$SKILL_PATH" ]]; then
  echo "Error: Skill file not found: $SKILL_PATH" >&2
  exit 1
fi

# ── Derive skill name from path ──────────────────────────────────────────────
SKILL_NAME="$(basename "$(dirname "$SKILL_PATH")")"
echo "╔══════════════════════════════════════════════════════════╗"
echo "║  SkillOpt Benchmark: $SKILL_NAME"
echo "║  Skill: $SKILL_PATH"
echo "║  Model: $MODEL | Split: $SPLIT"
echo "╚══════════════════════════════════════════════════════════╝"
echo

# ── Check prerequisites ──────────────────────────────────────────────────────
echo "▶ Checking prerequisites..."
if ! command -v skillopt-eval &>/dev/null; then
  echo "  ✗ skillopt not installed. Installing..."
  pip install --break-system-packages skillopt 2>&1 | tail -3
fi

if ! command -v codex &>/dev/null; then
  echo "  ✗ codex CLI not found. Please install: npm install -g @openai/codex" >&2
  exit 1
fi

# Check auth — either via auth.json file or ChatGPT tokens
if [[ ! -f ~/.codex/auth.json ]] && ! codex doctor 2>&1 | grep -q "ChatGPT tokens.*true"; then
  echo "  ✗ codex not authenticated. Run: codex login" >&2
  exit 1
fi

echo "  ✓ skillopt installed"
echo "  ✓ codex CLI found"
echo "  ✓ codex authenticated"
echo

# ── Step 1: Generate scenarios ───────────────────────────────────────────────
echo "▶ Step 1: Generating test scenarios..."
python3 "$SCRIPT_DIR/generate_scenarios.py" "$SKILL_PATH" --out-dir "benchmarks/$SKILL_NAME" 2>&1
echo

# ── Step 2: Set up benchmark ────────────────────────────────────────────────
echo "▶ Step 2: Setting up benchmark..."
python3 "$SCRIPT_DIR/setup_benchmark.py" "$SKILL_NAME" --skill-path "$SKILL_PATH" --model "$MODEL" --out-dir "benchmarks/$SKILL_NAME" 2>&1
echo

# ── Step 3: Copy adapter/evaluator/rollout to skillopt envs ──────────────────
echo "▶ Step 3: Installing adapter into SkillOpt..."
SKILLOPT_DIR="$(python3 -c 'import skillopt, os; print(os.path.dirname(skillopt.__file__))')"
SKILLOPT_ENVS="$SKILLOPT_DIR/envs"
SKILLOPT_SCRIPTS="$SKILLOPT_DIR/../scripts"
PYTHON_MODULE="$(echo "$SKILL_NAME" | sed 's/-/_/g')"

# Copy adapter files
mkdir -p "$SKILLOPT_ENVS/$PYTHON_MODULE"
cp "$SCRIPT_DIR/branch-sync/evaluator.py" "$SKILLOPT_ENVS/$PYTHON_MODULE/" 2>/dev/null || true
cp "$SCRIPT_DIR/branch-sync/dataloader.py" "$SKILLOPT_ENVS/$PYTHON_MODULE/" 2>/dev/null || true
cp "$SCRIPT_DIR/branch-sync/adapter.py" "$SKILLOPT_ENVS/$PYTHON_MODULE/" 2>/dev/null || true
cp "$SCRIPT_DIR/branch-sync/rollout.py" "$SKILLOPT_ENVS/$PYTHON_MODULE/" 2>/dev/null || true
touch "$SKILLOPT_ENVS/$PYTHON_MODULE/__init__.py"
echo "  ✓ Files copied to $SKILLOPT_ENVS/$PYTHON_MODULE/"

# Generate adapter class name from module name (CamelCase)
CLASS_NAME="$(echo "$PYTHON_MODULE" | sed 's/_\(.\)/\U\1/g; s/^./\U&/')Adapter"

# Register adapter in eval_only.py and train.py
for script in eval_only.py train.py; do
  SCRIPT_FILE="$SKILLOPT_SCRIPTS/$script"
  if [[ -f "$SCRIPT_FILE" ]] && ! grep -q "\"${SKILL_NAME}\"" "$SCRIPT_FILE" 2>/dev/null; then
    # Find the line before 'def get_adapter' and insert registration
    sed -i "/^def get_adapter/a\\
    try:\\
        from skillopt.envs.${PYTHON_MODULE}.adapter import ${CLASS_NAME}\\
        _ENV_REGISTRY[\"${SKILL_NAME}\"] = ${CLASS_NAME}\\
    except ImportError:\\
        pass" "$SCRIPT_FILE" 2>/dev/null || true
  fi
done
echo "  ✓ Adapter registered"
echo

# ── Step 4: Run evaluation ───────────────────────────────────────────────────
echo "▶ Step 4: Running evaluation with Codex ($MODEL)..."
echo "  This may take a few minutes..."
echo

skillopt-eval \
  --config "benchmarks/$SKILL_NAME/config.yaml" \
  --skill "$SKILL_PATH" \
  --backend codex_exec \
  --target_model "$MODEL" \
  --split "$SPLIT" \
  --env "$SKILL_NAME" 2>&1

echo

# ── Step 5: Optionally optimize ──────────────────────────────────────────────
if [[ "$OPTIMIZE" == "true" ]]; then
  echo "▶ Step 5: Optimizing skill with SkillOpt training loop..."
  if [[ -z "${OPENAI_API_KEY:-}" ]]; then
    echo "  ✗ OPENAI_API_KEY not set. Cannot run optimizer." >&2
    echo "  Set it with: export OPENAI_API_KEY=sk-..." >&2
    echo "  Or skip optimization and use the evaluation results." >&2
  else
    skillopt-train \
      --config "benchmarks/$SKILL_NAME/config.yaml" \
      --backend codex_exec \
      --target_model "$MODEL" \
      --optimizer_backend openai_chat \
      --optimizer_model gpt-4o \
      --split train 2>&1

    if [[ -f "benchmarks/$SKILL_NAME/skills/best_skill.md" ]]; then
      echo
      echo "  ✓ Optimized skill saved to: benchmarks/$SKILL_NAME/skills/best_skill.md"
      echo "  Review it before adopting:"
      echo "    diff $SKILL_PATH benchmarks/$SKILL_NAME/skills/best_skill.md"
    fi
  fi
fi

echo
echo "╔══════════════════════════════════════════════════════════╗"
echo "║  Done! Results saved to: outputs/eval_${SKILL_NAME}_*/  ║"
echo "╚══════════════════════════════════════════════════════════╝"
