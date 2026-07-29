---
name: session-resume
description: "Cross-session context persistence via .claude/idev/session-resume/last-session.json. Use when resuming work in a new session, or to save working context at task completion or when the user asks to save. Proactively prompts to save at natural stopping points."
---

# Session Resume Skill

## Purpose
Persist working context across sessions so Claude can resume exactly where it left off without re-discovering files, re-reading code, or re-learning what was being worked on.

## Activation
- **Save**: At task completion, when the user asks to save, or proactively at natural stopping points
- **Load**: At the start of a new session (before any task work)

---

## How It Works

A lightweight session snapshot is saved to:
`.claude/idev/session-resume/last-session.json`

This file is loaded at session start, giving Claude instant awareness of:
- What feature/area was being worked on
- Which files were recently read/modified
- What the last task was
- Any pending issues or blockers

---

## Phase 1: Save Session State

At task completion (or when the user asks to save context), save:

```json
{
  "savedAt": "YYYY-MM-DD HH:mm",
  "lastTask": {
    "description": "Brief description of what was being done",
    "status": "completed|in-progress|blocked",
    "blockedBy": "Description of blocker (if blocked)"
  },
  "activeFeature": "FeatureName (e.g., Orders)",
  "activeLayer": "frontend|backend|full-stack",
  "recentFiles": {
    "modified": [
      "relative/path/to/file1.ts",
      "relative/path/to/file2.cs"
    ],
    "read": [
      "relative/path/to/file3.ts"
    ]
  },
  "openIssues": [
    {
      "description": "Reject button not hitting API - needs browser console check",
      "file": "relative/path/to/file.tsx",
      "severity": "medium"
    }
  ],
  "workingBranch": "feature/branch-name",
  "notes": "Any important context that would be lost on session restart"
}
```

---

## Phase 2: Load Session State

At session start:

```
1. Read last-session.json (~30 lines, roughly 300 tokens)
2. If lastTask.status == "in-progress":
   → Inform user: "Last session was working on: [description]"
   → Offer to continue or start fresh
3. If openIssues exist:
   → Mention pending issues briefly
4. Use activeFeature + activeLayer to pre-load the right context
5. Use recentFiles.modified to know which files were changed
```

---

## Phase 3: When to Save (Proactive Prompts)

Save the session state when ANY of these occur:
1. User explicitly says "save session" or "save context"
2. A task is completed (update lastTask.status)
3. User switches to a different feature/task
4. A blocker is encountered (update openIssues)

### Proactive save prompts

At natural stopping points, prompt the user to save. This fixes the discoverability gap — the save path was never invoked because nothing reminded the user:

```
After completing a task:
  → "Task complete. Save session state so we can resume here later? (y/n)"
  
Before context compaction (if PreCompact hook is wired):
  → Auto-save without prompting — context is about to be compressed
  
When user says "done for today" or similar:
  → Auto-save immediately
  
When switching to a completely different feature:
  → "Switching from [Feature A] to [Feature B]. Save state for Feature A? (y/n)"
```

### Auto-save on session end

If the session is ending (user says goodbye, done, wrap up), save automatically without prompting. The cost is one file write; the benefit is the next session picks up seamlessly.

---

## Save Rules

- Keep recentFiles lists to max 10 entries each (most recent first)
- Keep openIssues to max 5 entries
- Overwrite previous session file (only latest session matters)
- Do NOT save file contents — only paths
- Do NOT save sensitive data (tokens, passwords, keys)
- Total file size should stay under 50 lines

---

## Integration with Other Skills

```
Session start:
  1. Load last-session.json (this skill)
  2. Load .claude/idev/smart-context/index.json (smart context skill)
  3. If activeFeature is set → grep file-index for that feature's files
  4. Ready to work in ~3 reads

Session end:
  1. Save session state (this skill)
  2. Update task-journal with what was accomplished
  3. remember plugin captures session for future reference
```

---

## Anti-Patterns
1. Do NOT save entire file contents in the session state
2. Do NOT save more than 10 recent files
3. Do NOT load the session state AND re-explore the codebase
4. Do NOT ignore the session state when it exists
5. Do NOT prompt to save on every minor action — only at natural stopping points
