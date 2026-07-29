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
