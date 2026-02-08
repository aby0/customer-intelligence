---
name: spec-e2e-test-generator
description: Generate E2E tests from feature spec acceptance criteria. Use when creating tests for a feature, validating acceptance criteria, or when the user mentions test generation from specs.
license: MIT
metadata:
  author: znck
  version: "1.0"
---

# E2E Test Generator

## When to Use

- Generate tests for a feature spec
- Validate acceptance criteria with automated tests
- Keep tests in sync with specs

## Core Principle

**Tests come from specs.** Each acceptance criterion should have a corresponding test.

## Process

1. **Read** the feature spec's acceptance criteria
2. **Map** each criterion to a test scenario
3. **Generate** tests using project's test framework
4. **Run** tests to verify implementation

## Mapping Criteria to Tests

For each acceptance criterion:

| Criterion | Test |
|-----------|------|
| `[ ] User can [action]` | `test('user can [action]')` |
| `[ ] System [behavior]` | `test('system [behavior]')` |

## Test Structure

```javascript
describe('Feature: [Name]', () => {
  beforeEach(async () => {
    // Setup
  });

  test('[criterion from spec]', async () => {
    // Arrange
    // Act
    // Assert
  });
});
```

## Principles

**One test per criterion:**
```javascript
// Spec: [ ] User can adjust timer from 5–90 minutes
test('user can adjust timer from 5 to 90 minutes', async () => {
  // ...
});
```

**Test names match spec language:**
- Spec says "User can pause and resume"
- Test named "user can pause and resume"

**Test user value, not implementation:**
- ❌ `test('component state updates')`
- ✅ `test('user sees updated value')`

**Edge cases get additional tests:**
- Spec mentions edge case in Key Interactions
- Create separate test for that edge case

## Mocking

**Mock:**
- External APIs
- Device APIs (speech, audio)
- Long-running operations

**Don't mock:**
- UI interactions
- Local state
- Core business logic

## Test Maintenance

When spec changes:
- Criterion added → Add test
- Criterion modified → Update test
- Criterion removed → Remove test

## Framework Examples

### Playwright

```javascript
test('user can [action]', async ({ page }) => {
  await page.goto('/feature');
  await page.click('[data-testid="button"]');
  await expect(page.locator('[data-testid="result"]')).toBeVisible();
});
```

### Cypress

```javascript
it('user can [action]', () => {
  cy.visit('/feature');
  cy.get('[data-testid="button"]').click();
  cy.get('[data-testid="result"]').should('be.visible');
});
```

## Summary

✅ Tests come from specs
✅ One test per criterion
✅ Test names match spec language
✅ Tests validate user value
✅ Tests stay in sync with specs
