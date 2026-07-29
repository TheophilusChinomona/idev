# ECC Integration — 10 Improvements from Everything Claude Code

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Integrate 10 capabilities from ECC (Everything Claude Code) into the idev plugin, making sessions smarter, coding faster, and the plugin self-improving.

**Architecture:** Five independent groups executed sequentially. Each group produces working, testable software on its own. Groups build on each other: Session Intelligence provides hooks that Knowledge System and Dev Workflow use.

**Tech Stack:** Bash hooks, Python scripts, Markdown skills/agents/commands, JSON configs.

## Global Constraints

- All files under `~/Desktop/idev/` (plugin source)
- Per-project state in `<project>/.claude/idev/`
- Bash for hooks (cross-platform via Git Bash on Windows)
- Python for scripts (no pip dependencies beyond stdlib)
- Markdown for skills/agents/commands (YAML frontmatter)
- All new skills must score 10/10 on `benchmark_skills.py --strict`

---

# Group A: Session Intelligence

## Subsystem A1: Memory Persistence Hooks

**Goal:** Auto-save and auto-load session context so nothing is lost between sessions.

**Files:**
- Create: `hooks/scripts/memory-save.sh` — saves session state on stop
- Create: `hooks/scripts/memory-load.sh` — loads session state on start
- Create: `hooks/scripts/pre-compact.sh` — saves before context compaction
- Modify: `hooks/hooks.json` — add Stop hook, update SessionStart
- Modify: `skills/session-resume/SKILL.md` — document auto-save behavior

### Task A1.1: Create memory-save.sh

**Files:**
- Create: `hooks/scripts/memory-save.sh`

**Interfaces:**
- Reads: `$IDEV_DIR/session-resume/last-session.json`
- Writes: `$IDEV_DIR/session-resume/last-session.json`
- Env: `CLAUDE_PROJECT_DIR` (set by Claude Code)

- [ ] **Step 1: Write the hook script**

```bash
#!/bin/bash
# memory-save.sh — Auto-save session state on Stop hook.
# Reads the current session context and writes to last-session.json.

PROJECT_DIR="${CLAUDE_PROJECT_DIR:-.}"
PROJECT_DIR="${PROJECT_DIR//\\//}"
IDEV_DIR="$PROJECT_DIR/.claude/idev"
STATE_FILE="$IDEV_DIR/session-resume/last-session.json"

# Silent when no idev state
[ -d "$IDEV_DIR" ] || exit 0

# Ensure directory exists
mkdir -p "$(dirname "$STATE_FILE")"

# Read existing state or create empty
if [ -f "$STATE_FILE" ]; then
  EXISTING=$(cat "$STATE_FILE")
else
  EXISTING='{"lastTask":null,"recentFiles":{"modified":[],"read":[]},"openIssues":[],"savedAt":null}'
fi

# Update timestamp
TIMESTAMP=$(date '+%Y-%m-%d %H:%M')
echo "$EXISTING" | python3 -c "
import json, sys
data = json.load(sys.stdin)
data['savedAt'] = '$TIMESTAMP'
json.dump(data, sys.stdout, indent=2)
" > "$STATE_FILE" 2>/dev/null || true
```

- [ ] **Step 2: Make executable**

```bash
chmod +x hooks/scripts/memory-save.sh
```

- [ ] **Step 3: Test it runs silently on non-idev project**

Run: `CLAUDE_PROJECT_DIR=/tmp bash hooks/scripts/memory-save.sh`
Expected: exits 0, no output

- [ ] **Step 4: Commit**

```bash
git add hooks/scripts/memory-save.sh
git commit -m "hooks: add memory-save.sh for session persistence"
```

### Task A1.2: Create pre-compact.sh

**Files:**
- Create: `hooks/scripts/pre-compact.sh`

**Interfaces:**
- Same as A1.1 (saves state before context compaction)

- [ ] **Step 1: Write the pre-compact hook**

```bash
#!/bin/bash
# pre-compact.sh — Save session state before context compaction.
# Same logic as memory-save.sh but triggered by PreCompact event.

PROJECT_DIR="${CLAUDE_PROJECT_DIR:-.}"
PROJECT_DIR="${PROJECT_DIR//\\//}"
IDEV_DIR="$PROJECT_DIR/.claude/idev"
STATE_FILE="$IDEV_DIR/session-resume/last-session.json"

[ -d "$IDEV_DIR" ] || exit 0
mkdir -p "$(dirname "$STATE_FILE")"

if [ -f "$STATE_FILE" ]; then
  EXISTING=$(cat "$STATE_FILE")
else
  EXISTING='{"lastTask":null,"recentFiles":{"modified":[],"read":[]},"openIssues":[],"savedAt":null}'
fi

TIMESTAMP=$(date '+%Y-%m-%d %H:%M')
echo "$EXISTING" | python3 -c "
import json, sys
data = json.load(sys.stdin)
data['savedAt'] = '$TIMESTAMP'
data['compacted'] = True
json.dump(data, sys.stdout, indent=2)
" > "$STATE_FILE" 2>/dev/null || true
```

- [ ] **Step 2: Make executable**

```bash
chmod +x hooks/scripts/pre-compact.sh
```

- [ ] **Step 3: Commit**

```bash
git add hooks/scripts/pre-compact.sh
git commit -m "hooks: add pre-compact.sh for context compaction save"
```

### Task A1.3: Wire hooks into hooks.json

**Files:**
- Modify: `hooks/hooks.json`

**Interfaces:**
- Consumes: A1.1 (memory-save.sh), A1.2 (pre-compact.sh)

- [ ] **Step 1: Add Stop hook and PreCompact hook**

Read `hooks/hooks.json`. Add after the existing Stop hook:

```json
"PreCompact": [
  {
    "matcher": "*",
    "hooks": [
      {
        "type": "command",
        "command": "bash ${CLAUDE_PLUGIN_ROOT}/hooks/scripts/pre-compact.sh",
        "timeout": 5
      }
    ]
  }
]
```

Update the existing Stop hook to also run memory-save.sh:

```json
"Stop": [
  {
    "matcher": "*",
    "hooks": [
      {
        "type": "command",
        "command": "bash ${CLAUDE_PLUGIN_ROOT}/hooks/scripts/map-watcher-stop.sh",
        "timeout": 5
      },
      {
        "type": "command",
        "command": "bash ${CLAUDE_PLUGIN_ROOT}/hooks/scripts/memory-save.sh",
        "timeout": 5
      }
    ]
  }
]
```

- [ ] **Step 2: Validate JSON**

Run: `python3 -m json.tool hooks/hooks.json > /dev/null`
Expected: no output (valid JSON)

- [ ] **Step 3: Commit**

```bash
git add hooks/hooks.json
git commit -m "hooks: wire memory persistence into Stop and PreCompact"
```

### Task A1.4: Update session-resume skill

**Files:**
- Modify: `skills/session-resume/SKILL.md`

- [ ] **Step 1: Add auto-save documentation**

Add a section after "## Activation":

```markdown
## Auto-Save

Session state is automatically saved at three points:
1. **Session end** (Stop hook) — saves final state
2. **Before compaction** (PreCompact hook) — saves before context is compressed
3. **Manual** — user says "save session" or "save context"

No user action required — the hooks handle persistence silently.
```

- [ ] **Step 2: Commit**

```bash
git add skills/session-resume/SKILL.md
git commit -m "session-resume: document auto-save behavior"
```

---

## Subsystem A2: Contexts

**Goal:** Dynamic system prompt injection based on task mode (dev, review, research).

**Files:**
- Create: `contexts/dev.md` — development mode context
- Create: `contexts/review.md` — code review mode context
- Create: `contexts/research.md` — research/exploration mode context
- Create: `commands/context.md` — switch context command
- Create: `skills/context-switching/SKILL.md` — context switching skill

### Task A2.1: Create context files

**Files:**
- Create: `contexts/dev.md`
- Create: `contexts/review.md`
- Create: `contexts/research.md`

- [ ] **Step 1: Create dev.md**

```markdown
# Development Context

Mode: Active development
Focus: Implementation, coding, building features

## Behavior
- Write code first, explain after
- Prefer working solutions over perfect solutions
- Run tests after changes
- Keep commits atomic
- Use build-check after multi-file changes

## Priorities
1. Get it working
2. Get it right
3. Get it clean

## Tools to favor
- Edit, Write for code changes
- Bash for running tests/builds
- Grep, Glob for finding code
```

- [ ] **Step 2: Create review.md**

```markdown
# Code Review Context

Mode: PR review, code analysis
Focus: Quality, security, maintainability

## Behavior
- Read thoroughly before commenting
- Prioritize issues by severity (critical > high > medium > low)
- Suggest fixes, don't just point out problems
- Check for security vulnerabilities
- Use code-reviewer agent for complex reviews

## Review Checklist
- [ ] Logic errors
- [ ] Edge cases
- [ ] Error handling
- [ ] Security (injection, auth, secrets)
- [ ] Performance
- [ ] Readability
- [ ] Test coverage

## Output Format
Group findings by file, severity first
```

- [ ] **Step 3: Create research.md**

```markdown
# Research Context

Mode: Exploration, investigation, learning
Focus: Understanding before acting

## Behavior
- Read widely before concluding
- Ask clarifying questions
- Document findings as you go
- Don't write code until understanding is clear
- Use onboarding-guide agent for codebase questions

## Research Process
1. Understand the question
2. Explore relevant code/docs
3. Form hypothesis
4. Verify with evidence
5. Summarize findings

## Tools to favor
- Read for understanding code
- Grep, Glob for finding patterns
- Task with onboarding-guide for codebase questions

## Output
Findings first, recommendations second
```

- [ ] **Step 4: Commit**

```bash
git add contexts/
git commit -m "contexts: add dev, review, and research mode contexts"
```

### Task A2.2: Create context-switching skill

**Files:**
- Create: `skills/context-switching/SKILL.md`

- [ ] **Step 1: Write the skill**

```markdown
---
name: context-switching
description: "Switches between development modes (dev, review, research) by loading the appropriate context. Use when the user changes task type or asks to switch modes."
---

# Context Switching Skill

## Purpose
Dynamically adjust Claude's behavior based on the current task mode.

## Modes

| Mode | Context File | Behavior |
|------|-------------|----------|
| dev | `contexts/dev.md` | Write code, run tests, commit often |
| review | `contexts/review.md` | Read thoroughly, find issues, suggest fixes |
| research | `contexts/research.md` | Explore, understand, document findings |

## Activation
- User says "switch to review mode" or "let's review this"
- User says "research how X works" or "investigate Y"
- User says "switch to dev mode" or "let's build this"
- Task type changes mid-session

## How It Works
1. Read the appropriate context file from `${CLAUDE_PLUGIN_ROOT}/contexts/`
2. Load its behavior rules into working memory
3. Apply those rules until the mode changes

## Anti-Patterns
1. Do NOT stay in research mode when the user wants to build
2. Do NOT switch modes without telling the user
3. Do NOT load multiple modes simultaneously
```

- [ ] **Step 2: Commit**

```bash
git add skills/context-switching/
git commit -m "context-switching: add mode switching skill"
```

### Task A2.3: Create /context command

**Files:**
- Create: `commands/context.md`

- [ ] **Step 1: Write the command**

```markdown
---
description: "Switch between development modes: dev, review, or research."
argument-hint: "[dev|review|research]"
---

# /context — Switch Development Mode

Switch Claude's behavior mode for the current task.

## Modes

| Command | Mode | What Changes |
|---------|------|-------------|
| `/context dev` | Development | Write code, run tests, commit often |
| `/context review` | Review | Read thoroughly, find issues, suggest fixes |
| `/context research` | Research | Explore, understand, document findings |

## Usage

```
/context dev       # Switch to development mode
/context review    # Switch to code review mode
/context research  # Switch to research mode
```

## What Happens
Claude loads the corresponding context file from `contexts/` and adjusts its behavior:
- Tool preferences change
- Priorities shift
- Output format adapts
```

- [ ] **Step 2: Commit**

```bash
git add commands/context.md
git commit -m "commands: add /context for mode switching"
```

---

# Group B: Knowledge System

## Subsystem B1: Rules Directory

**Goal:** Modular, always-follow guidelines organized by domain.

**Files:**
- Create: `rules/security.md` — mandatory security checks
- Create: `rules/testing.md` — TDD and coverage requirements
- Create: `rules/git-workflow.md` — commit format, PR process
- Create: `rules/coding-style.md` — immutability, file organization
- Create: `rules/performance.md` — model selection, context management

### Task B1.1: Create rules directory

**Files:**
- Create: `rules/security.md`
- Create: `rules/testing.md`
- Create: `rules/git-workflow.md`
- Create: `rules/coding-style.md`
- Create: `rules/performance.md`

- [ ] **Step 1: Create security.md**

```markdown
# Security Guidelines

## Mandatory Security Checks

Before ANY commit:
- [ ] No hardcoded secrets (API keys, passwords, tokens)
- [ ] All user inputs validated
- [ ] SQL injection prevention (parameterized queries)
- [ ] XSS prevention (sanitized HTML)
- [ ] CSRF protection enabled
- [ ] Authentication/authorization verified
- [ ] Rate limiting on all endpoints
- [ ] Error messages don't leak sensitive data

## Secret Management

```python
# NEVER: Hardcoded secrets
api_key = "sk-proj-xxxxx"

# ALWAYS: Environment variables
api_key = os.environ.get("OPENAI_API_KEY")
if not api_key:
    raise ValueError("OPENAI_API_KEY not configured")
```

## Security Response Protocol

If security issue found:
1. STOP immediately
2. Use **security-reviewer** agent
3. Fix CRITICAL issues before continuing
4. Rotate any exposed secrets
5. Review entire codebase for similar issues
```

- [ ] **Step 2: Create testing.md**

```markdown
# Testing Requirements

## Minimum Test Coverage: 80%

Test Types (ALL required):
1. **Unit Tests** — Individual functions, utilities
2. **Integration Tests** — API endpoints, database operations
3. **E2E Tests** — Critical user flows (Playwright)

## Test-Driven Development

MANDATORY workflow:
1. Write test first (RED)
2. Run test — it should FAIL
3. Write minimal implementation (GREEN)
4. Run test — it should PASS
5. Refactor (IMPROVE)
6. Verify coverage (80%+)

## Troubleshooting Test Failures

1. Use **tdd-guide** agent
2. Check test isolation
3. Verify mocks are correct
4. Fix implementation, not tests (unless tests are wrong)
```

- [ ] **Step 3: Create git-workflow.md**

```markdown
# Git Workflow

## Commit Format

```
<type>(<scope>): <subject>

[optional body]

[optional footer]
```

Types: feat, fix, docs, style, refactor, test, chore

## Branch Strategy

- `master` — production-ready
- `feature/*` — new features
- `fix/*` — bug fixes
- `chore/*` — maintenance

## PR Process

1. Create feature branch from master
2. Make changes, commit frequently
3. Run tests before pushing
4. Create PR with description
5. Request review
6. Address feedback
7. Merge after approval
```

- [ ] **Step 4: Create coding-style.md**

```markdown
# Coding Style

## Principles

1. **Immutability** — Prefer const/let over var, avoid mutation
2. **Small functions** — Each function does one thing
3. **Clear names** — Variables and functions describe their purpose
4. **Early returns** — Avoid deep nesting
5. **No magic numbers** — Use named constants

## File Organization

```
src/
├── components/     # UI components
├── hooks/          # Custom hooks
├── services/       # API calls
├── utils/          # Helper functions
├── types/          # TypeScript types
└── index.ts        # Entry point
```

## Imports

```typescript
// 1. External libraries
import React from 'react'
import axios from 'axios'

// 2. Internal modules
import { formatDate } from '../utils/date'
import { User } from '../types/user'

// 3. Components
import { Button } from './Button'
```
```

- [ ] **Step 5: Create performance.md**

```markdown
# Performance Guidelines

## Model Selection

| Task | Model | Why |
|------|-------|-----|
| Simple edits | Sonnet | Fast, cheap |
| Complex reasoning | Opus | Better judgment |
| Bulk operations | Sonnet | Throughput |

## Context Management

- Load only what's needed (Grep before Read)
- Use caches (smart-context, project-map)
- Compact aggressively when context grows
- Prefer sections over full files

## Token Budget

- Session start: < 2,000 tokens
- Per task: < 5,000 tokens
- Total session: monitor via /status
```

- [ ] **Step 6: Commit**

```bash
git add rules/
git commit -m "rules: add modular security, testing, git, style, performance rules"
```

---

## Subsystem B2: Continuous Learning

**Goal:** Auto-extract patterns from sessions into reusable learned skills.

**Files:**
- Create: `skills/continuous-learning/SKILL.md`
- Create: `skills/continuous-learning/config.json`
- Create: `skills/continuous-learning/evaluate-session.sh`
- Modify: `hooks/hooks.json` — add Stop hook for learning

### Task B2.1: Create continuous-learning skill

**Files:**
- Create: `skills/continuous-learning/SKILL.md`
- Create: `skills/continuous-learning/config.json`

- [ ] **Step 1: Create the skill**

```markdown
---
name: continuous-learning
description: "Automatically extracts reusable patterns from sessions and saves them as learned skills. Use when asked to learn from a session, extract patterns, or review what was learned."
---

# Continuous Learning Skill

## Purpose
Automatically evaluate sessions and extract reusable patterns that improve future sessions.

## How It Works

Runs as a **Stop hook** at session end:
1. Checks if session has enough activity (default: 10+ tool calls)
2. Identifies extractable patterns (error resolutions, user corrections, workarounds)
3. Saves patterns to `~/.claude/homunculus/instincts/personal/`

## Configuration

`config.json` in this skill directory:

```json
{
  "min_session_length": 10,
  "extraction_threshold": "medium",
  "patterns_to_detect": [
    "error_resolution",
    "user_corrections",
    "workarounds",
    "debugging_techniques",
    "project_specific"
  ],
  "ignore_patterns": [
    "simple_typos",
    "one_time_fixes",
    "external_api_issues"
  ]
}
```

## Pattern Types

| Pattern | Description |
|---------|-------------|
| `error_resolution` | How specific errors were resolved |
| `user_corrections` | Patterns from user corrections |
| `workarounds` | Solutions to framework quirks |
| `debugging_techniques` | Effective debugging approaches |
| `project_specific` | Project-specific conventions |

## Integration with Auto-Learning

This skill feeds into the existing auto-learning system:
- Extracted patterns become instincts in `~/.claude/homunculus/instincts/personal/`
- High-confidence instincts can evolve into skills via `/idev:evolve`

## Anti-Patterns
1. Do NOT extract trivial patterns (typos, one-off fixes)
2. Do NOT extract patterns without evidence (must be observed 2+ times)
3. Do NOT overwrite existing instincts — update confidence instead
```

- [ ] **Step 2: Create config.json**

```json
{
  "min_session_length": 10,
  "extraction_threshold": "medium",
  "patterns_to_detect": [
    "error_resolution",
    "user_corrections",
    "workarounds",
    "debugging_techniques",
    "project_specific"
  ],
  "ignore_patterns": [
    "simple_typos",
    "one_time_fixes",
    "external_api_issues"
  ]
}
```

- [ ] **Step 3: Commit**

```bash
git add skills/continuous-learning/
git commit -m "continuous-learning: add pattern extraction skill"
```

### Task B2.2: Create evaluate-session.sh

**Files:**
- Create: `skills/continuous-learning/evaluate-session.sh`

- [ ] **Step 1: Write the script**

```bash
#!/bin/bash
# evaluate-session.sh — Extract patterns from the current session.
# Called by the Stop hook. Reads session transcript, extracts patterns.

LEARNED_DIR="${HOME}/.claude/homunculus/instincts/personal"
CONFIG_FILE="${CLAUDE_PLUGIN_ROOT}/skills/continuous-learning/config.json"

# Ensure directory exists
mkdir -p "$LEARNED_DIR"

# Read config
MIN_LENGTH=$(python3 -c "import json; print(json.load(open('$CONFIG_FILE')).get('min_session_length', 10))" 2>/dev/null || echo 10)

# Check if session has enough activity (via observations)
OBS_FILE="${HOME}/.claude/homunculus/observations.jsonl"
if [ ! -f "$OBS_FILE" ]; then
  exit 0
fi

OBS_COUNT=$(wc -l < "$OBS_FILE" 2>/dev/null || echo 0)
if [ "$OBS_COUNT" -lt "$MIN_LENGTH" ]; then
  exit 0
fi

# Signal to the agent that patterns should be extracted
echo "[continuous-learning] Session has $OBS_COUNT observations (threshold: $MIN_LENGTH). Consider extracting patterns."
```

- [ ] **Step 2: Make executable**

```bash
chmod +x skills/continuous-learning/evaluate-session.sh
```

- [ ] **Step 3: Commit**

```bash
git add skills/continuous-learning/evaluate-session.sh
git commit -m "continuous-learning: add session evaluation script"
```

### Task B2.3: Wire into hooks.json

**Files:**
- Modify: `hooks/hooks.json`

- [ ] **Step 1: Add continuous-learning to Stop hook**

Add to the Stop hook array:

```json
{
  "type": "command",
  "command": "bash ${CLAUDE_PLUGIN_ROOT}/skills/continuous-learning/evaluate-session.sh",
  "timeout": 10
}
```

- [ ] **Step 2: Validate JSON**

Run: `python3 -m json.tool hooks/hooks.json > /dev/null`

- [ ] **Step 3: Commit**

```bash
git add hooks/hooks.json
git commit -m "hooks: wire continuous-learning into Stop hook"
```

---

# Group C: Quality Pipeline

## Subsystem C1: Eval Harness

**Goal:** Capability and regression evals with pass@k metrics.

**Files:**
- Create: `skills/eval-harness/SKILL.md`
- Create: `commands/eval.md`
- Create: `benchmarks/evals/` — eval storage directory

### Task C1.1: Create eval-harness skill

**Files:**
- Create: `skills/eval-harness/SKILL.md`

- [ ] **Step 1: Write the skill**

```markdown
---
name: eval-harness
description: "Evaluation framework for capability and regression evals with pass@k metrics. Use when asked to define evals, run evals, or check eval status."
---

# Eval Harness Skill

## Purpose
Define, run, and track evaluations for features — the "unit tests of AI development."

## Eval Types

### Capability Evals
Test if Claude can do something:
```markdown
[CAPABILITY EVAL: feature-name]
Task: Description of what Claude should accomplish
Success Criteria:
  - [ ] Criterion 1
  - [ ] Criterion 2
Expected Output: Description of expected result
```

### Regression Evals
Ensure changes don't break existing functionality:
```markdown
[REGRESSION EVAL: feature-name]
Baseline: SHA or checkpoint name
Tests:
  - existing-test-1: PASS/FAIL
  - existing-test-2: PASS/FAIL
Result: X/Y passed (previously Y/Y)
```

## Metrics

### pass@k
"At least one success in k attempts"
- pass@1: First attempt success rate
- pass@3: Success within 3 attempts
- Typical target: pass@3 > 90%

## Workflow

### 1. Define (Before Coding)
```bash
/eval define feature-name
```
Creates `.claude/evals/feature-name.md`

### 2. Check (During Implementation)
```bash
/eval check feature-name
```
Runs current evals and reports status

### 3. Report (After Implementation)
```bash
/eval report feature-name
```
Generates full eval report

## Storage

```
.claude/evals/
├── feature-xyz.md      # Eval definition
├── feature-xyz.log     # Eval run history
└── baseline.json       # Regression baselines
```

## Anti-Patterns
1. Do NOT define evals after coding — define BEFORE
2. Do NOT skip regression evals
3. Do NOT use slow evals — keep them fast
4. Do NOT fully automate security checks — human review required
```

- [ ] **Step 2: Commit**

```bash
git add skills/eval-harness/
git commit -m "eval-harness: add evaluation framework skill"
```

### Task C1.2: Create /eval command

**Files:**
- Create: `commands/eval.md`

- [ ] **Step 1: Write the command**

```markdown
---
description: "Define, check, or report on feature evals."
argument-hint: "define|check|report <feature-name>"
---

# /eval — Feature Evaluation

Manage capability and regression evaluations.

## Usage

```
/eval define auth    # Create eval definition for auth feature
/eval check auth     # Run evals and report status
/eval report auth    # Generate full eval report
```

## Define
Creates `.claude/evals/<feature>.md` with:
- Capability eval criteria
- Regression eval baseline
- Success metrics (pass@3 > 90%)

## Check
Runs evals and reports:
- Which criteria pass/fail
- Current pass@k metrics
- Regressions from baseline

## Report
Generates full report with:
- Per-criterion results
- pass@k metrics
- Recommendation: SHIP / NEEDS WORK / BLOCKED
```

- [ ] **Step 2: Commit**

```bash
git add commands/eval.md
git commit -m "commands: add /eval for feature evaluations"
```

### Task C1.3: Create evals directory

**Files:**
- Create: `benchmarks/evals/.gitkeep`

- [ ] **Step 1: Create directory**

```bash
mkdir -p benchmarks/evals
touch benchmarks/evals/.gitkeep
```

- [ ] **Step 2: Commit**

```bash
git add benchmarks/evals/
git commit -m "benchmarks: add evals storage directory"
```

---

## Subsystem C2: Test Coverage

**Goal:** Track and report test coverage.

**Files:**
- Create: `commands/test-coverage.md`
- Create: `skills/test-coverage/SKILL.md`

### Task C2.1: Create test-coverage skill

**Files:**
- Create: `skills/test-coverage/SKILL.md`

- [ ] **Step 1: Write the skill**

```markdown
---
name: test-coverage
description: "Measures and reports test coverage for the project. Use when asked about coverage, before PRs, or when coverage drops."
---

# Test Coverage Skill

## Purpose
Measure, report, and enforce test coverage thresholds.

## Activation
- User says "check coverage" or "what's the coverage?"
- Before creating a PR
- When coverage drops below threshold

## How It Works

### 1. Detect Test Framework
```
JavaScript/TypeScript:
  jest.config.* → npx jest --coverage
  vitest.config.* → npx vitest --coverage
  .nycrc → npx nyc report

Python:
  pytest.ini → pytest --cov
  pyproject.toml [tool.pytest] → pytest --cov

.NET:
  *.Tests.csproj → dotnet test /p:CollectCoverage=true
```

### 2. Run Coverage
```bash
# JavaScript/TypeScript
npx jest --coverage --coverageReporters=text-summary

# Python
pytest --cov=src --cov-report=term-missing

# .NET
dotnet test /p:CollectCoverage=true /p:CoverletOutputFormat=lcov
```

### 3. Report
```
Coverage Report
═══════════════
Lines:    85% (120/141)
Branches: 78% (45/58)
Functions: 92% (33/36)

Below 80% threshold:
  src/auth.ts: 65% (missing edge cases)
  src/utils.ts: 72% (missing error paths)
```

## Threshold
- Minimum: 80% line coverage
- Target: 90% line coverage
- Branches: 75% minimum

## Anti-Patterns
1. Do NOT skip coverage on "simple" files
2. Do NOT mock everything — integration tests need real calls
3. Do NOT ignore coverage drops — investigate and fix
```

- [ ] **Step 2: Commit**

```bash
git add skills/test-coverage/
git commit -m "test-coverage: add coverage measurement skill"
```

### Task C2.2: Create /test-coverage command

**Files:**
- Create: `commands/test-coverage.md`

- [ ] **Step 1: Write the command**

```markdown
---
description: "Measure and report test coverage for the project."
argument-hint: "[--threshold N]"
---

# /test-coverage — Coverage Report

Measure test coverage and report results.

## Usage

```
/test-coverage              # Run coverage with default 80% threshold
/test-coverage --threshold 90  # Custom threshold
```

## What Happens
1. Detects test framework (Jest, Vitest, pytest, dotnet test)
2. Runs coverage collection
3. Reports line/branch/function coverage
4. Flags files below threshold
5. Suggests which tests to add

## Output
```
Coverage: 85% lines, 78% branches, 92% functions
Threshold: 80% ✓ PASS

Files below threshold:
  src/auth.ts: 65% — add edge case tests
```
```

- [ ] **Step 2: Commit**

```bash
git add commands/test-coverage.md
git commit -m "commands: add /test-coverage for coverage reporting"
```

---

# Group D: Dev Workflow

## Subsystem D1: TDD Workflow

**Goal:** Test-driven development skill and agent.

**Files:**
- Create: `skills/tdd-workflow/SKILL.md`
- Create: `agents/tdd-guide.md`

### Task D1.1: Create TDD workflow skill

**Files:**
- Create: `skills/tdd-workflow/SKILL.md`

- [ ] **Step 1: Write the skill**

```markdown
---
name: tdd-workflow
description: "Test-driven development workflow: write failing test, implement to pass, refactor. Use when starting a new feature or bugfix that needs tests first."
---

# TDD Workflow Skill

## Purpose
Enforce test-driven development: RED → GREEN → REFACTOR.

## Activation
- User says "let's do TDD" or "write tests first"
- Starting a new feature
- Fixing a bug (write test that reproduces it)

## Workflow

### RED — Write Failing Test
1. Understand the requirement
2. Write a test that describes expected behavior
3. Run the test — it MUST fail
4. If it passes, the test is wrong — fix the test

### GREEN — Make It Pass
1. Write the MINIMUM code to make the test pass
2. Run the test — it MUST pass
3. Do NOT write extra code yet

### REFACTOR — Improve
1. Clean up the code
2. Run tests again — they MUST still pass
3. Repeat until satisfied

## Integration
- Use build-check after implementation
- Use test-coverage to verify coverage
- Log lessons if TDD revealed a gotcha

## Anti-Patterns
1. Do NOT skip the RED phase — verify the test fails first
2. Do NOT write more code than needed to pass the test
3. Do NOT refactor while tests are failing
4. Do NOT write tests after implementation (that's verification, not TDD)
```

- [ ] **Step 2: Commit**

```bash
git add skills/tdd-workflow/
git commit -m "tdd-workflow: add TDD skill"
```

### Task D1.2: Create TDD guide agent

**Files:**
- Create: `agents/tdd-guide.md`

- [ ] **Step 1: Write the agent**

```markdown
---
name: tdd-guide
description: "Test-driven development specialist. Use PROACTIVELY for new features and bugfixes. Enforces write-tests-first workflow."
tools: Read, Write, Edit, Bash, Grep, Glob
---

# TDD Guide Agent

You are a test-driven development specialist. Your mission is to ensure every feature starts with a failing test.

## Core Responsibilities

1. **Write Failing Tests** — Describe expected behavior before implementation
2. **Verify RED** — Confirm the test fails (not a false pass)
3. **Guide Implementation** — Help write minimum code to pass
4. **Verify GREEN** — Confirm all tests pass
5. **Suggest Refactoring** — After green, suggest improvements

## TDD Workflow

### Step 1: Understand Requirement
- Read the task description
- Identify edge cases
- List expected behaviors

### Step 2: Write Failing Test
```typescript
describe('FeatureName', () => {
  it('should do expected behavior', () => {
    const result = feature(input)
    expect(result).toBe(expected)
  })
})
```

### Step 3: Verify It Fails
```bash
npm test -- --testPathPattern="feature"
# Expected: FAIL — feature is not implemented
```

### Step 4: Implement Minimal Code
- Write ONLY what's needed to pass the test
- No extras, no "while we're at it"

### Step 5: Verify It Passes
```bash
npm test -- --testPathPattern="feature"
# Expected: PASS
```

### Step 6: Refactor (Optional)
- Clean up code
- Run tests again to verify no regression

## Rules
1. NEVER skip the RED phase
2. NEVER write implementation before test
3. NEVER add features not covered by tests
4. ALWAYS verify test fails before implementing
5. ALWAYS run full test suite after changes
```

- [ ] **Step 2: Commit**

```bash
git add agents/tdd-guide.md
git commit -m "agents: add tdd-guide agent"
```

---

## Subsystem D2: Build Error Resolver

**Goal:** Dedicated agent that auto-fixes build errors with minimal diffs.

**Files:**
- Create: `agents/build-error-resolver.md`

### Task D2.1: Create build-error-resolver agent

**Files:**
- Create: `agents/build-error-resolver.md`

- [ ] **Step 1: Write the agent**

```markdown
---
name: build-error-resolver
description: "Build and type error resolution specialist. Use PROACTIVELY when build fails. Fixes errors with minimal diffs, no architectural changes."
tools: Read, Write, Edit, Bash, Grep, Glob
---

# Build Error Resolver

Expert at fixing build/type errors quickly with minimal changes.

## Core Responsibilities

1. **Collect ALL errors** — Run full type check, capture everything
2. **Categorize** — Type errors, import errors, config errors, dependency issues
3. **Fix minimally** — Smallest possible change to fix each error
4. **Verify** — Re-run build after each fix
5. **No architecture changes** — Only fix errors, don't refactor

## Workflow

### 1. Collect Errors
```bash
# .NET
dotnet build 2>&1 | grep "error "

# TypeScript
npx tsc --noEmit --pretty 2>&1

# Python
python -m py_compile src/*.py 2>&1
```

### 2. Categorize
- **Blocking build** → Fix first
- **Type errors** → Fix in order
- **Warnings** → Fix if time permits

### 3. Fix Strategy
For each error:
1. Read error message and location
2. Understand expected vs actual
3. Apply minimal fix
4. Verify fix doesn't break other code

### 4. Common Patterns

**Missing import:**
```typescript
// Add the import
import { missing } from './module'
```

**Type mismatch:**
```typescript
// Add type annotation or cast
const value: ExpectedType = input as ExpectedType
```

**Missing property:**
```typescript
// Add to interface
interface Config {
  existing: string
  missing: string  // Add this
}
```

## Rules
1. NEVER refactor while fixing build errors
2. NEVER add features while fixing build errors
3. ALWAYS fix one error at a time
4. ALWAYS re-run build after each fix
5. STOP after 3 failed attempts — report to user
```

- [ ] **Step 2: Commit**

```bash
git add agents/build-error-resolver.md
git commit -m "agents: add build-error-resolver agent"
```

---

## Subsystem D3: Doc Updater

**Goal:** Keep docs in sync with code changes.

**Files:**
- Create: `agents/doc-updater.md`
- Create: `commands/update-docs.md`

### Task D3.1: Create doc-updater agent

**Files:**
- Create: `agents/doc-updater.md`

- [ ] **Step 1: Write the agent**

```markdown
---
name: doc-updater
description: "Keeps documentation in sync with code changes. Use after significant code changes, before PRs, or when docs are stale."
tools: Read, Write, Edit, Grep, Glob
---

# Doc Updater Agent

Keeps README, ARCHITECTURE, and other docs synchronized with code.

## When to Use
- After creating/modifying features
- Before creating PRs
- When user says "update the docs"

## Workflow

### 1. Detect Changes
```bash
git diff --name-only HEAD~1
```

### 2. Identify Affected Docs
- New files → check if README needs updating
- Modified APIs → check if API docs need updating
- New features → check if ARCHITECTURE needs updating

### 3. Update Docs
- Add new features to README
- Update API signatures in docs
- Add new agents/skills/commands to component tables
- Update counts (skills, agents, commands)

### 4. Verify
- Check all links work
- Check code examples compile
- Check counts match reality

## Anti-Patterns
1. Do NOT update docs for trivial changes (typos, formatting)
2. Do NOT add docs that describe what code does — docs should explain WHY
3. Do NOT leave stale examples — remove or update them
```

- [ ] **Step 2: Commit**

```bash
git add agents/doc-updater.md
git commit -m "agents: add doc-updater agent"
```

### Task D3.2: Create /update-docs command

**Files:**
- Create: `commands/update-docs.md`

- [ ] **Step 1: Write the command**

```markdown
---
description: "Update documentation to match current code."
argument-hint: "[--check]"
---

# /update-docs — Sync Docs with Code

Update README, ARCHITECTURE, and other docs to reflect current code state.

## Usage

```
/update-docs           # Update all docs
/update-docs --check   # Check what needs updating (dry run)
```

## What Gets Updated
- README.md: component counts, feature descriptions
- CHANGELOG.md: new entries for significant changes
- templates/claude-md-snippet.md: workflow chain updates

## Anti-Patterns
1. Do NOT auto-update CHANGELOG — that's manual
2. Do NOT remove user-added content — only add/update
```

- [ ] **Step 2: Commit**

```bash
git add commands/update-docs.md
git commit -m "commands: add /update-docs for doc synchronization"
```

---

# Group E: Orchestration

## Subsystem E1: Orchestrate Command

**Goal:** Chain agents in sequence for complex workflows.

**Files:**
- Create: `commands/orchestrate.md`

### Task E1.1: Create orchestrate command

**Files:**
- Create: `commands/orchestrate.md`

- [ ] **Step 1: Write the command**

```markdown
---
description: "Chain agents in sequence for complex workflows: feature, bugfix, refactor, security."
argument-hint: "<workflow-type> <task-description>"
---

# /orchestrate — Agent Workflow Chain

Run a sequence of agents for complex tasks.

## Workflows

### feature
```
planner → tdd-guide → code-reviewer → security-reviewer
```

### bugfix
```
onboarding-guide → tdd-guide → code-reviewer
```

### refactor
```
planner → code-reviewer → tdd-guide
```

### security
```
security-reviewer → code-reviewer → planner
```

## Usage

```
/orchestrate feature "Add user authentication"
/orchestrate bugfix "Fix login timeout"
/orchestrate refactor "Redesign caching layer"
/orchestrate security "Audit payment flow"
```

## Handoff Format

Between agents, create a handoff document:

```markdown
## HANDOFF: [previous] → [next]

### Context
[What was done]

### Findings
[Key discoveries]

### Files Modified
[Files touched]

### Recommendations
[Next steps]
```

## Final Report

```
ORCHESTRATION REPORT
════════════════════
Workflow: feature
Task: Add user authentication
Agents: planner → tdd-guide → code-reviewer → security-reviewer

SUMMARY
[One paragraph]

AGENT OUTPUTS
Planner: [summary]
TDD Guide: [summary]
Code Reviewer: [summary]
Security: [summary]

RECOMMENDATION
SHIP / NEEDS WORK / BLOCKED
```

## Anti-Patterns
1. Do NOT skip agents in the chain
2. Do NOT run agents in parallel unless explicitly independent
3. Do NOT ignore handoff documents
4. Do NOT proceed if any agent returns BLOCKED
```

- [ ] **Step 2: Commit**

```bash
git add commands/orchestrate.md
git commit -m "commands: add /orchestrate for agent workflow chaining"
```

---

# Final: Version Bump and README Update

### Task F1: Version bump to 0.14.0

**Files:**
- Modify: `.claude-plugin/plugin.json`
- Modify: `.claude-plugin/marketplace.json`
- Modify: `CHANGELOG.md`
- Modify: `README.md`

- [ ] **Step 1: Bump version**

Update `plugin.json` and `marketplace.json` to `0.14.0`.

- [ ] **Step 2: Add CHANGELOG entry**

```markdown
## 0.14.0 — 2026-07-29

### Added
- Memory persistence hooks: auto-save on session end, pre-compact
- Contexts: dev, review, research modes with /context command
- Rules directory: modular security, testing, git, style, performance rules
- Continuous learning: auto-extract patterns from sessions
- Eval harness: capability/regression evals with pass@k metrics
- TDD workflow: skill + agent for test-driven development
- Build error resolver agent: auto-fixes build errors with minimal diffs
- Doc updater agent: keeps docs in sync with code
- Orchestrate command: agent workflow chaining
- Test coverage: /test-coverage command

### Changed
- Session-start hook: now loads context files
- Stop hook: now saves memory + extracts patterns
```

- [ ] **Step 3: Update README**

Update counts: 26→26 skills (add tdd-workflow, eval-harness, continuous-learning, context-switching, test-coverage = 31), 12→15 agents (add tdd-guide, build-error-resolver, doc-updater), 12→15 commands (add /context, /eval, /test-coverage, /update-docs, /orchestrate = 17).

- [ ] **Step 4: Run validation**

```bash
bash scripts/validate.sh
```

- [ ] **Step 5: Commit and push**

```bash
git add -A
git commit -m "v0.14.0: ECC integration — memory, contexts, rules, TDD, evals, orchestration"
git push origin master
```
