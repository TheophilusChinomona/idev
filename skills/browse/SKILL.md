---
name: browse
description: "Interactive browser QA using xd://browser or (optionally) the gstack browse binary for headed mode. Navigate pages, snapshot accessibility trees, interact via element refs, capture screenshots, verify page state, and hand off for CAPTCHA. Use when you need to test a page live, debug a UI bug, verify a deployment, or dogfood a user flow."
---

# Browse — Interactive Browser QA

Two backends: `xd://browser` (runtime built-in, zero install, headless only)
or **gstack browse** (97KB binary, headed mode + handoff for CAPTCHA).
The skill auto-detects which is available.

## Setup (run first)

```bash
# Detect gstack browse binary
B=""
[ -x /home/theo/.claude/skills/gstack/browse/dist/browse ] && B="/home/theo/.claude/skills/gstack/browse/dist/browse"
[ -x /home/theo/.codex/skills/gstack/browse/dist/browse ] && B="/home/theo/.codex/skills/gstack/browse/dist/browse"
[ -x "$(git rev-parse --show-toplevel 2>/dev/null)/.agents/skills/gstack/browse/dist/browse" ] && B="$(git rev-parse --show-toplevel 2>/dev/null)/.agents/skills/gstack/browse/dist/browse"
export B
if [ -n "$B" ]; then echo "GSTACK_BROWSE=$B"; else echo "GSTACK_BROWSE=none (using xd://browser)"; fi
```

If `GSTACK_BROWSE=none`, all interactions use `xd://browser` (headless).
If `GSTACK_BROWSE` is set, `$B` works for all gstack browse commands.

## Quick Reference

```bash
# xd://browser (always available — headless only)
xd://browser { "action": "open", "url": "https://app.com", "name": "main" }
run code: tab.ariaSnapshot()   # ARIA YAML with [ref=eN]
run code: tab.fill('aria-ref=e2', 'Alice')
run code: tab.click('aria-ref=e5')

# gstack browse (headed + handoff — when available)
$B goto https://app.com
$B snapshot -i                  # @e1, @e2... refs
$B fill @e2 "Alice"
$B click @e5
$B handoff "solve CAPTCHA"     # visible browser for user
$B resume                       # continue after handoff
```

## Core Workflow

1. **Detect backend** via the Setup block above
2. **Open tab** — `xd://browser open` or `$B goto`
3. **Snapshot** — `tab.ariaSnapshot()` or `$B snapshot -i`
4. **Interact** — fill, click, select by @ref
5. **Verify** — check text, URL, console errors
6. **Handoff if stuck** — `$B handoff` for CAPTCHA/complex auth
7. **Screenshot** — capture evidence
8. **Close** — close tab or `$B stop`

## Patterns using xd://browser (always available)

### Pattern 1: Basic page verification
```
xd://browser { "action": "open", "url": "https://app.com/login" }
xd://browser { "action": "run", "name": "main", "code": "tab.observe()" }
xd://browser { "action": "run", "name": "main",
  "code": "const errs=[]; page.on('console',m=>m.type()==='error'&&errs.push(m.text())); page.on('requestfailed',r=>errs.push('NET: '+r.url())); await tab.goto('https://app.com/login'); errs" }
```

### Pattern 2: Snapshot + interact by @ref
```
xd://browser { "action": "run", "name": "main", "code": "tab.ariaSnapshot()" }
xd://browser { "action": "run", "name": "main",
  "code": "await tab.fill('aria-ref=e2', 'user@test.com'); await tab.click('aria-ref=e5'); tab.screenshot()" }
xd://browser { "action": "run", "name": "main", "code": "tab.observe()" }
```
Refs invalidate on navigation — re-observe after every `goto`.

### Pattern 3: Form fill and submit
```
xd://browser { "action": "run", "name": "main", "code": "
  await tab.fill('input[type=text]', 'Alice');
  await tab.select('select', 'green');
  await tab.click('button');
  await tab.waitForSelector('#result');
  tab.extract('#result')" }
```

### Pattern 4: Screenshot evidence
```
xd://browser { "action": "run", "name": "main",
  "code": "tab.screenshot()" }
xd://browser { "action": "run", "name": "main",
  "code": "tab.screenshot({ selector: '.dashboard' })" }
```

### Pattern 5: Dialog handling
```
xd://browser { "action": "open", "url": "...", "dialogs": "accept", "name": "main" }
xd://browser { "action": "run", "name": "main", "code": "
  page.on('dialog', d => d.accept());
  await tab.click('#delete-btn');" }
```

### Pattern 6: Multi-tab testing
```
xd://browser { "action": "open", "url": "https://app.com/a", "name": "tab1" }
xd://browser { "action": "open", "url": "https://app.com/b", "name": "tab2" }
xd://browser { "action": "run", "name": "tab1", "code": "tab.observe()" }
xd://browser { "action": "close", "name": "tab1" }
```

### Pattern 7: Viewport/responsive
```
xd://browser { "action": "open", "url": "...",
  "viewport": { "width": 375, "height": 812 }, "name": "mobile" }
```

### Pattern 8: Custom JS evaluation
```
xd://browser { "action": "run", "name": "main", "code": "
  const result = await tab.evaluate(() => ({
    title: document.title, url: location.href
  }));
  result" }
```

### Pattern 9: Wait conditions
```
xd://browser { "action": "run", "name": "main", "code": "
  await tab.waitForSelector('.toast-success', { timeout: 5000 }); 'found it'" }
xd://browser { "action": "run", "name": "main", "code": "
  await tab.click('button');
  await tab.waitForUrl('**/dashboard');
  tab.screenshot()" }
```

### Pattern 10: File upload
```
xd://browser { "action": "run", "name": "main",
  "code": "await tab.uploadFile('input[type=file]', '/path/to/file.pdf'); 'uploaded'" }
```

### Pattern 11: Drag and drop
```
xd://browser { "action": "run", "name": "main",
  "code": "await tab.drag('#source', '#target'); 'dragged'" }
```

### Pattern 12: Cookie and storage manipulation
```
xd://browser { "action": "run", "name": "main",
  "code": "tab.evaluate(() => { document.cookie='session=abc123;path=/';"+
    "localStorage.setItem('pref','dark');"+
    "return {cookies:document.cookie,storage:{...localStorage}} })" }
```

### Pattern 13: Wait for network response
```
xd://browser { "action": "run", "name": "main", "code": "
  const [resp] = await Promise.all([
    tab.waitForResponse(r => r.url().includes('/api/submit')),
    tab.click('#submit-btn')
  ]);
  { status: resp.status(), url: resp.url(), ok: resp.ok() }" }
```

### Pattern 14: Scroll element into view
```
xd://browser { "action": "run", "name": "main",
  "code": "await tab.scrollIntoView('#footer'); 'scrolled'" }
```

## Patterns using gstack browse (when available)

These require `$B` to be set (from the Setup step above).

### Pattern G1: Quick snapshot + interact
```bash
$B goto https://app.com/login
$B snapshot -i            # @e1 = email, @e2 = password, @e3 = submit
$B fill @e2 "user@test.com"
$B fill @e3 "pass123"
$B click @e4
$B snapshot -i            # verify post-login state
```

### Pattern G2: Snapshot diff (before/after)
```bash
$B snapshot -D            # baseline stored
$B click @e3              # do something
$B snapshot -D            # unified diff against baseline
```

### Pattern G3: Handoff for CAPTCHA or complex auth
```bash
$B handoff "Stuck on CAPTCHA at login page"
```
Then present an AskUserQuestion telling the user a browser is open.
After they solve it: `$B resume` to re-snapshot and continue.

### Pattern G4: Headed browser with extension
```bash
$B connect               # launches visible Chromium with sidebar
$B disconnect            # back to headless mode
```

### Pattern G5: Full QA workflow (gstack)
```bash
$B goto https://app.com/login
$B snapshot -i -a -o /tmp/annotated.png   # annotated screenshot
$B console --errors                        # check JS errors
$B fill @e2 "user@test.com"
$B fill @e3 "pass123"
$B click @e4
$B snapshot -D                             # diff post-login state
$B is visible ".dashboard"
$B screenshot /tmp/dashboard.png
```

### Pattern G6: Multi-step with browser state
```bash
$B state save login_state     # save cookies + URL
$B state load login_state     # restore later
```

### Pattern G7: Page cleanup and responsive
```bash
$B cleanup --all              # remove ads, cookies, sticky
$B viewport 375x812           # mobile
$B screenshot /tmp/mobile.png
$B viewport 1280x720          # desktop
$B screenshot /tmp/desktop.png
```

## Advanced patterns (xd://browser)

Load the on-demand reference for snapshot diff, annotated screenshots,
CSS inspection, page cleanup, and URL content comparison:

```md
${CLAUDE_PLUGIN_ROOT}/skills/browse/references/advanced-patterns.md
```

## Reference: gstack browse → idev equivalent
| gstack browse | idev equivalent |
|---|---|
| `$B goto url` | `open` with `url` (xd://browser) or `$B goto` (gstack) |
| `$B snapshot -i` | `tab.ariaSnapshot()` / `$B snapshot -i` |
| `$B fill @e2 "v"` | `tab.fill('aria-ref=e2', 'v')` / `$B fill @e2 "v"` |
| `$B click @e3` | `tab.click('aria-ref=e3')` / `$B click @e3` |
| `$B screenshot` | `tab.screenshot()` / `$B screenshot` |
| `$B console` | `page.on('console',...)` in `run` / `$B console` |
| `$B handoff "msg"` | — (gstack binary only) |
| `$B connect` | — (gstack binary only) |
| `$B state save/load` | — (gstack binary only) |

## Gotchas
- **`tab.fill` does NOT work on `<select>`** — use `tab.select` instead.
- **Navigation invalidates refs** for both backends — re-snapshot after
  every `goto`.
- **`$B snapshot -i`** is an accessibility tree; `$B snapshot` alone opens
  GNOME Screenshot on some systems. Always pass `-i` or `-c`.
- **Handoff** requires a user to be present — don't use it in unattended
  runs.
- **xd://browser** screenshot path is returned, not passed.
- **Stalled actions fail fast** — don't add sleep/retry loops.

## When to use which
| Need | Tool |
|---|---|
| Quick headless verification | `browse` (xd://browser backend) |
| CAPTCHA / complex auth | `browse` (gstack browse backend with handoff) |
| Visible browser session | `browse` (gstack backend, `$B connect`) |
| Durable E2E test script | `browser-test` skill |
| Static content read | `read` tool (no browser needed) |
