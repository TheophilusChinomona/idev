---
name: coding-standards
description: "Security-focused code review standards. Use when reviewing code for security issues, or when writing code that handles user input, authentication, secrets, file uploads, or database queries."
---

# Coding Standards: Security Review

## Scope

This skill covers security checks only. Style and structure conventions come from the project's own detected patterns — defer to the backend-patterns cache (`.claude/idev/backend-patterns/cache.md`) and frontend-patterns cache (`.claude/idev/frontend-patterns/cache.md`), not from this skill. Detect and follow project conventions; do not impose generic ones.

---

## Security Checks

Run these checks when writing or reviewing code that touches user input, auth, secrets, files, or data stores. Wording is stack-agnostic — apply the equivalent in the project's language/framework.

### 1. Injection (SQL, NoSQL, command, XSS)
- Never interpolate user input into queries — use parameterized queries, prepared statements, or the ORM's safe query API
- Never pass user input to a shell — use exec APIs that take an argument array, and whitelist allowed commands
- Never render user content as raw HTML — use text-content APIs, or sanitize with a vetted library before rendering
- Treat template/eval-style APIs fed by user input as injection sinks

### 2. Authentication & authorization
- Protected routes must enforce authentication; sensitive operations must also check authorization (role/ownership) server-side
- Compare passwords only against salted hashes (bcrypt/argon2-class), never plain text
- Verify tokens with secrets from configuration/environment, never hardcoded
- Prefer httpOnly cookies over script-accessible storage for session tokens
- Check object-level access: a valid user must not be able to read or mutate another user's records by changing an ID (IDOR)

### 3. Secrets handling
- No hardcoded API keys, passwords, connection strings, or tokens in source — load from environment or a secrets store
- Never log secrets or tokens; redact sensitive fields in structured logs
- Do not return password hashes, tokens, or internal identifiers in API responses — select response fields explicitly

### 4. Input validation at boundaries
- Validate all external input (request bodies, query params, headers, file uploads, webhook payloads) at the boundary, before business logic
- Validate type, range, length, and format; reject rather than coerce on failure
- File uploads: validate content type and size, strip path components from filenames, and resolve the final path to confirm it stays inside the intended directory (path traversal)
- Avoid deserialization modes that instantiate arbitrary types from input

### 5. Error-message and data leakage
- Error responses to clients must not expose stack traces, internal paths, query text, or framework internals — log details server-side, return a generic message
- CORS: restrict to known origins; never wildcard with credentials
- State-changing endpoints need CSRF protection when cookie-authenticated

---

## Security Alert Format

When a security issue is found, report it like this:

```
SECURITY ALERT: [Vulnerability Type]
Location: [file:line]
Severity: CRITICAL | HIGH | MEDIUM | LOW
Issue: [brief description]
Risk: [what could happen if exploited]
Fix: [how to fix it]
```

Alert before writing the fix, so the user understands the risk even if they decline the change.

---

## Security Checklist

Before completing work that touches input, auth, secrets, files, or queries:

- [ ] No hardcoded secrets, keys, or passwords
- [ ] All external input validated at the boundary
- [ ] Queries parameterized; no string-built SQL/commands
- [ ] No raw HTML rendering of user content (or sanitized)
- [ ] Authentication enforced on protected routes
- [ ] Authorization (role/ownership) checked before data access
- [ ] Sensitive data absent from logs and responses
- [ ] File uploads validated (type, size, name, resolved path)
- [ ] Error messages do not leak internals
- [ ] CORS/CSRF configured for the project's auth model
