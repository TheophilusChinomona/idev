---
description: "Generate a ticket completion report for the ERP: test steps, expected vs actual, and DevOps commit link. Copy-paste ready."
argument-hint: "<ticket-id>"
---

# /complete-ticket — Ticket Completion Report

Generates the three-section completion note needed to close a ticket on the ERP.

## Usage

```
/complete-ticket PROJ-1234
```

Claude will ask for your inputs, then produce:

```
PROJ-1234

How did you test this? (steps / test case)
[claude fills in the actual test steps performed during this session]

Expected vs actual result
Expected: [what you describe]
Actual: [what actually happened — matches or differs]

DevOps commit link
[commit SHA from this session]
```

No table formatting — plain copy-paste text.
