---
description: "Log in to the Speccon ERP at prod-erp.tap.co.za and navigate to a ticket. Sources credentials from .env.erp — set TEST_USER, TEST_PASS, and ERP_BASE there."
argument-hint: "[ticket-id]"
---

# /idev:erp-login

Log into the production ERP and optionally navigate to a ticket.

## Setup (one time)

Create `.env.erp` in the project root (gitignored):
```
TEST_USER=your@email.com
TEST_PASS=your-password
ERP_BASE=https://prod-erp.tap.co.za
```

## Steps

1. Source `.env.erp` and export vars. Fail with a clear message if the
   file is missing.
2. Run the Setup block from the `idev:browse` skill to detect if gstack
   browse is available, then:
3. Navigate to `${ERP_BASE}/login`
4. Fill email/username (`@e1`) with `$TEST_USER`
5. Fill password (`@e2`) with `$TEST_PASS`
6. Click "Login" button (`@e5`)
7. Verify login succeeded — check the URL changed from `/login`
8. If a ticket ID was provided, navigate to it:
   `${ERP_BASE}/devpm/tickets/<ticket-id>`
9. Snapshot the page and report the accessible elements
10. Present: "Logged in as $TEST_USER. Page shows: [summary]. What would
    you like to test?"
