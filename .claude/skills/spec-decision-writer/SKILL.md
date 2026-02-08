---
name: spec-decision-writer
description: Document architectural decisions with rationale, alternatives, and user impact. Use when explaining why things are done a certain way, capturing technical choices, or when the user mentions ADRs or decision records.
license: MIT
metadata:
  author: znck
  version: "1.0"
---

# Decision Record Writer

## When to Use

- Documenting an architectural choice
- Explaining "why we do things this way"
- Capturing decisions before or after implementation

## Process

1. **Identify** what was decided and why
2. **Document** alternatives considered
3. **Explain** user impact
4. **Save** to `spec/decision-records/YYYY-MM-DD-<name>.md`

## Questions to Ask

**The Decision:**
- What problem required this decision?
- What alternatives were considered?
- Why this approach?

**User Impact:**
- Does the user see this choice?
- What would break if reversed?

**Implementation:**
- How should this be implemented?
- What are the constraints?

## Template

```markdown
# Decision: [Topic]

**Date**: YYYY-MM-DD
**Status**: Active | Superseded
**Domain**: [e.g., Storage, Auth, Performance]

## The Question

[What needed to be decided? 1-2 sentences]

## Decision

[What was decided? 1-2 sentences, plain language]

## Rationale

[Why this approach? Focus on user benefit. 2-4 paragraphs]

## User Impact

[How does this affect users? Be concrete.]

## Implementation Notes

- [High-level guidance]

## Constraints

- [Constraint that influenced decision]

## Alternatives Considered

- **[Alternative]**: [Pros, cons, why rejected]

## Related Decisions

- [Decision] — [relationship]

## Timeline

- **YYYY-MM-DD**: Decision made
```

## Tips

**The Question:**
- ❌ "Use IndexedDB"
- ✅ "Where should session data be stored?"

**Rationale:**
- ❌ "IndexedDB is fast"
- ✅ "Users want privacy and offline access"

**Include:**
- Choices spanning multiple features
- Rationale for this approach over alternatives
- User impact (even if indirect)

**Exclude:**
- Low-level implementation details
- Code style decisions
- Internal process decisions

## Superseding

When overturning a decision:
1. Mark old decision `Status: Superseded`
2. Add timeline entry with reason
3. Create new decision record
4. Link back to old one

## After Writing

1. Save to `spec/decision-records/YYYY-MM-DD-<name>.md`
2. Update `spec/decision-records/README.md`
3. Link from related features/decisions
