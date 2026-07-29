---
description: Open an interactive browser QA session — navigate a URL, snapshot the page for interactive refs, verify state, and capture screenshot evidence. Uses xd://browser, no Playwright install needed.
argument-hint: "<URL> [--viewport WxH]"
---

# /idev:browse

Run interactive browser QA using `xd://browser` via the browser-qa agent.

Arguments: `$ARGUMENTS`

## Steps

1. If a URL is provided, use it; otherwise infer the target from the
   current session (deployment URL, local dev server, or mentioned URL).
   Confirm in one line.
2. Delegate to the **browser-qa** agent with: the target URL, any
   viewport preference from `--viewport`, and a pointer to follow the
   idev:browse skill patterns.
3. Relay the agent's findings — page state, element refs, console health,
   and any interactive options available.
