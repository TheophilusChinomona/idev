---
name: task-journal
description: "Persistent task log across sessions: pending tasks, completed work, known issues, backlog. Use when starting a session, completing a task, hitting a blocker, or asked what is pending or in progress. Delegates session persistence to the remember plugin."
---

# Task Journal Skill

## Purpose
Persistent task tracking across sessions. Records what was done, what's pending, and what broke — so nothing falls through the cracks when sessions restart or context is compacted.

## Activation
- **Write**: After completing any task, encountering a blocker, or discovering a new issue
- **Read**: At session start, or when user asks "what's pending?" or "what did we do?"

---

## How It Works

### Primary: remember plugin integration
The remember plugin (installed separately) handles session-level persistence via `.remember/` in the project root. When available, task-journal reads from and writes alongside the remember plugin's files:

- **Read at session start**: `.remember/` session files provide recent session history
- **Write task entries**: Append to `.claude/idev/task-journal/journal.md` (the persistent, human-curated log)

### Fallback: standalone journal
When the remember plugin is not installed, task-journal operates standalone using `.claude/idev/task-journal/journal.md`.

### Why two systems?
- remember plugin: automatic session capture, consolidation, compression — system-maintained
- task-journal: manually curated, structured task log — human-maintained for high-signal entries
- They complement each other: remember captures everything, task-journal captures what matters

---

## Journal Format

```markdown
# Task Journal
Last updated: YYYY-MM-DD HH:mm

## Active / In Progress
- [ ] [FEATURE] Task description
  - File: path/to/file
  - Status: what's been done so far
  - Blocker: what's blocking (if any)

## Completed (Recent)
- [x] [FEATURE] Task description — YYYY-MM-DD
  - Files changed: file1, file2, file3
  - Summary: one-line summary of what was done

## Known Issues
- [!] [FEATURE] Issue description — YYYY-MM-DD
  - File: path/to/file
  - Severity: low|medium|high|critical
  - Notes: debugging info, what was tried

## Backlog (User Mentioned)
- [ ] [FEATURE] Task description
  - Context: what the user said about it
```

---

## Write Rules

### When a task is completed:
```
1. Move from "Active" to "Completed (Recent)"
2. Add date and files changed
3. Add one-line summary
```

### When a blocker is found:
```
1. Add to "Known Issues" with severity
2. Update "Active" entry with blocker description
3. Include what was tried and what to check next
```

### When user mentions future work:
```
1. Add to "Backlog" with the user's context
2. Do NOT start working on backlog items unless user asks
```

### Housekeeping:
```
- Keep "Completed" list to last 20 entries (archive older ones)
- Keep "Known Issues" until explicitly resolved
- Keep "Backlog" until user addresses or dismisses
- Remove duplicate entries
```

---

## Read Rules

### At session start:
```
1. Read journal.md (~50-100 lines)
2. If "Active" items exist → inform user
3. If "Known Issues" exist → mention briefly
4. Do NOT read "Completed" unless user asks for history
```

### When user asks "what's pending?":
```
1. Show "Active" + "Known Issues" + "Backlog"
2. Exclude "Completed"
```

### When user asks "what did we do?":
```
1. Show "Completed (Recent)"
2. Group by date if multiple sessions
```

---

## Integration with Other Skills

```
Task Journal works WITH session-resume AND the remember plugin:
  - session-resume = ephemeral (current session snapshot, overwritten each time)
  - task-journal = persistent (rolling log across all sessions)
  - remember plugin = automatic session capture and consolidation

Workflow:
  1. Session starts → load session-resume (what was I doing?)
  2. Session starts → load task-journal (what's the big picture?)
  3. Session starts → remember plugin provides recent session history
  4. Task done → update task-journal (log it)
  5. Session ends → update session-resume (snapshot current state)
  6. Session ends → remember plugin captures session for future reference
```

---

## Anti-Patterns
1. Do NOT write to journal for trivial actions (reading files, searching)
2. Do NOT duplicate the same entry multiple times
3. Do NOT let the journal grow beyond ~150 lines (archive old completed items)
4. Do NOT use the journal as a substitute for actually reading code
5. Do NOT auto-generate backlog items — only log what the user explicitly mentions
