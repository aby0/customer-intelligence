# Specification-Driven Development

**Specs precede code.** For significant changes, write a spec first, get approval, then implement.

---

## When to Use

**Use spec-driven development for:**
- New user-facing functionality
- Behavior changes users will notice
- Architectural decisions
- Multi-component changes
- Ambiguous requirements

**Skip for:** bug fixes, small tweaks, docs—but flag if scope creep makes it significant.

---

## Skills

| Skill | Purpose |
|-------|---------|
| `/spec-feature-writer` | Draft feature specs |
| `/spec-decision-writer` | Document architectural decisions |
| `/spec-e2e-test-generator` | Generate tests from acceptance criteria |
| `/spec-maintenance` | Update indices, activate features |

---

## Workflow

### 1. Draft

Use `/spec-feature-writer` or `/spec-decision-writer`:
1. Ask clarifying questions about user value, workflows, edge cases
2. Draft spec with acceptance criteria
3. Iterate based on feedback
4. Save to `spec/features/` or `spec/decision-records/`

### 2. Lock

Summarize acceptance criteria, confirm with user, then proceed.

### 3. Implement

Build code satisfying **all acceptance criteria**—nothing more, nothing less.

Flag ambiguities immediately:
```
SPEC CLARIFICATION NEEDED
[Quote ambiguous part]
Interpretations: 1) ... 2) ...
Which is correct?
```

### 4. Test

Use `/spec-e2e-test-generator`:
- One test per criterion
- Test names match spec language

### 5. Activate

When tests pass, confirm with user, then use `/spec-maintenance` to:
1. Check acceptance criteria boxes
2. Update status: `WIP` → `Active`
3. Update indices

---

## Spec States

| State | Editable | Notes |
|-------|----------|-------|
| **WIP** | ✅ | Edit freely |
| **Active** | ❌ | Create new spec to change behavior |
| **Inactive** | ❌ | Can only append deprecation reason |

---

## Key Rules

- Implement acceptance criteria exactly
- Flag ambiguities: `SPEC CLARIFICATION NEEDED`
- Flag conflicts: `DESIGN CONFLICT DETECTED`
- Only WIP specs can be edited
- Code reviews are against acceptance criteria, not style/efficiency

---

## Spec Structure

**`spec/README.md`** — Product overview, workflows, constraints, links to features/decisions

**`spec/features/YYYY-MM-DD-<name>.md`** — User Value, How It Works, Key Interactions, Acceptance Criteria, Related Features, Design Decisions

**`spec/decision-records/YYYY-MM-DD-<name>.md`** — The Question, Decision, Rationale, User Impact, Implementation Notes, Alternatives

---

## Summary

1. Draft spec → 2. Lock → 3. Implement → 4. Test → 5. Activate

Trust the spec.
