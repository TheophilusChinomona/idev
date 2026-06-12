---
name: browser-test
description: "Code-as-action browser testing: verify UI changes and user flows by writing re-runnable Playwright scripts, capturing screenshots/console/network evidence, and producing test reports. Use when verifying a web feature in a real browser, reproducing a UI bug, smoke-testing a flow after changes, or asked to test the site / run browser tests."
---

# Browser Test — Code-as-Action Browser Verification

Verify web features by **writing Playwright scripts, not by imagining what a
browser would show**. The script is the durable artifact: it lands in the
project's test library and re-runs on every future change to that flow.
(Concept adapted from Microsoft's Webwright: treat the browser as a
disposable environment your code spawns; the workspace — scripts, logs,
screenshots — is the state.)

## State layout

```
.claude/idev/browser-tests/
├── scripts/        # one script per flow — the accumulated E2E library
├── artifacts/      # screenshots, console/network logs per run (gitignorable)
└── reports/        # structured test reports
```

## Setup detection (in order)

1. Project already has `@playwright/test` in package.json → use it
   (`npx playwright test`). Respect the project's `playwright.config.*`.
2. Python `playwright` importable → use the sync API
   (`python3 script.py`).
3. Neither → tell the user the one-time setup
   (`npm i -D @playwright/test && npx playwright install chromium`) and ask
   before installing anything.

## Script conventions

- **Reuse first**: grep `scripts/` for the flow before writing a new script.
  Adapt and parameterize an existing one rather than duplicating it.
- **One flow per script**, named for the flow: `login-flow.spec.ts`,
  `checkout-smoke.spec.ts`.
- **Base URL from env**, never hardcoded:
  `const BASE = process.env.BASE_URL ?? 'http://localhost:3000'` — scripts
  must run against dev, staging, or CI unchanged.
- **Assert real outcomes**, not just "page loaded": visible text, URL after
  navigation, row counts, toast messages. Prefer role/label selectors
  (`getByRole`, `getByLabel`) over CSS chains — they survive refactors.
- **Capture evidence on every run**: screenshot at each key step and on
  failure; collect console errors and failed network requests:

```ts
import { test, expect } from '@playwright/test';
const BASE = process.env.BASE_URL ?? 'http://localhost:3000';

test('user can log in', async ({ page }) => {
  const consoleErrors: string[] = [];
  page.on('console', m => m.type() === 'error' && consoleErrors.push(m.text()));
  page.on('requestfailed', r => consoleErrors.push(`NET ${r.url()}`));

  await page.goto(`${BASE}/login`);
  await page.getByLabel('Email').fill(process.env.TEST_USER ?? 'test@example.com');
  await page.getByLabel('Password').fill(process.env.TEST_PASS ?? 'test');
  await page.getByRole('button', { name: 'Sign in' }).click();

  await expect(page).toHaveURL(/dashboard/);
  await page.screenshot({ path: '.claude/idev/browser-tests/artifacts/login-ok.png' });
  expect(consoleErrors, `console/network errors: ${consoleErrors}`).toHaveLength(0);
});
```

- **Credentials via env vars only** (`TEST_USER`, `TEST_PASS`) — never
  commit secrets into scripts; note required vars at the top of the script.
- Headless by default; headed only while debugging a script.

## Failure discipline (the important part)

When a run fails, classify before acting:

- **Script bug** (wrong selector, missing wait, bad assumption) → fix the
  script and re-run. Max 3 repair iterations; then report what's blocking.
- **App bug** (console error, failed request, wrong behavior) → do NOT
  silently change the app to make the test pass. Capture the evidence
  (screenshot, error text, request) and report it as a finding.
- **Environment issue** (server not running, missing test data) → report
  what's needed; see the project's run conventions.

## Report format

Write to `reports/<YYYY-MM-DD>-<flow>.md`:

```markdown
# Browser Test Report: <flow> — <date>
Target: <BASE_URL>   Script: scripts/<name>   Result: PASS | FAIL

| # | Check | Result | Evidence |
|---|-------|--------|----------|
| 1 | login redirects to /dashboard | PASS | artifacts/login-ok.png |
| 2 | zero console errors | FAIL | "TypeError: x is undefined" |

## App bugs found
- <error + repro + evidence path>  (also log per the lessons-learned skill if recurring)

## Not covered
- <flows/states this run did not exercise>
```

Report only what actually ran — no inferred results. If a check didn't
execute, it's "not covered", not "pass".

## Anti-patterns

- Verifying UI changes by reading the JSX/HTML and declaring it works —
  that's what this skill exists to replace.
- Writing a throwaway script and deleting it — save it to `scripts/`; the
  library is the point.
- `waitForTimeout(3000)` sprinkled to "fix" flakiness — wait for conditions
  (`expect(...).toBeVisible()`, `waitForURL`) instead.
- Testing through 10 UI steps what one API call could set up — use the API
  for arrange, the browser for act/assert.

---
Concept adapted from [Webwright](https://github.com/microsoft/Webwright)
(MIT, © Microsoft Corporation).
