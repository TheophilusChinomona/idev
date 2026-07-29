---
description: Open an interactive browser QA session — navigate a URL, snapshot the page for interactive refs, verify state, and capture screenshot evidence. Uses xd://browser in the runtime, no Playwright install needed.
argument-hint: "<URL> [--viewport WxH] [--responsive]"
---

# /idev:browse

Run an interactive browser QA session using `xd://browser`.

Arguments: `$ARGUMENTS`

## Steps

1. If a URL is provided, use it; otherwise infer the target from the
   current session context (deployment URL, local dev server, or recently
   mentioned URL). Confirm in one line.
2. Open a tab: `xd://browser { "action": "open", "url": "<target>",
   "name": "main" }`. If `--viewport` is passed, include
   `"viewport": {"width": W, "height": H}`.
3. Snapshot: run `tab.ariaSnapshot()` for the accessibility tree with
   element refs (the `@eN` selectors).
4. Present the findings: page title, visible elements, any console errors
   (if captured), and the URL.
5. Offer to interact further: "I can fill forms, click elements, or take
   screenshots. What would you like to verify?"
