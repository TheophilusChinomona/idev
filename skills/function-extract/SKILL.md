---
name: function-extract
description: Reads only the needed function from a large file (300+ lines) instead of the entire file, using grep/index line numbers. Use when one function is needed from a big file.
---

# Function Extract Skill

## Purpose
Read only the exact function/method body from a large file instead of the entire file. Reduces token usage when files are 500+ lines but you only need one function.

## Activation
When you need to read a specific function from a file that is known to be large (300+ lines), or when the function-index provides a line number.

---

## How It Works

Instead of reading an entire 800-line file, this skill:
1. Uses the function-index (from pattern caches) to get the start line
2. Reads a targeted range (start line - 5 context lines, to start line + estimated length)
3. If the function is longer than expected, extends the read

No cache needed — this is a technique, not a data store.

---

## Phase 1: Locate the Function

### Option A: From Function Index (fastest)
```
If the backend-patterns/cache.md or frontend-patterns/cache.md has a Function Index section:
  Look up: "FunctionName → L{N}"
  Read file from line N-5 to N+80 (typical function length)
```

### Option B: From Grep (when index doesn't have it)
```
Grep the file for the function signature:
  C#:     "public.*{FunctionName}\("
  TS/JS:  "const {FunctionName}|function {FunctionName}|{FunctionName} ="
  Python: "def {FunctionName}\("
  Java:   "public.*{FunctionName}\("
  Go:     "func.*{FunctionName}\("
  Ruby:   "def {FunctionName}"

The grep returns the line number → use that as start line
```

### Option C: From Class/Component Name (when function name unknown)
```
Grep for class/component declaration:
  C#:     "class {ClassName}"
  TS/JS:  "const {ComponentName}.*FC|function {ComponentName}"
  Python: "class {ClassName}"

Then read from that line with a larger range
```

---

## Phase 2: Smart Range Reading

### Estimating function length by language:

```
C# method:          ~30-80 lines (read start-5 to start+80)
TS/JS function:     ~20-60 lines (read start-5 to start+60)
React component:    ~50-200 lines (read start-5 to start+150)
Python function:    ~20-50 lines (read start-3 to start+50)
Java method:        ~30-80 lines (read start-5 to start+80)
Go function:        ~20-60 lines (read start-3 to start+60)
```

### If function is longer than estimate:
```
1. Check if the last line read contains a closing brace/end marker
2. If not, extend read by 50 more lines
3. Max 2 extensions (total max: estimate + 100 lines)
4. If still not complete, read the whole file (fallback)
```

---

## Phase 3: Detecting Function Boundaries

### Brace-based languages (C#, Java, TS/JS, Go, Rust):
```
Track brace depth:
  - Function signature line: depth starts at 0
  - Opening { : depth += 1
  - Closing } : depth -= 1
  - When depth returns to 0: function ends
```

### Indentation-based languages (Python, Ruby):
```
Track indentation:
  - Function def line: base indentation = N spaces
  - Lines with indentation > N: part of function
  - First line with indentation <= N (and not blank): function ends
```

---

## Phase 4: Usage Patterns

### Reading a specific backend method:
```
Need to read OrderService.CancelOrder
  1. Check function-index: "CancelOrder → L174"
  2. Read file from line 169 to line 250
  3. Got the full method in ~80 lines instead of reading 800-line file
  Token savings: ~720 lines saved
```

### Reading a specific frontend handler:
```
Need to read handleCancelOrder in OrdersPortalContainer
  1. Check function-index: "handleCancelOrder → L112"
  2. Read file from line 107 to line 140
  3. Got the handler in ~33 lines instead of reading 500-line file
  Token savings: ~470 lines saved
```

### Reading a specific hook:
```
Need to read useCancelOrder
  1. Grep orders.hook.ts for "useCancelOrder"
  2. Returns line 245
  3. Read from line 240 to line 270
  Token savings: ~300+ lines saved
```

---

## Integration with Other Skills

```
file-index → tells you WHICH file
function-index (in pattern caches) → tells you WHICH line
function-extract (this skill) → reads ONLY that function

Together: feature name → file path → line number → function body
Zero wasted tokens.
```

---

## Anti-Patterns

1. Do NOT read entire files when you only need one function
2. Do NOT guess line numbers — use function-index or grep
3. Do NOT read more than 200 lines in a single extract (if function is that big, read the whole file)
4. Do NOT use this for small files (<100 lines) — just read the whole file
5. Do NOT skip context lines (5 lines before function for imports/comments is useful)
