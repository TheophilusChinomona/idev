---
name: auto-approve-policy
description: Operation safety policy: file/cache adds and updates are auto-approved, deletions and destructive operations never are. Load when deciding whether an operation needs user confirmation or when configuring auto-approval.
---

# Auto-Approve Policy

## Command: Auto-Approve Add or Update

**Status**: ACTIVE for all Claude Code sessions

### Purpose
Claude is allowed to automatically add or update code/text/project content without asking for confirmation. Claude must **never delete** any existing content unless explicitly instructed by the user. This ensures safety while still allowing automated workflow.

### Instructions for Claude

#### 1. Automatic Actions (No Confirmation Needed)
For any action that **adds or updates** content:
- ✅ Automatically assume "yes" and proceed
- ✅ Provide the updated or added code/text in full
- ✅ Apply changes immediately when requested

#### 2. Protected Actions (Always Require Confirmation)
For any action that would **delete existing content**:
- ❌ **Do not delete anything** without explicit user confirmation
- ✅ Instead, suggest alternatives:
  - Comment it out
  - Mark as `[Obsolete]` or deprecated
  - Rename with "Legacy" or "Deprecated" prefix
  - Document why it should be removed
- ⚠️ Always ask the user for explicit confirmation before performing deletion
- 📝 Wait for clear "yes, delete" instruction

#### 3. Session Behavior
- Do not ask the user to confirm additions or updates — these are automatically allowed
- Maintain this behavior throughout the session unless explicitly disabled by the user
- Prioritize safety: preserve all existing content; automatic yes only applies to additions or modifications

### Allowed Automatic Operations

✅ **Code Additions**
- Create new classes, methods, properties
- Add new files and components
- Implement new features
- Add error handling and logging
- Insert new configuration entries

✅ **Code Updates**
- Refactor existing code
- Fix bugs and issues
- Rename variables, methods, classes
- Update logic and algorithms
- Modify configurations
- Apply documented patterns
- Change property values
- Update method signatures

✅ **Safe Alternatives to Deletion**
- Comment out unused code
- Add `[Obsolete("Reason", error: false)]` attributes
- Rename to `LegacyClassName` or `DeprecatedMethod`
- Move to a "Deprecated" folder
- Document with comments explaining why it's obsolete

### Prohibited Automatic Operations

❌ **Never Auto-Delete**
- Files or folders
- Methods or classes
- Database migrations
- Configuration entries
- Code blocks or sections
- Comments or documentation

❌ **Never Auto-Execute Destructive Commands**
- `git push --force`
- `rm -rf` or file deletion commands
- Database drop operations
- Hard resets

### Example Workflows

#### Example 1: Automatic Update ✅
```
User: "Refactor UserService methods to follow async naming conventions."
Claude: [Automatically updates method names like GetUser → GetUserAsync]
Claude: "Updated all UserService methods to async naming conventions:
- GetUser → GetUserAsync
- SaveUser → SaveUserAsync
- DeleteUser → DeleteUserAsync"
```

#### Example 2: Automatic Addition ✅
```
User: "Add input validation to the CreateCourse method"
Claude: [Automatically adds validation code]
Claude: "Added validation to CreateCourse:
- Null checks for courseDto
- Title length validation (1-200 chars)
- Category ID existence check"
```

#### Example 3: Deletion Request → Suggest Alternative ⚠️
```
User: "Remove obsolete helper functions from Utilities.cs."
Claude: "I can comment them out and mark as [Obsolete] instead of deleting:

[Obsolete("This method is deprecated. Use NewHelperMethod instead.", error: false)]
// Old implementation commented out below
// public static void OldHelper() { ... }

To permanently delete them, please confirm: 'yes, delete the obsolete helpers'"
```

#### Example 4: User Confirms Deletion ✅
```
User: "yes, delete the obsolete helpers"
Claude: [Proceeds with deletion]
Claude: "Deleted 3 obsolete helper methods from Utilities.cs:
- OldHelper
- LegacyFormatter
- DeprecatedValidator"
```

### Integration with Other Commands

This policy works in conjunction with:
- **Project Map** (`.claude/idev/project-map/project.map.md`) - Context for where to make changes
- **Instructions** (`CLAUDE.md`) - Patterns to apply automatically
- **Settings** (`.claude/idev/project-config.json`) - Conventions to follow

### Workflow Integration

```
1. User makes request
   ↓
2. Check project-map.md for context
   ↓
3. Identify if action is add/update or delete
   ↓
4. If add/update: Execute immediately
   If delete: Suggest alternatives, wait for confirmation
   ↓
5. Apply documented patterns from instructions.md
   ↓
6. Provide clear summary of changes made
```

### Safety Guarantees

🛡️ **This policy ensures**:
- No accidental deletions
- Fast execution for safe operations
- User maintains control over destructive actions
- Existing code is always preserved unless explicitly confirmed
- Reversible changes are automatic, irreversible changes require confirmation

### Disabling This Policy

To disable auto-approve for the current session, user can say:
- "Disable auto-approve"
- "Ask before making changes"
- "Require confirmation for all changes"

### Policy Active

**This policy is ACTIVE by default for all Claude Code sessions working with this repository.**
