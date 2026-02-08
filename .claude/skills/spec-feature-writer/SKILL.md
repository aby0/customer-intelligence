---
name: spec-feature-writer
description: Draft feature specifications with user value, workflows, and acceptance criteria. Use when planning a new feature, documenting existing functionality, or when the user mentions feature specs.
license: MIT
metadata:
  author: znck
  version: "1.0"
---

# Feature Spec Writer

## When to Use

- User wants to create or update a feature spec
- Planning a new feature before implementation
- Documenting an existing feature

## Process

1. **Ask clarifying questions** about user value, workflows, edge cases
2. **Draft the spec** with acceptance criteria
3. **Iterate** based on feedback
4. **Save** to `spec/features/YYYY-MM-DD-<name>.md`

## Questions to Ask

**User Value:**
- Who is this for?
- What problem does it solve?

**How It Works:**
- Walk through a typical interaction
- What edge cases matter?

**Acceptance Criteria:**
- How do we know it's done?
- What must be included?

## Template

```markdown
# Feature: [Name]

**Date**: YYYY-MM-DD
**Status**: WIP | Active | Inactive
**Last updated**: YYYY-MM-DD

## User Value

[1 paragraph: Why does the user care?]

## How It Works

[2-3 paragraphs: User-centric description]

## Key Interactions

- **When [scenario]**: [behavior]
- **Edge case [X]**: [how handled]

## Acceptance Criteria

- [ ] User can [action]
- [ ] System [behavior]
- [ ] [Requirement]

## Related Features

- [Feature] — [relationship]

## Design Decisions

- **Why this approach?** [Rationale]

## Notes

- [Implementation hints]
```

## Tips

**User Value:**
- ❌ "Allow users to configure settings"
- ✅ "Users can adjust difficulty to match their level"

**Acceptance Criteria:**
- ❌ "Feature works"
- ✅ "User can adjust timer from 5–90 minutes"

**Keep it concise:**
- User Value: 1 paragraph
- How It Works: 2-3 paragraphs
- Acceptance Criteria: 5-8 items

## After Writing

1. Save to `spec/features/YYYY-MM-DD-<name>.md`
2. Update `spec/features/README.md`
3. Proceed to SPEC LOCK
