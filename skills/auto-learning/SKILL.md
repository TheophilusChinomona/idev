---
name: auto-learning
description: Instinct-based learning system that observes sessions via hooks and evolves patterns into skills/commands/agents. Use when the user asks about learned instincts, wants to analyze session patterns, sets up auto-learning or observation hooks, or runs /idev:instinct-status, /idev:instinct-export, /idev:instinct-import, or /idev:evolve.
---

# Auto-Learning - Instinct-Based Architecture

A learning system that turns Claude Code sessions into reusable knowledge through atomic "instincts" - small learned behaviors with confidence scoring.

## The Instinct Model

An instinct is a small learned behavior:

```yaml
---
id: prefer-functional-style
trigger: "when writing new functions"
confidence: 0.7
domain: "code-style"
source: "session-observation"
---

# Prefer Functional Style

## Action
Use functional patterns over classes when appropriate.

## Evidence
- Observed 5 instances of functional pattern preference
- User corrected class-based approach to functional on 2025-01-15
```

**Properties:**
- **Atomic** — one trigger, one action
- **Confidence-weighted** — 0.3 = tentative, 0.9 = near certain
- **Domain-tagged** — code-style, testing, git, debugging, workflow, etc.
- **Evidence-backed** — tracks what observations created it

## How It Works

```
Session Activity
      │
      │ PreToolUse/PostToolUse hooks (observe.sh → observe.py)
      ▼
┌─────────────────────────────────────────┐
│         observations.jsonl              │
│   (tool calls + outcomes, redacted)     │
└─────────────────────────────────────────┘
      │
      │ Observer loop (start-observer.sh, headless Haiku)
      ▼
┌─────────────────────────────────────────┐
│         instincts/personal/             │
│   atomic instincts with confidence      │
└─────────────────────────────────────────┘
      │
      │ /idev:evolve clusters
      ▼
┌─────────────────────────────────────────┐
│              evolved/                   │
│   skills / commands / agents            │
└─────────────────────────────────────────┘
```

## Quick Start

### 1. Enable Observation Hooks (opt-in)

Add to your `~/.claude/settings.json`. NOTE: `${CLAUDE_PLUGIN_ROOT}` is NOT expanded in user settings — replace `<idev-plugin-root>` below with the absolute path of the installed idev plugin (find it with `claude plugin list` or under `~/.claude/plugins/`):

```json
{
  "hooks": {
    "PreToolUse": [{
      "matcher": "*",
      "hooks": [{
        "type": "command",
        "command": "<idev-plugin-root>/skills/auto-learning/hooks/observe.sh pre"
      }]
    }],
    "PostToolUse": [{
      "matcher": "*",
      "hooks": [{
        "type": "command",
        "command": "<idev-plugin-root>/skills/auto-learning/hooks/observe.sh post"
      }]
    }]
  }
}
```

`observe.sh` is a thin wrapper that pipes the hook JSON to `observe.py` (the canonical implementation). The `pre`/`post` argument tells it the hook phase; if omitted, it falls back to the `hook_event_name` field in the payload. The hook truncates inputs/outputs at 5000 chars, redacts secret-looking values, honors `capture_tools`/`ignore_tools` from `config.json`, and rotates `observations.jsonl` into `observations.archive/` past `max_file_size_mb`.

### 2. Initialize Directory Structure

```bash
mkdir -p ~/.claude/homunculus/{instincts/{personal,inherited},evolved/{agents,skills,commands}}
touch ~/.claude/homunculus/observations.jsonl
```

### 3. Run the Observer Agent (Optional)

The observer runs in the background, analyzing observations every 5 minutes (and on SIGUSR1 from the hook). It only archives observations after a successful analysis that produced an instinct:

```bash
"${CLAUDE_PLUGIN_ROOT}/skills/auto-learning/agents/start-observer.sh"          # start
"${CLAUDE_PLUGIN_ROOT}/skills/auto-learning/agents/start-observer.sh" status   # check
"${CLAUDE_PLUGIN_ROOT}/skills/auto-learning/agents/start-observer.sh" stop     # stop
```

## CLI and Commands

`scripts/instinct-cli.py` manages the instinct store. Four plugin commands wrap it:

| Command | CLI invocation | Description |
|---------|----------------|-------------|
| `/idev:instinct-status` | `instinct-cli.py status` | Show all instincts with confidence, by domain |
| `/idev:instinct-export` | `instinct-cli.py export [--domain] [--min-confidence] [--output]` | Export sanitized instincts for sharing |
| `/idev:instinct-import` | `instinct-cli.py import <file-or-url> [--dry-run] [--force] [--min-confidence]` | Import instincts; updates existing ids in place |
| `/idev:evolve` | `instinct-cli.py evolve [--generate]` | Print instinct clusters; Claude writes the evolved files |

Run it directly with:

```bash
python3 "${CLAUDE_PLUGIN_ROOT}/skills/auto-learning/scripts/instinct-cli.py" status
```

## Configuration

`config.json` (in this skill's directory) is the source of truth:

```json
{
  "version": "2.0",
  "observation": {
    "enabled": true,
    "store_path": "~/.claude/homunculus/observations.jsonl",
    "max_file_size_mb": 10,
    "archive_after_days": 7,
    "capture_tools": ["Edit", "Write", "Bash", "Read", "Grep", "Glob"],
    "ignore_tools": ["TodoWrite"]
  },
  "instincts": {
    "personal_path": "~/.claude/homunculus/instincts/personal/",
    "inherited_path": "~/.claude/homunculus/instincts/inherited/",
    "min_confidence": 0.3,
    "auto_approve_threshold": 0.7,
    "confidence_decay_rate": 0.02,
    "max_instincts": 100
  },
  "observer": {
    "enabled": false,
    "model": "haiku",
    "run_interval_minutes": 5,
    "min_observations_to_analyze": 20,
    "patterns_to_detect": [
      "user_corrections",
      "error_resolutions",
      "repeated_workflows",
      "tool_preferences",
      "file_patterns"
    ]
  },
  "evolution": {
    "cluster_threshold": 3,
    "evolved_path": "~/.claude/homunculus/evolved/",
    "auto_evolve": false
  }
}
```

Field reference:

- `observation.enabled` — master switch for the observation hook (`false` disables capture)
- `observation.capture_tools` — if non-empty, ONLY these tools are observed
- `observation.ignore_tools` — tools never observed (checked before capture_tools)
- `observation.max_file_size_mb` — observations.jsonl rotates to the archive past this size
- `observation.archive_after_days` — retention hint for archived observations
- `instincts.min_confidence` — floor for keeping an instinct
- `instincts.auto_approve_threshold` — confidence at which an instinct applies without asking
- `instincts.confidence_decay_rate` — weekly decay when a pattern stops being observed
- `instincts.max_instincts` — cap on the instinct store; prune lowest-confidence first
- `observer.enabled` — whether the background observer should run
- `observer.min_observations_to_analyze` — observations required before an analysis run (read by start-observer.sh)
- `evolution.cluster_threshold` — instincts required to form an evolution cluster
- `evolution.auto_evolve` — if true, evolution may be proposed without an explicit /idev:evolve

You can also disable capture entirely by creating `~/.claude/homunculus/disabled`.

## File Structure

```
~/.claude/homunculus/
├── observations.jsonl      # Current session observations
├── observations.archive/   # Rotated + processed observations
├── observer.log            # Background observer log
├── instincts/
│   ├── personal/           # Auto-learned instincts
│   └── inherited/          # Imported from others
└── evolved/
    ├── agents/             # Evolved specialist agents
    ├── skills/             # Evolved skills
    └── commands/           # Evolved commands
```

## Confidence Scoring

| Score | Meaning | Behavior |
|-------|---------|----------|
| 0.3 | Tentative | Suggested but not enforced |
| 0.5 | Moderate | Applied when relevant |
| 0.7 | Strong | Auto-approved for application |
| 0.9 | Near-certain | Core behavior |

**Confidence increases** when a pattern is repeatedly observed, the user doesn't correct the behavior, or similar instincts from other sources agree.

**Confidence decreases** when the user explicitly corrects the behavior, the pattern isn't observed for extended periods (see `confidence_decay_rate`), or contradicting evidence appears.

## Privacy

- Observations stay **local** on your machine
- The hook redacts secret-looking values (api keys, tokens, passwords) before writing
- Export sanitizes absolute file paths and secrets; only instinct patterns are shared
- You control what gets exported

---

*Architecture inspired by the Homunculus continuous-learning project.*
