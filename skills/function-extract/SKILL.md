---
name: function-extract
description: "Reads only the needed function from a large file (300+ lines) instead of the entire file, using grep/index line numbers. Use when one function is needed from a big file."
---

# Function Extract Skill

## Purpose
Read only the exact function/method body from a large file instead of the entire file. Reduces token usage when files are 300+ lines but you only need one function. This is a technique, not a data store — no cache needed.

---

## Technique

Core idea: find the function's start line, then Read with offset/limit instead of reading the whole file.

### Option A: Function Index (fastest)
```
If .claude/idev/backend-patterns/cache.md or frontend-patterns/cache.md has a
"Function Index" section (functionName — file:line — purpose):
  1. Look up the function's file and line number
  2. Read from line N-5 (context) with a limit of ~80 lines
```

### Option B: Grep for the signature
```
Grep the file for the function signature, e.g.:
  C#/Java: "public.*{FunctionName}\("
  TS/JS:   "const {FunctionName}|function {FunctionName}|{FunctionName} ="
  Python:  "def {FunctionName}\("
  Go:      "func.*{FunctionName}\("
  Ruby:    "def {FunctionName}"

Use the returned line number as the start, then Read with offset/limit
(start-5, limit ~80; larger for React components).
```

If the read window doesn't reach the end of the function (no closing brace / dedent), extend the read by ~50 lines, at most twice. If still incomplete, fall back to reading the whole file.

---

## Anti-Patterns

1. Do NOT read entire files when you only need one function
2. Do NOT guess line numbers — use the Function Index or grep
3. Do NOT read more than ~200 lines in a single extract (if the function is that big, read the whole file)
4. Do NOT use this for small files (<100 lines) — just read the whole file
5. Do NOT skip the few context lines before the function (imports/comments are useful)
