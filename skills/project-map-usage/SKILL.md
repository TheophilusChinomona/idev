---
name: project-map-usage
description: Policy for using the generated project map as primary context: Grep relevant sections on demand, never load the full map. Load whenever the project map exists and context is being gathered.
---

# Persistent Claude Instructions: Project Map Usage

## Core Directive

**ALWAYS reference `project-map.md` as the primary context for every user prompt.**

This file contains the authoritative project structure, module locations, key patterns, and architectural decisions. Use it to:

1. **Answer questions** about project structure, file locations, or architecture
2. **Navigate the codebase** efficiently without reading full source files
3. **Understand relationships** between modules and components
4. **Apply correct patterns** when making code changes

## Automatic Context Loading

For every user prompt, follow this workflow:

### Step 1: Check Project Map First
Before reading any source files, consult `project-map.md` to:
- Locate relevant modules and files
- Understand the architectural layer involved
- Identify related components and patterns
- Check for known gotchas or important conventions

### Step 2: Use Module Summaries
The project map contains module-level summaries. Use these to:
- Answer high-level questions without reading code
- Identify the correct service/component to modify
- Understand data flow and dependencies

### Step 3: Read Source Files Only When Necessary
Only read actual source files when:
- The user asks for specific code details
- You need to see implementation to answer a question
- You're making code changes and need exact syntax
- The project map doesn't contain sufficient detail

### Step 4: Apply Known Patterns
The project map documents this project's critical patterns (e.g., entity tracking
conventions, soft delete approach, error logging service, required default values).

Apply these patterns automatically when relevant.

## Token Usage Optimization

**Minimize token consumption** by:
1. Referencing project map summaries instead of full file reads
2. Using Grep/Glob to locate specific code, not full file reads
3. Reading only the specific sections of large files (use offset/limit)
4. Citing module locations from the map: "Check `CourseCreationService` in the Course Creation module"

## Example Interactions

### ❌ Wrong Approach (High Token Usage)
```
User: "How does authentication work?"
Claude: [Reads Program.cs, reads Cookie.cs, reads AppDbContext.cs...]
```

### ✅ Right Approach (Low Token Usage)
```
User: "How does authentication work?"
Claude: [Checks project-map.md → Authentication section]
Response: "Authentication uses <framework auth> with <secret store>.
Flow is in <entry point> with cookie/token-based auth via <auth service>.
Details in the Authentication module of the project map."
```

### ❌ Wrong Approach (Unnecessary File Read)
```
User: "Where is the quiz editing UI?"
Claude: [Reads multiple .razor files to find it...]
```

### ✅ Right Approach (Project Map Reference)
```
User: "Where is the order editing UI?"
Claude: [Checks project-map.md → Orders module]
Response: "OrderEditorDialog at <path from project map>"
```

### ✅ Good Use of Source Files
```
User: "Show me the exact code for updating an order"
Claude: [Checks project-map.md for location → Then reads the specific method only]
```

## Critical Patterns to Apply Automatically

The project map's "patterns" section documents this project's conventions —
e.g., how entities are updated (tracked vs explicit update calls), whether
deletes are soft or hard, which error logging service to use, and any required
default values. When making code changes that touch one of these areas, apply
the documented pattern automatically instead of inventing a new approach.

## When to Update Project Map

Suggest updating `project-map.md` when:
- New major features are added
- Architectural patterns change
- New modules/services are created
- File structure is reorganized
- Important conventions are established

## Remember

🎯 **Project map is your first stop, source code is your second stop**

🎯 **Use summaries over full reads**

🎯 **Apply documented patterns automatically**

🎯 **Minimize token usage while maximizing accuracy**
