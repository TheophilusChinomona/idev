---
description: "Full ticket closure workflow: log into the ERP, test the fix in the browser, generate the completion report, and update the ticket status. Sources credentials from .env.erp."
argument-hint: "<ticket-id> [--branch <branch-name>]"
---

# /idev:close-ticket <ticket-id>

Close a ticket end-to-end: test → report → update status.

## Setup

Create `.env.erp` in the project root (gitignored):
```
TEST_USER=your@email.com
TEST_PASS=your-password
ERP_BASE=https://prod-erp.tap.co.za
```

## Steps

1. **Source credentials** — load `.env.erp`, export vars, fail if missing.

2. **Log into ERP** — follow the `erp-login` workflow:
   - Navigate to `${ERP_BASE}/login`
   - Fill credentials, click Login
   - Confirm redirect from `/login` (verify auth)

3. **Test the fix** — follow the `idev:browse` skill patterns:
   - Navigate to the ticket's feature area in the ERP
   - Run the test steps described in the ticket
   - Capture screenshot evidence
   - Check console for errors
   - Report PASS/FAIL per test step

4. **Generate completion report** — output in this format:

   ```
   <TICKET-ID>

   How did you test this?
   [numbered test steps actually performed]

   Expected vs actual result
   Expected: [from ticket description]
   Actual: [PASS/FAIL with evidence]

   DevOps commit link
   <branch name or commit SHA>
   ```

5. **Update ticket status** — return to the kanban board at
   `${ERP_BASE}/dev-pm/kanban`. If the ticket has a drag-to-done
   mechanism, move it to "Done". If not, copy the completion report
   text to the clipboard for manual pasting into the ticket.

6. **Present result** — "Ticket <id> tested and closed. Evidence
   at <path>. Completion report ready to paste."
