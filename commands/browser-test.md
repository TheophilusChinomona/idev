---
description: Run code-as-action browser tests — verify a web feature or user flow with a real Playwright run and get a structured report with screenshot/console evidence.
argument-hint: "<flow description or URL> [--against <base-url>]"
---

# /idev:browser-test

Verify a web feature in a real browser and produce a test report.

Arguments: `$ARGUMENTS`

## Steps

1. If the arguments name a flow or URL, use them; otherwise infer the flow
   from the most recent UI change in this session (and confirm it with the
   user in one line).
2. Delegate to the **browser-tester** agent with: the flow description, the
   base URL (`--against` value, or the project's dev-server default), and a
   pointer to follow the idev:browser-test skill conventions.
3. Relay the agent's report verbatim — per-check results with evidence
   paths, app bugs found, and what wasn't covered. If app bugs were found,
   offer (don't auto-start) fixing them.
