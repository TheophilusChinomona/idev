---
name: tdd-workflow
description: "Test-driven development workflow: write failing test, implement to pass, refactor. Use when starting a new feature or bugfix that needs tests first."
---

# TDD Workflow Skill

## Purpose
Enforce test-driven development: RED → GREEN → REFACTOR.

## Activation
- User says "let's do TDD" or "write tests first"
- Starting a new feature
- Fixing a bug (write test that reproduces it)

## Workflow

### RED — Write Failing Test
1. Understand the requirement
2. Write a test that describes expected behavior
3. Run the test — it MUST fail
4. If it passes, the test is wrong — fix the test

### GREEN — Make It Pass
1. Write the MINIMUM code to make the test pass
2. Run the test — it MUST pass
3. Do NOT write extra code yet

### REFACTOR — Improve
1. Clean up the code
2. Run tests again — they MUST still pass
3. Repeat until satisfied

## Example

```typescript
// RED: Write a failing test first
describe('UserService', () => {
  it('should hash passwords on create', async () => {
    const user = await createUser({ password: 'secret123' })
    expect(user.passwordHash).not.toBe('secret123')
    expect(user.passwordHash).toMatch(/^\$2[abyb]\$.{56}$/) // bcrypt
  })
})

// GREEN: Write minimal implementation
async function createUser(data: { password: string }) {
  const passwordHash = await bcrypt.hash(data.password, 12)
  return db.user.create({ ...data, passwordHash })
}
```

## Integration
- Use build-check after implementation
- Use test-coverage to verify coverage
- Log lessons if TDD revealed a gotcha

## Anti-Patterns
1. Do NOT skip the RED phase — verify the test fails first
2. Do NOT write more code than needed to pass the test
3. Do NOT refactor while tests are failing
4. Do NOT write tests after implementation (that's verification, not TDD)
