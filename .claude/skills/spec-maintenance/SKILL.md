---
name: spec-maintenance
description: Update spec indices, activate features, and maintain spec files. Use when activating completed features, deprecating old ones, or updating the spec index files.
license: MIT
metadata:
  author: znck
  version: "1.0"
---

# Spec Maintenance

## When to Use

- Activating a completed feature (WIP → Active)
- Adding/removing features or decisions from indices
- Updating recent changes
- Deprecating a feature (Active → Inactive)

## Files to Keep in Sync

| File | Contains |
|------|----------|
| `spec/README.md` | Product overview, recent changes |
| `spec/features/README.md` | Feature index (WIP, Active, Inactive) |
| `spec/decision-records/README.md` | Decision index (Active, Superseded) |

## Common Tasks

### Activate Feature (WIP → Active)

1. Update feature file: `Status: Active`
2. Check all acceptance criteria boxes
3. Move from WIP to Active in `spec/features/README.md`
4. Add to Recent Changes in `spec/README.md`

### Add New Feature/Decision

1. Add to appropriate index table
2. Add to Recent Changes

### Deprecate Feature (Active → Inactive)

1. Update feature file: `Status: Inactive`
2. Append deprecation reason (no other edits)
3. Move to Inactive in `spec/features/README.md`
4. Add to Recent Changes

### Supersede Decision

1. Mark old decision: `Status: Superseded`
2. Add timeline entry with reason
3. Create new decision record
4. Move old to Superseded in index
5. Add to Recent Changes

## Recent Changes Format

```markdown
## Recent Changes

- **YYYY-MM-DD** [What changed](./path/to/spec.md)
```

Keep 5-10 entries, newest first. Older changes live in git history.

## Index Formats

### `spec/features/README.md`

```markdown
# Features

## WIP

| Feature | Started | Detail |
|---------|---------|--------|
| [Name](YYYY-MM-DD-<name>.md) | YYYY-MM-DD | Summary |

## Active

| Feature | Started | Detail |
|---------|---------|--------|
| [Name](YYYY-MM-DD-<name>.md) | YYYY-MM-DD | Summary |

## Inactive

| Feature | Detail |
|---------|--------|
| [Name](YYYY-MM-DD-<name>.md) | Reason |
```

### `spec/decision-records/README.md`

```markdown
# Decision Records

## Active

| Decision | Domain | Date | Detail |
|----------|--------|------|--------|
| [Topic](YYYY-MM-DD-<name>.md) | Domain | YYYY-MM-DD | Summary |

## Superseded

| Decision | Superseded By |
|----------|---------------|
| [Topic](YYYY-MM-DD-<name>.md) | [New](YYYY-MM-DD-<name>.md) |
```

## Rules

- Keep indices synchronized with spec files
- Use relative links
- Brief recent changes (one line per entry)
- Status values: `WIP`, `Active`, `Inactive`, `Superseded`

## When to Update

**Update for:**
- Feature launched
- Feature deprecated
- Decision made or superseded

**Don't update for:**
- Code changes
- Bug fixes
- Refactoring

Specs track product evolution, not implementation details.
