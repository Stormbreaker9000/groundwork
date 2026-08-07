---
id: ADR-001
type: adr
traces_from:
  - NFR-001
traces_to: {}
decision_status: accepted
---

# ADR-001: Single-writer database

## Context and Problem Statement

Whether the order store admits concurrent writers.

## Decision Drivers

- NFR-001
- CON-001

## Considered Options

- Single writer
- Multi-writer with optimistic locking

## Decision Outcome

Single writer. CON-001 resolves, but is absent from frontmatter traces_from.

### Consequences

- Good: no conflict-resolution path to get wrong.
